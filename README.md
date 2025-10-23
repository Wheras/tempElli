# Элли — офлайн голосовой ассистент (Vosk + FastAPI WebSocket + локальная LLM)

Актуальная структура:

- backend (Python): FastAPI‑сервер `backend/websocket_server.py` с WebSocket `/ws` и REST `/health`, распознавание речи (Vosk), опционально локальная LLM (GPT4All)
- frontend (React + Vite + Tailwind): каталог `react-ts-vite-tailwind`

Файлы `backend/Beta.py` и `backend/Controller.py` больше не используются.

## Требования

- Windows 10/11, PowerShell 5.1+
- Python 3.10+
- Node.js LTS (npm)

## Установка

```powershell
# из корня проекта
py -m venv .venv

# PowerShell:
./.venv/Scripts/Activate.ps1

# CMD (альтернатива):
REM .\.venv\Scripts\activate.bat

# Установка Python-зависимостей
python -m pip install -r backend/requirements.txt

# Установка фронтенда
cd ./react-ts-vite-tailwind
npm ci
cd ..
```

Опционально: скачайте GGUF‑модель в `backend/` (например Qwen 1.5B): `qwen2.5-1.5b-instruct-q4_k_m.gguf`.

## Запуск

Backend:

```powershell
python ./backend/websocket_server.py
# WebSocket: ws://127.0.0.1:8003/ws
# Health:    http://127.0.0.1:8003/health
```

Frontend:

```powershell
cd ./react-ts-vite-tailwind
npm run dev
# Открыть: http://127.0.0.1:5173
```

## Конфигурация

- Путь к модели Vosk: `backend/websocket_server.py` → `MODEL_PATH` (по умолчанию `backend/vosk-model-small-ru-0.22`)
- Частота дискретизации: `SAMPLE_RATE` (по умолчанию 16000)
- Локальная LLM: `GGUF_PATH` в `backend/websocket_server.py`
- CORS открыт для локальной разработки

## Диагностика WebSocket

1. Убедитесь, что backend запущен и `http://127.0.0.1:8003/health` отвечает JSON.
2. Фронтенд должен подключаться к `ws://127.0.0.1:8003/ws` (см. `react-ts-vite-tailwind/src/App.tsx` и `src/hooks/useWebSocket.ts`).
3. Если соединение закрывается кодом 1006/1005:
   - Откройте фронт по HTTP (для локалки используем `ws://`, не `wss://`).
   - Разрешите соединения в брандмауэре Windows для Python/uvicorn.
   - В `health` поле `connections` должно быть ≥ 1 при открытой вкладке фронта.

## Состав backend/requirements.txt

- sounddevice, vosk, torch, numpy, fastapi, uvicorn[standard], omegaconf, gpt4all

## Примечания

- Крупные файлы (venv, node_modules, модели Vosk/GGUF) исключены в `.gitignore`
- Если LLM не нужна — ассистент отвечает базовыми фразами без сети
