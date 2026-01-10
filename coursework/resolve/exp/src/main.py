from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from dialog import DialogSession
from frames_repo import build_options, frames_dir_from_repo_root, load_frames, option_map, repo_root_from_src_file
from recommender import build_engine_class, recommend


repo_root = repo_root_from_src_file(Path(__file__))
frames_dir = frames_dir_from_repo_root(repo_root)
frames = load_frames(frames_dir)
options = build_options(frames)
labels = option_map(options)
EngineCls = build_engine_class(frames, labels)


app = FastAPI()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


async def _send(ws: WebSocket, payload: Dict[str, Any]) -> None:
    await ws.send_text(json.dumps(payload, ensure_ascii=False))


async def _recv_answer(ws: WebSocket) -> str:
    raw = await ws.receive_text()
    text = raw.strip()
    if not text:
        return ""
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "text" in data:
            return str(data["text"]).strip().lower()
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    return text


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    session = DialogSession(labels)

    try:
        while True:
            if session.is_done():
                recs = recommend(EngineCls, frames, session.prefs, top_k=5)
                if not recs:
                    await _send(
                        ws,
                        {
                            "type": "result",
                            "text": "Не нашёл совпадений по выбранным критериям. Напишите restart чтобы начать заново.",
                            "items": [],
                        },
                    )
                else:
                    items: List[Dict[str, Any]] = []
                    for r in recs:
                        info = r.info
                        items.append(
                            {
                                "title": r.title,
                                "score": r.score,
                                "matched": r.matched,
                                "author": info.get("автор"),
                                "жанр": info.get("жанр"),
                                "эпоха": info.get("эпоха"),
                                "настроение": info.get("настроение"),
                                "сложность": info.get("сложность"),
                                "объём": info.get("объём"),
                                "изображение": info.get("изображение"),
                            }
                        )
                    await _send(
                        ws,
                        {
                            "type": "result",
                            "text": "Топ рекомендаций. Напишите restart чтобы начать заново.",
                            "items": items,
                        },
                    )

                answer = await _recv_answer(ws)
                if answer.lower() == "restart":
                    session = DialogSession(labels)
                    await _send(ws, {"type": "info", "text": "Ок, начнём заново."})
                    continue
                await _send(ws, {"type": "info", "text": "Закрываю соединение."})
                await ws.close()
                return

            q = session.current()
            assert q is not None
            hints = session.hints_for(q.field, limit=12)
            await _send(
                ws,
                {
                    "type": "question",
                    "field": q.field,
                    "text": q.prompt,
                    "examples": hints,
                },
            )

            answer = await _recv_answer(ws)
            ok, err = session.add_answer(answer)
            if not ok:
                await _send(ws, {"type": "error", "text": err})
                continue

    except WebSocketDisconnect:
        return