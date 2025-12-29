from __future__ import annotations

from typing import List

from  application.recommendation import RankedBook
from  domain.text import extract_phrases


def dynamic_options_from_candidates(items: List[RankedBook], field: str, limit: int = 10) -> List[str]:
    """Генерирует варианты ответа из текстовых полей книг по топ-кандидатам.

    field: author_position | audience | weaknesses | interpretations
    """
    phrases: List[str] = []
    for it in items:
        txt = getattr(it.book, field, "") or ""
        phrases.extend(extract_phrases(txt))
    freq: dict[str, int] = {}
    for p in phrases:
        freq[p.lower()] = freq.get(p.lower(), 0) + 1
    phrases_sorted = sorted({p for p in phrases}, key=lambda p: (-freq.get(p.lower(), 0), len(p)))
    return phrases_sorted[:limit]



