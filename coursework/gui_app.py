# -*- coding: utf-8 -*-
"""
Графический интерфейс экспертной системы подбора книг
Использует tkinter для GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os

from expert_system import get_recommendations, BookExpertSystem


class BookRecommenderApp:
    """Главное окно приложения"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Экспертная система подбора классической литературы")
        self.root.geometry("1000x750")
        self.root.configure(bg='#1a1a2e')
        
        # Цветовая схема
        self.colors = {
            'bg': '#1a1a2e',
            'fg': '#eaeaea',
            'accent': '#e94560',
            'secondary': '#16213e',
            'button': '#0f3460',
            'button_hover': '#e94560',
            'success': '#00d9ff',
            'card': '#16213e'
        }
        
        # Стили
        self.setup_styles()
        
        # Переменные для хранения выбора
        self.preferences = {}
        self.current_step = 0
        self.steps = [
            self.create_step_volume,
            self.create_step_complexity,
            self.create_step_mood,
            self.create_step_themes,
            self.create_step_hero,
            self.create_step_conflict,
            self.create_step_tools,
        ]
        
        # Создание интерфейса
        self.create_header()
        self.create_main_frame()
        self.create_footer()
        
        # Показать первый шаг
        self.show_step(0)
    
    def setup_styles(self):
        """Настройка стилей ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Кнопки
        style.configure('Custom.TButton',
                       background=self.colors['button'],
                       foreground=self.colors['fg'],
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 10))
        style.map('Custom.TButton',
                 background=[('active', self.colors['button_hover'])])
        
        # Радиокнопки
        style.configure('Custom.TRadiobutton',
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       font=('Segoe UI', 11),
                       padding=10)
        
        # Чекбоксы
        style.configure('Custom.TCheckbutton',
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       font=('Segoe UI', 11),
                       padding=8)
        
        # Лейблы
        style.configure('Title.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 24, 'bold'))
        
        style.configure('Question.TLabel',
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       font=('Segoe UI', 14))
        
        style.configure('Step.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['success'],
                       font=('Segoe UI', 10))
    
    def create_header(self):
        """Создание заголовка"""
        header = tk.Frame(self.root, bg=self.colors['bg'], height=80)
        header.pack(fill='x', padx=20, pady=10)
        header.pack_propagate(False)
        
        title = tk.Label(header, 
                        text="📚 Подбор классической литературы",
                        font=('Segoe UI', 22, 'bold'),
                        bg=self.colors['bg'],
                        fg=self.colors['accent'])
        title.pack(pady=15)
        
        subtitle = tk.Label(header,
                           text="Ответьте на несколько вопросов, и система подберёт для вас идеальную книгу",
                           font=('Segoe UI', 11),
                           bg=self.colors['bg'],
                           fg=self.colors['fg'])
        subtitle.pack()
    
    def create_main_frame(self):
        """Создание основной области"""
        self.main_frame = tk.Frame(self.root, bg=self.colors['secondary'])
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Прогресс
        self.progress_frame = tk.Frame(self.main_frame, bg=self.colors['secondary'])
        self.progress_frame.pack(fill='x', padx=20, pady=15)
        
        self.progress_label = tk.Label(self.progress_frame,
                                       text="Шаг 1 из 7",
                                       font=('Segoe UI', 10),
                                       bg=self.colors['secondary'],
                                       fg=self.colors['success'])
        self.progress_label.pack(side='left')
        
        # Прогресс-бар
        self.progress_canvas = tk.Canvas(self.progress_frame, 
                                         height=8, 
                                         bg=self.colors['bg'],
                                         highlightthickness=0)
        self.progress_canvas.pack(side='right', fill='x', expand=True, padx=(20, 0))
        
        # Контейнер для вопросов
        self.question_frame = tk.Frame(self.main_frame, bg=self.colors['secondary'])
        self.question_frame.pack(fill='both', expand=True, padx=20, pady=10)
    
    def create_footer(self):
        """Создание нижней панели с кнопками"""
        footer = tk.Frame(self.root, bg=self.colors['bg'], height=70)
        footer.pack(fill='x', padx=20, pady=10)
        footer.pack_propagate(False)
        
        # Кнопка "Назад"
        self.back_btn = tk.Button(footer,
                                  text="← Назад",
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['secondary'],
                                  fg=self.colors['fg'],
                                  activebackground=self.colors['button'],
                                  activeforeground=self.colors['fg'],
                                  border=0,
                                  padx=25, pady=10,
                                  cursor='hand2',
                                  command=self.prev_step)
        self.back_btn.pack(side='left', padx=10, pady=10)
        
        # Кнопка "Далее" / "Получить рекомендации"
        self.next_btn = tk.Button(footer,
                                  text="Далее →",
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['accent'],
                                  fg='white',
                                  activebackground=self.colors['button_hover'],
                                  activeforeground='white',
                                  border=0,
                                  padx=25, pady=10,
                                  cursor='hand2',
                                  command=self.next_step)
        self.next_btn.pack(side='right', padx=10, pady=10)
        
        # Кнопка "Сбросить"
        self.reset_btn = tk.Button(footer,
                                   text="🔄 Начать заново",
                                   font=('Segoe UI', 10),
                                   bg=self.colors['bg'],
                                   fg=self.colors['fg'],
                                   activebackground=self.colors['secondary'],
                                   border=0,
                                   padx=15, pady=8,
                                   cursor='hand2',
                                   command=self.reset)
        self.reset_btn.pack(side='right', padx=10, pady=10)
    
    def update_progress(self):
        """Обновление прогресс-бара"""
        self.progress_label.config(text=f"Шаг {self.current_step + 1} из {len(self.steps)}")
        
        # Рисуем прогресс-бар
        self.progress_canvas.delete('all')
        width = self.progress_canvas.winfo_width()
        if width > 1:
            progress = (self.current_step + 1) / len(self.steps)
            self.progress_canvas.create_rectangle(0, 0, width * progress, 8,
                                                  fill=self.colors['accent'],
                                                  outline='')
    
    def clear_question_frame(self):
        """Очистка области вопросов"""
        for widget in self.question_frame.winfo_children():
            widget.destroy()
    
    def show_step(self, step_num):
        """Показать определённый шаг"""
        self.current_step = step_num
        self.clear_question_frame()
        self.steps[step_num]()
        self.update_progress()
        
        # Обновление кнопок
        self.back_btn.config(state='normal' if step_num > 0 else 'disabled')
        if step_num == len(self.steps) - 1:
            self.next_btn.config(text="🎯 Получить рекомендации")
        else:
            self.next_btn.config(text="Далее →")
    
    def next_step(self):
        """Переход к следующему шагу"""
        # Сохраняем текущий выбор
        self.save_current_step()
        
        if self.current_step < len(self.steps) - 1:
            self.show_step(self.current_step + 1)
        else:
            self.show_results()
    
    def prev_step(self):
        """Переход к предыдущему шагу"""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
    
    def reset(self):
        """Сброс всех выборов"""
        self.preferences = {}
        self.show_step(0)
    
    def save_current_step(self):
        """Сохранение выбора текущего шага"""
        pass  # Реализовано в каждом шаге через переменные tkinter
    
    # ==================== ШАГИ ОПРОСА ====================
    
    def create_step_volume(self):
        """Шаг 1: Объём книги"""
        question = tk.Label(self.question_frame,
                           text="📖 Сколько времени вы готовы потратить на чтение?",
                           font=('Segoe UI', 16, 'bold'),
                           bg=self.colors['secondary'],
                           fg=self.colors['fg'])
        question.pack(pady=(30, 20))
        
        self.volume_var = tk.StringVar(value=self.preferences.get('объём', ''))
        
        options = [
            ('короткое', '⚡ Немного — хочу прочитать быстро (до 200 страниц)'),
            ('среднее', '📚 Средне — готов потратить несколько вечеров (200-500 страниц)'),
            ('длинное', '📖 Много — готов к долгому погружению (более 500 страниц)')
        ]
        
        for value, text in options:
            rb = tk.Radiobutton(self.question_frame,
                               text=text,
                               variable=self.volume_var,
                               value=value,
                               font=('Segoe UI', 12),
                               bg=self.colors['secondary'],
                               fg=self.colors['fg'],
                               selectcolor=self.colors['button'],
                               activebackground=self.colors['secondary'],
                               activeforeground=self.colors['accent'],
                               cursor='hand2',
                               padx=20, pady=10)
            rb.pack(anchor='w', padx=50, pady=5)
        
        self.volume_var.trace_add('write', lambda *args: self.preferences.update({'объём': self.volume_var.get()}))
    
    def create_step_complexity(self):
        """Шаг 2: Сложность"""
        question = tk.Label(self.question_frame,
                           text="🧠 Готовы ли вы к сложному, требующему внимания тексту?",
                           font=('Segoe UI', 16, 'bold'),
                           bg=self.colors['secondary'],
                           fg=self.colors['fg'])
        question.pack(pady=(30, 20))
        
        self.complexity_var = tk.StringVar(value=self.preferences.get('сложность', ''))
        
        options = [
            ('низкая', '😌 Нет, хочу лёгкое чтение для отдыха'),
            ('средняя', '🤔 Средне — готов к некоторым сложностям'),
            ('высокая', '🎓 Да, люблю глубокие и сложные произведения')
        ]
        
        for value, text in options:
            rb = tk.Radiobutton(self.question_frame,
                               text=text,
                               variable=self.complexity_var,
                               value=value,
                               font=('Segoe UI', 12),
                               bg=self.colors['secondary'],
                               fg=self.colors['fg'],
                               selectcolor=self.colors['button'],
                               activebackground=self.colors['secondary'],
                               activeforeground=self.colors['accent'],
                               cursor='hand2',
                               padx=20, pady=10)
            rb.pack(anchor='w', padx=50, pady=5)
        
        self.complexity_var.trace_add('write', lambda *args: self.preferences.update({'сложность': self.complexity_var.get()}))
    
    def create_step_mood(self):
        """Шаг 3: Настроение"""
        question = tk.Label(self.question_frame,
                           text="🎭 Какое настроение вы хотите получить от книги?",
                           font=('Segoe UI', 16, 'bold'),
                           bg=self.colors['secondary'],
                           fg=self.colors['fg'])
        question.pack(pady=(30, 20))
        
        self.mood_var = tk.StringVar(value=self.preferences.get('настроение', ''))
        
        options = [
            ('философское', '💭 Философское — хочу задуматься о важном'),
            ('драматическое', '😢 Драматическое — хочу переживать за героев'),
            ('сатирическое', '😄 Сатирическое — хочу посмеяться над пороками'),
            ('романтическое', '💕 Романтическое — хочу возвышенных чувств'),
            ('трагическое', '💔 Трагическое — готов к тяжёлым эмоциям'),
            ('лирическое', '🌸 Лирическое — хочу поэтичности и красоты')
        ]
        
        # Два столбца
        frame = tk.Frame(self.question_frame, bg=self.colors['secondary'])
        frame.pack(fill='x', padx=30)
        
        left_frame = tk.Frame(frame, bg=self.colors['secondary'])
        left_frame.pack(side='left', fill='both', expand=True)
        
        right_frame = tk.Frame(frame, bg=self.colors['secondary'])
        right_frame.pack(side='right', fill='both', expand=True)
        
        for i, (value, text) in enumerate(options):
            parent = left_frame if i < 3 else right_frame
            rb = tk.Radiobutton(parent,
                               text=text,
                               variable=self.mood_var,
                               value=value,
                               font=('Segoe UI', 11),
                               bg=self.colors['secondary'],
                               fg=self.colors['fg'],
                               selectcolor=self.colors['button'],
                               activebackground=self.colors['secondary'],
                               activeforeground=self.colors['accent'],
                               cursor='hand2',
                               padx=10, pady=8)
            rb.pack(anchor='w', pady=3)
        
        self.mood_var.trace_add('write', lambda *args: self.preferences.update({'настроение': self.mood_var.get()}))
    
    def create_step_themes(self):
        """Шаг 4: Темы"""
        question = tk.Label(self.question_frame,
                           text="📌 Какие темы вас интересуют? (выберите несколько)",
                           font=('Segoe UI', 16, 'bold'),
                           bg=self.colors['secondary'],
                           fg=self.colors['fg'])
        question.pack(pady=(20, 15))
        
        themes = [
            ('любовь', '❤️ Любовь и отношения'),
            ('война', '⚔️ Война, история, героизм'),
            ('свобода', '🕊️ Свобода и борьба за неё'),
            ('вера', '✨ Вера, духовность, смысл жизни'),
            ('общество', '👥 Общество, социальная критика'),
            ('власть', '👑 Власть и её природа'),
            ('семья', '👨‍👩‍👧 Семья и родственные отношения'),
            ('смерть', '💀 Смерть, экзистенциальные вопросы'),
            ('природа', '🌲 Природа, естественность'),
            ('честь', '🎖️ Честь, долг, благородство'),
            ('нигилизм', '🚫 Нигилизм, отрицание'),
            ('искусство', '🎨 Искусство, творчество')
        ]
        
        self.theme_vars = {}
        current_themes = self.preferences.get('темы', [])
        
        # Три столбца
        frame = tk.Frame(self.question_frame, bg=self.colors['secondary'])
        frame.pack(fill='x', padx=20)
        
        columns = [tk.Frame(frame, bg=self.colors['secondary']) for _ in range(3)]
        for col in columns:
            col.pack(side='left', fill='both', expand=True)
        
        for i, (value, text) in enumerate(themes):
            var = tk.BooleanVar(value=value in current_themes)
            self.theme_vars[value] = var
            
            cb = tk.Checkbutton(columns[i % 3],
                               text=text,
                               variable=var,
                               font=('Segoe UI', 10),
                               bg=self.colors['secondary'],
                               fg=self.colors['fg'],
                               selectcolor=self.colors['button'],
                               activebackground=self.colors['secondary'],
                               activeforeground=self.colors['accent'],
                               cursor='hand2',
                               padx=5, pady=5)
            cb.pack(anchor='w', pady=2)
            
            var.trace_add('write', lambda *args: self._update_themes())
    
    def _update_themes(self):
        """Обновление списка выбранных тем"""
        selected = [k for k, v in self.theme_vars.items() if v.get()]
        self.preferences['темы'] = selected
    
    def create_step_hero(self):
        """Шаг 5: Тип героя"""
        question = tk.Label(self.question_frame,
                           text="🦸 Какой тип главного героя вам ближе?",
                           font=('Segoe UI', 16, 'bold'),
                           bg=self.colors['secondary'],
                           fg=self.colors['fg'])
        question.pack(pady=(30, 20))
        
        self.hero_var = tk.StringVar(value=self.preferences.get('тип_героя', ''))
        
        options = [
            ('идеалист', '😇 Идеалист — верит в добро и справедливость'),
            ('бунтарь', '✊ Бунтарь — борется против системы'),
            ('лишний_человек', '😔 «Лишний человек» — талантливый, но не находит места'),
            ('обыватель', '👤 Обыватель — обычный человек в необычных обстоятельствах'),
            ('искатель', '🔍 Искатель — ищет истину и смысл жизни'),
            ('жертва', '😢 Жертва — страдает от обстоятельств'),
            ('антигерой', '🖤 Антигерой — неоднозначный персонаж с тёмной стороной')
        ]
        
        # Два столбца
        frame = tk.Frame(self.question_frame, bg=self.colors['secondary'])
        frame.pack(fill='x', padx=30)
        
        left = tk.Frame(frame, bg=self.colors['secondary'])
        left.pack(side='left', fill='both', expand=True)
        
        right = tk.Frame(frame, bg=self.colors['secondary'])
        right.pack(side='right', fill='both', expand=True)
        
        for i, (value, text) in enumerate(options):
            parent = left if i < 4 else right
            rb = tk.Radiobutton(parent,
                               text=text,
                               variable=self.hero_var,
                               value=value,
                               font=('Segoe UI', 11),
                               bg=self.colors['secondary'],
                               fg=self.colors['fg'],
                               selectcolor=self.colors['button'],
                               activebackground=self.colors['secondary'],
                               activeforeground=self.colors['accent'],
                               cursor='hand2',
                               padx=10, pady=6)
            rb.pack(anchor='w', pady=2)
        
        self.hero_var.trace_add('write', lambda *args: self.preferences.update({'тип_героя': self.hero_var.get()}))
    
    def create_step_conflict(self):
        """Шаг 6: Тип конфликта"""
        question = tk.Label(self.question_frame,
                           text="⚡ Какой тип конфликта вам интереснее?",
                           font=('Segoe UI', 16, 'bold'),
                           bg=self.colors['secondary'],
                           fg=self.colors['fg'])
        question.pack(pady=(30, 20))
        
        self.conflict_var = tk.StringVar(value=self.preferences.get('тип_конфликта', ''))
        
        options = [
            ('личность_vs_общество', '👤 vs 👥 Личность против общества'),
            ('добро_vs_зло', '😇 vs 😈 Добро против зла, нравственный выбор'),
            ('долг_vs_чувство', '⚖️ Долг против чувства, разум против сердца'),
            ('идеал_vs_реальность', '✨ vs 🌍 Идеал против жестокой реальности'),
            ('старое_vs_новое', '📜 vs 🆕 Старое против нового, конфликт поколений'),
            ('свобода_vs_система', '🕊️ vs 🏛️ Свобода против системы')
        ]
        
        for value, text in options:
            rb = tk.Radiobutton(self.question_frame,
                               text=text,
                               variable=self.conflict_var,
                               value=value,
                               font=('Segoe UI', 12),
                               bg=self.colors['secondary'],
                               fg=self.colors['fg'],
                               selectcolor=self.colors['button'],
                               activebackground=self.colors['secondary'],
                               activeforeground=self.colors['accent'],
                               cursor='hand2',
                               padx=20, pady=8)
            rb.pack(anchor='w', padx=50, pady=3)
        
        self.conflict_var.trace_add('write', lambda *args: self.preferences.update({'тип_конфликта': self.conflict_var.get()}))
    
    def create_step_tools(self):
        """Шаг 7: Художественные средства"""
        question = tk.Label(self.question_frame,
                           text="🎨 Какие художественные приёмы вам нравятся?",
                           font=('Segoe UI', 16, 'bold'),
                           bg=self.colors['secondary'],
                           fg=self.colors['fg'])
        question.pack(pady=(20, 15))
        
        tools = [
            ('психологизм', '🧠 Глубокий психологизм'),
            ('символизм', '🔮 Символизм, скрытые смыслы'),
            ('ирония', '😏 Ирония, тонкий юмор'),
            ('лиризм', '🌸 Лиризм, поэтичность'),
            ('фантастика', '🚀 Фантастика'),
            ('гротеск', '🎭 Гротеск, преувеличение'),
            ('диалоги', '💬 Живые диалоги'),
            ('пейзажи', '🏞️ Описания природы'),
            ('сатира', '📢 Острая сатира'),
            ('фольклор', '🎻 Фольклорные мотивы'),
            ('монологи', '💭 Внутренние монологи'),
            ('аллюзии', '📚 Литературные аллюзии')
        ]
        
        self.tool_vars = {}
        current_tools = self.preferences.get('художественные_средства', [])
        
        # Три столбца
        frame = tk.Frame(self.question_frame, bg=self.colors['secondary'])
        frame.pack(fill='x', padx=20)
        
        columns = [tk.Frame(frame, bg=self.colors['secondary']) for _ in range(3)]
        for col in columns:
            col.pack(side='left', fill='both', expand=True)
        
        for i, (value, text) in enumerate(tools):
            var = tk.BooleanVar(value=value in current_tools)
            self.tool_vars[value] = var
            
            cb = tk.Checkbutton(columns[i % 3],
                               text=text,
                               variable=var,
                               font=('Segoe UI', 10),
                               bg=self.colors['secondary'],
                               fg=self.colors['fg'],
                               selectcolor=self.colors['button'],
                               activebackground=self.colors['secondary'],
                               activeforeground=self.colors['accent'],
                               cursor='hand2',
                               padx=5, pady=5)
            cb.pack(anchor='w', pady=2)
            
            var.trace_add('write', lambda *args: self._update_tools())
    
    def _update_tools(self):
        """Обновление списка выбранных средств"""
        selected = [k for k, v in self.tool_vars.items() if v.get()]
        self.preferences['художественные_средства'] = selected
    
    # ==================== РЕЗУЛЬТАТЫ ====================
    
    def show_results(self):
        """Показать результаты рекомендаций"""
        self.clear_question_frame()
        self.progress_label.config(text="✅ Результаты")
        
        # Создаём скроллируемую область для всего контента
        main_canvas = tk.Canvas(self.question_frame, 
                               bg=self.colors['secondary'],
                               highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(self.question_frame, orient='vertical', command=main_canvas.yview)
        content_frame = tk.Frame(main_canvas, bg=self.colors['secondary'])
        
        content_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=content_frame, anchor='nw', width=950)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Привязка колеса мыши
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # ==================== ПУТЬ ПРИНЯТИЯ РЕШЕНИЯ ====================
        path_frame = tk.Frame(content_frame, bg=self.colors['card'], padx=15, pady=10)
        path_frame.pack(fill='x', pady=(10, 15), padx=10)
        
        # Заголовок и кнопка копирования
        header_frame = tk.Frame(path_frame, bg=self.colors['card'])
        header_frame.pack(fill='x')
        
        path_title = tk.Label(header_frame,
                             text="📋 Ваш выбор:",
                             font=('Segoe UI', 11, 'bold'),
                             bg=self.colors['card'],
                             fg=self.colors['fg'])
        path_title.pack(side='left')
        
        # Формируем текст для копирования
        self.path_text = self._format_simple_path()
        
        copy_btn = tk.Button(header_frame,
                            text="📋 Копировать",
                            font=('Segoe UI', 9),
                            bg=self.colors['button'],
                            fg=self.colors['fg'],
                            activebackground=self.colors['accent'],
                            border=0,
                            padx=10, pady=3,
                            cursor='hand2',
                            command=self._copy_path_to_clipboard)
        copy_btn.pack(side='right')
        
        # Текстовое поле с путём (можно выделять и копировать)
        path_text_widget = tk.Text(path_frame,
                                   height=6,
                                   font=('Consolas', 10),
                                   bg='#0d1117',
                                   fg='#c9d1d9',
                                   relief='flat',
                                   padx=10, pady=10,
                                   wrap='word',
                                   cursor='arrow')
        path_text_widget.pack(fill='x', pady=(10, 0))
        path_text_widget.insert('1.0', self.path_text)
        path_text_widget.config(state='disabled')  # Только чтение, но можно выделять
        
        # ==================== ЗАГОЛОВОК РЕКОМЕНДАЦИЙ ====================
        title = tk.Label(content_frame,
                        text="🎯 Ваши рекомендации",
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['secondary'],
                        fg=self.colors['accent'])
        title.pack(pady=(20, 10))
        
        results = get_recommendations(self.preferences)
        
        if not results:
            no_results = tk.Label(content_frame,
                                 text="😕 К сожалению, не удалось подобрать книги по вашим критериям.\nПопробуйте изменить параметры поиска.",
                                 font=('Segoe UI', 12),
                                 bg=self.colors['secondary'],
                                 fg=self.colors['fg'])
            no_results.pack(pady=30)
        else:
            # Показываем результаты
            for i, result in enumerate(results):
                self._create_book_card(content_frame, result, i + 1)
        
        # Размещаем скролл
        main_canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        main_scrollbar.pack(side='right', fill='y')
        
        # Обновляем кнопки
        self.next_btn.config(text="🔄 Начать заново", command=self.reset)
        self.back_btn.config(state='normal')
    
    def _copy_path_to_clipboard(self):
        """Копирование пути в буфер обмена"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.path_text)
        # Показываем уведомление
        messagebox.showinfo("Скопировано", "Путь принятия решения скопирован в буфер обмена!")
    
    def _format_simple_path(self):
        """Форматирование простого текста пути"""
        lines = []
        
        # Объём
        volume = self.preferences.get('объём', '')
        if volume:
            vol_text = {'короткое': 'до 200 стр.', 'среднее': '200-500 стр.', 'длинное': 'более 500 стр.'}
            lines.append(f"Объём: {volume} ({vol_text.get(volume, '')})")
        
        # Сложность
        complexity = self.preferences.get('сложность', '')
        if complexity:
            lines.append(f"Сложность: {complexity}")
        
        # Настроение
        mood = self.preferences.get('настроение', '')
        if mood:
            lines.append(f"Настроение: {mood}")
        
        # Темы
        themes = self.preferences.get('темы', [])
        if themes:
            lines.append(f"Темы: {', '.join(themes)}")
        
        # Тип героя
        hero = self.preferences.get('тип_героя', '')
        if hero:
            lines.append(f"Тип героя: {hero.replace('_', ' ')}")
        
        # Тип конфликта
        conflict = self.preferences.get('тип_конфликта', '')
        if conflict:
            lines.append(f"Конфликт: {conflict.replace('_', ' ')}")
        
        # Художественные средства
        tools = self.preferences.get('художественные_средства', [])
        if tools:
            lines.append(f"Приёмы: {', '.join(tools)}")
        
        return '\n'.join(lines)
    
    def _format_details_text(self):
        """Форматирование детального текста выбора"""
        lines = []
        
        # Объём
        volume = self.preferences.get('объём', '')
        if volume:
            volume_text = {'короткое': 'до 200 стр.', 'среднее': '200-500 стр.', 'длинное': 'более 500 стр.'}
            lines.append(f"📖 Объём: {volume} ({volume_text.get(volume, '')})")
        
        # Сложность
        complexity = self.preferences.get('сложность', '')
        if complexity:
            lines.append(f"🧠 Сложность: {complexity}")
        
        # Настроение
        mood = self.preferences.get('настроение', '')
        if mood:
            lines.append(f"🎭 Настроение: {mood}")
        
        # Темы
        themes = self.preferences.get('темы', [])
        if themes:
            lines.append(f"📌 Темы: {', '.join(themes)}")
        
        # Тип героя
        hero = self.preferences.get('тип_героя', '')
        if hero:
            lines.append(f"🦸 Тип героя: {hero.replace('_', ' ')}")
        
        # Тип конфликта
        conflict = self.preferences.get('тип_конфликта', '')
        if conflict:
            lines.append(f"⚔️ Конфликт: {conflict.replace('_', ' ')}")
        
        # Художественные средства
        tools = self.preferences.get('художественные_средства', [])
        if tools:
            lines.append(f"🎨 Приёмы: {', '.join(tools)}")
        
        return '\n'.join(lines)
    
    def _create_book_card(self, parent, result, num):
        """Создание карточки книги"""
        card = tk.Frame(parent, bg=self.colors['card'], padx=15, pady=15)
        card.pack(fill='x', pady=8, padx=5)
        
        # Номер и название
        header = tk.Frame(card, bg=self.colors['card'])
        header.pack(fill='x')
        
        num_label = tk.Label(header,
                            text=f"#{num}",
                            font=('Segoe UI', 14, 'bold'),
                            bg=self.colors['accent'],
                            fg='white',
                            padx=10, pady=2)
        num_label.pack(side='left')
        
        # Название скрыто, показываем при нажатии
        self.revealed = {}
        
        title_btn = tk.Button(header,
                             text="🔮 Нажмите, чтобы узнать название",
                             font=('Segoe UI', 14, 'bold'),
                             bg=self.colors['card'],
                             fg=self.colors['success'],
                             activebackground=self.colors['card'],
                             activeforeground=self.colors['accent'],
                             border=0,
                             cursor='hand2')
        title_btn.pack(side='left', padx=15)
        
        book_name = result.get('название', 'Неизвестно')
        title_btn.config(command=lambda btn=title_btn, name=book_name: self._reveal_title(btn, name))
        
        # Объяснение
        explanation = tk.Label(card,
                              text=f"💡 {result.get('объяснение', '')}",
                              font=('Segoe UI', 11),
                              bg=self.colors['card'],
                              fg=self.colors['fg'],
                              wraplength=800,
                              justify='left')
        explanation.pack(anchor='w', pady=(10, 5))
        
        # Дополнительная информация
        data = result.get('данные', {})
        if data:
            info_frame = tk.Frame(card, bg=self.colors['card'])
            info_frame.pack(fill='x', pady=(5, 0))
            
            info_text = []
            if data.get('автор'):
                info_text.append(f"✍️ {data['автор']}")
            if data.get('жанр'):
                info_text.append(f"📖 {data['жанр']}")
            if data.get('страницы'):
                info_text.append(f"📄 {data['страницы']} стр.")
            if data.get('год'):
                info_text.append(f"📅 {data['год']}")
            
            if info_text:
                info_label = tk.Label(info_frame,
                                     text="  |  ".join(info_text),
                                     font=('Segoe UI', 10),
                                     bg=self.colors['card'],
                                     fg='#888')
                info_label.pack(anchor='w')
    
    def _reveal_title(self, btn, name):
        """Показать название книги"""
        btn.config(text=f"📚 {name}", fg=self.colors['accent'])
    

def main():
    """Точка входа"""
    root = tk.Tk()
    app = BookRecommenderApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()

