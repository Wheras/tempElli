# Элли — офлайн голосовой ассистент (Vosk + Silero TTS + локальная LLM)

Проект содержит:

- backend (Python): распознавание речи (Vosk), синтез речи (Silero TTS), офлайн-логика/локальная LLM (GPT4All)
- frontend (React + Vite + Tailwind): пример фронта

## Требования

- Windows 10/11, PowerShell 5.1+
- Python 3.10+
- Node.js LTS (npm)

## Быстрый старт

1. Открыть PowerShell в корне проекта и запустить установку:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
.\setup.ps1
```

2. Активировать виртуальное окружение Python:

```powershell
# из корня проекта
.ackend\.venv\Scripts\Activate.ps1
```

3. (Опционально) Локальная LLM: скачать GGUF в `backend/` (например, Qwen 1.5B):

- `https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF`
- файл: `qwen2.5-1.5b-instruct-q4_k_m.gguf`

4. Запустить бэкенд:

```powershell
python .\backend\Beta.py
```

5. Запустить фронтенд:

```powershell
cd .\react-ts-vite-tailwind
npm run dev
```

## Конфигурация

- Путь к модели Vosk: `backend/Beta.py` → `MODEL_PATH` указывает на `backend/vosk-model-small-ru-0.22`
- Частота дискретизации: `SAMPLE_RATE` (по умолчанию 18000)
- Локальная LLM (опционально): `GGUF_PATH` в `backend/Beta.py` — имя `.gguf` в папке `backend/`

## Состав backend/requirements.txt

- sounddevice, vosk, torch, numpy, fastapi, uvicorn[standard], omegaconf, gpt4all

## Публикация на GitHub

```powershell
# в корне проекта
git init
git branch -M main
git add .
git commit -m "Initial commit: setup + backend/frontend"
# создайте пустой репозиторий на GitHub и замените URL ниже
git remote add origin https://github.com/<your_user>/<your_repo>.git
git push -u origin main
```

## Примечания

- Крупные файлы (venv, node_modules, модели Vosk/GGUF) исключены в .gitignore
- Если не нужна LLM — всё уже работает офлайн на правилах без сети
