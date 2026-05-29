from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from lisp_bridge import LispBridgeError, create_bridge

bridge = create_bridge()
app = FastAPI(title="Expert System (Lisp core)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _encode_answers(body: Dict[str, Any]) -> str:
    parts: List[str] = []
    for qid, value in body.items():
        if isinstance(value, list):
            parts.append(f"{qid}={','.join(str(v) for v in value)}")
        else:
            parts.append(f"{qid}={value}")
    return ";".join(parts)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "lisp": bridge.call("health")}


@app.get("/questions")
def questions() -> Dict[str, Any]:
    return bridge.call("get_questions")


@app.post("/recommend")
async def recommend(request: Request, top_k: int = Query(default=5, ge=1)) -> Dict[str, Any]:
    body = await request.json()
    if not isinstance(body, dict) or not body:
        raise HTTPException(status_code=400, detail="Ожидается JSON-объект с ответами на вопросы")

    if "top_k" in body:
        top_k = int(body.pop("top_k"))

    try:
        return bridge.call("submit_answers", str(top_k), _encode_answers(body))
    except LispBridgeError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.get("/frames")
def frames() -> Dict[str, Any]:
    return bridge.call("get_frames")


@app.get("/rules")
def rules(
    rule_type: str = Query(default=None),
    limit: int = Query(default=None),
) -> Dict[str, Any]:
    parts: List[str] = []
    if rule_type is not None:
        parts.append(rule_type)
    if limit is not None:
        parts.append(str(limit))
    return bridge.call("get_rules", *parts)
