from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

from models import BookFrame


def string_normalize(v: str) -> str:
    return v.strip().lower().replace(" ", "_")


MATCH_FIELDS: Tuple[str, ...] = (
    "автор",
    "жанр",
    "эпоха",
    "направление",
    "сложность",
    "объём",
    "настроение",
    "тип_конфликта",
    "тип_героя",
    "темы",
    "художественные_средства",
)

LIST_FIELDS: Set[str] = {"темы", "художественные_средства"}




def frames_dir_from_repo_root(repo_root: Path) -> Path:
    return repo_root / "sourses" / "frames"


def repo_root_from_src_file(src_file: Path) -> Path:
    # exp/src/<this_file>.py -> exp -> <repo_root>
    return src_file.resolve().parents[2]


def load_frames(frames_dir: Path, id_counter:int) -> Tuple[BookFrame, ...]:
    """
    Кэшированная версия загрузки фреймов.
    Использует строку вместо Path для хэширования.
    Возвращает tuple вместо list для хэширования.
    """
    id_counter = 0
    frames: List[BookFrame] = []
    for p in sorted(frames_dir.glob("*.json")):
        with p.open("r", encoding="utf-8") as f:
            raw: Dict[str, Any] = json.load(f)

        title = p.stem
        match: Dict[str, Any] = {}
        for k in MATCH_FIELDS:
            if k not in raw:
                continue
            v = raw[k]
            if k in LIST_FIELDS and isinstance(v, list):
                match[k] = [string_normalize(str(x)) for x in v]
            elif isinstance(v, str):
                match[k] = string_normalize(v)
            else:
                # числовые поля пока не используем для матчей
                match[k] = v

        frames.append(BookFrame(title=title, raw=raw, match=match, id="frame-" + id_counter))
        id_counter += 1

    return tuple(frames)



# Глобальный кэш для build_options (нельзя использовать lru_cache из-за unhashable dict в BookFrame)
_build_options_cache: Optional[Dict[str, List[str]]] = None


def build_options(frames: Iterable[BookFrame]) -> Dict[str, List[str]]:
    """
    Строит список опций из фреймов с кэшированием.
    """
    global _build_options_cache
    
    if _build_options_cache is not None:
        return _build_options_cache
    
    options: Dict[str, Set[str]] = {k: set() for k in MATCH_FIELDS}
    for b in frames:
        for k, v in b.raw.items():
            if k not in options:
                continue
            if k in LIST_FIELDS and isinstance(v, list):
                for x in v:
                    options[k].add(str(x))
            elif isinstance(v, str):
                options[k].add(v)

    _build_options_cache = {k: sorted(v) for k, v in options.items()}
    return _build_options_cache


@lru_cache(maxsize=1)
def _option_map_cached(options_tuple: Tuple[Tuple[str, Tuple[str, ...]], ...]) -> Dict[str, Dict[str, str]]:
    """Кэшированная версия option_map."""
    out: Dict[str, Dict[str, str]] = {}
    for field, vals in options_tuple:
        m: Dict[str, str] = {}
        for v in vals:
            m[string_normalize(str(v))] = str(v)
        out[field] = m
    return out


def option_map(options: Mapping[str, Iterable[str]]) -> Dict[str, Dict[str, str]]:
    """
    field -> normalized_token -> canonical (as in json)
    С кэшированием результата.
    """
    # Конвертируем в хэшируемый формат для кэширования
    options_tuple = tuple(
        (field, tuple(vals) if not isinstance(vals, tuple) else vals)
        for field, vals in sorted(options.items())
    )
    return _option_map_cached(options_tuple)


def clear_frames_cache() -> None:
    """
    Очищает кэш загрузки фреймов и связанных данных.
    Используется для перезагрузки данных или в тестах.
    """
    global _build_options_cache
    _build_options_cache = None
    load_frames.cache_clear()
    _option_map_cached.cache_clear()


