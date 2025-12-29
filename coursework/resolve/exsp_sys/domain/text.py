from __future__ import annotations

import re
from typing import List


def contains_any(text: str, phrases: List[str]) -> int:
    if not text or not phrases:
        return 0
    t = text.lower()
    c = 0
    for p in phrases:
        ps = (p or "").strip().lower()
        if ps and ps in t:
            c += 1
    return c


def _normalize_phrase(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s.strip(" -–—•\t")


def extract_phrases(text: str, max_len: int = 120) -> List[str]:
    """Режет длинный текст на короткие фразы для вариантов ответа."""
    t = (text or "").replace("\r", "\n")
    t = re.sub(r"[•*]+", " ", t)
    chunks = re.split(r"[.;\n]+", t)
    out: List[str] = []
    for c in chunks:
        c = _normalize_phrase(c)
        if not c:
            continue
        if len(c) > max_len:
            for part in c.split(","):
                part = _normalize_phrase(part)
                if 6 <= len(part) <= max_len:
                    out.append(part)
        else:
            if len(c) >= 6:
                out.append(c)
    seen = set()
    uniq: List[str] = []
    for x in out:
        k = x.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(x)
    return uniq



