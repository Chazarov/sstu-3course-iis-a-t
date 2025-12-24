# -*- coding: utf-8 -*-
"""
Экспертная система подбора классической литературы
Использует библиотеку experta для продукционных правил
"""

from experta import *
import json
import os

# Путь к данным
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_PATH, "sourses")


class BookPreferences(Fact):
    """Факт с предпочтениями пользователя"""
    pass


class BookRecommendation(Fact):
    """Факт с рекомендацией книги"""
    pass


class BookExpertSystem(KnowledgeEngine):
    """Экспертная система подбора книг"""
    
    def __init__(self):
        super().__init__()
        self.recommendations = []
        self.explanations = []
        self.books_data = {}
        self.catalog = {}
        self._load_data()
    
    def _load_data(self):
        """Загрузка данных о книгах"""
        # Загрузка каталога
        catalog_path = os.path.join(DATA_PATH, "data", "каталог.json")
        if os.path.exists(catalog_path):
            with open(catalog_path, 'r', encoding='utf-8') as f:
                self.catalog = json.load(f)
        
        # Загрузка данных о книгах
        params_path = os.path.join(DATA_PATH, "parametrs")
        if os.path.exists(params_path):
            for filename in os.listdir(params_path):
                if filename.endswith('.json'):
                    filepath = os.path.join(params_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Находим название книги по файлу
                            book_name = self._get_book_name(filename)
                            if book_name:
                                self.books_data[book_name] = data
                    except:
                        pass
    
    def _get_book_name(self, filename):
        """Получить название книги по имени файла"""
        if 'произведения' in self.catalog:
            for book_id, info in self.catalog['произведения'].items():
                if info.get('файл') == filename:
                    return info.get('название')
        # Fallback - по имени файла
        name_map = {
            'Евгенийонегин.json': 'Евгений Онегин',
            'Борисгодунов.json': 'Борис Годунов',
            'Капитанскаядочка.json': 'Капитанская дочка',
            'Мцыри.json': 'Мцыри',
            'Тарасбульба.json': 'Тарас Бульба',
            'Мртвыедуши.json': 'Мёртвые души',
            'Гореотума.json': 'Горе от ума',
            'Миргород.json': 'Миргород',
            'Собачьесердце.json': 'Собачье сердце',
            'Мастеримаргарита.json': 'Мастер и Маргарита',
            'Войнаимир.json': 'Война и мир',
            'Аннакаренина.json': 'Анна Каренина',
            'Казаки.json': 'Казаки',
            'Смертьиванаильича.json': 'Смерть Ивана Ильича',
            'Хаджимурат.json': 'Хаджи-Мурат',
            'Братьякарамазовы.json': 'Братья Карамазовы',
            'Бесы.json': 'Бесы',
            'Преступлениеинаказание.json': 'Преступление и наказание',
            'Идиот.json': 'Идиот',
            'Запискиохотника.json': 'Записки охотника',
            'Отцыидети.json': 'Отцы и дети',
            'Господаголовлвы.json': 'Господа Головлёвы',
            'Жизньарсеньева.json': 'Жизнь Арсеньева',
        }
        return name_map.get(filename)
    
    def _add_recommendation(self, book, explanation):
        """Добавить рекомендацию"""
        if book not in self.recommendations:
            self.recommendations.append(book)
            self.explanations.append(explanation)
    
    def get_book_info(self, book_name):
        """Получить информацию о книге"""
        return self.books_data.get(book_name, {})
    
    # ===================== ПРАВИЛА =====================
    
    @Rule(BookPreferences(объём='короткое', сложность='низкая', настроение='сатирическое'))
    def rule_01(self):
        """Быстрое лёгкое чтение с юмором"""
        self._add_recommendation('Собачье сердце', 'Короткое сатирическое произведение для лёгкого чтения')
        self._add_recommendation('Миргород', 'Короткое сатирическое произведение для лёгкого чтения')
    
    @Rule(BookPreferences(настроение='философское', объём='короткое'),
          BookPreferences(темы=MATCH.t))
    def rule_02(self, t):
        """Философские размышления"""
        if 'смерть' in t:
            self._add_recommendation('Смерть Ивана Ильича', 'Глубокое, но компактное произведение об экзистенциальных вопросах')
    
    @Rule(BookPreferences(настроение='романтическое'),
          BookPreferences(темы=MATCH.t))
    def rule_03(self, t):
        """Романтика и свобода"""
        if 'свобода' in t:
            self._add_recommendation('Мцыри', 'Романтическое произведение о стремлении к свободе')
            self._add_recommendation('Капитанская дочка', 'Романтическое произведение о любви и чести')
    
    @Rule(BookPreferences(сложность='высокая'),
          BookPreferences(темы=MATCH.t),
          BookPreferences(художественные_средства=MATCH.h))
    def rule_04(self, t, h):
        """Глубокий психологизм Достоевского"""
        if 'вера' in t and 'психологизм' in h:
            self._add_recommendation('Братья Карамазовы', 'Сложный философско-психологический роман о вере')
            self._add_recommendation('Идиот', 'Глубокий роман о столкновении идеала с реальностью')
            self._add_recommendation('Преступление и наказание', 'Психологический роман о преступлении и искуплении')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(тип_конфликта='личность_vs_общество'))
    def rule_05(self, t):
        """Критика общества"""
        if 'общество' in t:
            self._add_recommendation('Горе от ума', 'Произведение о конфликте личности с обществом')
            self._add_recommendation('Евгений Онегин', 'Роман о "лишнем человеке" в обществе')
            self._add_recommendation('Мёртвые души', 'Сатира на российское общество')
    
    @Rule(BookPreferences(темы=MATCH.t))
    def rule_06(self, t):
        """Историческая тематика"""
        if 'война' in t and 'честь' in t:
            self._add_recommendation('Капитанская дочка', 'Историческая повесть о чести и долге')
            self._add_recommendation('Тарас Бульба', 'Эпическая повесть о казачестве')
            self._add_recommendation('Хаджи-Мурат', 'Повесть о войне на Кавказе')
            self._add_recommendation('Война и мир', 'Эпопея о войне 1812 года')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(настроение='драматическое'),
          BookPreferences(тип_конфликта='долг_vs_чувство'))
    def rule_07(self, t):
        """Любовная драма"""
        if 'любовь' in t:
            self._add_recommendation('Анна Каренина', 'Драматическая история о любви и долге')
            self._add_recommendation('Евгений Онегин', 'История несостоявшейся любви')
    
    @Rule(BookPreferences(тип_конфликта='старое_vs_новое'),
          BookPreferences(темы=MATCH.t))
    def rule_08(self, t):
        """Конфликт поколений"""
        if 'нигилизм' in t:
            self._add_recommendation('Отцы и дети', 'Роман о столкновении поколений')
            self._add_recommendation('Бесы', 'Роман о разрушительной силе нигилизма')
    
    @Rule(BookPreferences(художественные_средства=MATCH.h))
    def rule_09(self, h):
        """Фантастика и гротеск"""
        if 'фантастика' in h and 'гротеск' in h:
            self._add_recommendation('Мастер и Маргарита', 'Роман с фантастическими элементами')
            self._add_recommendation('Собачье сердце', 'Сатирическая фантастика')
            self._add_recommendation('Миргород', 'Сборник с фантастическими элементами')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(художественные_средства=MATCH.h))
    def rule_10(self, t, h):
        """Природа и естественность"""
        if 'природа' in t and 'пейзажи' in h:
            self._add_recommendation('Записки охотника', 'Произведение с богатыми описаниями природы')
            self._add_recommendation('Казаки', 'Повесть о единении с природой')
            self._add_recommendation('Мцыри', 'Поэма с яркими пейзажами Кавказа')
    
    @Rule(BookPreferences(тип_конфликта='свобода_vs_система'),
          BookPreferences(тип_героя='бунтарь'))
    def rule_11(self):
        """Борьба за свободу"""
        self._add_recommendation('Мцыри', 'Поэма о стремлении к свободе')
        self._add_recommendation('Хаджи-Мурат', 'Повесть о борьбе за свободу')
        self._add_recommendation('Горе от ума', 'Комедия о бунтаре против общества')
        self._add_recommendation('Тарас Бульба', 'Повесть о борьбе за независимость')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(настроение='трагическое'))
    def rule_12(self, t):
        """Трагедия власти"""
        if 'власть' in t:
            self._add_recommendation('Борис Годунов', 'Трагедия о власти и совести')
            self._add_recommendation('Господа Головлёвы', 'Роман о разложении семьи')
            self._add_recommendation('Бесы', 'Трагический роман о разрушении')
    
    @Rule(BookPreferences(сложность='низкая'),
          BookPreferences(объём='короткое'))
    def rule_13(self):
        """Лёгкое знакомство с классикой"""
        self._add_recommendation('Собачье сердце', 'Доступное произведение для начала')
        self._add_recommendation('Капитанская дочка', 'Увлекательная историческая повесть')
        self._add_recommendation('Миргород', 'Лёгкие для чтения рассказы')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(объём='длинное'))
    def rule_14(self, t):
        """Семейная сага"""
        if 'семья' in t:
            self._add_recommendation('Война и мир', 'Эпопея о судьбах семей')
            self._add_recommendation('Анна Каренина', 'Роман о семье и обществе')
            self._add_recommendation('Братья Карамазовы', 'Роман о семье Карамазовых')
            self._add_recommendation('Господа Головлёвы', 'Семейная хроника')
    
    @Rule(BookPreferences(тип_конфликта='идеал_vs_реальность'),
          BookPreferences(тип_героя='идеалист'))
    def rule_15(self):
        """Идеалист против реальности"""
        self._add_recommendation('Идиот', 'Роман о столкновении идеала с жестокой реальностью')
        self._add_recommendation('Капитанская дочка', 'Повесть о благородстве и чести')
    
    @Rule(BookPreferences(тип_героя='антигерой'),
          BookPreferences(тип_конфликта='добро_vs_зло'))
    def rule_16(self):
        """Антигерой в центре"""
        self._add_recommendation('Преступление и наказание', 'Роман с неоднозначным героем')
        self._add_recommendation('Мёртвые души', 'Поэма с антигероем Чичиковым')
        self._add_recommendation('Борис Годунов', 'Трагедия о преступлении царя')
        self._add_recommendation('Господа Головлёвы', 'Роман с антигероем Иудушкой')
    
    @Rule(BookPreferences(эпоха='советский_период'))
    def rule_17(self):
        """Советская эпоха"""
        self._add_recommendation('Мастер и Маргарита', 'Роман о советской действительности')
        self._add_recommendation('Собачье сердце', 'Сатира на советское общество')
    
    @Rule(BookPreferences(настроение='лирическое'),
          BookPreferences(художественные_средства=MATCH.h))
    def rule_18(self, h):
        """Лирическая проза"""
        if 'лиризм' in h:
            self._add_recommendation('Жизнь Арсеньева', 'Лирический роман-воспоминание')
            self._add_recommendation('Евгений Онегин', 'Роман в стихах с лирическими отступлениями')
    
    @Rule(BookPreferences(жанр='пьеса'))
    def rule_19(self):
        """Пьеса для чтения"""
        self._add_recommendation('Горе от ума', 'Классическая комедия в стихах')
        self._add_recommendation('Борис Годунов', 'Историческая трагедия')
    
    @Rule(BookPreferences(жанр='эпопея'),
          BookPreferences(объём='длинное'))
    def rule_20(self):
        """Эпический размах"""
        self._add_recommendation('Война и мир', 'Грандиозный эпос о народной судьбе')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(тип_героя='искатель'))
    def rule_21(self, t):
        """Духовные искания"""
        if 'вера' in t:
            self._add_recommendation('Братья Карамазовы', 'Роман о духовном поиске')
            self._add_recommendation('Мастер и Маргарита', 'Роман о вечных вопросах')
            self._add_recommendation('Жизнь Арсеньева', 'Роман о становлении личности')
    
    @Rule(BookPreferences(эпоха='начало_XIX'),
          BookPreferences(сложность=L('низкая') | L('средняя')))
    def rule_22(self):
        """Первая половина XIX века"""
        self._add_recommendation('Евгений Онегин', 'Энциклопедия русской жизни')
        self._add_recommendation('Капитанская дочка', 'Историческая повесть Пушкина')
        self._add_recommendation('Горе от ума', 'Комедия Грибоедова')
        self._add_recommendation('Мцыри', 'Романтическая поэма Лермонтова')
    
    @Rule(BookPreferences(объём='среднее'),
          BookPreferences(сложность='средняя'))
    def rule_23(self):
        """Средний объём для занятого читателя"""
        self._add_recommendation('Евгений Онегин', 'Роман в стихах среднего объёма')
        self._add_recommendation('Отцы и дети', 'Роман среднего объёма')
        self._add_recommendation('Мастер и Маргарита', 'Увлекательный роман')
        self._add_recommendation('Казаки', 'Повесть среднего объёма')
        self._add_recommendation('Жизнь Арсеньева', 'Лирический роман')
    
    @Rule(BookPreferences(сложность='высокая'),
          BookPreferences(объём='длинное'))
    def rule_24(self):
        """Классика для подготовленного читателя"""
        self._add_recommendation('Война и мир', 'Великий роман-эпопея')
        self._add_recommendation('Братья Карамазовы', 'Философский роман Достоевского')
        self._add_recommendation('Идиот', 'Сложный психологический роман')
        self._add_recommendation('Анна Каренина', 'Великий роман о любви')
    
    @Rule(BookPreferences(тип_героя='обыватель'),
          BookPreferences(настроение=L('сатирическое') | L('философское')))
    def rule_25(self):
        """Обыватель под прицелом"""
        self._add_recommendation('Смерть Ивана Ильича', 'Повесть о жизни обычного человека')
        self._add_recommendation('Миргород', 'Рассказы о провинциальной жизни')
        self._add_recommendation('Мёртвые души', 'Галерея обывателей')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(направление='реализм'))
    def rule_26(self, t):
        """Русская деревня и крестьянство"""
        if 'природа' in t and 'свобода' in t:
            self._add_recommendation('Записки охотника', 'Цикл о народной жизни')
            self._add_recommendation('Казаки', 'Повесть о естественной жизни')
    
    @Rule(BookPreferences(тип_героя='антигерой'),
          BookPreferences(темы=MATCH.t))
    def rule_27(self, t):
        """Преступление и искупление"""
        if 'смерть' in t and 'вера' in t:
            self._add_recommendation('Преступление и наказание', 'Роман о преступлении и муках совести')
            self._add_recommendation('Борис Годунов', 'Трагедия о цареубийце')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(тип_героя='бунтарь'))
    def rule_28(self, t):
        """Нигилизм и его последствия"""
        if 'нигилизм' in t:
            self._add_recommendation('Отцы и дети', 'Роман о нигилисте Базарове')
            self._add_recommendation('Бесы', 'Роман о разрушительной силе нигилизма')
    
    @Rule(BookPreferences(автор='Тургенев'))
    def rule_29(self):
        """Реализм Тургенева"""
        self._add_recommendation('Отцы и дети', 'Главный роман Тургенева')
        self._add_recommendation('Записки охотника', 'Лирический цикл рассказов')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(тип_конфликта='свобода_vs_система'))
    def rule_30(self, t):
        """Кавказская тема"""
        if 'война' in t and 'свобода' in t:
            self._add_recommendation('Мцыри', 'Поэма о свободе')
            self._add_recommendation('Хаджи-Мурат', 'Повесть о Кавказе')
            self._add_recommendation('Казаки', 'Повесть о казачьей жизни')
    
    @Rule(BookPreferences(художественные_средства=MATCH.h),
          BookPreferences(тип_конфликта='добро_vs_зло'),
          BookPreferences(сложность='высокая'))
    def rule_31(self, h):
        """Психологический детектив"""
        if 'психологизм' in h:
            self._add_recommendation('Преступление и наказание', 'Психологический роман-детектив')
            self._add_recommendation('Бесы', 'Глубокий психологический роман')
    
    @Rule(BookPreferences(объём='короткое'),
          BookPreferences(настроение=L('философское') | L('трагическое')))
    def rule_32(self):
        """Короткое и глубокое"""
        self._add_recommendation('Смерть Ивана Ильича', 'Философская повесть')
        self._add_recommendation('Мцыри', 'Трагическая поэма')
        self._add_recommendation('Хаджи-Мурат', 'Трагическая повесть')
    
    @Rule(BookPreferences(темы=MATCH.t),
          BookPreferences(художественные_средства=MATCH.h))
    def rule_33(self, t, h):
        """Национальная история"""
        if 'война' in t and 'честь' in t and 'фольклор' in h:
            self._add_recommendation('Тарас Бульба', 'Эпос о казачестве')
            self._add_recommendation('Капитанская дочка', 'Историческая повесть')
            self._add_recommendation('Борис Годунов', 'Историческая трагедия')
    
    @Rule(BookPreferences(художественные_средства=MATCH.h),
          BookPreferences(настроение='лирическое'))
    def rule_34(self, h):
        """Лирическое погружение в природу"""
        if 'пейзажи' in h:
            self._add_recommendation('Записки охотника', 'Лирические описания природы')
            self._add_recommendation('Жизнь Арсеньева', 'Поэтическая проза')
            self._add_recommendation('Казаки', 'Яркие картины природы')
    
    @Rule(BookPreferences(жанр='пьеса'),
          BookPreferences(эпоха='начало_XIX'))
    def rule_35(self):
        """Драматургия XIX века"""
        self._add_recommendation('Горе от ума', 'Бессмертная комедия')
        self._add_recommendation('Борис Годунов', 'Историческая трагедия Пушкина')


