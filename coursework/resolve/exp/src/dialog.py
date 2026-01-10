from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Optional, Tuple

from frames_repo import string_normalize


from models import *


def default_questions() -> List[Question]:
    # Минимальный, но полезный набор признаков (можно расширять позже без переделки архитектуры)
    return [
        Question(field="жанр", prompt="Выберите жанр (пример: роман, эпопея, повесть) или напишите skip"),
        Question(field="эпоха", prompt="Выберите эпоху (пример: начало_XIX, середина_XIX) или skip"),
        Question(field="настроение", prompt="Выберите настроение (пример: философское, лирическое, сатирическое) или skip"),
        Question(field="сложность", prompt="Выберите сложность (низкая/средняя/высокая) или skip"),
        Question(field="объём", prompt="Выберите объём (короткое/среднее/длинное) или skip"),
        Question(field="темы", prompt="Темы: можно 1 или несколько через запятую (пример: любовь, война) или skip", multi=True),
    ]


class DialogSession:
    def __init__(self, option_map: Mapping[str, Mapping[str, str]]) -> None:
        self.option_map = option_map
        self.questions = default_questions()
        self.idx = 0
        self.prefs: List[Tuple[str, str]] = []

    def is_done(self) -> bool:
        return self.idx >= len(self.questions)

    def current(self) -> Optional[Question]:
        if self.is_done():
            return None
        return self.questions[self.idx]

    def advance(self) -> None:
        self.idx += 1



    def add_answer(self, answer: ClientAnswer) -> None:
        """
        Добавляет ответ пользователя в сессию.
        
        Raises:
            DialogError: если ответ невалиден.
        """
        q = self.current()
        if not q:
            raise DialogError("Диалог уже завершён.")

        if not answer:
            raise DialogError("Пустой ответ. Необходимо значение.")

        field = q.field
        options_map = self.option_map.get(field, {})

        if q.multi:
            accepted = 0
            unknown: List[str] = []
            for it in answer.items_answer:
                n = string_normalize(it)
                if n not in options_map:
                    unknown.append(it)
                    continue
                self.prefs.append((field, it))
                accepted += 1
            if accepted == 0:
                raise DialogError(f"Неизвестные значения: {', '.join(unknown)}")
            self.advance()
            return

        if answer.text_answer not in options_map:
            raise DialogError(f"Неизвестное значение. Ваш ответ: {answer.text_answer} Используйте вариант из {options_map} ваших фреймов или skip.")

        self.prefs.append((field, answer.text_answer))
        self.advance()

    def hints_for(self, field: str, limit: int = 16) -> List[str]:
        vals = list(self.option_map.get(field, {}).values())
        vals.sort()
        return vals[: max(1, limit)]
    
    def get_question_message(self):
        q = self.current()
        hints = self.hints_for(q.field, limit=12)
        return QuestionMessage(
                field=q.field,
                text=q.prompt,
                examples=hints,
            )



def format_recommendations(recommendations: Iterable[Any]) -> List[RecommendationItem]:
    """Форматирует список рекомендаций в структуру для отправки клиенту."""
    items: List[RecommendationItem] = []
    for rec in recommendations:
        info = rec.info
        items.append(
            RecommendationItem(
                title=rec.title,
                score=rec.score,
                matched=rec.matched,
                author=info.get("автор"),
                genre=info.get("жанр"),
                epoch=info.get("эпоха"),
                mood=info.get("настроение"),
                difficulty=info.get("сложность"),
                volume=info.get("объём"),
                image=info.get("изображение"),
            )
        )
    return items


