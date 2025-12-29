from __future__ import annotations

from typing import Any, Dict, List

from .entities import Preferences


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def rule_matches(rule_if: Dict[str, Any], prefs: Preferences) -> bool:
    for key, wanted in (rule_if or {}).items():
        if key == "объём" and prefs.volume is not None and prefs.volume != wanted:
            return False
        if key == "сложность" and prefs.complexity is not None:
            if isinstance(wanted, list) and prefs.complexity not in wanted:
                return False
            if not isinstance(wanted, list) and prefs.complexity != wanted:
                return False
        if key == "настроение" and prefs.mood is not None:
            if isinstance(wanted, list) and prefs.mood not in wanted:
                return False
            if not isinstance(wanted, list) and prefs.mood != wanted:
                return False
        if key == "темы" and prefs.themes:
            need = set(_as_list(wanted))
            if not (need & set(prefs.themes)):
                return False
        if key == "тип_героя" and prefs.hero_type is not None and prefs.hero_type != wanted:
            return False
        if key == "тип_конфликта" and prefs.conflict_type is not None and prefs.conflict_type != wanted:
            return False
        if key == "художественные_средства" and prefs.artistic_means:
            need = set(_as_list(wanted))
            if not (need & set(prefs.artistic_means)):
                return False
        if key == "эпоха" and prefs.era is not None and prefs.era != wanted:
            return False
        if key == "жанр" and prefs.genre_group:
            need = set(_as_list(wanted))
            if not (need & set(prefs.genre_group)):
                return False
    return True


def rules_by_book(rules: Dict[str, Any], prefs: Preferences) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for _, rule in (rules or {}).items():
        if not rule_matches((rule or {}).get("если", {}) or {}, prefs):
            continue
        for book_name in _as_list((rule or {}).get("то", [])):
            if isinstance(book_name, str) and book_name.strip():
                name = book_name.strip()
                out[name] = out.get(name, 0) + 1
    return out



