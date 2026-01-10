from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Union

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from dialog import DialogSession, format_recommendations
from frames_repo import build_options, frames_dir_from_repo_root, load_frames, option_map, repo_root_from_src_file
from recommender import build_engine_class, get_recomendations
from models import *


# ============ Pydantic модели для WebSocket сообщений ============




WSMessage = Union[QuestionMessage, RecomendationsMessage, ErrorMessage, InfoMessage]


# ============ Инициализация ============


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


async def _send(ws: WebSocket, message: WSMessage) -> None:
    """Отправка типизированного сообщения через WebSocket."""
    await ws.send_text(message.model_dump_json(exclude_none=True))


async def _recv_answer(ws: WebSocket) -> ClientAnswer:
    raw = await ws.receive_text()
    js_raw = json.loads(raw)
    serialized = ClientAnswer.model_validate(js_raw)
    serialized.text_answer = serialized.text_answer.lower()
    if(serialized.items_answer):
        for i in serialized.items_answer:
            i = i.lower()
    
    
    return serialized


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    session = DialogSession(labels)

    try:
        while True:
            if session.is_done():
                recs = get_recomendations(EngineCls, frames, session.prefs, top_k=5)
                if not recs:
                    await _send(ws, RecomendationsMessage(
                            text="Не нашёл совпадений по выбранным критериям. Напишите restart чтобы начать заново.",
                            items=[]))
                else:
                    items = format_recommendations(recs)
                    await _send(ws, RecomendationsMessage(
                            text="Топ рекомендаций. Напишите restart чтобы начать заново.",
                            items=items))

                answer:ClientAnswer = await _recv_answer(ws)
                if answer.lower() == "restart":
                    session = DialogSession(labels)
                    await _send(ws, InfoMessage(text="Ок, начнём заново."))
                    continue
                await _send(ws, InfoMessage(text="Закрываю соединение."))
                await ws.close()
                return

            question_messgae = session.get_question_message()
            await _send(ws, question_messgae)

            try:
                answer = await _recv_answer(ws)
                session.add_answer(answer)
            except DialogError as e:
                await _send(ws, ErrorMessage(text=str(e)))
                continue
            except Exception as e:
                await _send(ws, ErrorMessage(text=f"Ошибка: {str(e)}"))
                continue

    except WebSocketDisconnect:
        return