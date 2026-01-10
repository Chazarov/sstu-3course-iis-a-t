from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, DefaultDict, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from experta import Fact, KnowledgeEngine, Rule

from frames_repo import BookFrame
from models import Recommendation


class Pref(Fact):
    field: str
    value: Any




def _human_match(field: str, value: str, label_map: Mapping[str, Mapping[str, str]]) -> str:
    m = label_map.get(field, {})
    return f"{field}={m.get(value, value)}"


def build_engine_class(
    frames: Sequence[BookFrame],
    label_map: Mapping[str, Mapping[str, str]],
) -> type:
    attrs: Dict[str, Any] = {}

    def _make_rule(book: BookFrame, field: str, expected: str) -> Callable[[KnowledgeEngine], None]:
        @Rule(Pref(field=field, value=expected))
        def _r(self: KnowledgeEngine) -> None:
            self.scores[book.title] += 1
            self.matched[book.title].add(_human_match(field, expected, label_map))

        return _r

    seen: Set[Tuple[str, str, str]] = set()
    for book in frames:
        for field, v in book.match.items():
            if isinstance(v, list):
                for item in v:
                    key = (book.title, field, str(item))
                    if key in seen:
                        continue
                    seen.add(key)
                    attrs[f"rule__{book.title}__{field}__{item}"] = _make_rule(book, field, str(item))
            elif isinstance(v, str):
                key = (book.title, field, v)
                if key in seen:
                    continue
                seen.add(key)
                attrs[f"rule__{book.title}__{field}__{v}"] = _make_rule(book, field, v)

    class RecommenderEngine(KnowledgeEngine):
        def __init__(self) -> None:
            super().__init__()
            self.scores: DefaultDict[str, int] = defaultdict(int)
            self.matched: DefaultDict[str, Set[str]] = defaultdict(set)

    for k, v in attrs.items():
        setattr(RecommenderEngine, k, v)

    return RecommenderEngine


def get_recomendations(
    engine_cls: type,
    frames: Sequence[BookFrame],
    prefs: Iterable[Tuple[str, str]],
    top_k: int = 5,
) -> List[Recommendation]:
    engine: KnowledgeEngine = engine_cls()
    engine.reset()
    for field, value in prefs:
        engine.declare(Pref(field=field, value=value))
    engine.run()

    by_title: Dict[str, BookFrame] = {b.title: b for b in frames}
    scored = [(t, engine.scores.get(t, 0)) for t in by_title.keys()]
    scored.sort(key=lambda x: x[1], reverse=True)

    out: List[Recommendation] = []
    for title, score in scored[: max(top_k, 1)]:
        if score <= 0:
            continue
        out.append(
            Recommendation(
                title=title,
                score=score,
                matched=sorted(engine.matched.get(title, set())),
                info=by_title[title].raw,
            )
        )
    return out


