# websocket_server.py
import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import base64
import tempfile

# ================== Настройки ==================
SAMPLE_RATE = 16000
MODEL_PATH = os.path.join(os.path.dirname(__file__), "vosk-model-small-ru-0.22")
ASSISTANT_NAME = "Элли"
SPEAKER = "kseniya_v2" 
GGUF_PATH = os.path.join(os.path.dirname(__file__), "qwen2.5-1.5b-instruct-q4_k_m.gguf")

# ================== Импорт моделей ==================
print("🔄 Загружаю AI модели...")

# Пробуем загрузить Vosk для распознавания речи
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

# Пробуем загрузить GPT4All для AI
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

# ================== FastAPI приложение ==================
app = FastAPI(title="Elli AI Assistant")

# CORS настройки
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== Функции из Beta.py ==================
def generate_response(user_text: str) -> str:
    """Генерация ответа (LLM или fallback)"""
    text = (user_text or "").strip()
    if not text:
        return "Я не расслышала — повтори, пожалуйста."

    # GPT4All
    if HAS_LLM and llm is not None:
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
            print(f"Ошибка локальной LLM: {e}")

    # Простой fallback
    lower = text.lower()
    if any(x in lower for x in ["как тебя зовут", "твое имя", "твоё имя", "кто ты"]):
        return "Меня зовут Элли. Чем могу помочь?"
    if any(x in lower for x in ["привет", "здравств", "добрый"]):
        return "Привет! Я слушаю."
    if any(x in lower for x in ["пока", "до свид", "увидимс"]):
        return "Пока!"
    if any(x in lower for x in ["спасибо", "благодар"]):
        return "Пожалуйста! Рада была помочь!"

    return f"Вы сказали: '{text}'. Я ваш AI-помощник Элли! 🤖"

def transcribe_audio_chunk(audio_data: bytes) -> str:
    """Распознает речь из аудио данных"""
    if not HAS_VOSK or vosk_model is None:
        return ""
    
    try:
        recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)
        if recognizer.AcceptWaveform(audio_data):
            result = json.loads(recognizer.Result())
            return result.get("text", "").strip()
        else:
            partial = json.loads(recognizer.PartialResult())
            return partial.get("partial", "").strip()
    except Exception as e:
        print(f"Ошибка распознавания: {e}")
        return ""

# ================== WebSocket логика ==================
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        self.recognizers = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Создаем распознаватель для каждого соединения
        if HAS_VOSK:
            self.recognizers[websocket] = KaldiRecognizer(vosk_model, SAMPLE_RATE)
        print(f"✅ Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.recognizers:
            del self.recognizers[websocket]
        print(f"❌ Client disconnected. Total: {len(self.active_connections)}")

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Получаем данные от клиента
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "text_message":
                # Обрабатываем текстовое сообщение
                user_text = message.get("text", "")
                print(f"👤 Текст: {user_text}")
                
                # Генерируем ответ
                response_text = generate_response(user_text)
                
                await manager.send_message({
                    "type": "assistant_response", 
                    "text": response_text,
                    "transcribed_text": user_text
                }, websocket)
                print(f"🤖 Ответ: {response_text}")
                
            elif message["type"] == "voice_chunk":
                # Обрабатываем аудио чанк
                if HAS_VOSK:
                    try:
                        # Декодируем base64 аудио
                        audio_base64 = message.get("audio", "")
                        if audio_base64.startswith('data:audio'):
                            audio_base64 = audio_base64.split(',')[1]
                        
                        audio_data = base64.b64decode(audio_base64)
                        
                        # Распознаем речь
                        recognizer = manager.recognizers.get(websocket)
                        if recognizer:
                            text = transcribe_audio_chunk(audio_data)
                            
                            if text and len(text) > 2:  # Если есть осмысленный текст
                                response = generate_response(text)
                                await manager.send_message({
                                    "type": "assistant_response",
                                    "text": response,
                                    "transcribed_text": text
                                }, websocket)
                    except Exception as e:
                        print(f"❌ Ошибка обработки аудио: {e}")
                        await manager.send_message({
                            "type": "error",
                            "message": "Ошибка обработки аудио"
                        }, websocket)
                
            elif message["type"] == "voice_start":
                # Начало записи - сбрасываем распознаватель
                if HAS_VOSK and websocket in manager.recognizers:
                    manager.recognizers[websocket] = KaldiRecognizer(vosk_model, SAMPLE_RATE)
                await manager.send_message({
                    "type": "listening_started",
                    "text": "Слушаю..."
                }, websocket)
                
            elif message["type"] == "voice_stop":
                # Конец записи - получаем финальный результат
                if HAS_VOSK:
                    recognizer = manager.recognizers.get(websocket)
                    if recognizer:
                        final_result = json.loads(recognizer.FinalResult())
                        text = final_result.get('text', '')
                        if text:
                            response = generate_response(text)
                            await manager.send_message({
                                "type": "assistant_response",
                                "text": response,
                                "transcribed_text": text
                            }, websocket)
                        
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

# REST endpoint для тестирования
@app.post("/api/chat")
async def chat(text: str):
    """REST endpoint для текстовых сообщений"""
    response = generate_response(text)
    return {
        "response": response,
        "transcribed_text": text,
        "status": "success"
    }

@app.get("/")
async def root():
    return {
        "message": "Elli AI WebSocket Server", 
        "status": "healthy",
        "ai_loaded": HAS_LLM,
        "speech_loaded": HAS_VOSK,
        "assistant_name": ASSISTANT_NAME
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "connections": len(manager.active_connections),
        "models": {
            "ai": HAS_LLM,
            "speech_recognition": HAS_VOSK
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🚀 Elli AI WebSocket Server")
    print("=" * 50)
    print(f"📡 WebSocket: ws://localhost:8002/ws")
    print(f"📖 REST API:  http://localhost:8002/docs")
    print(f"🤖 AI Model:  {'✅ Загружена' if HAS_LLM else '❌ Не доступна'}")
    print(f"🎤 Speech:    {'✅ Загружена' if HAS_VOSK else '❌ Не доступна'}")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")