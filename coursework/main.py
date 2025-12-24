

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


# ---------------------------
# ТЁМНАЯ ТЕМА (палитра)
# ---------------------------
COL_PRIMARY = "#FC703C"
COL_DARK = "#5D0703"
COL_LIGHT = "#F4F3E6"
COL_ACCENT = "#FFA175"

COL_BG = COL_DARK
COL_SURFACE = COL_DARK
COL_TEXT = COL_LIGHT
COL_MUTED = COL_ACCENT


# ---------------------------
# МОДЕЛЬ ДАННЫХ
# ---------------------------
@dataclass(frozen=True)
class Book:
    name: str
    author: str
    genre: str
    era: str
    direction: str
    complexity: str
    volume: str
    mood: str
    themes: Tuple[str, ...]
    conflict_type: str
    hero_type: str
    artistic_means: Tuple[str, ...]
    pages: int
    year: int
    author_position: str  # (14)
    audience: str  # (15)
    attention_points: str  # (16)
    weaknesses: str  # (17)
    interpretations: str  # (18)
    image_file: str  # имя файла изображения обложки


@dataclass
class Preferences:
    volume: Optional[str] = None
    complexity: Optional[str] = None
    mood: Optional[str] = None
    themes: List[str] = None
    hero_type: Optional[str] = None
    conflict_type: Optional[str] = None
    artistic_means: List[str] = None
    era: Optional[str] = None
    genre_group: Optional[List[str]] = None

    # 14/15/17/18 — текстовые предпочтения
    liked_author_position: List[str] = None  # 14
    liked_audience: List[str] = None  # 15
    disliked_weaknesses: List[str] = None  # 17 (негатив)
    liked_interpretations: List[str] = None  # 18

    def __post_init__(self) -> None:
        self.themes = self.themes or []
        self.artistic_means = self.artistic_means or []
        self.liked_author_position = self.liked_author_position or []
        self.liked_audience = self.liked_audience or []
        self.disliked_weaknesses = self.disliked_weaknesses or []
        self.liked_interpretations = self.liked_interpretations or []


