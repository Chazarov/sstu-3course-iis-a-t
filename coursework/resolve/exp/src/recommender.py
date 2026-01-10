from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from experta import AS, Fact, KnowledgeEngine, Rule
from loguru import logger

from frames_repo import BookFrame
from models import Recommendation


class Pref(Fact):
    """Факт предпочтения пользователя."""
    field: str
    value: Any


class BookCandidate(Fact):
    """Факт-кандидат для рекомендации."""
    book_id: str
    title: str
    score: int
    matched: Set[str]


def _human_match(field: str, value: str, label_map: Mapping[str, Mapping[str, str]]) -> str:
    """Форматирует совпадение для отображения."""
    m = label_map.get(field, {})
    return f"{field}={m.get(value, value)}"


def build_engine_class(
    frames: Sequence[BookFrame],
    label_map: Mapping[str, Mapping[str, str]],
) -> type:
    """
    Строит класс движка экспертной системы.
    Использует forward chaining для вывода рекомендаций.
    """
    attrs: Dict[str, Any] = {}
    
    # Правила для инициализации кандидатов (высокий приоритет)
    for book in frames:
        def _make_init_rule(b: BookFrame) -> Callable:
            @Rule(salience=100)  # Высокий приоритет - выполняются первыми
            def _init(self: KnowledgeEngine) -> None:
                self.declare(BookCandidate(
                    book_id=b.id,
                    title=b.title,
                    score=0,
                    matched=set()
                ))
            return _init
        
        attrs[f"init__{book.title}"] = _make_init_rule(book)
    
    # Правила для увеличения score при совпадении
    seen: Set[Tuple[str, str, str]] = set()
    for book in frames:
        for field, v in book.match.items():
            values = [v] if isinstance(v, str) else (v if isinstance(v, list) else [])
            
            for value in values:
                value_str = str(value)
                key = (book.title, field, value_str)
                if key in seen:
                    continue
                seen.add(key)
                
                def _make_match_rule(b: BookFrame, f: str, val: str) -> Callable:
                    @Rule(
                        Pref(field=f, value=val),
                        AS.candidate << BookCandidate(book_id=b.id, title=b.title),
                        salience=50
                    )
                    def _match(self: KnowledgeEngine, candidate: Fact) -> None:
                        # Модифицируем факт: увеличиваем score
                        self.modify(candidate,
                            score=candidate['score'] + 1,
                            matched=candidate['matched'] | {_human_match(f, val, label_map)}
                        )
                    return _match
                
                attrs[f"match__{book.title}__{field}__{value_str}"] = _make_match_rule(book, field, value_str)
    
    # Правило для сбора результатов (низкий приоритет - выполняется последним)
    @Rule(
        AS.candidate << BookCandidate(score=lambda s: s > 0),
        salience=10
    )
    def _collect_result(self: KnowledgeEngine, candidate: Fact) -> None:
        """Собирает кандидатов с ненулевым score в результаты."""
        self.results.append(candidate)
    
    attrs['_collect_result'] = _collect_result

    class RecommenderEngine(KnowledgeEngine):
        """Движок рекомендаций на основе experta."""
        def __init__(self) -> None:
            super().__init__()
            self.results: List[Fact] = []  # Движок сам собирает результаты

    for k, v in attrs.items():
        setattr(RecommenderEngine, k, v)

    return RecommenderEngine


def get_recomendations(
    engine_cls: type,
    frames: Sequence[BookFrame],
    prefs: Iterable[Tuple[str, str]],
    top_k: int = 5
) -> List[Recommendation]:
    """
    Получает рекомендации используя экспертную систему.
    Движок сам собирает результаты через правила.
    """
    engine: KnowledgeEngine = engine_cls()
    engine.reset()

    logger.info(" движок перезапущен")
    
    # Декларируем предпочтения
    for field, value in prefs:
        engine.declare(Pref(field=field, value=value))

    logger.info(" предпочтения загружены")
    
    # Движок сам выводит все через forward chaining
    # Результаты автоматически собираются в engine.results
    engine.run()
    logger.info(" движок отработал")
    
    # Результаты УЖЕ в engine.results! Просто сортируем и форматируем
    by_title: Dict[str, BookFrame] = {b.title: b for b in frames}
    
    # Сортируем по score
    sorted_results = sorted(engine.results, key=lambda c: c['score'], reverse=True)
    
    # Формируем финальный список рекомендаций
    return [
        Recommendation(
            id=by_title[candidate['title']].id,
            title=candidate['title'],
            score=candidate['score'],
            matched=sorted(candidate['matched']),
            info=by_title[candidate['title']].raw,
        )
        for candidate in sorted_results[:top_k]
    ]


 