from __future__ import annotations

from pathlib import Path

from  application.recommendation import RecommendationService
from  infrastructure.json_data_source import FileSystemJsonDataSource
from  infrastructure.sklearn_similarity_ranker import SklearnSimilarityRanker
from  presentation.tkinter_app import WizardApp


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "sourses"

    bundle = FileSystemJsonDataSource(data_dir=data_dir).load()
    ranker = SklearnSimilarityRanker(books=bundle.books)
    service = RecommendationService(books=bundle.books, rules=bundle.rules, ranker=ranker)

    app = WizardApp(service=service, questions=bundle.questions, data_dir=data_dir)
    if app.winfo_exists():
        app.mainloop()


if __name__ == "__main__":
    main()



