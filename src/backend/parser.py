import re
import os
from langchain_community.document_loaders import UnstructuredFileLoader

def fix_hyphenated_words(text):
    """
    Комплексное исправление переносов слов
    """
    text = re.sub(r'(\b\w+)-\s+(\w+\b)', r'\1\2', text)
    text = re.sub(r'(\b\w+)-[\r\n]+\s*(\w+\b)', r'\1\2', text)

    return text


def clean_pdf_artifacts(text: str) -> str:
    """
    Удаление мусорных символов
    """
    # Заменяем мусор на пробелы
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
    text = re.sub(r'[■●◆♦•\u2022\u25a0\u25cf]+', ' ', text)

    return text


def preprocess_for_embeddings(text: str) -> str:
    """
    Комплексная предобработка текста
    """
    # Исправляем переносы
    text = fix_hyphenated_words(text)
    # Чистим артефакты PDF
    text = clean_pdf_artifacts(text)

    return text


def parse_document(document_path):
    if not os.path.isfile(document_path):
        raise FileNotFoundError(f"Файл не найден: {document_path}")

    # Создаём loader
    loader = UnstructuredFileLoader(
        file_path=document_path,
        strategy="fast",
        languages=["rus"]
    )

    document = loader.load()
    if not document:
        raise ValueError("Парсер не извлёк ни одного документа")

    # Постобработка
    document[0].page_content = preprocess_for_embeddings(document[0].page_content)
    if not document[0].page_content.strip():
        raise ValueError("Парсер не извлёк текст из документа")

    return document[0].page_content


if __name__ == "__main__":
    text = parse_document(os.path.join("Парсер", "Тестовые документы", "История python.pdf"))
    print(text)
