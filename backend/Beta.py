# elli_assistant.py
# Требования: pip install sounddevice vosk ollama torch numpy fastapi uvicorn
# (fastapi/uvicorn нужны только если хочешь запускать HTTP API)

import os
import json
from pyexpat import model
import queue
import time
import threading
import numpy as np
import sounddevice as sd
import torch
from vosk import Model, KaldiRecognizer

# Попытка загрузить лёгкую локальную LLM через GPT4All (без сборки)
try:
    from gpt4all import GPT4All
except Exception:
    GPT4All = None

# ========== Настройки ==========
SAMPLE_RATE =18000           # рекомендую 16000 для Vosk/воспроизведения
TIMEOUT_SEC = 10
MODEL_PATH = os.path.join(os.path.dirname(__file__), "vosk-model-small-ru-0.22")
ASSISTANT_NAME = "Элли"
SPEAKER = "kseniya_v2"       # или другой доступный голос Silero

# Путь к локальной GGUF-модели
GGUF_PATH = os.path.join(os.path.dirname(__file__), "qwen2.5-1.5b-instruct-q4_k_m.gguf")

# ========== Устройство для PyTorch ==========
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Torch device:", DEVICE)

# ========== Загрузка моделей (единоразово) ==========
# 1) Silero TTS
silero_tts = None
try:
    print("Загружаю Silero TTS (может занять время)...")

    silero_tts, example_text = torch.hub.load(
        repo_or_dir='snakers4/silero-models',
        model='silero_tts',
        language='ru',
        speaker=SPEAKER,
        verbose=False
    )
    # перенести на device (если модель поддерживает .to)
    try:
        silero_tts.to(DEVICE)
    except Exception:
        # иногда hub возвращает не обычный nn.Module; игнорируем если .to не сработал
        pass
    print("Silero TTS загружена.")
except Exception as e:
    print("Не удалось загрузить Silero TTS:", e)
    tts_model = None

# 2) Vosk ASR
try:
    print("Загружаю Vosk модель...")
    vosk_model = Model(MODEL_PATH)
    print("Vosk модель загружена.")
except Exception as e:
    print("Ошибка загрузки Vosk:", e)
    raise

# 1.5) Опциональная LLM через GPT4All
llm = None
if GPT4All is not None and os.path.exists(GGUF_PATH):
    try:
        print("Загружаю локальную LLM (GPT4All)...")
        llm = GPT4All(os.path.basename(GGUF_PATH), model_path=os.path.dirname(GGUF_PATH))
        print("Локальная LLM загружена.")
    except Exception as e:
        print("Не удалось загрузить локальную LLM:", e)
        llm = None

# ========== Функции ==========
def speak(text: str):
    if not text.strip() or silero_tts is None:
        return

    try:
        if hasattr(silero_tts, "speakers"):
            audio = silero_tts.apply_tts([text], speaker="xenia", sample_rate=SAMPLE_RATE)
        else:
            audio = silero_tts.apply_tts([text], sample_rate=SAMPLE_RATE)

        # Преобразуем в правильный формат (N, 1)
        import numpy as np
        audio = np.array(audio).reshape(-1, 1)

        sd.play(audio, samplerate=SAMPLE_RATE)
        sd.wait()
    except Exception as e:
        print("Ошибка генерации TTS:", e)

        return

    # apply_tts часто возвращает список аудио; берём первый элемент
    arr = audio[0] if isinstance(audio, (list, tuple)) else audio
    arr = np.asarray(arr, dtype=np.float32)

    def _play(a):
        try:
            sd.play(a, samplerate=SAMPLE_RATE)
            sd.wait()
        except Exception as e:
            print("Ошибка воспроизведения:", e)

    threading.Thread(target=_play, args=(arr,), daemon=True).start()

def transcribe_once(timeout: int = TIMEOUT_SEC) -> str:
    """
    Слушает с микрофона до первого распознанного предложения или таймаута.
    Возвращает транскрипт (str) или пустую строку.
    """
    rec = KaldiRecognizer(vosk_model, SAMPLE_RATE)
    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print("Audio status:", status)
        # RawInputStream отдаёт уже байты при dtype='int16', поэтому безопасно взять bytes(indata)
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16', channels=1, callback=callback):
        print(f"Говорите (макс {timeout} сек)...")
        start = time.time()
        while True:
            try:
                data = q.get(timeout=0.1)
            except queue.Empty:
                data = None

            if data:
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    text = res.get("text", "")
                    if text.strip():
                        return text
                else:
                    # можно обработать partial через rec.PartialResult(), если хочется показать промежуточно
                    pass

            if time.time() - start > timeout:
                # возьмём финальную часть (если что-то осталось)
                try:
                    final = json.loads(rec.FinalResult())
                    return final.get("text", "") or ""
                except Exception:
                    return ""

def generate_response(user_text: str) -> str:
    """Сначала пробуем локальную LLM (если доступна), иначе офлайн-правила."""
    text = (user_text or "").strip()
    if not text:
        return "Я не расслышала — повтори, пожалуйста."

    if llm is not None:
        try:
            prompt = (
                f"Ты помощник по имени {ASSISTANT_NAME}. Отвечай кратко на русском.\n"
                f"Вопрос: {text}\nОтвет:"
            )
            with llm.chat_session():
                resp = llm.generate(prompt, max_tokens=256, temp=0.6)
            if isinstance(resp, str) and resp.strip():
                return resp.strip()
        except Exception as e:
            print("Ошибка локальной LLM:", e)

    # fallback: простые правила
    lower = text.lower()
    if any(x in lower for x in ["как тебя зовут", "твоё имя", "твое имя", "кто ты"]):
        return "Меня зовут Элли. Чем могу помочь?"
    if any(x in lower for x in ["привет", "здравств", "добрый"]):
        return "Привет! Я слушаю."
    if any(x in lower for x in ["пока", "до свид", "увидимс"]):
        return "Пока!"

    return f"Ты сказал: {text}"

# ========== Главный цикл (CLI) ==========
if __name__ == "__main__":
    print(f"{ASSISTANT_NAME} запущена. Говорите что-нибудь (Ctrl+C чтобы выйти).")
    try:
        while True:
            user_text = transcribe_once()
            print("Вы сказали:", user_text)
            if not user_text:
                # можно проиграть короткое уведомление
                continue
            reply = generate_response(user_text)
            print(f"{ASSISTANT_NAME}: {reply}")
            speak(reply)
    except KeyboardInterrupt:
        print("Выход по Ctrl+C. Пока!")
