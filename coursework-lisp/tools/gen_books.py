import json
import glob
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "sourses" / "frames"
OUT = ROOT / "lisp" / "src" / "books.lisp"

MATCH = [
    "автор", "жанр", "эпоха", "направление", "сложность", "объём",
    "настроение", "тип_конфликта", "тип_героя", "темы", "художественные_средства",
]
LIST = {"темы", "художественные_средства"}


def norm(v: str) -> str:
    return v.strip().lower().replace(" ", "_")


def lisp_str(s) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def kw(k: str) -> str:
    return ":" + k


def raw_plist(raw: dict) -> str:
    parts = []
    for k, v in raw.items():
        if isinstance(v, list):
            parts.append(f"({kw(k)} ({' '.join(lisp_str(x) for x in v)}))")
        elif isinstance(v, str):
            parts.append(f"({kw(k)} {lisp_str(v)})")
        elif isinstance(v, (int, float)):
            parts.append(f"({kw(k)} {v})")
    return " ".join(parts)


def match_lisp(match: list) -> str:
    parts = []
    for k, v in match:
        if isinstance(v, list):
            parts.append(f"({lisp_str(k)} ({' '.join(lisp_str(x) for x in v)}))")
        else:
            parts.append(f"({lisp_str(k)} {lisp_str(v)})")
    return " ".join(parts)


def main() -> None:
    lines = ["(in-package :expert/frames)", "", "(defparameter +books-data+", "  '("]
    for i, path in enumerate(sorted(FRAMES.glob("*.json"))):
        raw = json.loads(path.read_text(encoding="utf-8"))
        title = path.stem
        match = []
        for k in MATCH:
            if k not in raw:
                continue
            v = raw[k]
            if k in LIST and isinstance(v, list):
                match.append((k, [norm(str(x)) for x in v]))
            elif isinstance(v, str):
                match.append((k, norm(v)))
        lines.append(f"   (list :id {lisp_str(f'frame-{i}')} :title {lisp_str(title)}")
        lines.append(f"         :raw (list {raw_plist(raw)})")
        lines.append(f"         :match (list {match_lisp(match)}))")
    lines.append("   ))")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written {OUT} ({i + 1} books)")


if __name__ == "__main__":
    main()
