# -*- coding: utf-8 -*-
"""
Экспертная система подбора классической литературы
Использует scikit-learn для классификации и рекомендаций

Курсовая работа по ИИСиТ
"""

import json
import os
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

# Scikit-learn импорты
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Book:
    """Класс для представления книги"""
    name: str
    author: str
    genre: str
    era: str
    direction: str
    complexity: str
    volume: str
    mood: str
    themes: List[str]
    conflict_type: str
    hero_type: str
    artistic_means: List[str]
    pages: int
    year: int
    author_position: str = ""
    audience: str = ""
    attention_points: str = ""
    weaknesses: str = ""
    interpretations: str = ""
    
    def __str__(self):
        return f"{self.name} ({self.author}, {self.year})"


@dataclass
class UserPreferences:
    """Класс для хранения предпочтений пользователя"""
    volume: Optional[str] = None
    complexity: Optional[str] = None
    mood: Optional[str] = None
    themes: List[str] = field(default_factory=list)
    hero_type: Optional[str] = None
    conflict_type: Optional[str] = None
    artistic_means: List[str] = field(default_factory=list)
    era: Optional[str] = None
    genre_group: Optional[List[str]] = None


class DataLoader:
    """Загрузчик данных из JSON файлов"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        
    def load_json(self, filepath: str) -> Dict:
        """Загрузка JSON файла"""
        full_path = self.base_path / filepath
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_catalog(self) -> Dict:
        """Загрузка каталога произведений"""
        return self.load_json("data/каталог.json")
    
    def load_questions(self) -> Dict:
        """Загрузка вопросов"""
        return self.load_json("data/вопросы.json")
    
    def load_rules(self) -> Dict:
        """Загрузка продукционных правил"""
        return self.load_json("rules/правила.json")
    
    def load_config(self) -> Dict:
        """Загрузка конфигурации"""
        return self.load_json("config.json")
    
    def load_frames(self) -> Dict:
        """Загрузка фреймов"""
        return {
            "authors": self.load_json("frames/авторы.json"),
            "genres": self.load_json("frames/жанры.json"),
            "directions": self.load_json("frames/направления.json")
        }
    
    def load_all_books(self, catalog: Dict) -> List[Book]:
        """Загрузка всех книг из каталога"""
        books = []
        for book_id, book_info in catalog["произведения"].items():
            try:
                book_data = self.load_json(f"parametrs/{book_info['файл']}")
                book = Book(
                    name=book_info["название"],
                    author=book_data.get("автор", book_info["автор"]),
                    genre=book_data.get("жанр", ""),
                    era=book_data.get("эпоха", ""),
                    direction=book_data.get("направление", ""),
                    complexity=book_data.get("сложность", ""),
                    volume=book_data.get("объём", ""),
                    mood=book_data.get("настроение", ""),
                    themes=book_data.get("темы", []),
                    conflict_type=book_data.get("тип_конфликта", ""),
                    hero_type=book_data.get("тип_героя", ""),
                    artistic_means=book_data.get("художественные_средства", []),
                    pages=book_data.get("страницы", 0),
                    year=book_data.get("год", book_info["год"]),
                    author_position=book_data.get("авторская_позиция", ""),
                    audience=book_data.get("аудитория", ""),
                    attention_points=book_data.get("точки_внимания", ""),
                    weaknesses=book_data.get("слабые_стороны", ""),
                    interpretations=book_data.get("интерпретации", "")
                )
                books.append(book)
            except Exception as e:
                print(f"Ошибка загрузки книги {book_info['название']}: {e}")
        return books


class FeatureVectorizer:
    """Векторизатор признаков для машинного обучения"""
    
    def __init__(self):
        # Энкодеры для категориальных признаков
        self.volume_encoder = LabelEncoder()
        self.complexity_encoder = LabelEncoder()
        self.mood_encoder = LabelEncoder()
        self.conflict_encoder = LabelEncoder()
        self.hero_encoder = LabelEncoder()
        self.era_encoder = LabelEncoder()
        self.genre_encoder = LabelEncoder()
        self.direction_encoder = LabelEncoder()
        
        # Бинаризаторы для множественных меток
        self.themes_binarizer = MultiLabelBinarizer()
        self.means_binarizer = MultiLabelBinarizer()
        
        self.is_fitted = False
        
    def fit(self, books: List[Book]):
        """Обучение энкодеров на данных книг"""
        # Собираем все уникальные значения
        volumes = [b.volume for b in books if b.volume]
        complexities = [b.complexity for b in books if b.complexity]
        moods = [b.mood for b in books if b.mood]
        conflicts = [b.conflict_type for b in books if b.conflict_type]
        heroes = [b.hero_type for b in books if b.hero_type]
        eras = [b.era for b in books if b.era]
        genres = [b.genre for b in books if b.genre]
        directions = [b.direction for b in books if b.direction]
        
        # Обучаем энкодеры
        self.volume_encoder.fit(volumes)
        self.complexity_encoder.fit(complexities)
        self.mood_encoder.fit(moods)
        self.conflict_encoder.fit(conflicts)
        self.hero_encoder.fit(heroes)
        self.era_encoder.fit(eras)
        self.genre_encoder.fit(genres)
        self.direction_encoder.fit(directions)
        
        # Обучаем бинаризаторы
        all_themes = [b.themes for b in books]
        all_means = [b.artistic_means for b in books]
        self.themes_binarizer.fit(all_themes)
        self.means_binarizer.fit(all_means)
        
        self.is_fitted = True
        
    def transform_book(self, book: Book) -> np.ndarray:
        """Преобразование книги в вектор признаков"""
        if not self.is_fitted:
            raise ValueError("Vectorizer not fitted. Call fit() first.")
        
        features = []
        
        # Категориальные признаки (one-hot encoding через порядковый номер)
        features.append(self._safe_encode(self.volume_encoder, book.volume))
        features.append(self._safe_encode(self.complexity_encoder, book.complexity))
        features.append(self._safe_encode(self.mood_encoder, book.mood))
        features.append(self._safe_encode(self.conflict_encoder, book.conflict_type))
        features.append(self._safe_encode(self.hero_encoder, book.hero_type))
        features.append(self._safe_encode(self.era_encoder, book.era))
        features.append(self._safe_encode(self.genre_encoder, book.genre))
        features.append(self._safe_encode(self.direction_encoder, book.direction))
        
        # Множественные метки (бинарные векторы)
        themes_vec = self.themes_binarizer.transform([book.themes])[0]
        means_vec = self.means_binarizer.transform([book.artistic_means])[0]
        
        # Объединяем все признаки
        categorical = np.array(features)
        return np.concatenate([categorical, themes_vec, means_vec])
    
    def transform_preferences(self, prefs: UserPreferences) -> np.ndarray:
        """Преобразование предпочтений пользователя в вектор"""
        if not self.is_fitted:
            raise ValueError("Vectorizer not fitted. Call fit() first.")
        
        features = []
        
        # Категориальные признаки
        features.append(self._safe_encode(self.volume_encoder, prefs.volume) if prefs.volume else -1)
        features.append(self._safe_encode(self.complexity_encoder, prefs.complexity) if prefs.complexity else -1)
        features.append(self._safe_encode(self.mood_encoder, prefs.mood) if prefs.mood else -1)
        features.append(self._safe_encode(self.conflict_encoder, prefs.conflict_type) if prefs.conflict_type else -1)
        features.append(self._safe_encode(self.hero_encoder, prefs.hero_type) if prefs.hero_type else -1)
        features.append(self._safe_encode(self.era_encoder, prefs.era) if prefs.era else -1)
        features.append(-1)  # genre - пропускаем
        features.append(-1)  # direction - пропускаем
        
        # Множественные метки
        themes_vec = self.themes_binarizer.transform([prefs.themes])[0] if prefs.themes else np.zeros(len(self.themes_binarizer.classes_))
        means_vec = self.means_binarizer.transform([prefs.artistic_means])[0] if prefs.artistic_means else np.zeros(len(self.means_binarizer.classes_))
        
        categorical = np.array(features)
        return np.concatenate([categorical, themes_vec, means_vec])
    
    def _safe_encode(self, encoder: LabelEncoder, value: str) -> int:
        """Безопасное кодирование значения"""
        try:
            if value and value in encoder.classes_:
                return encoder.transform([value])[0]
            return -1
        except:
            return -1
    
    def transform_all_books(self, books: List[Book]) -> np.ndarray:
        """Преобразование всех книг в матрицу признаков"""
        return np.array([self.transform_book(b) for b in books])


class RuleEngine:
    """Движок продукционных правил"""
    
    def __init__(self, rules: Dict):
        self.rules = rules.get("правила", {})
        
    def evaluate_rule(self, rule: Dict, prefs: UserPreferences, books: List[Book]) -> Tuple[bool, List[str]]:
        """Проверка применимости правила к предпочтениям"""
        conditions = rule.get("если", {})
        matches = True
        
        for param, value in conditions.items():
            if param == "объём" and prefs.volume:
                if prefs.volume != value:
                    matches = False
                    break
            elif param == "сложность" and prefs.complexity:
                if isinstance(value, list):
                    if prefs.complexity not in value:
                        matches = False
                        break
                elif prefs.complexity != value:
                    matches = False
                    break
            elif param == "настроение" and prefs.mood:
                if isinstance(value, list):
                    if prefs.mood not in value:
                        matches = False
                        break
                elif prefs.mood != value:
                    matches = False
                    break
            elif param == "темы" and prefs.themes:
                required_themes = value if isinstance(value, list) else [value]
                if not any(t in prefs.themes for t in required_themes):
                    matches = False
                    break
            elif param == "тип_конфликта" and prefs.conflict_type:
                if prefs.conflict_type != value:
                    matches = False
                    break
            elif param == "тип_героя" and prefs.hero_type:
                if prefs.hero_type != value:
                    matches = False
                    break
            elif param == "художественные_средства" and prefs.artistic_means:
                required_means = value if isinstance(value, list) else [value]
                if not any(m in prefs.artistic_means for m in required_means):
                    matches = False
                    break
            elif param == "эпоха" and prefs.era:
                if prefs.era != value:
                    matches = False
                    break
            elif param == "жанр" and prefs.genre_group:
                required_genres = value if isinstance(value, list) else [value]
                if not any(g in prefs.genre_group for g in required_genres):
                    matches = False
                    break
        
        if matches:
            return True, rule.get("то", [])
        return False, []
    
    def get_recommendations(self, prefs: UserPreferences, books: List[Book]) -> List[Tuple[str, str, str]]:
        """Получение рекомендаций на основе правил"""
        recommendations = []
        
        for rule_id, rule in self.rules.items():
            matched, book_names = self.evaluate_rule(rule, prefs, books)
            if matched:
                for book_name in book_names:
                    recommendations.append((
                        book_name,
                        rule.get("название", ""),
                        rule.get("объяснение", "")
                    ))
        
        return recommendations


class MLRecommender:
    """Рекомендательная система на основе машинного обучения"""
    
    def __init__(self, vectorizer: FeatureVectorizer):
        self.vectorizer = vectorizer
        self.knn = NearestNeighbors(n_neighbors=5, metric='cosine')
        self.decision_tree = DecisionTreeClassifier(max_depth=10, random_state=42)
        self.books: List[Book] = []
        self.book_vectors: np.ndarray = None
        
    def fit(self, books: List[Book]):
        """Обучение моделей"""
        self.books = books
        self.vectorizer.fit(books)
        self.book_vectors = self.vectorizer.transform_all_books(books)
        
        # Обучаем KNN для поиска похожих книг
        self.knn.fit(self.book_vectors)
        
        # Обучаем дерево решений для классификации по сложности
        y_complexity = [b.complexity for b in books]
        if len(set(y_complexity)) > 1:
            complexity_encoder = LabelEncoder()
            y_encoded = complexity_encoder.fit_transform(y_complexity)
            self.decision_tree.fit(self.book_vectors, y_encoded)
            self.complexity_encoder = complexity_encoder
    
    def find_similar_books(self, prefs: UserPreferences, n_recommendations: int = 5) -> List[Tuple[Book, float]]:
        """Поиск похожих книг по предпочтениям пользователя"""
        pref_vector = self.vectorizer.transform_preferences(prefs)
        
        # Находим ближайших соседей
        distances, indices = self.knn.kneighbors([pref_vector], n_neighbors=min(n_recommendations, len(self.books)))
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            similarity = 1 - dist  # Конвертируем расстояние в подобие
            results.append((self.books[idx], similarity))
        
        return results
    
    def calculate_match_score(self, book: Book, prefs: UserPreferences) -> float:
        """Вычисление оценки соответствия книги предпочтениям"""
        score = 0.0
        max_score = 0.0
        
        # Проверяем объём (вес 20)
        if prefs.volume:
            max_score += 20
            if book.volume == prefs.volume:
                score += 20
        
        # Проверяем сложность (вес 20)
        if prefs.complexity:
            max_score += 20
            if book.complexity == prefs.complexity:
                score += 20
        
        # Проверяем настроение (вес 15)
        if prefs.mood:
            max_score += 15
            if book.mood == prefs.mood:
                score += 15
        
        # Проверяем темы (вес 20)
        if prefs.themes:
            max_score += 20
            common_themes = set(book.themes) & set(prefs.themes)
            if prefs.themes:
                score += 20 * (len(common_themes) / len(prefs.themes))
        
        # Проверяем тип конфликта (вес 10)
        if prefs.conflict_type:
            max_score += 10
            if book.conflict_type == prefs.conflict_type:
                score += 10
        
        # Проверяем тип героя (вес 10)
        if prefs.hero_type:
            max_score += 10
            if book.hero_type == prefs.hero_type:
                score += 10
        
        # Проверяем художественные средства (вес 10)
        if prefs.artistic_means:
            max_score += 10
            common_means = set(book.artistic_means) & set(prefs.artistic_means)
            if prefs.artistic_means:
                score += 10 * (len(common_means) / len(prefs.artistic_means))
        
        # Проверяем эпоху (вес 5)
        if prefs.era:
            max_score += 5
            if book.era == prefs.era:
                score += 5
        
        # Проверяем жанр (вес 5)
        if prefs.genre_group:
            max_score += 5
            if book.genre in prefs.genre_group:
                score += 5
        
        if max_score > 0:
            return (score / max_score) * 100
        return 0.0


class BookExpertSystem:
    """Главный класс экспертной системы подбора книг"""
    
    def __init__(self, base_path: str = "sourses"):
        self.base_path = base_path
        self.data_loader = DataLoader(base_path)
        self.vectorizer = FeatureVectorizer()
        self.rule_engine: Optional[RuleEngine] = None
        self.ml_recommender: Optional[MLRecommender] = None
        self.books: List[Book] = []
        self.questions: Dict = {}
        self.config: Dict = {}
        self.frames: Dict = {}
        
    def initialize(self):
        """Инициализация системы"""
        print("=" * 60)
        print("ИНИЦИАЛИЗАЦИЯ ЭКСПЕРТНОЙ СИСТЕМЫ")
        print("=" * 60)
        
        # Загружаем конфигурацию
        print("\n📚 Загрузка конфигурации...")
        self.config = self.data_loader.load_config()
        
        # Загружаем каталог и книги
        print("📖 Загрузка каталога книг...")
        catalog = self.data_loader.load_catalog()
        self.books = self.data_loader.load_all_books(catalog)
        print(f"   Загружено {len(self.books)} произведений")
        
        # Загружаем вопросы
        print("❓ Загрузка вопросов...")
        self.questions = self.data_loader.load_questions()
        
        # Загружаем правила
        print("📋 Загрузка продукционных правил...")
        rules = self.data_loader.load_rules()
        self.rule_engine = RuleEngine(rules)
        print(f"   Загружено {len(rules.get('правила', {}))} правил")
        
        # Загружаем фреймы
        print("🏗️ Загрузка фреймов...")
        self.frames = self.data_loader.load_frames()
        
        # Инициализируем ML-рекомендатор
        print("🤖 Обучение ML-моделей (scikit-learn)...")
        self.ml_recommender = MLRecommender(self.vectorizer)
        self.ml_recommender.fit(self.books)
        print("   ✓ KNN-модель обучена")
        print("   ✓ Дерево решений обучено")
        
        print("\n✅ Система готова к работе!")
        print("=" * 60)
    
    def ask_question(self, question_id: str) -> Any:
        """Задать вопрос пользователю"""
        question = self.questions["вопросы"].get(question_id)
        if not question:
            return None
        
        print(f"\n📌 {question['текст']}")
        print("-" * 50)
        
        variants = question["варианты"]
        multiple = question.get("множественный_выбор", False)
        
        for i, variant in enumerate(variants, 1):
            print(f"  {i}. {variant['текст']}")
        
        if multiple:
            print(f"\n💡 Можно выбрать несколько вариантов (через запятую, например: 1,3,5)")
            print("   Или нажмите Enter для пропуска")
        else:
            print(f"\n💡 Введите номер варианта (или Enter для пропуска)")
        
        while True:
            try:
                user_input = input("\n➤ Ваш выбор: ").strip()
                
                if not user_input:
                    return None
                
                if multiple:
                    indices = [int(x.strip()) - 1 for x in user_input.split(",")]
                    values = []
                    for idx in indices:
                        if 0 <= idx < len(variants):
                            val = variants[idx]["значение"]
                            if val is not None:
                                if isinstance(val, list):
                                    values.extend(val)
                                else:
                                    values.append(val)
                    return values if values else None
                else:
                    idx = int(user_input) - 1
                    if 0 <= idx < len(variants):
                        return variants[idx]["значение"]
                    else:
                        print("❌ Неверный номер варианта. Попробуйте снова.")
            except ValueError:
                print("❌ Введите корректное число.")
    
    def conduct_interview(self) -> UserPreferences:
        """Проведение интервью с пользователем"""
        prefs = UserPreferences()
        
        print("\n" + "=" * 60)
        print("ОПРОС ДЛЯ ПОДБОРА КНИГИ")
        print("=" * 60)
        print("\n📝 Ответьте на несколько вопросов, чтобы получить рекомендации.")
        print("   Вы можете пропустить любой вопрос, нажав Enter.\n")
        
        # Порядок вопросов из конфигурации
        question_order = self.questions.get("сценарий_диалога", {}).get("порядок", 
                                            ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9"])
        
        for q_id in question_order:
            answer = self.ask_question(q_id)
            
            # Сохраняем ответы в предпочтения
            if q_id == "Q1":
                prefs.volume = answer
            elif q_id == "Q2":
                prefs.complexity = answer
            elif q_id == "Q3":
                prefs.mood = answer
            elif q_id == "Q4":
                prefs.themes = answer if answer else []
            elif q_id == "Q5":
                prefs.hero_type = answer
            elif q_id == "Q6":
                prefs.conflict_type = answer
            elif q_id == "Q7":
                prefs.artistic_means = answer if answer else []
            elif q_id == "Q8":
                prefs.era = answer
            elif q_id == "Q9":
                prefs.genre_group = answer if answer else None
        
        return prefs
    
    def get_recommendations(self, prefs: UserPreferences, max_recommendations: int = 5) -> List[Dict]:
        """Получение рекомендаций на основе предпочтений"""
        recommendations = {}
        
        # 1. Получаем рекомендации от правил
        rule_recommendations = self.rule_engine.get_recommendations(prefs, self.books)
        for book_name, rule_name, explanation in rule_recommendations:
            if book_name not in recommendations:
                recommendations[book_name] = {
                    "book": None,
                    "rules": [],
                    "ml_score": 0,
                    "match_score": 0
                }
            recommendations[book_name]["rules"].append({
                "name": rule_name,
                "explanation": explanation
            })
        
        # 2. Получаем рекомендации от ML-модели
        ml_results = self.ml_recommender.find_similar_books(prefs, n_recommendations=10)
        for book, similarity in ml_results:
            if book.name not in recommendations:
                recommendations[book.name] = {
                    "book": book,
                    "rules": [],
                    "ml_score": similarity,
                    "match_score": 0
                }
            else:
                recommendations[book.name]["ml_score"] = similarity
            recommendations[book.name]["book"] = book
        
        # 3. Вычисляем итоговую оценку для каждой книги
        for book_name, rec_data in recommendations.items():
            if rec_data["book"] is None:
                # Находим книгу по имени
                for b in self.books:
                    if b.name == book_name:
                        rec_data["book"] = b
                        break
            
            if rec_data["book"]:
                rec_data["match_score"] = self.ml_recommender.calculate_match_score(
                    rec_data["book"], prefs
                )
        
        # 4. Сортируем по комбинированной оценке
        final_recommendations = []
        for book_name, rec_data in recommendations.items():
            if rec_data["book"]:
                # Комбинированная оценка: вес правил + ML-оценка + оценка соответствия
                rule_bonus = len(rec_data["rules"]) * 15
                combined_score = rec_data["match_score"] + rule_bonus + rec_data["ml_score"] * 50
                
                final_recommendations.append({
                    "book": rec_data["book"],
                    "score": combined_score,
                    "match_percent": rec_data["match_score"],
                    "rules": rec_data["rules"],
                    "ml_similarity": rec_data["ml_score"]
                })
        
        # Сортируем по убыванию оценки
        final_recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return final_recommendations[:max_recommendations]
    
    def display_recommendations(self, recommendations: List[Dict], prefs: UserPreferences):
        """Отображение рекомендаций"""
        print("\n" + "=" * 60)
        print("📚 РЕКОМЕНДОВАННЫЕ КНИГИ")
        print("=" * 60)
        
        if not recommendations:
            print("\n😔 К сожалению, не удалось найти подходящие книги.")
            print("   Попробуйте изменить критерии поиска.")
            return
        
        for i, rec in enumerate(recommendations, 1):
            book = rec["book"]
            print(f"\n{'─' * 60}")
            print(f"📖 #{i}: {book.name}")
            print(f"{'─' * 60}")
            print(f"   ✍️  Автор: {book.author}")
            print(f"   📅 Год: {book.year}")
            print(f"   📚 Жанр: {book.genre}")
            print(f"   📏 Объём: {book.volume} ({book.pages} стр.)")
            print(f"   📊 Сложность: {book.complexity}")
            print(f"   🎭 Настроение: {book.mood}")
            print(f"   🏷️  Темы: {', '.join(book.themes)}")
            
            print(f"\n   📈 ОЦЕНКА СООТВЕТСТВИЯ: {rec['match_percent']:.1f}%")
            
            if rec["rules"]:
                print(f"\n   🔍 Подходит по правилам:")
                for rule in rec["rules"][:3]:  # Показываем максимум 3 правила
                    print(f"      • {rule['name']}: {rule['explanation']}")
            
            if book.attention_points:
                print(f"\n   💡 На что обратить внимание: {book.attention_points}")
            
            if book.audience:
                print(f"   👤 Аудитория: {book.audience}")
    
    def display_book_details(self, book: Book):
        """Показать детальную информацию о книге"""
        print(f"\n{'═' * 60}")
        print(f"📖 {book.name}")
        print(f"{'═' * 60}")
        print(f"\n✍️  Автор: {book.author}")
        print(f"📅 Год издания: {book.year}")
        print(f"📚 Жанр: {book.genre}")
        print(f"🎨 Направление: {book.direction}")
        print(f"📅 Эпоха: {book.era}")
        print(f"📏 Объём: {book.volume} ({book.pages} страниц)")
        print(f"📊 Сложность: {book.complexity}")
        print(f"🎭 Настроение: {book.mood}")
        print(f"⚔️  Тип конфликта: {book.conflict_type}")
        print(f"🦸 Тип героя: {book.hero_type}")
        print(f"\n🏷️  Темы: {', '.join(book.themes)}")
        print(f"🎨 Художественные средства: {', '.join(book.artistic_means)}")
        
        if book.author_position:
            print(f"\n📝 Авторская позиция: {book.author_position}")
        if book.audience:
            print(f"👤 Для кого: {book.audience}")
        if book.attention_points:
            print(f"💡 Точки внимания: {book.attention_points}")
        if book.weaknesses:
            print(f"⚠️  Возможные сложности: {book.weaknesses}")
        if book.interpretations:
            print(f"🔮 Интерпретации: {book.interpretations}")
    
    def list_all_books(self):
        """Показать список всех книг"""
        print("\n" + "=" * 60)
        print("📚 КАТАЛОГ ПРОИЗВЕДЕНИЙ")
        print("=" * 60)
        
        # Группируем по авторам
        by_author = {}
        for book in self.books:
            if book.author not in by_author:
                by_author[book.author] = []
            by_author[book.author].append(book)
        
        for author in sorted(by_author.keys()):
            print(f"\n✍️  {author}:")
            for book in sorted(by_author[author], key=lambda x: x.year):
                print(f"   • {book.name} ({book.year}) - {book.genre}, {book.complexity} сложность")
    
    def run(self):
        """Запуск экспертной системы"""
        self.initialize()
        
        while True:
            print("\n" + "=" * 60)
            print("ГЛАВНОЕ МЕНЮ")
            print("=" * 60)
            print("\n1. 🔍 Подобрать книгу (интервью)")
            print("2. 📚 Показать все книги")
            print("3. 📖 Информация о конкретной книге")
            print("4. ℹ️  О системе")
            print("5. 🚪 Выход")
            
            choice = input("\n➤ Выберите действие (1-5): ").strip()
            
            if choice == "1":
                prefs = self.conduct_interview()
                max_recs = self.config.get("параметры_системы", {}).get("максимум_рекомендаций", 5)
                recommendations = self.get_recommendations(prefs, max_recs)
                self.display_recommendations(recommendations, prefs)
                
                # Предложить подробности о книге
                if recommendations:
                    print("\n💡 Хотите узнать подробнее о какой-либо книге?")
                    detail_choice = input("   Введите номер книги или Enter для продолжения: ").strip()
                    if detail_choice.isdigit():
                        idx = int(detail_choice) - 1
                        if 0 <= idx < len(recommendations):
                            self.display_book_details(recommendations[idx]["book"])
            
            elif choice == "2":
                self.list_all_books()
            
            elif choice == "3":
                print("\n📚 Введите название книги (или часть названия):")
                search = input("➤ ").strip().lower()
                found = [b for b in self.books if search in b.name.lower()]
                if found:
                    if len(found) == 1:
                        self.display_book_details(found[0])
                    else:
                        print("\nНайдено несколько книг:")
                        for i, b in enumerate(found, 1):
                            print(f"  {i}. {b.name}")
                        idx = input("Выберите номер: ").strip()
                        if idx.isdigit() and 0 < int(idx) <= len(found):
                            self.display_book_details(found[int(idx) - 1])
                else:
                    print("❌ Книга не найдена")
            
            elif choice == "4":
                system_info = self.config.get("система", {})
                print(f"\n{'=' * 60}")
                print(f"ℹ️  {system_info.get('название', 'Экспертная система')}")
                print(f"{'=' * 60}")
                print(f"Версия: {system_info.get('версия', '1.0')}")
                print(f"Автор: {system_info.get('автор', 'Неизвестен')}")
                print(f"Описание: {system_info.get('описание', '')}")
                print(f"\n📊 Статистика:")
                print(f"   • Произведений в базе: {len(self.books)}")
                print(f"   • Продукционных правил: {len(self.rule_engine.rules)}")
                print(f"\n🤖 Используемые ML-модели (scikit-learn):")
                print(f"   • KNN (K-Nearest Neighbors) для поиска похожих книг")
                print(f"   • Decision Tree для классификации")
                print(f"   • Косинусное сходство для оценки соответствия")
            
            elif choice == "5":
                print("\n👋 До свидания! Приятного чтения!")
                break
            
            else:
                print("❌ Неверный выбор. Попробуйте снова.")


def main():
    """Точка входа"""
    # Определяем путь к данным
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "sourses")
    
    if not os.path.exists(data_path):
        print(f"❌ Папка с данными не найдена: {data_path}")
        return
    
    # Создаём и запускаем экспертную систему
    expert_system = BookExpertSystem(data_path)
    expert_system.run()


if __name__ == "__main__":
    main()

