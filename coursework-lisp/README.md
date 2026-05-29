# Экспертная система на Common Lisp

Подбор русской классической литературы: **ядро на Common Lisp (SBCL)**, **HTTP/WebSocket — Python (FastAPI)**.

## Структура

```
coursework-lisp/
├── lisp/src/
│   ├── books.lisp     # База знаний: 23 книги (фреймы) напрямую на Lisp
│   ├── frames.lisp    # Инициализация и опции
│   ├── engine.lisp    # Продукционные правила, forward chaining
│   ├── dialog.lisp    # Диалог с пользователем
│   ├── server.lisp    # Команды через |, ответы JSON через format
└── exp/src/           # Python-шлюз (FastAPI)
```

Протокол: Python → Lisp: `init`, `dialog_question|session-1`. Lisp → Python: JSON-строки.

## Архитектура

```
React UI  ──WebSocket──►  Python (exp)  ──текст|stdin, JSON|stdout──►  SBCL
```

Все фреймы описаны в `lisp/src/books.lisp` — без загрузки JSON-файлов.

## Запуск через Docker

```powershell
cd coursework-lisp/exp
docker compose up --build
```

API: `http://localhost:8001`

## Локальный запуск

Требуется [SBCL](https://www.sbcl.org/) и Python 3.10+.

```powershell
cd coursework-lisp/exp
pip install -r requirements.txt
cd src
uvicorn main:app --reload --port 8001
```

## React-фронтенд

```powershell
cd coursework/resolve/frontend
$env:VITE_WS_PORT="8001"
npm run dev
```

## Редактирование базы знаний

Добавляйте или изменяйте книги в `lisp/src/books.lisp`. Для перегенерации из JSON (если нужно):

```powershell
python coursework-lisp/tools/gen_books.py
```

## API

- `GET /health` — статус Python + Lisp
- `GET /labels`, `/options`, `/frames`, `/rules`
- `GET /dialog-graph`
- `WS /ws` — интерактивный диалог

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SBCL_PATH` | Путь к SBCL | `sbcl` |
