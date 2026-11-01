from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PdfTextError(Exception):
    pass


def text_from_reader(reader):
    page_texts = []
    for page in reader.pages:
        page_text = page.extract_text()
        page_texts.append(page_text)

    full_text = "\n".join(page_texts).strip()

    if not full_text:
        raise PdfTextError("This PDF has no text. It may be a scanned image.")

    return full_text


def read_pdf_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
    except (PdfReadError, FileNotFoundError, OSError) as error:
        raise PdfTextError(f"The PDF could not be opened: {error}")

    return text_from_reader(reader)


def read_pdf_bytes(pdf_bytes):
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except (PdfReadError, OSError) as error:
        raise PdfTextError(f"The PDF could not be opened: {error}")

    return text_from_reader(reader)