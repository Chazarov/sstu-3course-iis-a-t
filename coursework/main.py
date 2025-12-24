# -*- coding: utf-8 -*-
"""
Экспертная система подбора классической литературы
Главный файл для запуска приложения

Использование:
    python main.py          - запуск GUI
    python main.py --cli    - запуск в консольном режиме
    python main.py --test   - запуск тестов
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_gui():
    """Запуск графического интерфейса"""
    try:
        from gui_app import main
        main()
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Убедитесь, что установлены все зависимости:")
        print("  pip install -r requirements.txt")
        sys.exit(1)


def run_cli():
    """Запуск консольного интерфейса"""
    try:
        from expert_system import get_recommendations
    except ImportError:
        print("Ошибка: не удалось импортировать экспертную систему")
        print("Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)
    
    print("=" * 60)
    print("📚 ЭКСПЕРТНАЯ СИСТЕМА ПОДБОРА КЛАССИЧЕСКОЙ ЛИТЕРАТУРЫ")
    print("=" * 60)
    print()
    
    preferences = {}
    
    # Объём
    print("1. Сколько времени готовы потратить на чтение?")
    print("   [1] Немного (до 200 страниц)")
    print("   [2] Средне (200-500 страниц)")
    print("   [3] Много (более 500 страниц)")
    choice = input("   Ваш выбор (1-3): ").strip()
    preferences['объём'] = {'1': 'короткое', '2': 'среднее', '3': 'длинное'}.get(choice, 'среднее')
    print()
    
    # Сложность
    print("2. Готовы к сложному тексту?")
    print("   [1] Нет, хочу лёгкое чтение")
    print("   [2] Средне")
    print("   [3] Да, люблю сложные произведения")
    choice = input("   Ваш выбор (1-3): ").strip()
    preferences['сложность'] = {'1': 'низкая', '2': 'средняя', '3': 'высокая'}.get(choice, 'средняя')
    print()
    
    # Настроение
    print("3. Какое настроение хотите?")
    print("   [1] Философское")
    print("   [2] Драматическое")
    print("   [3] Сатирическое")
    print("   [4] Романтическое")
    print("   [5] Трагическое")
    print("   [6] Лирическое")
    choice = input("   Ваш выбор (1-6): ").strip()
    moods = {'1': 'философское', '2': 'драматическое', '3': 'сатирическое',
             '4': 'романтическое', '5': 'трагическое', '6': 'лирическое'}
    preferences['настроение'] = moods.get(choice, 'философское')
    print()
    
    # Темы
    print("4. Какие темы интересуют? (введите номера через запятую)")
    print("   [1] Любовь     [2] Война      [3] Свобода")
    print("   [4] Вера       [5] Общество   [6] Власть")
    print("   [7] Семья      [8] Смерть     [9] Природа")
    choices = input("   Ваш выбор: ").strip().split(',')
    theme_map = {'1': 'любовь', '2': 'война', '3': 'свобода', '4': 'вера',
                 '5': 'общество', '6': 'власть', '7': 'семья', '8': 'смерть', '9': 'природа'}
    preferences['темы'] = [theme_map[c.strip()] for c in choices if c.strip() in theme_map]
    print()
    
    # Тип героя
    print("5. Какой тип героя ближе?")
    print("   [1] Идеалист       [2] Бунтарь")
    print("   [3] Лишний человек [4] Обыватель")
    print("   [5] Искатель       [6] Антигерой")
    choice = input("   Ваш выбор (1-6): ").strip()
    heroes = {'1': 'идеалист', '2': 'бунтарь', '3': 'лишний_человек',
              '4': 'обыватель', '5': 'искатель', '6': 'антигерой'}
    preferences['тип_героя'] = heroes.get(choice, 'искатель')
    print()
    
    # Художественные средства
    print("6. Какие приёмы нравятся? (номера через запятую)")
    print("   [1] Психологизм  [2] Символизм  [3] Ирония")
    print("   [4] Лиризм       [5] Фантастика [6] Гротеск")
    print("   [7] Диалоги      [8] Пейзажи    [9] Сатира")
    choices = input("   Ваш выбор: ").strip().split(',')
    tool_map = {'1': 'психологизм', '2': 'символизм', '3': 'ирония', '4': 'лиризм',
                '5': 'фантастика', '6': 'гротеск', '7': 'диалоги', '8': 'пейзажи', '9': 'сатира'}
    preferences['художественные_средства'] = [tool_map[c.strip()] for c in choices if c.strip() in tool_map]
    print()
    
    # Показываем путь принятия решения
    print("=" * 60)
    print("🛤️  ПУТЬ ПРИНЯТИЯ РЕШЕНИЯ")
    print("=" * 60)
    
    path_items = []
    
    if preferences.get('объём'):
        vol_map = {'короткое': '⚡ Короткое', 'среднее': '📚 Среднее', 'длинное': '📖 Длинное'}
        path_items.append(vol_map.get(preferences['объём'], preferences['объём']))
    
    if preferences.get('сложность'):
        comp_map = {'низкая': '😌 Лёгкое', 'средняя': '🤔 Среднее', 'высокая': '🎓 Сложное'}
        path_items.append(comp_map.get(preferences['сложность'], preferences['сложность']))
    
    if preferences.get('настроение'):
        path_items.append(f"🎭 {preferences['настроение'].capitalize()}")
    
    if preferences.get('тип_героя'):
        hero_map = {
            'идеалист': '😇 Идеалист', 'бунтарь': '✊ Бунтарь',
            'лишний_человек': '😔 Лишний человек', 'обыватель': '👤 Обыватель',
            'искатель': '🔍 Искатель', 'антигерой': '🖤 Антигерой'
        }
        path_items.append(hero_map.get(preferences['тип_героя'], preferences['тип_героя']))
    
    # Отображаем путь
    print("\n   " + " → ".join(path_items))
    
    # Детали
    print("\n📋 Детали выбора:")
    if preferences.get('темы'):
        print(f"   📌 Темы: {', '.join(preferences['темы'])}")
    if preferences.get('тип_конфликта'):
        print(f"   ⚔️  Конфликт: {preferences['тип_конфликта'].replace('_', ' ')}")
    if preferences.get('художественные_средства'):
        print(f"   🎨 Приёмы: {', '.join(preferences['художественные_средства'])}")
    
    # Получаем рекомендации
    print()
    print("=" * 60)
    print("🎯 РЕКОМЕНДАЦИИ")
    print("=" * 60)
    
    results = get_recommendations(preferences)
    
    if not results:
        print("\n😕 Не удалось подобрать книги по вашим критериям.")
        print("   Попробуйте изменить параметры.")
    else:
        for i, r in enumerate(results, 1):
            print(f"\n#{i} 📚 {r['название']}")
            print(f"   💡 {r['объяснение']}")
            data = r.get('данные', {})
            if data:
                info = []
                if data.get('автор'):
                    info.append(f"✍️ {data['автор']}")
                if data.get('страницы'):
                    info.append(f"📄 {data['страницы']} стр.")
                if data.get('год'):
                    info.append(f"📅 {data['год']}")
                if info:
                    print(f"   {' | '.join(info)}")
    
    print()
    print("=" * 60)


def run_tests():
    """Запуск тестов"""
    print("🧪 Запуск тестов экспертной системы...")
    print()
    
    try:
        from expert_system import get_recommendations
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return
    
    test_cases = [
        {
            'name': 'Лёгкое короткое сатирическое',
            'prefs': {
                'объём': 'короткое',
                'сложность': 'низкая',
                'настроение': 'сатирическое',
                'художественные_средства': ['сатира', 'гротеск']
            },
            'expected': ['Собачье сердце', 'Миргород']
        },
        {
            'name': 'Философское о вере',
            'prefs': {
                'сложность': 'высокая',
                'настроение': 'философское',
                'темы': ['вера'],
                'художественные_средства': ['психологизм']
            },
            'expected': ['Братья Карамазовы', 'Идиот']
        },
        {
            'name': 'Романтическое о свободе',
            'prefs': {
                'настроение': 'романтическое',
                'темы': ['свобода'],
                'тип_героя': 'бунтарь'
            },
            'expected': ['Мцыри']
        },
    ]
    
    passed = 0
    for test in test_cases:
        results = get_recommendations(test['prefs'])
        result_names = [r['название'] for r in results]
        
        # Проверяем, что хотя бы одна ожидаемая книга есть в результатах
        found = any(exp in result_names for exp in test['expected'])
        
        status = "✅" if found else "❌"
        print(f"{status} {test['name']}")
        print(f"   Ожидалось: {test['expected']}")
        print(f"   Получено:  {result_names}")
        print()
        
        if found:
            passed += 1
    
    print(f"Результат: {passed}/{len(test_cases)} тестов пройдено")


def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == '--cli':
            run_cli()
        elif arg == '--test':
            run_tests()
        elif arg == '--help':
            print(__doc__)
        else:
            print(f"Неизвестный аргумент: {arg}")
            print("Используйте: python main.py [--cli|--test|--help]")
    else:
        run_gui()


if __name__ == '__main__':
    main()

