from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from frames_repo import LIST_FIELDS, MATCH_FIELDS, string_normalize




@dataclass
class Question:
    field: str
    prompt: str
    multi: bool = False


def default_questions() -> List[Question]:
    # Минимальный, но полезный набор признаков (можно расширять позже без переделки архитектуры)
    return [
        Question("жанр", "Выберите жанр (пример: роман, эпопея, повесть) или напишите skip"),
        Question("эпоха", "Выберите эпоху (пример: начало_XIX, середина_XIX) или skip"),
        Question("настроение", "Выберите настроение (пример: философское, лирическое, сатирическое) или skip"),
        Question("сложность", "Выберите сложность (низкая/средняя/высокая) или skip"),
        Question("объём", "Выберите объём (короткое/среднее/длинное) или skip"),
        Question("темы", "Темы: можно 1 или несколько через запятую (пример: любовь, война) или skip", multi=True),
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



    def add_answer(self, answer: List[str]) -> Tuple[bool, str]:
        q = self.current()
        if not q:
            return False, "Диалог уже завершён."

        if not answer:
            return False, "Пустой ответ. Необходимо значение."


        field = q.field
        options_map = self.option_map.get(field, {})

        if q.multi:
            accepted = 0
            unknown: List[str] = []
            for it in answer:
                n = string_normalize(it)
                if n not in options_map:
                    unknown.append(it)
                    continue
                self.prefs.append((field, answer))
                accepted += 1
            if accepted == 0:
                return False, f"Неизвестные значения: {', '.join(unknown)}"
            self.advance()
            return True, "ok"


        if answer not in options_map:
            return False, f"Неизвестное значение. Ваш ответ: {answer} Используйте вариант из {options_map} ваших фреймов или skip."

        self.prefs.append((field, answer))
        self.advance()
        return True, "ok"

    def hints_for(self, field: str, limit: int = 16) -> List[str]:
        vals = list(self.option_map.get(field, {}).values())
        vals.sort()
        return vals[: max(1, limit)]


