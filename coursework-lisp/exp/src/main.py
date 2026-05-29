from __future__ import annotations

import json
import random
from typing import Any, Dict, List, Tuple, Union

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from lisp_bridge import LispBridgeError, create_bridge
from models import (
    ClientAnswer,
    DialogError,
    ErrorMessage,
    InfoMessage,
    QuestionMessage,
    RecommendationItem,
    RecomendationsMessage,
)

WSMessage = Union[QuestionMessage, RecomendationsMessage, ErrorMessage, InfoMessage]

bridge = create_bridge()
app = FastAPI(title="Expert System (Lisp core)")


def _labels_to_dict(resp: Dict[str, Any]) -> Dict[str, List[str]]:
    labels = resp.get("labels", [])
    return {field: values for field, values in labels}


def _options_to_dict(resp: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    options = resp.get("options", [])
    return {field: dict(mapping) for field, mapping in options}


def _items_to_recommendation_items(items: List[Dict[str, Any]]) -> List[RecommendationItem]:
    return [RecommendationItem(**item) for item in items]


@app.get("/health")
def health() -> Dict[str, Any]:
    resp = bridge.call("health")
    return {"status": "ok", "lisp": resp}


@app.get("/labels")
def get_labels() -> Dict[str, List[str]]:
    return _labels_to_dict(bridge.call("get_labels"))


@app.get("/options")
def get_options() -> Dict[str, Dict[str, str]]:
    return _options_to_dict(bridge.call("get_options"))


@app.get("/frames")
def get_frames() -> List[Dict[str, Any]]:
    return bridge.call("get_frames").get("frames", [])


@app.get("/rules")
def get_rules(
    rule_type: str = Query(default=None, description="Фильтр: init, match или all"),
    limit: int = Query(default=None, description="Ограничение количества правил"),
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if rule_type is not None:
        payload["rule_type"] = rule_type
    if limit is not None:
        payload["limit"] = limit
    return bridge.call("get_rules", **payload)


@app.get("/dialog-graph")
def dialog_graph(
    max_paths: int = Query(default=1000),
    max_multi_answer_iterations: int = Query(default=10),
) -> Dict[str, Any]:
    """Граф диалога — Python обходит дерево, рекомендации запрашивает у Lisp."""
    questions_resp = bridge.call("get_labels")
    labels = _labels_to_dict(questions_resp)
    options = _options_to_dict(bridge.call("get_options"))

    question_defs = [
        ("gq-1", "жанр", False),
        ("gq-2", "эпоха", False),
        ("gq-3", "настроение", False),
        ("gq-4", "сложность", False),
        ("gq-5", "объём", False),
        ("gq-6", "темы", True),
    ]

    adj_map: Dict[str, Dict[str, Any]] = {}
    max_path_limit = [max_paths]
    powersets: Dict[str, List[List[str]]] = {}

    all_recs = bridge.call("get_all_recommendations").get("items", [])
    for rec in all_recs:
        adj_map[rec["id"]] = {
            "graph_id": rec["id"],
            "text": rec["title"],
            "depth": 0,
            "edges": [],
        }

    def get_powerset(values: List[str], key: str) -> List[List[str]]:
        if key in powersets:
            return powersets[key].copy()
        n = len(values)
        result = []
        for i in range(1, 1 << n):
            subset = [values[j] for j in range(n) if i & (1 << j)]
            result.append(subset)
        powersets[key] = result
        return result

    class LocalSession:
        def __init__(self) -> None:
            self.idx = 0
            self.prefs: List[Tuple[str, str]] = []
            self.history: List[int] = []

        def is_done(self) -> bool:
            return self.idx >= len(question_defs)

        def current(self) -> Tuple[str, str, bool]:
            return question_defs[self.idx]

        def add_single(self, field: str, value: str) -> None:
            norm = value.lower().replace(" ", "_")
            self.prefs.append((field, norm))
            self.history.append(1)
            self.idx += 1

        def add_multi(self, field: str, values: List[str]) -> None:
            count = 0
            for value in values:
                norm = value.lower().replace(" ", "_")
                self.prefs.append((field, norm))
                count += 1
            self.history.append(count)
            self.idx += 1

        def go_back(self) -> None:
            self.idx -= 1
            count = self.history.pop()
            for _ in range(count):
                self.prefs.pop()

    def make_recursion(session: LocalSession, counter: int, depth: int) -> Tuple[str, int]:
        depth += 1
        if session.is_done():
            recs = bridge.call(
                "recommend",
                prefs=[[f, v] for f, v in session.prefs],
                top_k=1,
            ).get("items", [])
            max_path_limit[0] -= 1
            if recs:
                adj_map[recs[0]["id"]]["depth"] = depth
                return recs[0]["id"], counter
            return "unknown", counter

        qid, field, is_multi = session.current()
        counter += 1
        graph_id = f"qu-{counter}"
        hints = sorted(labels.get(field, []))
        adj_map[graph_id] = {
            "graph_id": graph_id,
            "text": f"Выберите {field}",
            "depth": depth,
            "edges": [],
        }

        if is_multi:
            subsets = get_powerset(hints, field)
            random.shuffle(subsets)
            subsets = subsets[:max_multi_answer_iterations]
            for subset in subsets:
                normalized = [x.lower().replace(" ", "_") for x in subset]
                session.add_multi(field, normalized)
                to_id, counter = make_recursion(session, counter, depth)
                adj_map[graph_id]["edges"].append({"to": to_id, "value": normalized})
                if max_path_limit[0] == 0:
                    break
                session.go_back()
        else:
            answers = hints.copy()
            random.shuffle(answers)
            for ans in answers:
                session.add_single(field, ans)
                to_id, counter = make_recursion(session, counter, depth)
                adj_map[graph_id]["edges"].append({"to": to_id, "value": ans})
                if max_path_limit[0] == 0:
                    break
                session.go_back()

        return graph_id, counter

    session = LocalSession()
    make_recursion(session, 0, 0)
    return {"adj_map": adj_map}


async def _send(ws: WebSocket, message: WSMessage) -> None:
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

    try:
        session_resp = bridge.call("dialog_new")
        session_id = session_resp["session_id"]
    except LispBridgeError as e:
        await ws.send_text(ErrorMessage(text=str(e)).model_dump_json())
        await ws.close()
        return

    try:
        while True:
            done_resp = bridge.call("dialog_is_done", session_id=session_id)
            if done_resp.get("done"):
                rec_resp = bridge.call("dialog_recommend", session_id=session_id, top_k=5)
                items_raw = rec_resp.get("items", [])
                if not items_raw:
                    await _send(
                        ws,
                        RecomendationsMessage(
                            text="Не нашёл совпадений по выбранным критериям.",
                            items=[],
                        ),
                    )
                else:
                    await _send(
                        ws,
                        RecomendationsMessage(
                            text="Топ рекомендаций.",
                            items=_items_to_recommendation_items(items_raw),
                        ),
                    )

                answer = await _recv_answer(ws)
                if answer.text_answer and answer.text_answer.lower() == "restart":
                    session_resp = bridge.call("dialog_new")
                    session_id = session_resp["session_id"]
                    await _send(ws, InfoMessage(text="Ок, начнём заново."))
                    continue

                await _send(ws, InfoMessage(text="Закрываю соединение."))
                await ws.close()
                return

            question_resp = bridge.call("dialog_question", session_id=session_id)
            question = QuestionMessage(
                question_id=question_resp["question_id"],
                field=question_resp["field"],
                text=question_resp["text"],
                avaliable_answers=question_resp["avaliable_answers"],
                is_multiple_response_options=question_resp["is_multiple_response_options"],
            )
            await _send(ws, question)

            try:
                answer = await _recv_answer(ws)
                if answer.text_answer and answer.text_answer.lower() == "back":
                    can_back = bridge.call("dialog_can_go_back", session_id=session_id)
                    if can_back.get("can_go_back"):
                        bridge.call("dialog_go_back", session_id=session_id)
                        await _send(ws, InfoMessage(text="Возвращаюсь к предыдущему вопросу."))
                    else:
                        await _send(ws, InfoMessage(text="Невозможно вернуться назад. Вы на первом вопросе."))
                    continue

                bridge.call(
                    "dialog_add_answer",
                    session_id=session_id,
                    text_answer=answer.text_answer,
                    items_answer=answer.items_answer,
                )
            except LispBridgeError as e:
                await _send(ws, ErrorMessage(text=str(e)))
                continue
            except DialogError as e:
                await _send(ws, ErrorMessage(text=str(e)))
                continue

    except WebSocketDisconnect:
        return