# ---------------------------
# ЗАГРУЗКА ДАННЫХ
# ---------------------------
def _read_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_data(data_dir: Path) -> Tuple[List[Book], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    config = _read_json(data_dir / "config.json")
    questions = _read_json(data_dir / "data" / "вопросы.json")
    rules = _read_json(data_dir / "rules" / "правила.json").get("правила", {})
    catalog = _read_json(data_dir / "data" / "каталог.json").get("произведения", {})

    books: List[Book] = []
    for _, info in catalog.items():
        fp = data_dir / "parametrs" / info["файл"]
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

    return books, config, questions, rules


# ---------------------------
# ПРАВИЛА (минимально)
# ---------------------------
def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def rule_matches(rule_if: Dict[str, Any], prefs: Preferences) -> bool:
    for key, wanted in rule_if.items():
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
    for _, rule in rules.items():
        if not rule_matches(rule.get("если", {}), prefs):
            continue
        for book_name in _as_list(rule.get("то", [])):
            if isinstance(book_name, str) and book_name.strip():
                out[book_name.strip()] = out.get(book_name.strip(), 0) + 1
    return out


# ---------------------------
# ML + текстовые предпочтения
# ---------------------------
def _contains_any(text: str, phrases: List[str]) -> int:
    if not text or not phrases:
        return 0
    t = text.lower()
    c = 0
    for p in phrases:
        ps = (p or "").strip().lower()
        if ps and ps in t:
            c += 1
    return c


class Recommender:
    def __init__(self, books: List[Book], rules: Dict[str, Any]):
        self.books = books
        self.rules = rules

        self.ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        cats = [[b.volume, b.complexity, b.mood, b.conflict_type, b.hero_type, b.era, b.genre, b.direction] for b in books]
        self.cat_matrix = self.ohe.fit_transform(cats) if books else np.zeros((0, 0))

        self.mlb_themes = MultiLabelBinarizer()
        self.mlb_means = MultiLabelBinarizer()
        themes = [list(b.themes) for b in books]
        means = [list(b.artistic_means) for b in books]
        self.themes_matrix = self.mlb_themes.fit_transform(themes) if books else np.zeros((0, 0))
        self.means_matrix = self.mlb_means.fit_transform(means) if books else np.zeros((0, 0))

        self.book_matrix = np.hstack([self.cat_matrix, self.themes_matrix, self.means_matrix]) if books else np.zeros((0, 0))

    def _prefs_vec(self, p: Preferences) -> np.ndarray:
        cat = [[p.volume, p.complexity, p.mood, p.conflict_type, p.hero_type, p.era, None, None]]
        cat_vec = self.ohe.transform(cat)
        themes_vec = self.mlb_themes.transform([p.themes]) if p.themes else np.zeros((1, len(self.mlb_themes.classes_)))
        means_vec = self.mlb_means.transform([p.artistic_means]) if p.artistic_means else np.zeros((1, len(self.mlb_means.classes_)))
        return np.hstack([cat_vec, themes_vec, means_vec]).astype(float)

    def rank(self, prefs: Preferences, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self.books:
            return []

        allowed_genres = set(prefs.genre_group or [])
        v = self._prefs_vec(prefs)
        sims = cosine_similarity(v, self.book_matrix)[0]

        rb = rules_by_book(self.rules, prefs)

        items: List[Dict[str, Any]] = []
        for i, b in enumerate(self.books):
            if allowed_genres and b.genre not in allowed_genres:
                continue

            score = float(sims[i])

            # Бонус от правил
            score += 0.10 * float(rb.get(b.name, 0))

            # Текстовые предпочтения (14/15/17/18)
            score += 0.06 * _contains_any(b.author_position, prefs.liked_author_position)
            score += 0.06 * _contains_any(b.audience, prefs.liked_audience)
            score += 0.08 * _contains_any(b.interpretations, prefs.liked_interpretations)
            score -= 0.10 * _contains_any(b.weaknesses, prefs.disliked_weaknesses)

            items.append(
                {
                    "book": b,
                    "score": score,
                    "similarity": float(sims[i]),
                    "rules_count": int(rb.get(b.name, 0)),
                }
            )

        items.sort(key=lambda x: x["score"], reverse=True)
        return items[: max(1, top_k)]


# ---------------------------
# ДИНАМИЧЕСКИЕ ОПЦИИ (14/15/17/18)
# ---------------------------
def _normalize_phrase(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s.strip(" -–—•\t")


def extract_phrases(text: str, max_len: int = 120) -> List[str]:
    """
    Делает варианты из длинного текста: режем по . ; \\n и частично по запятым,
    чистим, убираем слишком короткие, ограничиваем длину.
    """
    t = (text or "").replace("\r", "\n")
    t = re.sub(r"[•*]+", " ", t)
    chunks = re.split(r"[.;\n]+", t)
    out: List[str] = []
    for c in chunks:
        c = _normalize_phrase(c)
        if not c:
            continue
        # дополнительно режем слишком длинные куски по запятым
        if len(c) > max_len:
            for part in c.split(","):
                part = _normalize_phrase(part)
                if 6 <= len(part) <= max_len:
                    out.append(part)
        else:
            if len(c) >= 6:
                out.append(c)
    # уникализация с сохранением порядка
    seen = set()
    uniq: List[str] = []
    for x in out:
        k = x.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(x)
    return uniq


def dynamic_options_from_candidates(items: List[Dict[str, Any]], field: str, limit: int = 10) -> List[str]:
    """
    field: author_position | audience | weaknesses | interpretations
    """
    phrases: List[str] = []
    for it in items:
        b: Book = it["book"]
        txt = getattr(b, field, "") or ""
        phrases.extend(extract_phrases(txt))
    # лёгкая сортировка: сначала более частотные
    freq: Dict[str, int] = {}
    for p in phrases:
        freq[p.lower()] = freq.get(p.lower(), 0) + 1
    phrases_sorted = sorted({p for p in phrases}, key=lambda p: (-freq.get(p.lower(), 0), len(p)))
    return phrases_sorted[:limit]


# ---------------------------
# GUI-ВИДЖЕТЫ
# ---------------------------
class ScrollFrame(tk.Frame):
    def __init__(self, master: tk.Widget):
        super().__init__(master, bg=COL_SURFACE)
        self.canvas = tk.Canvas(self, bg=COL_SURFACE, highlightthickness=0)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.inner = tk.Frame(self.canvas, bg=COL_SURFACE)
        self.win_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_cfg)
        self.canvas.bind("<Configure>", self._on_canvas_cfg)
        self.canvas.bind("<MouseWheel>", self._on_wheel)

    def _on_cfg(self, _e: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_cfg(self, e: tk.Event) -> None:
        self.canvas.itemconfigure(self.win_id, width=e.width)

    def _on_wheel(self, e: tk.Event) -> None:
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")


@dataclass(frozen=True)
class Option:
    label: str
    value: Any


@dataclass(frozen=True)
class Step:
    id: str
    title: str
    kind: str  # "single" | "multi" | "result"
    optional: bool
    # source: "json" для Q*, "dynamic" для 14/15/17/18
    source: str
    qid: Optional[str] = None
    dynamic_field: Optional[str] = None


class WizardApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Экспертная система подбора книг")
        self.geometry("1100x720")
        self.minsize(980, 640)
        self.configure(bg=COL_BG)

        self.data_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "sourses"
        if not self.data_dir.exists():
            messagebox.showerror("Ошибка", f"Папка с данными не найдена:\n{self.data_dir}")
            self.destroy()
            return

        try:
            self.books, self.config, self.questions, self.rules = load_data(self.data_dir)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}")
            self.destroy()
            return

        if not self.books:
            messagebox.showerror("Ошибка", "Книги не загружены. Проверьте папку `sourses/parametrs`.")
            self.destroy()
            return

        self.recommender = Recommender(self.books, self.rules)
        self.prefs = Preferences()

        # ДИНАМИЧНЫЙ ОПРОС: вопросы выбираются для уточнения итогового произведения
        self.max_dynamic_questions = 8
        self.finished_flow = False

        # Банк доступных уточняющих вопросов (без P16/RESULT)
        self.step_bank: List[Step] = [
            Step(id="Q1", title="Объём", kind="single", optional=False, source="json", qid="Q1"),
            Step(id="Q2", title="Сложность", kind="single", optional=False, source="json", qid="Q2"),
            Step(id="Q3", title="Настроение", kind="single", optional=False, source="json", qid="Q3"),
            Step(id="Q9", title="Жанровая группа", kind="single", optional=True, source="json", qid="Q9"),
            Step(id="Q5", title="Тип героя", kind="single", optional=True, source="json", qid="Q5"),
            Step(id="Q6", title="Тип конфликта", kind="single", optional=True, source="json", qid="Q6"),
            Step(id="Q8", title="Эпоха", kind="single", optional=True, source="json", qid="Q8"),
            Step(id="THEME", title="Тема (уточнение)", kind="single", optional=True, source="dynamic", dynamic_field="themes"),
            Step(id="MEANS", title="Приём (уточнение)", kind="single", optional=True, source="dynamic", dynamic_field="artistic_means"),
            Step(id="P15", title="Аудитория (15)", kind="single", optional=True, source="dynamic", dynamic_field="audience"),
            Step(id="P14", title="Авторская позиция (14)", kind="single", optional=True, source="dynamic", dynamic_field="author_position"),
            Step(id="P17", title="Слабые стороны (17) — НЕ хочу", kind="single", optional=True, source="dynamic", dynamic_field="weaknesses"),
            Step(id="P18", title="Интерпретации (18)", kind="single", optional=True, source="dynamic", dynamic_field="interpretations"),
        ]

        # Финальные шаги (всегда в конце)
        self.step_final_pick = Step(id="P16", title="Финальный выбор (16): точки внимания", kind="single", optional=False, source="dynamic", dynamic_field="attention_points")
        self.step_result = Step(id="RESULT", title="Итог", kind="result", optional=False, source="dynamic")

        # Поток шагов (формируется динамически)
        self.steps: List[Step] = []
        first = self._choose_next_step()
        self.steps.append(first if first is not None else self.step_bank[0])
        self.step_index = 0

        # ответы: step_id -> {"value": ..., "labels": [...]}
        self.answers: Dict[str, Dict[str, Any]] = {}
        self.final_choice: Optional[Book] = None

        self._build_ui()
        self._render_step()

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        # Header
        header = tk.Frame(self, bg=COL_BG)
        header.pack(fill="x", padx=16, pady=(14, 10))
        tk.Label(
            header,
            text="Подбор книги — пошаговый опрос",
            bg=COL_BG,
            fg=COL_TEXT,
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        # progress bar line
        self.progress = tk.Canvas(self, height=10, bg=COL_BG, highlightthickness=0)
        self.progress.pack(fill="x", padx=16, pady=(0, 12))

        # body split
        body = tk.Frame(self, bg=COL_BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.left = tk.Frame(body, bg=COL_BG)
        self.right = tk.Frame(body, bg=COL_BG, width=320)
        self.right.pack_propagate(False)
        self.left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.right.pack(side="right", fill="y", padx=(10, 0))

        # Question card
        self.card = tk.Frame(self.left, bg=COL_SURFACE, highlightthickness=2, highlightbackground=COL_PRIMARY)
        self.card.pack(fill="both", expand=True)

        self.lbl_step = tk.Label(self.card, text="", bg=COL_SURFACE, fg=COL_MUTED, font=("Segoe UI", 10, "bold"))
        self.lbl_step.pack(anchor="w", padx=14, pady=(12, 0))

        self.lbl_question = tk.Label(
            self.card,
            text="",
            bg=COL_SURFACE,
            fg=COL_TEXT,
            font=("Segoe UI", 14, "bold"),
            wraplength=520,
            justify="left",
        )
        self.lbl_question.pack(anchor="w", padx=14, pady=(6, 6))

        self.lbl_hint = tk.Label(self.card, text="", bg=COL_SURFACE, fg=COL_MUTED, font=("Segoe UI", 9))
        self.lbl_hint.pack(anchor="w", padx=14, pady=(0, 10))

        self.options_scroll = ScrollFrame(self.card)
        self.options_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Buttons
        btns = tk.Frame(self.card, bg=COL_SURFACE)
        btns.pack(fill="x", padx=12, pady=(0, 12))

        self.btn_back = tk.Button(
            btns,
            text="Назад",
            command=self.on_back,
            bg=COL_SURFACE,
            fg=COL_TEXT,
            activebackground=COL_ACCENT,
            activeforeground=COL_DARK,
            relief="flat",
            padx=14,
            pady=8,
            highlightthickness=1,
            highlightbackground=COL_ACCENT,
            font=("Segoe UI", 10, "bold"),
        )
        self.btn_back.pack(side="left")

        self.btn_skip = tk.Button(
            btns,
            text="Пропустить",
            command=self.on_skip,
            bg=COL_SURFACE,
            fg=COL_MUTED,
            activebackground=COL_SURFACE,
            activeforeground=COL_TEXT,
            relief="flat",
            padx=14,
            pady=8,
            highlightthickness=1,
            highlightbackground=COL_ACCENT,
            font=("Segoe UI", 10, "bold"),
        )
        self.btn_skip.pack(side="left", padx=10)

        self.btn_next = tk.Button(
            btns,
            text="Далее",
            command=self.on_next,
            bg=COL_PRIMARY,
            fg=COL_DARK,
            activebackground=COL_ACCENT,
            activeforeground=COL_DARK,
            relief="flat",
            padx=16,
            pady=8,
            font=("Segoe UI", 10, "bold"),
        )
        self.btn_next.pack(side="right")

        # Right: путь ответов (кандидаты во время опроса НЕ показываем)
        path_title = tk.Label(self.right, text="Путь ответов", bg=COL_BG, fg=COL_TEXT, font=("Segoe UI", 14, "bold"))
        path_title.pack(anchor="w")
        

        self.path_text = tk.Text(
            self.right,
            bg=COL_SURFACE,
            fg=COL_TEXT,
            insertbackground=COL_TEXT,
            highlightthickness=2,
            highlightbackground=COL_ACCENT,
            relief="flat",
            font=("Segoe UI", 10),
            wrap="word",
        )
        self.path_text.pack(fill="both", expand=True)
        self.path_text.configure(state="disabled")

        self.btn_copy = tk.Button(
            self.right,
            text="Скопировать путь",
            command=self.on_copy_path,
            bg=COL_ACCENT,
            fg=COL_DARK,
            activebackground=COL_PRIMARY,
            activeforeground=COL_DARK,
            relief="flat",
            padx=14,
            pady=8,
            font=("Segoe UI", 10, "bold"),
        )
        self.btn_copy.pack(anchor="e", pady=(10, 0))
        self.btn_copy.configure(state="disabled")

    # ------------- steps/options -------------
    def _update_progress(self) -> None:
        self.progress.delete("all")
        w = self.progress.winfo_width() or 900
        h = 10
        # Длина опроса динамическая, поэтому прогресс оцениваем относительно лимита
        total = max(1, self.max_dynamic_questions + 2)  # + P16 + RESULT
        done = min(total, self.step_index)
        frac = done / total
        self.progress.create_rectangle(0, 0, w, h, fill=COL_SURFACE, outline=COL_SURFACE)
        self.progress.create_rectangle(0, 0, int(w * frac), h, fill=COL_PRIMARY, outline=COL_PRIMARY)

    def _get_json_question(self, qid: str) -> Dict[str, Any]:
        return (self.questions.get("вопросы", {}) or {}).get(qid, {})

    @staticmethod
    def _entropy(probs: np.ndarray) -> float:
        p = probs[probs > 0]
        if p.size == 0:
            return 0.0
        return float(-(p * np.log2(p)).sum())

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        if x.size == 0:
            return x
        z = x - np.max(x)
        e = np.exp(z)
        s = e.sum()
        return e / s if s > 0 else np.ones_like(x) / len(x)

    def _rank_all(self) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        # 23 книги — можно ранжировать все, это быстро
        ranked = self.recommender.rank(self.prefs, top_k=len(self.books))
        scores = np.array([float(it.get("score", 0.0)) for it in ranked], dtype=float)
        probs = self._softmax(scores)
        return ranked, probs

    def _asked_dynamic_count(self) -> int:
        # считаем только “уточняющие” вопросы (без P16/RESULT)
        cnt = 0
        for s in self.steps:
            if s.id in ("P16", "RESULT"):
                continue
            cnt += 1
        return cnt

    def _should_finish_questions(self) -> bool:
        ranked, probs = self._rank_all()
        if len(ranked) <= 1:
            return True
        top_prob = float(probs[0])
        ent = self._entropy(probs)
        asked = self._asked_dynamic_count()
        if asked >= self.max_dynamic_questions:
            return True
        # если уже достаточно уверенно — переходим к финальному выбору (16)
        if asked >= 2 and top_prob >= 0.58:
            return True
        if ent <= 1.2:
            return True
        return False

    def _match_for_step(self, step: Step, book: Book, option_value: Any) -> bool:
        if option_value is None:
            return False

        # JSON-вопросы
        if step.source == "json":
            if step.id == "Q1":
                return book.volume == option_value
            if step.id == "Q2":
                return book.complexity == option_value
            if step.id == "Q3":
                return book.mood == option_value
            if step.id == "Q5":
                return book.hero_type == option_value
            if step.id == "Q6":
                return book.conflict_type == option_value
            if step.id == "Q8":
                return book.era == option_value
            if step.id == "Q9":
                return isinstance(option_value, list) and book.genre in option_value

        # Динамические
        if step.id == "THEME":
            return isinstance(option_value, str) and option_value in set(book.themes)
        if step.id == "MEANS":
            return isinstance(option_value, str) and option_value in set(book.artistic_means)

        if step.id in ("P14", "P15", "P18", "P17"):
            if not isinstance(option_value, str) or not option_value.strip():
                return False
            needle = option_value.strip().lower()
            if step.id == "P14":
                hay = (book.author_position or "").lower()
                return needle in hay
            if step.id == "P15":
                hay = (book.audience or "").lower()
                return needle in hay
            if step.id == "P18":
                hay = (book.interpretations or "").lower()
                return needle in hay
            if step.id == "P17":
                # “НЕ хочу” → оставляем книги, где этого нет
                hay = (book.weaknesses or "").lower()
                return needle not in hay

        return False

    def _expected_entropy(self, step: Step, ranked: List[Dict[str, Any]], probs: np.ndarray) -> float:
        opts = self._options_for_step(step)
        if len(opts) < 2:
            return 1e9

        masses = 0
        exp_ent = 0.0
        for opt in opts:
            subset_idx: List[int] = []
            for i, it in enumerate(ranked):
                b: Book = it["book"]
                if self._match_for_step(step, b, opt.value):
                    subset_idx.append(i)
            if not subset_idx:
                continue

            mass = float(probs[subset_idx].sum())
            if mass < 0.05:
                continue
            masses += 1
            sub = probs[subset_idx] / mass
            exp_ent += mass * self._entropy(sub)

        # если почти все варианты пустые — вопрос неинформативен
        if masses < 2:
            return 1e9
        return exp_ent

    def _choose_next_step(self) -> Optional[Step]:
        # если уже решили закончить — следующий шаг не нужен
        if self.finished_flow:
            return None
        if self._should_finish_questions():
            return None

        ranked, probs = self._rank_all()
        asked_ids = {s.id for s in self.steps}

        best: Optional[Step] = None
        best_score = 1e18

        for s in self.step_bank:
            if s.id in asked_ids:
                continue
            e = self._expected_entropy(s, ranked, probs)
            if e < best_score:
                best_score = e
                best = s

        return best

    def _options_for_step(self, step: Step) -> List[Option]:
        if step.source == "json" and step.qid:
            q = self._get_json_question(step.qid)
            opts: List[Option] = []
            for v in q.get("варианты", []):
                label = str(v.get("текст", "")).strip()
                value = v.get("значение", None)
                opts.append(Option(label=label, value=value))
            return opts

        if step.source == "dynamic" and step.dynamic_field:
            if step.id == "P16":
                items = self.recommender.rank(self.prefs, top_k=8)
                if not items:
                    return [Option(label="(Не удалось сформировать варианты — вернитесь и выберите больше критериев)", value=None)]
                opts: List[Option] = []
                for it in items:
                    b: Book = it["book"]
                    fit = int(round(float(it["similarity"]) * 100))
                    ap = (b.attention_points or "(нет точек внимания)").strip()
                    ap = re.sub(r"\s+", " ", ap)
                    if len(ap) > 160:
                        ap = ap[:160].rstrip() + "…"
                    # value — индекс книги в self.books (не светим название)
                    try:
                        idx = self.books.index(b)
                    except ValueError:
                        continue
                    opts.append(Option(label=f"{fit}% — {ap}", value=idx))
                return opts or [Option(label="(Нет вариантов — попробуйте изменить ответы)", value=None)]

            if step.id == "THEME":
                items = self.recommender.rank(self.prefs, top_k=10)
                freq: Dict[str, int] = {}
                for it in items:
                    b: Book = it["book"]
                    for t in b.themes:
                        freq[t] = freq.get(t, 0) + 1
                themes = sorted(freq.keys(), key=lambda k: (-freq[k], k))[:8]
                return [Option(label=t, value=t) for t in themes] or [Option(label="(Нет тем для уточнения — пропустите)", value=None)]

            if step.id == "MEANS":
                items = self.recommender.rank(self.prefs, top_k=10)
                freq2: Dict[str, int] = {}
                for it in items:
                    b: Book = it["book"]
                    for m in b.artistic_means:
                        freq2[m] = freq2.get(m, 0) + 1
                means = sorted(freq2.keys(), key=lambda k: (-freq2[k], k))[:8]
                return [Option(label=m, value=m) for m in means] or [Option(label="(Нет приёмов для уточнения — пропустите)", value=None)]

            # 14/15/17/18: варианты из текущих топ-кандидатов
            items = self.recommender.rank(self.prefs, top_k=10)
            phrases = dynamic_options_from_candidates(items, step.dynamic_field, limit=10)
            return [Option(label=p, value=p) for p in phrases] or [Option(label="(Пока нет явных вариантов — пропустите этот шаг)", value=None)]

        return []

    def _apply_answer_to_prefs(self, step_id: str, value: Any) -> None:
        def to_list(v: Any) -> List[str]:
            if v is None:
                return []
            if isinstance(v, list):
                return [x for x in v if isinstance(x, str) and x.strip()]
            if isinstance(v, str) and v.strip():
                return [v.strip()]
            return []

        # Переназначаем prefs на основе step_id; value уже "чистое" значение.
        if step_id == "Q1":
            self.prefs.volume = value
        elif step_id == "Q2":
            self.prefs.complexity = value
        elif step_id == "Q3":
            self.prefs.mood = value
        elif step_id == "Q5":
            self.prefs.hero_type = value
        elif step_id == "Q6":
            self.prefs.conflict_type = value
        elif step_id == "Q8":
            self.prefs.era = value
        elif step_id == "Q9":
            self.prefs.genre_group = value if isinstance(value, list) else None

        # 14/15/17/18
        elif step_id == "THEME":
            self.prefs.themes = list({*self.prefs.themes, *to_list(value)})
        elif step_id == "MEANS":
            self.prefs.artistic_means = list({*self.prefs.artistic_means, *to_list(value)})
        elif step_id == "P14":
            self.prefs.liked_author_position = to_list(value)
        elif step_id == "P15":
            self.prefs.liked_audience = to_list(value)
        elif step_id == "P17":
            self.prefs.disliked_weaknesses = to_list(value)
        elif step_id == "P18":
            self.prefs.liked_interpretations = to_list(value)
        elif step_id == "P16":
            self.final_choice = None
            if isinstance(value, int) and 0 <= value < len(self.books):
                self.final_choice = self.books[value]

    def _render_step(self) -> None:
        step = self.steps[self.step_index]
        self._update_progress()

        # Buttons state
        self.btn_back.configure(state=("disabled" if self.step_index == 0 else "normal"))
        self.btn_skip.configure(state=("normal" if step.optional else "disabled"))
        if step.kind == "result":
            self.btn_next.configure(text="Готово", state="disabled")
            self.btn_skip.configure(state="disabled")
        else:
            self.btn_next.configure(state="normal")
            self.btn_next.configure(text=("Показать итог" if step.id == "P16" else "Далее"))

        # Titles (кол-во вопросов динамическое)
        self.lbl_step.configure(text=f"Шаг {self.step_index + 1}  •  {step.title}")

        # Итоговый экран
        if step.kind == "result":
            self._render_result_screen()
            return

        if step.source == "json" and step.qid:
            q = self._get_json_question(step.qid)
            self.lbl_question.configure(text=str(q.get("текст", "")).strip())
            multi = bool(q.get("множественный_выбор", False))
            self.lbl_hint.configure(text=("Можно выбрать несколько вариантов" if multi else "Выберите один вариант"))
        else:
            # динамические вопросы по 14/15/17/18
            if step.id == "P17":
                self.lbl_question.configure(text="Какие слабые стороны (по мнению критиков) вы бы НЕ хотели видеть в книге?")
                self.lbl_hint.configure(text="Выберите всё, что вам точно не подходит (это понизит рейтинг книг с такими особенностями).")
            elif step.id == "P18":
                self.lbl_question.configure(text="Какая интерпретация/ракурс вам интереснее?")
                self.lbl_hint.configure(text="Выбор увеличит вероятность книг, где встречается такой ракурс.")
            elif step.id == "P16":
                self.lbl_question.configure(text="Финальный вопрос: какие темы вам подходят больше всего?")
                self.lbl_hint.configure(text="Выберите один вариант. Процент — насколько подходит по вашим ответам.")
            elif step.id == "THEME":
                self.lbl_question.configure(text="Какая тема вам ближе?")
                self.lbl_hint.configure(text="Этот вопрос подбирается динамически по текущим кандидатам.")
            elif step.id == "MEANS":
                self.lbl_question.configure(text="Какой художественный приём вам интереснее?")
                self.lbl_hint.configure(text="Этот вопрос подбирается динамически по текущим кандидатам.")
            elif step.id == "P15":
                self.lbl_question.configure(text="Для какой аудитории должна быть книга?")
                self.lbl_hint.configure(text="Подберу ближе по формулировкам из описаний книг.")
            elif step.id == "P14":
                self.lbl_question.configure(text="Какая авторская позиция вам ближе?")
                self.lbl_hint.configure(text="Подберу ближе по формулировкам из описаний книг.")
            else:
                self.lbl_question.configure(text=step.title)
                self.lbl_hint.configure(text="")

        # render options
        for w in self.options_scroll.inner.winfo_children():
            w.destroy()

        opts = self._options_for_step(step)
        saved = (self.answers.get(step.id, {}) or {}).get("value", None)

        if step.kind == "single":
            sv = tk.StringVar(value=self._encode_value(saved))
            self._current_var = ("single", sv)
            for opt in opts:
                tk.Radiobutton(
                    self.options_scroll.inner,
                    text=opt.label,
                    variable=sv,
                    value=self._encode_value(opt.value),
                    bg=COL_SURFACE,
                    fg=COL_TEXT,
                    activebackground=COL_SURFACE,
                    activeforeground=COL_TEXT,
                    selectcolor=COL_SURFACE,
                    wraplength=450,
                    justify="left",
                    font=("Segoe UI", 10),
                    anchor="w",
                ).pack(anchor="w", padx=12, pady=6, fill="x")
        else:
            # multi
            items: List[Tuple[tk.BooleanVar, Any]] = []
            saved_set = set(self._safe_list(saved))
            for opt in opts:
                bv = tk.BooleanVar(value=(opt.value in saved_set))
                items.append((bv, opt.value))
                tk.Checkbutton(
                    self.options_scroll.inner,
                    text=opt.label,
                    variable=bv,
                    bg=COL_SURFACE,
                    fg=COL_TEXT,
                    activebackground=COL_SURFACE,
                    activeforeground=COL_TEXT,
                    selectcolor=COL_SURFACE,
                    wraplength=450,
                    justify="left",
                    font=("Segoe UI", 10),
                    anchor="w",
                ).pack(anchor="w", padx=12, pady=6, fill="x")
            self._current_var = ("multi", items)

        # обновляем путь ответов, но не показываем кандидатов
        self._render_path()
        self.btn_copy.configure(state="disabled")

    # кандидаты во время опроса не показываем — вместо этого ведём “путь ответов”
    def _render_path(self) -> None:
        text = self._build_path_text()
        self.path_text.configure(state="normal")
        self.path_text.delete("1.0", "end")
        self.path_text.insert("1.0", text)
        self.path_text.configure(state="disabled")

    # ---------------- actions ----------------
    def on_back(self) -> None:
        if self.step_index <= 0:
            return
        self.step_index -= 1
        self._rebuild_prefs_from_answers()
        self._render_step()

    def on_skip(self) -> None:
        step = self.steps[self.step_index]
        if not step.optional:
            return
        # если пропускаем вопрос в середине — отбрасываем будущие шаги и пересчитаем дальше
        self._truncate_future()
        self.answers.pop(step.id, None)
        self._rebuild_prefs_from_answers()
        self._advance()

    def on_next(self) -> None:
        step = self.steps[self.step_index]
        if step.kind == "result":
            return

        # если пользователь вернулся назад и отвечает заново — удаляем будущую ветку
        self._truncate_future()

        opts = self._options_for_step(step)
        value = self._read_current_selection(step.kind)
        labels = self._labels_for_value(opts, value)

        # обязательные шаги не пропускаем
        if (not step.optional) and (value is None or (isinstance(value, list) and len(value) == 0)):
            messagebox.showwarning("Нужно выбрать", "Пожалуйста, выберите вариант, чтобы продолжить.")
            return

        self.answers[step.id] = {"value": value, "labels": labels}
        self._apply_answer_to_prefs(step.id, value)
        self._advance()

    def _truncate_future(self) -> None:
        """Если ответ меняют не на последнем шаге — удаляем все будущие шаги и ответы, чтобы опрос пересчитался."""
        if self.step_index >= len(self.steps) - 1:
            return
        keep = [s.id for s in self.steps[: self.step_index + 1]]
        self.steps = self.steps[: self.step_index + 1]
        for k in list(self.answers.keys()):
            if k not in keep:
                self.answers.pop(k, None)
        self.final_choice = None
        self.finished_flow = False

    def _advance(self) -> None:
        current = self.steps[self.step_index]

        # если мы в конце текущего потока — добавляем следующий шаг динамически
        if self.step_index == len(self.steps) - 1 and current.id != "RESULT":
            if current.id == "P16":
                # после финального выбора идём в RESULT
                if not any(s.id == "RESULT" for s in self.steps):
                    self.steps.append(self.step_result)
                self.finished_flow = True
            else:
                # решаем: задаём ещё уточняющий вопрос или переходим к P16
                nxt = self._choose_next_step()
                if nxt is None:
                    if not any(s.id == "P16" for s in self.steps):
                        self.steps.append(self.step_final_pick)
                    self.finished_flow = True
                else:
                    self.steps.append(nxt)

        # двигаемся вперёд
        if self.step_index < len(self.steps) - 1:
            self.step_index += 1
        self._render_step()

    def _labels_for_value(self, opts: List[Option], value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            out: List[str] = []
            for v in value:
                out.extend(self._labels_for_value(opts, v))
            return [x for x in out if x]
        for o in opts:
            if o.value == value:
                return [o.label]
        return [str(value)]

    def _build_path_text(self) -> str:
        lines: List[str] = []
        for step in self.steps:
            if step.kind == "result":
                continue
            if step.id not in self.answers:
                continue
            labels = (self.answers.get(step.id, {}) or {}).get("labels", []) or []
            if not labels:
                continue

            lines.append(step.title)
            if len(labels) > 1:
                for lab in labels:
                    lines.append(f"  - {lab}")
            else:
                lines.append(f"  Ответ: {labels[0]}")
            lines.append("")
        return "\n".join(lines).strip() or "Пока нет ответов."

    def on_copy_path(self) -> None:
        text = self._build_path_text()
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
        except Exception:
            messagebox.showerror("Ошибка", "Не удалось скопировать путь в буфер обмена.")

    # ------------- helpers -------------
    def _rebuild_prefs_from_answers(self) -> None:
        self.prefs = Preferences()
        for step in self.steps:
            if step.id in self.answers:
                self._apply_answer_to_prefs(step.id, (self.answers[step.id] or {}).get("value"))

    def _render_result_screen(self) -> None:
        # чистим область опций
        for w in self.options_scroll.inner.winfo_children():
            w.destroy()

        self.lbl_question.configure(text="Итоговая книга выбрана")
        if not self.final_choice:
            tk.Label(
                self.options_scroll.inner,
                text="Финальный вариант не выбран. Нажмите \"Назад\" и выберите пункт на шаге параметра 16.",
                bg=COL_SURFACE,
                fg=COL_TEXT,
                font=("Segoe UI", 11),
                wraplength=520,
                justify="left",
            ).pack(anchor="w", padx=12, pady=12)
            self.btn_copy.configure(state="disabled")
            self._render_path()
            return

        # Название книги
        tk.Label(
            self.options_scroll.inner,
            text=f"📖 {self.final_choice.name}",
            bg=COL_SURFACE,
            fg=COL_PRIMARY,
            font=("Segoe UI", 16, "bold"),
            wraplength=520,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(12, 4))

        tk.Label(
            self.options_scroll.inner,
            text=f"Автор: {self.final_choice.author} ({self.final_choice.year})",
            bg=COL_SURFACE,
            fg=COL_TEXT,
            font=("Segoe UI", 11),
            wraplength=520,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 12))

        # Обложка книги (если есть)
        if self.final_choice.image_file:
            img_path = self.data_dir / "images" / self.final_choice.image_file
            if img_path.exists():
                try:
                    pil_img = Image.open(img_path)
                    # Масштабируем до разумного размера (макс 400px по ширине)
                    w, h = pil_img.size
                    if w > 400:
                        ratio = 400 / w
                        pil_img = pil_img.resize((400, int(h * ratio)), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_img)
                    lbl_img = tk.Label(self.options_scroll.inner, image=photo, bg=COL_SURFACE)
                    lbl_img.image = photo  # сохраняем ссылку, чтобы не удалилась
                    lbl_img.pack(anchor="w", padx=12, pady=(0, 12))
                except Exception:
                    pass  # если не удалось загрузить — просто пропускаем

        # Точки внимания (16)
        ap = (self.final_choice.attention_points or "(нет точек внимания)").strip()
        tk.Label(
            self.options_scroll.inner,
            text=f"💡 На эти темы Эксперты ставят акцент в этом произведении:\n{ap}",
            bg=COL_SURFACE,
            fg=COL_TEXT,
            font=("Segoe UI", 11),
            wraplength=480,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 12), fill="x")

        # Процент — берём из сохранённого ответа P16 (он уже отображался пользователю)
        p16_labels = (self.answers.get("P16", {}) or {}).get("labels", []) or []
        if p16_labels:
            tk.Label(
                self.options_scroll.inner,
                text=f"Вы выбрали: {p16_labels[0]}",
                bg=COL_SURFACE,
                fg=COL_MUTED,
                font=("Segoe UI", 10, "bold"),
                wraplength=520,
                justify="left",
            ).pack(anchor="w", padx=12, pady=(0, 12))

        # Показ "пути" справа + включаем копирование
        self._render_path()
        self.btn_copy.configure(state="normal")

    @staticmethod
    def _safe_list(x: Any) -> List[Any]:
        if x is None:
            return []
        return x if isinstance(x, list) else [x]

    @staticmethod
    def _encode_value(v: Any) -> str:
        # Нужен стабильный перенос в строку для tkinter variables
        if v is None:
            return ""
        return json.dumps(v, ensure_ascii=False)

    def _read_current_selection(self, kind: str) -> Any:
        if kind == "single":
            _, sv = self._current_var
            raw = sv.get().strip()
            if not raw:
                return None
            try:
                return json.loads(raw)
            except Exception:
                return None

        # multi
        _, items = self._current_var
        out: List[Any] = []
        for bv, value in items:
            if not bv.get():
                continue
            if value is None:
                continue
            if isinstance(value, list):
                out.extend(value)
            else:
                out.append(value)
        return out


def main() -> None:
    app = WizardApp()
    if app.winfo_exists():
        app.mainloop()


if __name__ == "__main__":
    main()


