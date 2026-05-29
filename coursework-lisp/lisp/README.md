# Курсовая: экспертная система на Common Lisp

Реализация той же экспертной системы подбора русской классической литературы, где **вся логика БЗ, правил, вывода и диалога** написана на **Common Lisp**, а **Python (FastAPI)** выступает фронтенд-шлюзом и вызывает интерпретатор SBCL.

## Архитектура

```
React UI  ──WebSocket/REST──►  Python (exp-lisp)  ──JSON/stdin──►  SBCL (lisp/src)
```

### Lisp (`coursework/resolve/lisp/src/`)

| Файл | Назначение |
|------|------------|
| `frames.lisp` | Загрузка фреймов из JSON, опции и метки |
| `engine.lisp` | Forward chaining, продукционные правила, рекомендации |
| `dialog.lisp` | Сессия диалога, вопросы, валидация ответов |
| `server.lisp` | JSON-RPC протокол через stdin/stdout |
| `main.lisp` | Точка входа SBCL |

### Python (`coursework/resolve/exp-lisp/src/`)

| Файл | Назначение |
|------|------------|
| `lisp_bridge.py` | Запуск SBCL, обмен JSON-командами |
| `main.py` | FastAPI + WebSocket API (совместим с React-фронтендом) |

## Требования

- **SBCL** (Steel Bank Common Lisp): https://www.sbcl.org/
- Python 3.10+
- Node.js (для React-фронтенда из `resolve/frontend`)

### Установка SBCL

**Windows (winget):**
```powershell
winget install SBCL.SBCL
```

**Linux:**
```bash
sudo apt install sbcl
```

## Запуск локально

### 1. Python API + Lisp-ядро

```powershell
cd coursework/resolve/exp-lisp
pip install -r requirements.txt
cd src
uvicorn main:app --reload --port 8001
```

### 2. React-фронтенд

```powershell
cd coursework/resolve/frontend
# VITE_WS_PORT=8001
npm install
npm run dev
```

### 3. Docker (SBCL + Python в одном контейнере)

```powershell
cd coursework/resolve/exp-lisp
docker compose up --build
```

API будет на `http://localhost:8001`.

## Протокол Python ↔ Lisp

Каждая строка — JSON-объект. Примеры команд:

```json
{"cmd": "init", "frames_dir": "/path/to/frames"}
{"cmd": "recommend", "prefs": [["жанр", "роман"], ["эпоха", "начало_xix"]], "top_k": 5}
{"cmd": "dialog_new"}
{"cmd": "dialog_question", "session_id": "session-1"}
{"cmd": "dialog_add_answer", "session_id": "session-1", "text_answer": "роман"}
```

## REST API

Совместим с исходной версией на experta:

- `GET /health` — статус Python + Lisp
- `GET /labels`, `/options`, `/frames`, `/rules`
- `GET /dialog-graph`
- `WS /ws` — интерактивный диалог

## Отличие от Python-версии (`resolve/exp`)

| Компонент | Python (experta) | Lisp (SBCL) |
|-----------|------------------|-------------|
| Загрузка фреймов | `frames_repo.py` | `frames.lisp` |
| Продукционные правила | `recommender.py` | `engine.lisp` |
| Forward chaining | experta | собственный движок |
| Диалог | `dialog.py` | `dialog.lisp` |
| HTTP/WebSocket | `main.py` | `exp-lisp/main.py` (прокси) |
