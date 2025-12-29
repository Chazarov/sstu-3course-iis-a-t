from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from  application.ports import DataBundle
from  domain import Book


def _read_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


@dataclass(frozen=True)
class FileSystemJsonDataSource:
    """Загрузка данных из папки `sourses/`."""

    data_dir: Path

    def load(self) -> DataBundle:
        config = _read_json(self.data_dir / "config.json")
        questions = _read_json(self.data_dir / "data" / "вопросы.json")
        rules = (_read_json(self.data_dir / "rules" / "правила.json") or {}).get("правила", {}) or {}
        catalog = (_read_json(self.data_dir / "data" / "каталог.json") or {}).get("произведения", {}) or {}

        books: List[Book] = []
        for _, info in catalog.items():
            fp = self.data_dir / "parametrs" / info["файл"]
            try:
                d = _read_json(fp)
            except Exception:
                continue

            books.append(
                Book(
                    name=str(info.get("название", "")).strip(),
                    author=str(d.get("автор", info.get("автор", "")) or "").strip(),
                    genre=str(d.get("жанр", "") or "").strip(),
                    era=str(d.get("эпоха", "") or "").strip(),
                    direction=str(d.get("направление", "") or "").strip(),
                    complexity=str(d.get("сложность", "") or "").strip(),
                    volume=str(d.get("объём", "") or "").strip(),
                    mood=str(d.get("настроение", "") or "").strip(),
                    themes=tuple(d.get("темы", []) or []),
                    conflict_type=str(d.get("тип_конфликта", "") or "").strip(),
                    hero_type=str(d.get("тип_героя", "") or "").strip(),
                    artistic_means=tuple(d.get("художественные_средства", []) or []),
                    pages=int(d.get("страницы", 0) or 0),
                    year=int(d.get("год", info.get("год", 0)) or 0),
                    author_position=str(d.get("авторская_позиция", "") or "").strip(),
                    audience=str(d.get("аудитория", "") or "").strip(),
                    attention_points=str(d.get("точки_внимания", "") or "").strip(),
                    weaknesses=str(d.get("слабые_стороны", "") or "").strip(),
                    interpretations=str(d.get("интерпретации", "") or "").strip(),
                    image_file=str(d.get("изображение", "") or "").strip(),
                )
            )

        return DataBundle(books=books, config=config, questions=questions, rules=rules)



