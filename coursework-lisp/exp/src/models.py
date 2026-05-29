"""Pydantic-модели для API (при необходимости расширения)."""

from typing import List, Optional

from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    title: str
    score: int
    matched: List[str]
    author: Optional[str] = None
    genre: Optional[str] = None
    epoch: Optional[str] = None
    mood: Optional[str] = None
    difficulty: Optional[str] = None
    volume: Optional[str] = None
    image: Optional[str] = None


class RecommendResponse(BaseModel):
    status: str = "ok"
    items: List[RecommendationItem] = Field(default_factory=list)
