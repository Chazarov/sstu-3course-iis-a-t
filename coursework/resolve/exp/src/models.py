
from dataclasses import dataclass
from typing import Any, List, Literal, Mapping, Optional

from pydantic import BaseModel, Field


# ============ Исключения ============


class DialogError(Exception):
    """Исключение для ошибок валидации в диалоге."""
    pass

class ClientAnswer(BaseModel):
    type: Literal["client-answer"] = "answer"
    text_answer: Optional[str] = Field(None, description="ответ")
    items_answer: Optional[List[str]] = Field(None, description="ответ в виде списка значений")

class QuestionMessage(BaseModel):
    """Сообщение с вопросом пользователю."""
    type: Literal["question"] = "question"
    is_multiple_response_options: bool = Field(..., description="Можно выбрать несколько")
    field: str = Field(..., description="Поле для фильтрации")
    text: str = Field(..., description="Текст вопроса")
    avaliable_answers: List[str] = Field(..., description="Примеры значений")


class Recommendation(BaseModel):
    id: str
    title: str
    score: int
    matched: List[str]
    info: Mapping[str, Any]


@dataclass(frozen=True)
class BookFrame:
    id: str
    title: str
    raw: Mapping[str, Any]
    match: Mapping[str, Any]





class RecommendationItem(BaseModel):
    """Модель элемента рекомендации для отправки клиенту."""
    title: str = Field(..., description="Название произведения")
    score: int = Field(..., description="Количество совпадений")
    matched: List[str] = Field(..., description="Список совпавших критериев")
    author: Optional[str] = Field(None, description="Автор")
    genre: Optional[str] = Field(None, description="Жанр")
    epoch: Optional[str] = Field(None, description="Эпоха")
    mood: Optional[str] = Field(None, description="Настроение")
    difficulty: Optional[str] = Field(None, description="Сложность")
    volume: Optional[str] = Field(None, description="Объём")
    image: Optional[str] = Field(None, description="URL изображения")

class RecomendationsMessage(BaseModel):
    """Сообщение с результатами рекомендаций."""
    type: Literal["result"] = "result"
    text: str = Field(..., description="Текст сообщения")
    items: List[RecommendationItem] = Field(..., description="Список рекомендаций")


class ErrorMessage(BaseModel):
    """Сообщение об ошибке."""
    type: Literal["error"] = "error"
    text: str = Field(..., description="Текст ошибки")


class InfoMessage(BaseModel):
    """Информационное сообщение."""
    type: Literal["info"] = "info"
    text: str = Field(..., description="Текст сообщения")


class Question(BaseModel):
    """Модель вопроса в диалоге."""
    field: str = Field(..., description="Поле для фильтрации (жанр, эпоха и т.д.)")
    prompt: str = Field(..., description="Текст вопроса пользователю")
    is_multi: bool = Field(default=False, description="Разрешены ли множественные значения")
