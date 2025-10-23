# websocket_server.py
import os
import json
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ================== Настройки ==================
SAMPLE_RATE = 16000
MODEL_PATH = os.path.join(os.path.dirname(__file__), "vosk-model-small-ru-0.22")
ASSISTANT_NAME = "Элли"
SPEAKER = "kseniya_v2"
GGUF_PATH = os.path.join(os.path.dirname(__file__), "qwen2.5-1.5b-instruct-q4_k_m.gguf")

# ================== Импорт моделей ==================
print("🔄 Загружаю AI модели...")

# Vosk
try:
    from vosk import Model, KaldiRecognizer
    print("📦 Загружаю Vosk модель...")
    vosk_model = Model(MODEL_PATH)
    print("✅ Vosk модель загружена")
    HAS_VOSK = True
except Exception as e:
    print(f"❌ Vosk не загружен: {e}")
    vosk_model = None
    HAS_VOSK = False

# GPT4All
try:
    from gpt4all import GPT4All
    print("📦 Загружаю GPT4All...")
    llm = GPT4All(os.path.basename(GGUF_PATH), model_path=os.path.dirname(GGUF_PATH))
    print("✅ GPT4All загружена")
    HAS_LLM = True
except Exception as e:
    print(f"❌ GPT4All не загружена: {e}")
    llm = None
    HAS_LLM = False

# ================== FastAPI ==================
app = FastAPI(title="Elli AI Assistant")

# 🧩 CORS полностью открыт для фронта (localhost / 127.0.0.1)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== Помощники ==================
def generate_response(user_text: str) -> str:
    if not user_text.strip():
        return "Я не расслышала — повтори, пожалуйста."

    if HAS_LLM and llm:
        try:
            with llm.chat_session():
                prompt = f"Ты помощник {ASSISTANT_NAME}. Отвечай кратко и дружелюбно.\nВопрос: {user_text}\nОтвет:"
                resp = llm.generate(prompt, max_tokens=128, temp=0.7)
                return resp.strip() if isinstance(resp, str) else str(resp)
        except Exception as e:
            print(f"Ошибка LLM: {e}")

    low = user_text.lower()
    if "привет" in low: return "Привет! Я слушаю тебя 👋"
    if "как тебя зовут" in low: return f"Я {ASSISTANT_NAME}."
    if "пока" in low: return "Пока! 👋"
    if "спасибо" in low: return "Всегда пожалуйста 💚"
    return f"Вы сказали: {user_text}"

def transcribe_audio_chunk(audio_data: bytes) -> str:
    if not HAS_VOSK or not vosk_model:
        return ""
    try:
        rec = KaldiRecognizer(vosk_model, SAMPLE_RATE)
        if rec.AcceptWaveform(audio_data):
            res = json.loads(rec.Result())
            return res.get("text", "")
        return ""
    except Exception as e:
        print(f"Ошибка распознавания: {e}")
        return ""

# ================== WebSocket ==================
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        self.recognizers = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
        if HAS_VOSK:
            self.recognizers[ws] = KaldiRecognizer(vosk_model, SAMPLE_RATE)
        print(f"✅ Подключился клиент ({len(self.active_connections)})")

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)
        if ws in self.recognizers:
            del self.recognizers[ws]
        print(f"❌ Клиент отключился ({len(self.active_connections)})")

    async def send_json(self, ws: WebSocket, message: dict):
        try:
            await ws.send_text(json.dumps(message))
        except Exception as e:
            print(f"Ошибка отправки: {e}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    print("✅ Клиент подключился")

    try:
        while True:
            msg_data = await ws.receive_text()
            print(msg_data)
            if not msg_data:
                continue  # пустое сообщение — просто ждём следующее

            try:
                msg = json.loads(msg_data)
            except json.JSONDecodeError:
                print(f"⚠️ Некорректный JSON: {msg_data}")
                continue

            msg_type = msg.get("type")

            # 🧠 Обработка текстовых сообщений
            if msg_type == "text_message":
                text = msg.get("text", "")
                print(f"👤 Текст: {text}")
                reply = generate_response(text)
                await manager.send_json(ws, {
                    "type": "assistant_response",
                    "text": reply,
                    "transcribed_text": text
                })
                print(f"🤖 Ответ: {reply}")

            # 🎤 Обработка голосовых чанков
            elif msg_type == "voice_chunk":
                b64 = msg.get("audio", "")
                if b64.startswith("data:"):
                    b64 = b64.split(",")[1]
                audio = base64.b64decode(b64)
                text = transcribe_audio_chunk(audio)
                if text:
                    reply = generate_response(text)
                    await manager.send_json(ws, {
                        "type": "assistant_response",
                        "text": reply,
                        "transcribed_text": text
                    })

            else:
                print(f"⚠️ Неизвестный тип сообщения: {msg_type}")

    except WebSocketDisconnect as e:
        print(f"❌ Клиент отключился: {e}1")
        manager.disconnect(ws)
    except Exception as e:
        print(f"❌ Ошибка WebSocket: {e}")
        manager.disconnect(ws)

# ================== REST тест ==================
@app.get("/")
async def root():
    return {"message": "Elli AI WebSocket Server работает 🚀"}

@app.get("/health")
async def health():
    return {"connections": len(manager.active_connections), "vosk": HAS_VOSK, "llm": HAS_LLM}

# ================== Запуск ==================
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 Elli AI WebSocket Server")
    print("=" * 50)
    print("📡 WebSocket: ws://localhost:8003/ws")
    print("📖 REST API:  http://localhost:8003/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8003)
