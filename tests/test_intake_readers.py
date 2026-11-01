from email.message import EmailMessage
from pathlib import Path

import pytest

from intake.email_reader import html_to_text, read_email_file
from intake.pdf_reader import PdfTextError, read_pdf_bytes, read_pdf_text

samples_folder = Path(__file__).parent / "samples"


def save_email(message, tmp_path):
    email_path = tmp_path / "test.eml"
    email_path.write_bytes(bytes(message))
    return str(email_path)


def test_read_pdf_text_finds_the_order_lines():
    text = read_pdf_text(str(samples_folder / "order_gupta.pdf"))
    assert "Gupta Stores" in text
    assert "Steel Bolts M8" in text


def test_read_pdf_text_missing_file_raises():
    with pytest.raises(PdfTextError):
        read_pdf_text(str(samples_folder / "does_not_exist.pdf"))


def test_read_pdf_bytes_garbage_raises():
    with pytest.raises(PdfTextError):
        read_pdf_bytes(b"this is not a pdf")


def test_read_pdf_bytes_matches_read_pdf_text():
    pdf_path = samples_folder / "order_gupta.pdf"
    from_bytes = read_pdf_bytes(pdf_path.read_bytes())
    from_path = read_pdf_text(str(pdf_path))
    assert from_bytes == from_path


def test_plain_email_has_sender_subject_and_body():
    text = read_email_file(str(samples_folder / "email_plain.eml"))
    assert "From: Rakesh Gupta" in text
    assert "Subject: Order for this week" in text
    assert "40 steel bolts M8" in text


def test_email_with_pdf_includes_the_pdf_text():
    text = read_email_file(str(samples_folder / "email_with_pdf.eml"))
    assert "Attachment PO-1042.pdf:" in text
    assert "Steel Bolts M8" in text


def test_html_to_text_removes_tags():
    text = html_to_text("<p>Send <b>5</b> bolts</p><style>p {color: red}</style>")
    assert "Send" in text
    assert "<" not in text
    assert "color" not in text


def test_html_only_email_is_read_as_text(tmp_path):
    message = EmailMessage()
    message["From"] = "a@example.com"
    message["Subject"] = "Html order"
    message.set_content("<html><body><p>Send 5 bolts</p></body></html>", subtype="html")
    text = read_email_file(save_email(message, tmp_path))
    assert "Send 5 bolts" in text
    assert "<p>" not in text


def test_non_pdf_attachment_is_skipped_with_a_note(tmp_path):
    message = EmailMessage()
    message["From"] = "a@example.com"
    message["Subject"] = "With notes"
    message.set_content("See file.")
    message.add_attachment(b"hello", maintype="text", subtype="plain", filename="notes.txt")
    text = read_email_file(save_email(message, tmp_path))
    assert "notes.txt was skipped" in text


def test_broken_pdf_attachment_does_not_crash(tmp_path):
    message = EmailMessage()
    message["From"] = "a@example.com"
    message["Subject"] = "Bad pdf"
    message.set_content("See file.")
    message.add_attachment(b"garbage", maintype="application", subtype="pdf", filename="bad.pdf")
    text = read_email_file(save_email(message, tmp_path))
    assert "bad.pdf could not be read" in text
    assert "See file." in text