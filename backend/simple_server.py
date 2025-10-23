# simple_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

app = FastAPI()

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"❌ Client disconnected. Total: {len(self.active_connections)}")

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

# Упрощенная функция для генерации ответов
def generate_response(text: str) -> str:
    """Генерация ответов без Vosk"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["привет", "здравств", "хай", "hello"]):
        return "Привет! Я Elli, ваш голосовой помощник! 👋"
    elif any(word in text_lower for word in ["как дела", "как ты"]):
        return "У меня всё отлично! Готов помочь вам! 😊"
    elif any(word in text_lower for word in ["пока", "до свидан", "увидимся"]):
        return "До свидания! Возвращайтесь скорее! 👋"
    elif any(word in text_lower for word in ["спасибо", "благодар"]):
        return "Всегда пожалуйста! Рад помочь! 🤗"
    elif any(word in text_lower for word in ["погода", "weather"]):
        return "Пока я не могу проверить погоду, но скоро научусь! 🌤️"
    elif any(word in text_lower for word in ["время", "time"]):
        return "К сожалению, я еще не умею определять время ⏰"
    elif any(word in text_lower for word in ["тест", "test"]):
        return "Тест пройден! WebSocket работает отлично! ✅"
    else:
        return f"Вы сказали: '{text}'. Я еще учусь, но скоро стану умнее! 🧠"

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Получаем данные от клиента
            data = await websocket.receive_text()
            message = json.loads(data)
            print(f"📨 Получено сообщение: {message['type']}")
            
            if message["type"] == "text_message":
                # Обрабатываем текстовое сообщение
                user_text = message.get("text", "")
                print(f"👤 Пользователь: {user_text}")
                
                response_text = generate_response(user_text)
                
                await manager.send_message({
                    "type": "assistant_response", 
                    "text": response_text,
                    "transcribed_text": user_text
                }, websocket)
                print(f"🤖 Ответ: {response_text}")
                
            elif message["type"] == "voice_start":
                print("🎤 Начало записи голоса")
                await manager.send_message({
                    "type": "listening_started",
                    "text": "Слушаю..."
                }, websocket)
                
            elif message["type"] == "voice_chunk":
                print("🎵 Получен аудио чанк")
                # Пока просто логируем получение аудио
                await manager.send_message({
                    "type": "processing_audio", 
                    "text": "Обрабатываю аудио..."
                }, websocket)
                
            elif message["type"] == "voice_stop":
                print("⏹️ Конец записи голоса")
                # Для теста отправляем фиктивный ответ
                response_text = "Я получил ваше голосовое сообщение! Пока что работаю над интеграцией распознавания речи. 🎤"
                await manager.send_message({
                    "type": "assistant_response",
                    "text": response_text,
                    "transcribed_text": "[голосовое сообщение]"
                }, websocket)
                        
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "WebSocket server is running!", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "connections": len(manager.active_connections)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SIMPLE WebSocket server on http://localhost:8000")
    print("📖 Documentation: http://localhost:8000/docs")
    print("🔗 WebSocket: ws://localhost:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")