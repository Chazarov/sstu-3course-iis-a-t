"""Domain layer (Entities + pure domain logic).

Правило: домен не импортирует application/infrastructure/presentation и не использует сторонние библиотеки.
"""

from .entities import Book, Preferences

__all__ = ["Book", "Preferences"]



