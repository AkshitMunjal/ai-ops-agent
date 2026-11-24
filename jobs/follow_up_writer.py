import re

from extraction.llm_client import ask_llm
from jobs.text_format import format_amount
from jobs.text_format import format_date

writer_instruction = (
    "You write short, polite payment reminder emails for the accounts team of a small company. "
    "Write only the email body, in plain text. "
    "Start with 'Dear' and the customer name. "
    "Mention the invoice number, the amount and the due date exactly as given. "
    "Ask the customer to pay, or to reply if they have already paid. "
    "Use only the facts given. Do not add bank details, late fees, new deadlines, threats or promises. "
    "End with 'Accounts Team'. Keep it under 120 words."
)


def amount_is_in_text(amount, text):
    text_without_commas = text.replace(",", "")
    wanted_texts = [f"{amount:.2f}"]

    if amount == int(amount):
        wanted_texts.append(str(int(amount)))

    for wanted_text in wanted_texts:
        pattern = r"(?<!\d)" + re.escape(wanted_text) + r"(?!\d)"

        if re.search(pattern, text_without_commas):
            return True

    return False


def facts_are_in_text(invoice, text):
    invoice_number_pattern = r"(?<!\d)" + str(invoice["id"]) + r"(?!\d)"

    if re.search(invoice_number_pattern, text) is None:
        return False

    if invoice["customer_name"] not in text:
        return False

    if format_date(invoice["due_date"]) not in text:
        return False

    return amount_is_in_text(invoice["amount_in_rupees"], text)


def make_subject(invoice):
    return f"Payment reminder: invoice {invoice['id']}"


def make_template_body(invoice):
    amount_text = format_amount(invoice["amount_in_rupees"])
    due_date_text = format_date(invoice["due_date"])

    return (
        f"Dear {invoice['customer_name']},\n\n"
        f"This is a friendly reminder that invoice {invoice['id']} for Rs {amount_text} "
        f"was due on {due_date_text}. "
        "Please arrange the payment, or reply to this email if you have already paid.\n\n"
        "Thank you.\n"
        "Accounts Team"
    )


def make_facts_text(invoice):
    return (
        f"Customer name: {invoice['customer_name']}\n"
        f"Invoice number: {invoice['id']}\n"
        f"Amount due: Rs {format_amount(invoice['amount_in_rupees'])}\n"
        f"Due date: {format_date(invoice['due_date'])}"
    )


def write_follow_up_email(invoice):
    subject = make_subject(invoice)

    try:
        ai_body = ask_llm(writer_instruction, make_facts_text(invoice))
    except Exception as error:
        print(f"The AI could not write the email, using the fixed text: {error}")
        return {"subject": subject, "body": make_template_body(invoice), "written_by": "template"}

    ai_body = ai_body.strip()

    if not facts_are_in_text(invoice, ai_body):
        print(f"The AI text for invoice {invoice['id']} missed a fact, using the fixed text.")
        return {"subject": subject, "body": make_template_body(invoice), "written_by": "template"}

    return {"subject": subject, "body": ai_body, "written_by": "ai"}