def get_recommendations(preferences):
    """
    Получить рекомендации на основе предпочтений
    
    preferences: dict с ключами:
        - объём: 'короткое' | 'среднее' | 'длинное'
        - сложность: 'низкая' | 'средняя' | 'высокая'
        - настроение: str
        - темы: list[str]
        - тип_героя: str
        - тип_конфликта: str
        - художественные_средства: list[str]
        - жанр: str (опционально)
        - эпоха: str (опционально)
        - направление: str (опционально)
        - автор: str (опционально)
    """
    engine = BookExpertSystem()
    engine.reset()
    engine.recommendations = []
    engine.explanations = []
    
    # Добавляем факты
    for key, value in preferences.items():
        if value is not None and value != '' and value != []:
            engine.declare(BookPreferences(**{key: value}))
    
    # Запускаем движок
    engine.run()
    
    # Формируем результат
    results = []
    seen = set()
    for book, explanation in zip(engine.recommendations, engine.explanations):
        if book not in seen:
            seen.add(book)
            book_info = engine.get_book_info(book)
            results.append({
                'название': book,
                'объяснение': explanation,
                'данные': book_info
            })
    
    return results[:5]  # Максимум 5 рекомендаций


if __name__ == '__main__':
    # Тест
    prefs = {
        'объём': 'короткое',
        'сложность': 'низкая',
        'настроение': 'сатирическое',
        'темы': ['общество'],
        'художественные_средства': ['сатира', 'гротеск']
    }
    
    results = get_recommendations(prefs)
    print("Рекомендации:")
    for r in results:
        print(f"  - {r['название']}: {r['объяснение']}")

