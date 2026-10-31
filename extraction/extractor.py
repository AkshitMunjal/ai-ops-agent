from pydantic import ValidationError

from extraction.llm_client import ask_llm
from extraction.schemas import ExtractedOrder

extraction_instruction = """You read customer emails and extract the order.
customer_name is the company or shop placing the order, not the
person who signed the email. If only a person's name is given, use that.
Reply with JSON only, no other text, in exactly this shape:
{"customer_name": "...", "lines": [{"product_name": "...", "quantity": 0}]}"""


class ExtractionError(Exception):
    pass


def remove_code_fences(text):
    text = text.strip()
    if text.startswith("```"):
        all_lines = text.split("\n")
        inner_lines = all_lines[1:-1]
        text = "\n".join(inner_lines)
    return text


def extract_order(email_text):
    reply_text = ask_llm(extraction_instruction, email_text)
    clean_text = remove_code_fences(reply_text)

    try:
        order = ExtractedOrder.model_validate_json(clean_text)
    except ValidationError as error:
        raise ExtractionError(f"The model reply was not a valid order: {error}")

    return order