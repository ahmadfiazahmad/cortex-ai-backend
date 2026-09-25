from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


class ExtractionError(Exception):
    pass


def extract_text(file_path: str, file_type: str) -> tuple[str, int | None]:
    path = Path(file_path)

    try:
        if file_type == "pdf":
            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            return "\n".join(pages), len(reader.pages)

        if file_type == "docx":
            document = DocxDocument(str(path))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            return text, None

        if file_type == "txt":
            return path.read_text(encoding="utf-8", errors="replace"), None

        raise ExtractionError(f"Unsupported file type: {file_type}")

    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"Failed to extract text from file: {exc}") from exc
