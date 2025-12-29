from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder

from  application.ports import SimilarityRanker
from  domain import Book, Preferences


@dataclass(frozen=True)
class SklearnSimilarityRanker(SimilarityRanker):
    """Similarity engine на sklearn.

    Это инфраструктурный адаптер: здесь допустимы numpy/sklearn.
    """

    books: Sequence[Book]
    w_cat: float = 2.5
    w_themes: float = 6.0
    w_means: float = 4.0

    def __post_init__(self) -> None:
        # dataclass(frozen=True) — используем object.__setattr__
        books = list(self.books)
        object.__setattr__(self, "books", books)

        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        cats = [
            [b.volume, b.complexity, b.mood, b.conflict_type, b.hero_type, b.era, b.genre, b.direction] for b in books
        ]
        cat_matrix = ohe.fit_transform(cats) if books else np.zeros((0, 0))

        mlb_themes = MultiLabelBinarizer()
        mlb_means = MultiLabelBinarizer()
        themes = [list(b.themes) for b in books]
        means = [list(b.artistic_means) for b in books]
        themes_matrix = mlb_themes.fit_transform(themes) if books else np.zeros((0, 0))
        means_matrix = mlb_means.fit_transform(means) if books else np.zeros((0, 0))

        book_matrix = (
            np.hstack([cat_matrix * self.w_cat, themes_matrix * self.w_themes, means_matrix * self.w_means])
            if books
            else np.zeros((0, 0))
        )

        object.__setattr__(self, "_ohe", ohe)
        object.__setattr__(self, "_mlb_themes", mlb_themes)
        object.__setattr__(self, "_mlb_means", mlb_means)
        object.__setattr__(self, "_book_matrix", book_matrix)

    def _prefs_vec(self, p: Preferences) -> np.ndarray:
        # genre/direction в предпочтениях явно не спрашиваем => None
        cat = [[p.volume, p.complexity, p.mood, p.conflict_type, p.hero_type, p.era, None, None]]
        cat_vec = self._ohe.transform(cat)
        if p.themes:
            themes_vec = self._mlb_themes.transform([p.themes])
        else:
            themes_vec = np.zeros((1, len(self._mlb_themes.classes_)))
        if p.artistic_means:
            means_vec = self._mlb_means.transform([p.artistic_means])
        else:
            means_vec = np.zeros((1, len(self._mlb_means.classes_)))
        return np.hstack([cat_vec * self.w_cat, themes_vec * self.w_themes, means_vec * self.w_means]).astype(float)

    def similarities(self, prefs: Preferences) -> List[float]:
        if not self.books:
            return []
        v = self._prefs_vec(prefs)
        sims = cosine_similarity(v, self._book_matrix)[0]
        return [float(x) for x in sims.tolist()]



