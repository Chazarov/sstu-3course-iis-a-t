from __future__ import annotations

import json
import os
from pathlib import Path
import random
from typing import Any, Dict, List, Tuple, Union

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from dialog import DialogSession, default_questions, format_recommendations
from frames_repo import build_options, load_frames, option_map, load_frames, option_map
from recommender import build_engine_class, get_all_recomendations, get_recomendations
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


@app.get("/rules")
def get_rules(
    rule_type: str = Query(default=None, description="Фильтр по типу правила: 'init', 'match' или 'all'"),
    limit: int = Query(default=None, description="Ограничение количества возвращаемых правил")
) -> Dict[str, Any]:
    """
    Возвращает все метапродукции (правила) экспертной системы.
    Использует встроенный метод get_rules() из библиотеки experta.
    """
    # Создаём экземпляр движка
    engine = EngineCls()
    engine.reset()
    
    # Получаем все правила через встроенный метод experta
    rules = engine.get_rules()
    
    # Форматируем информацию о правилах
    rules_info = []
    init_count = 0
    match_count = 0
    other_count = 0
    
    for rule in rules:
        rule_name = rule.__name__ if hasattr(rule, '__name__') else str(rule)
        
        if rule_name in ("_init"):
            continue
        # Определяем тип правила по имени
        current_rule_type = "other"
        if rule_name.startswith("init__"):
            current_rule_type = "initialization"
            init_count += 1
        elif rule_name.startswith("match__"):
            current_rule_type = "matching"
            match_count += 1
        else:
            other_count += 1
        
        # Фильтрация по типу
        if rule_type:
            if rule_type == "init" and current_rule_type != "initialization":
                continue
            elif rule_type == "match" and current_rule_type != "matching":
                continue
        
        # Получаем информацию о салиенсе (приоритете)
        salience = getattr(rule, 'salience', None)
        
        # Извлекаем дополнительную информацию из имени правила
        extra_info = {}
        if current_rule_type == "initialization":
            # Для правил инициализации извлекаем название книги
            book_name = rule_name.replace("init__", "")
            extra_info["book"] = book_name
        elif current_rule_type == "matching":
            # Для правил сопоставления извлекаем книгу, поле и значение
            parts = rule_name.replace("match__", "").split("__")
            if len(parts) >= 3:
                extra_info["book"] = parts[0]
                extra_info["field"] = parts[1]
                extra_info["value"] = parts[2]
        
        rules_info.append({
            "name": rule_name,
            "type": current_rule_type,
            "salience": salience,
            "rule_object": str(rule),
            **extra_info
        })
    
    # Применяем лимит если указан
    if limit and limit > 0:
        rules_info = rules_info[:limit]
    
    return {
        "total_rules": len(rules),
        "init_rules_count": init_count,
        "match_rules_count": match_count,
        "other_rules_count": other_count,
        "filtered_rules_count": len(rules_info),
        "rules": rules_info,
        "statistics": {
            "total_books": len(frames),
            "questions": len(default_questions()),
            "average_rules_per_book": len(rules) / len(frames) if len(frames) > 0 else 0
        }
    }




@app.get("/dialog-graph")
def dialog_graph(max_paths: int = Query(default=1000, description="Максимальное количество путей для построения"),
                    max_multi_answer_iterations: int = Query(default=10, description="Ограничение на количество ветвлений на вопросах с возможностью выбора нескольких вариантов")) -> Dict[str, Any]:
    """
    Возвращает граф всех возможных путей диалога в виде списка смежности.
    Граф состояний диалога, где узлы переиспользуются.
    """

    
    questions = default_questions()
    max_path_limit = [max_paths]

    powersets = dict()
    
    adj_map: Dict[str, Dict[str, Any]] = {}
    session = DialogSession(labels)
    total_path_count = session.calculate_total_paths(questions, labels)
    logger.info(f"Поиск путей диалога... Максимальное возможное количество путей в системе: {total_path_count}. Ограничение:{max_paths}")

    def get_powerset(s: List[str], question_id:str):

        if question_id in powersets.keys():
            return powersets[question_id].copy()
        n = len(s)
        result = []
        for i in range(1, 1 << n):  # от 1, исключая пустое
            subset = []
            for j in range(n):
                if i & (1 << j):
                    subset.append(s[j])
            result.append(subset)

        powersets[question_id] = result
        return result
    
    def make_recursion(session:DialogSession, graph_obj_id_counter:int, depth:int, adj_map: Dict[str, Any]) -> Tuple[str, int]:

        depth += 1


        if session.is_done():
            recs = get_recomendations(EngineCls, frames, session.prefs, top_k=1)
            max_path_limit[0] -= 1

            adj_map[recs[0].id]["depth"] = depth

            logger.info(f" Осталось {max_path_limit[0]} из {max_paths} путей")
            return recs[0].id, graph_obj_id_counter
        
        question = session.get_question_message()
        graph_obj_id_counter += 1 
        graph_id = "qu-" + str(graph_obj_id_counter)
        adj_map[graph_id] = {
            "graph_id": graph_id,
            "text": question.text,
            "depth": depth,
            "edges": list()
        }
        
        if question.is_multiple_response_options:
            powerset = get_powerset(question.avaliable_answers, question.field) 
            random.shuffle(powerset)
            powerset = powerset[:max_multi_answer_iterations]
            for multi_ans in powerset:

                multi_ans = list(map(lambda x: x.lower(), multi_ans))
                
                session.add_answer(ClientAnswer(items_answer=multi_ans))
                to_id, graph_obj_id_counter = make_recursion(session, graph_obj_id_counter, depth, adj_map)
                adj_map[graph_id]["edges"].append({
                    "to": to_id,
                    "value": multi_ans
                })

                if(max_path_limit[0] == 0):
                    break
                
                session.go_back()

        else:
            answers = question.avaliable_answers.copy()
            random.shuffle(answers)
            for ans in answers:
                
                session.add_answer(ClientAnswer(text_answer=ans.lower()))
                to_id, graph_obj_id_counter = make_recursion(session, graph_obj_id_counter, depth, adj_map)
                adj_map[graph_id]["edges"].append({
                    "to": to_id,
                    "value": ans
                })
                
                if(max_path_limit[0] == 0):
                    break
                session.go_back()

        return graph_id, graph_obj_id_counter



    graph_obj_id_counter:int = 0
    
    recomendations = get_all_recomendations(frames=frames)

    for rec in recomendations:
        adj_map[rec.id] = {
            "graph_id": rec.id,
            "text": rec.title,
            "depth": 0,
            "edges": list()
        }

    make_recursion(session, graph_obj_id_counter, depth=0, adj_map=adj_map)

    
    return {
        "adj_map": adj_map
    }



async def _send(ws: WebSocket, message: WSMessage) -> None:
    """Отправка типизированного сообщения через WebSocket."""
    await ws.send_text(message.model_dump_json(exclude_none=True))


async def _recv_answer(ws: WebSocket) -> ClientAnswer:
    raw = await ws.receive_text()
    js_raw = json.loads(raw)
    serialized = ClientAnswer.model_validate(js_raw)
    if serialized.text_answer:
        serialized.text_answer = serialized.text_answer.lower()
    if serialized.items_answer:
        serialized.items_answer = [i.lower() for i in serialized.items_answer]
    
    
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
                if answer.text_answer and answer.text_answer.lower() == "restart":
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