from io import BytesIO

import httpx
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from cost_control.limit import SpendLimitReached
from extraction.llm_client import ask_llm_with_pictures
from intake.pdf_pictures import PdfPictureError, pdf_to_picture_links
from intake.submit import TryLaterError

ocr_instruction = (
    "These pictures are the pages of a scanned document. "
    "Read all the text in them exactly as written. "
    "Reply with the text only. Do not add code fences or comments."
)


class PdfTextError(Exception):
    pass


def remove_code_fences(text):
    kept_lines = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            continue
        kept_lines.append(line)

    return "\n".join(kept_lines).strip()


def read_scanned_pdf_with_ai(pdf_bytes):
    try:
        picture_links = pdf_to_picture_links(pdf_bytes)
    except PdfPictureError as error:
        raise PdfTextError(str(error))

    try:
        ai_reply = ask_llm_with_pictures(ocr_instruction, picture_links)
    except SpendLimitReached as error:
        raise TryLaterError(str(error))
    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code
        if status_code == 429 or status_code >= 500:
            raise TryLaterError("The AI service is busy, so the scanned PDF could not be read yet")
        raise PdfTextError(f"The AI service refused to read the scanned PDF ({status_code})")
    except httpx.RequestError:
        raise TryLaterError("The AI service is not reachable, so the scanned PDF could not be read yet")

    text = remove_code_fences(ai_reply)

    if not text:
        raise PdfTextError("The AI could not read any text in this scanned PDF.")

    return text


def text_from_pdf_bytes(pdf_bytes):
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except (PdfReadError, OSError) as error:
        raise PdfTextError(f"The PDF could not be opened: {error}")

    page_texts = []
    for page in reader.pages:
        page_text = page.extract_text()
        page_texts.append(page_text)

    return "\n".join(page_texts).strip()


def read_pdf_bytes(pdf_bytes):
    text = text_from_pdf_bytes(pdf_bytes)

    if text:
        return text

    return read_scanned_pdf_with_ai(pdf_bytes)


def read_pdf_text(pdf_path):
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
    except (FileNotFoundError, OSError) as error:
        raise PdfTextError(f"The PDF could not be opened: {error}")

    return read_pdf_bytes(pdf_bytes)