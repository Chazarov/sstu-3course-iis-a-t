from __future__ import annotations

from dataclasses import dataclass
from math import exp, log2
from typing import Any, Dict, List, Optional, Sequence, Tuple

from  application.ports import SimilarityRanker
from  domain import Book, Preferences
from  domain.rules import rules_by_book
from  domain.text import contains_any


@dataclass(frozen=True)
class RankedBook:
    book: Book
    score: float
    similarity: float
    rules_count: int


class RecommendationService:
    """Use-case: ранжирование книг по предпочтениям."""

    def __init__(self, books: Sequence[Book], rules: Dict[str, Any], ranker: SimilarityRanker) -> None:
        self._books = list(books)
        self._rules = rules or {}
        self._ranker = ranker

    @property
    def books(self) -> Sequence[Book]:
        return self._books

    @property
    def rules(self) -> Dict[str, Any]:
        return self._rules

    def rank(self, prefs: Preferences, top_k: int = 10) -> List[RankedBook]:
        if not self._books:
            return []

        sims = self._ranker.similarities(prefs)
        rb = rules_by_book(self._rules, prefs)
        allowed_genres = set(prefs.genre_group or [])

        items: List[RankedBook] = []
        for i, b in enumerate(self._books):
            if allowed_genres and b.genre not in allowed_genres:
                continue

            similarity = float(sims[i]) if i < len(sims) else 0.0
            rules_count = int(rb.get(b.name, 0))

            score = similarity
            score += 0.10 * float(rules_count)
            score += 0.06 * float(contains_any(b.author_position, prefs.liked_author_position))
            score += 0.06 * float(contains_any(b.audience, prefs.liked_audience))
            score += 0.08 * float(contains_any(b.interpretations, prefs.liked_interpretations))
            score -= 0.10 * float(contains_any(b.weaknesses, prefs.disliked_weaknesses))

            items.append(RankedBook(book=b, score=score, similarity=similarity, rules_count=rules_count))

        items.sort(key=lambda x: x.score, reverse=True)
        return items[: max(1, top_k)]

    @staticmethod
    def softmax(scores: Sequence[float], sharpness: float = 1.0) -> List[float]:
        if not scores:
            return []
        scaled = [float(s) * float(sharpness) for s in scores]
        m = max(scaled)
        exps = [exp(x - m) for x in scaled]
        s = sum(exps)
        if s <= 0:
            return [1.0 / len(exps)] * len(exps)
        return [e / s for e in exps]

    @staticmethod
    def entropy(probs: Sequence[float]) -> float:
        p = [float(x) for x in probs if float(x) > 0.0]
        if not p:
            return 0.0
        return float(-sum(x * log2(x) for x in p))

    def rank_all_with_probs(self, prefs: Preferences, sharpness: float = 10.0) -> Tuple[List[RankedBook], List[float]]:
        ranked = self.rank(prefs, top_k=len(self._books))
        probs = self.softmax([it.score for it in ranked], sharpness=sharpness)
        return ranked, probs

    def should_finish_questions(self, prefs: Preferences, asked_dynamic_count: int, max_dynamic_questions: int, sharpness: float = 10.0) -> bool:
        ranked, probs = self.rank_all_with_probs(prefs, sharpness=sharpness)
        if len(ranked) <= 1:
            return True
        top_prob = float(probs[0]) if probs else 0.0
        ent = self.entropy(probs)

        if asked_dynamic_count >= max_dynamic_questions:
            return True
        if asked_dynamic_count >= 2 and top_prob >= 0.58:
            return True
        if ent <= 1.2:
            return True
        return False



