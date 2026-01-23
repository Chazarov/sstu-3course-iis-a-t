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


class MatchProcessed(Fact):
    """Факт о том, что матчинг для книги и предпочтения уже обработан."""
    book_id: str
    field: str
    value: str


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
    
    # Конфигурация весов и приоритетов для разных полей
    FIELD_WEIGHTS = {
        "жанр": 10,           # Жанр - самый важный (вес x3)
        "эпоха": 2,          # Эпоха - важный (вес x2)
        "настроение": 2,     # Настроение - важный (вес x2)
        "темы": 2,           # Темы - важные (вес x2)
        "сложность": 1,      # Обычный вес
        "объём": 1,          # Обычный вес
    }
    
    FIELD_SALIENCE = {
        "жанр": 333,          # Самый высокий приоритет
        "эпоха": 60,
        "настроение": 60,
        "темы": 55,
        "сложность": 50,
        "объём": 50,
    }
    
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
                    # Получаем вес и приоритет для этого поля
                    weight = FIELD_WEIGHTS.get(f, 1)
                    rule_salience = FIELD_SALIENCE.get(f, 50)
                    
                    @Rule(
                        Pref(field=f, value=val),
                        AS.candidate << BookCandidate(book_id=b.id, title=b.title),
                        ~MatchProcessed(book_id=b.id, field=f, value=val),  # Ещё НЕ обработано
                        salience=rule_salience  # Динамический приоритет
                    )
                    def _match(self: KnowledgeEngine, candidate: Fact) -> None:
                        # Модифицируем факт: увеличиваем score с учетом веса
                        self.modify(candidate,
                            score=candidate['score'] + weight,  # Взвешенный score
                            matched=candidate['matched'] | {_human_match(f, val, label_map)}
                        )
                        # Отмечаем как обработанное
                        self.declare(MatchProcessed(book_id=b.id, field=f, value=val))
                    return _match
                
                attrs[f"match__{book.title}__{field}__{value_str}"] = _make_match_rule(book, field, value_str)

    class RecommenderEngine(KnowledgeEngine):
        """Движок рекомендаций на основе experta."""
        pass

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
    Собирает результаты из фактов после выполнения правил.
    """
    engine: KnowledgeEngine = engine_cls()
    engine.reset()
    
    # Декларируем предпочтения
    for field, value in prefs:
        engine.declare(Pref(field=field, value=value))
    
    # Движок выполняет правила через forward chaining
    engine.run()
    
    # Собираем результаты вручную из фактов
    candidates: List[Fact] = []
    for fact in engine.facts.values():
        if isinstance(fact, BookCandidate) and fact['score'] > 0:
            candidates.append(fact)
    
    
    # Сортируем по score
    sorted_results = sorted(candidates, key=lambda c: c['score'], reverse=True)
    
    # Формируем финальный список рекомендаций
    by_title: Dict[str, BookFrame] = {b.title: b for b in frames}
    
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


def get_all_recomendations(frames: Sequence[BookFrame]) -> List[Recommendation]:
    """
    Возвращает все возможные рекомендации (все книги из базы).
    Книги возвращаются без оценки (score=0) и совпадений.
    """
    return [
        Recommendation(
            id=frame.id,
            title=frame.title,
            score=0,
            matched=[],
            info=frame.raw,
        )
        for frame in frames
    ]


 