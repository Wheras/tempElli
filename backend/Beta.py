# elli_assistant.py
# Требования: pip install torch vosk sounddevice numpy gpt4all

import os
import threading
import numpy as np
import sounddevice as sd
import torch
from vosk import Model, KaldiRecognizer

try:
    from gpt4all import GPT4All
except Exception:
    GPT4All = None

# ================== Настройки ==================
SAMPLE_RATE = 16000
MODEL_PATH = os.path.join(os.path.dirname(__file__), "vosk-model-small-ru-0.22")
ASSISTANT_NAME = "Элли"
SPEAKER = "kseniya_v2"
GGUF_PATH = os.path.join(os.path.dirname(__file__), "qwen2.5-1.5b-instruct-q4_k_m.gguf")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Torch device:", DEVICE)

# ================== Загрузка моделей ==================
# Silero TTS
silero_tts = None
try:
    print("Загружаю Silero TTS (может занять время)...")
    silero_tts = torch.hub.load(
        repo_or_dir="snakers4/silero-models",
        model="silero_tts",
        language="ru",
        speaker=SPEAKER,
        verbose=False
    )
    try:
        silero_tts.to(DEVICE)
    except Exception:
        pass
    print("Silero TTS загружена.")
except Exception as e:
    print("❌ Не удалось загрузить Silero TTS:", e)
    silero_tts = None

# Vosk ASR
try:
    print("Загружаю Vosk модель...")
    vosk_model = Model(MODEL_PATH)
    print("Vosk модель загружена.")
except Exception as e:
    print("❌ Ошибка загрузки Vosk:", e)
    vosk_model = None

# GPT4All LLM (опционально)
llm = None
if GPT4All is not None and os.path.exists(GGUF_PATH):
    try:
        print("Загружаю локальную LLM (GPT4All)...")
        llm = GPT4All(os.path.basename(GGUF_PATH), model_path=os.path.dirname(GGUF_PATH))
        print("Локальная LLM загружена.")
    except Exception as e:
        print("❌ Не удалось загрузить локальную LLM:", e)

# ================== Функции ==================
def speak(text: str):
    """Озвучивает текст при помощи Silero TTS."""
    if not text.strip() or silero_tts is None:
        return
    try:
        audio = silero_tts.apply_tts([text], speaker="xenia", sample_rate=SAMPLE_RATE)
        audio = np.array(audio).reshape(-1, 1)
        sd.play(audio, samplerate=SAMPLE_RATE)
        sd.wait()
    except Exception as e:
        print("Ошибка TTS:", e)


def transcribe_from_file(audio_path: str) -> str:
    """Распознаёт речь из аудиофайла (для API)."""
    import wave, json

    if vosk_model is None:
        return ""

    wf = wave.open(audio_path, "rb")
    rec = KaldiRecognizer(vosk_model, wf.getframerate())

    text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text += result.get("text", "") + " "
    result = json.loads(rec.FinalResult())
    text += result.get("text", "")
    return text.strip()


def generate_response(user_text: str) -> str:
    """Генерация ответа (LLM или fallback)."""
    text = (user_text or "").strip()
    if not text:
        return "Я не расслышала — повтори, пожалуйста."

    # GPT4All
    if llm is not None:
        try:
            prompt = (
                f"Ты помощник по имени {ASSISTANT_NAME}. Отвечай кратко и дружелюбно.\n"
                f"Вопрос: {text}\nОтвет:"
            )
            with llm.chat_session():
                resp = llm.generate(prompt, max_tokens=256, temp=0.6)
            if isinstance(resp, str) and resp.strip():
                return resp.strip()
        except Exception as e:
            print("Ошибка локальной LLM:", e)

    # Простой fallback
    lower = text.lower()
    if any(x in lower for x in ["как тебя зовут", "твое имя", "твоё имя", "кто ты"]):
        return "Меня зовут Элли. Чем могу помочь?"
    if any(x in lower for x in ["привет", "здравств", "добрый"]):
        return "Привет! Я слушаю."
    if any(x in lower for x in ["пока", "до свид", "увидимс"]):
        return "Пока!"

    return f"Ты сказал: {text}"
