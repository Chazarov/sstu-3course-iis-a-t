from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger

from dialog import DialogSession, default_questions, format_recommendations
from frames_repo import build_options, load_frames, option_map, load_frames, option_map
from recommender import build_engine_class, get_recomendations
from models import *
from dotenv import load_dotenv
import os

load_dotenv()

# ============ Pydantic модели для WebSocket сообщений ============




WSMessage = Union[QuestionMessage, RecomendationsMessage, ErrorMessage, InfoMessage]


# ============ Инициализация ============

# Вычисляем путь к фреймам относительно main.py
# main.py: resolve/exp/src/main.py
# Фреймы: resolve/sourses/frames/
current_file = Path(__file__).resolve()
repo_root = current_file.parents[2]  # resolve/
frames_dir = repo_root / "sourses" / "frames"


logger.info(f"Frames directory: {frames_dir}")
logger.info(f"Directory exists: {frames_dir.exists()}")

frames = load_frames(frames_dir)
options = build_options(frames)
labels = option_map(options)

EngineCls = build_engine_class(frames, labels)


app = FastAPI()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/labels")
def get_labels() -> Dict[str, List[str]]:
    return options

@app.get("/options")
def get_options() -> Dict[str, Dict[str, str]]:
    return labels

@app.get("/frames")
def get_frames():
    return frames


@app.get("/dialog-graph")
def dialog_graph() -> Dict[str, Any]:
    """
    Возвращает граф всех возможных путей диалога в виде списка смежности.
    Граф состояний диалога, где узлы переиспользуются.
    """
    def make_powerset(s: List[str]):
        n = len(s)
        result = []
        for i in range(1, 1 << n):  # от 1, исключая пустое
            subset = []
            for j in range(n):
                if i & (1 << j):
                    subset.append(s[j])
            result.append(subset)
        return result
    
    def make_recursion(session:DialogSession, graph_obj_id_counter:int, adj_map: Dict[str, Any]):


        question = session.get_question_message()
        graph_obj_id_counter +=1 
        graph_id = "qu-" + graph_obj_id_counter
        adj_map[graph_id] = {
            "graph_id": graph_id,
            "text": question.text,
            "edges": list()
        }
        if question.is_multiple_response_options:
            powerset = make_powerset(question.avaliable_answers) 
            for ans in powerset:
                session.add_answer(ClientAnswer(text_answer=ans))
        else:
            for ans in question.avaliable_answers:
                make_recursion(session, graph_obj_id_counter, adj_map)
                session.add_answer(ClientAnswer(text_answer=ans))

        if session.is_done():
            recs = get_recomendations(EngineCls, frames, session.prefs, top_k=1)
        
        return graph_obj_id_counter, False



    graph_obj_id_counter:int = 0
    nodes_count = 0
    edjes_count = 0
    questions = default_questions()
    adj_map: Dict[str, Dict[str, Any]] = {}

    
    
    # Создаем начальный узел
    start_node_id = "start"
    adj_map[start_node_id] = {
        "id": start_node_id,
        "type": "start",
        "depth": 0
    }

    session = DialogSession(labels)
    
   

    
    
    
    return {
        "total_nodes": nodes_count,
        "total_edges": edjes_count,
        "questions_count": len(questions),
        "adj_map": adj_map
    }



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
                logger.info(" сессия закончена")
                recs = get_recomendations(EngineCls, frames, session.prefs, top_k=5)
                logger.info(" рекомендации получены")
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
                
                # Проверяем команду "back" для отмены выбора
                if answer.text_answer and answer.text_answer.lower() == "back":
                    if session.can_go_back():
                        session.go_back()
                        await _send(ws, InfoMessage(text="Возвращаюсь к предыдущему вопросу."))
                    else:
                        await _send(ws, InfoMessage(text="Невозможно вернуться назад. Вы на первом вопросе."))
                    continue
                
                session.add_answer(answer)
            except DialogError as e:
                await _send(ws, ErrorMessage(text=str(e)))
                continue
            except Exception as e:
                await _send(ws, ErrorMessage(text=f"Ошибка: {str(e)}"))
                continue

    except WebSocketDisconnect:
        return