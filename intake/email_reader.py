import html
import re
from email import policy
from email.parser import BytesParser
from intake.pdf_reader import PdfTextError, read_pdf_bytes


def html_to_text(html_body):
    text = re.sub(r"<(script|style).*?</\1>", " ", html_body, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return text.strip()


def get_body_text(message):
    body_part = message.get_body(preferencelist=("plain", "html"))
    if body_part is None:
        return ""

    body_text = body_part.get_content()
    if body_part.get_content_type() == "text/html":
        body_text = html_to_text(body_text)

    return body_text.strip()


def is_pdf(attachment):
    file_name = attachment.get_filename() or ""
    content_type = attachment.get_content_type()
    return content_type == "application/pdf" or file_name.lower().endswith(".pdf")


def get_attachment_text(message):
    attachment_texts = []

    for attachment in message.iter_attachments():
        file_name = attachment.get_filename() or "unnamed file"

        if not is_pdf(attachment):
            attachment_texts.append(f"[Attachment {file_name} was skipped: not a PDF]")
            continue

        pdf_bytes = attachment.get_payload(decode=True)
        try:
            pdf_text = read_pdf_bytes(pdf_bytes)
        except PdfTextError as error:
            attachment_texts.append(f"[Attachment {file_name} could not be read: {error}]")
            continue

        attachment_texts.append(f"Attachment {file_name}:\n{pdf_text}")

    return attachment_texts


def read_email_file(eml_path):
    with open(eml_path, "rb") as email_file:
        message = BytesParser(policy=policy.default).parse(email_file)

    header_text = f"From: {message['from']}\nSubject: {message['subject']}"

    parts = [header_text, get_body_text(message)]
    parts.extend(get_attachment_text(message))

    return "\n\n".join(parts)