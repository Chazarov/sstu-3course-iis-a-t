from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class Book:
    name: str
    author: str
    genre: str
    era: str
    direction: str
    complexity: str
    volume: str
    mood: str
    themes: Tuple[str, ...]
    conflict_type: str
    hero_type: str
    artistic_means: Tuple[str, ...]
    pages: int
    year: int
    author_position: str
    audience: str
    attention_points: str
    weaknesses: str
    interpretations: str
    image_file: str


@dataclass
class Preferences:
    volume: Optional[str] = None
    complexity: Optional[str] = None
    mood: Optional[str] = None
    themes: List[str] | None = None
    hero_type: Optional[str] = None
    conflict_type: Optional[str] = None
    artistic_means: List[str] | None = None
    era: Optional[str] = None
    genre_group: Optional[List[str]] = None

    liked_author_position: List[str] | None = None
    liked_audience: List[str] | None = None
    disliked_weaknesses: List[str] | None = None
    liked_interpretations: List[str] | None = None

    def __post_init__(self) -> None:
        self.themes = self.themes or []
        self.artistic_means = self.artistic_means or []
        self.liked_author_position = self.liked_author_position or []
        self.liked_audience = self.liked_audience or []
        self.disliked_weaknesses = self.disliked_weaknesses or []
        self.liked_interpretations = self.liked_interpretations or []



