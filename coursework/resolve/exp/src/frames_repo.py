from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple


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


@dataclass(frozen=True)
class BookFrame:
    title: str
    raw: Mapping[str, Any]
    match: Mapping[str, Any]


def frames_dir_from_repo_root(repo_root: Path) -> Path:
    return repo_root / "sourses" / "frames"


def repo_root_from_src_file(src_file: Path) -> Path:
    # exp/src/<this_file>.py -> exp -> <repo_root>
    return src_file.resolve().parents[2]


def load_frames(frames_dir: Path) -> List[BookFrame]:
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

        frames.append(BookFrame(title=title, raw=raw, match=match))

    return frames


def build_options(frames: Iterable[BookFrame]) -> Dict[str, List[str]]:
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

    return {k: sorted(v) for k, v in options.items()}


def option_map(options: Mapping[str, Iterable[str]]) -> Dict[str, Dict[str, str]]:
    """
    field -> normalized_token -> canonical (as in json)
    """
    out: Dict[str, Dict[str, str]] = {}
    for field, vals in options.items():
        m: Dict[str, str] = {}
        for v in vals:
            m[string_normalize(str(v))] = str(v)
        out[field] = m
    return out


