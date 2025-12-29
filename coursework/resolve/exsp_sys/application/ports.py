from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, Sequence

from  domain import Book, Preferences


class SimilarityRanker(Protocol):
    """Порт: вычисление similarity (0..1) для каждой книги по текущим Preferences."""

    def similarities(self, prefs: Preferences) -> List[float]:
        raise NotImplementedError


@dataclass(frozen=True)
class DataBundle:
    books: Sequence[Book]
    config: Dict[str, Any]
    questions: Dict[str, Any]
    rules: Dict[str, Any]



