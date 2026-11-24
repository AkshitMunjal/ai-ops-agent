from pathlib import Path

import pytest

from intake.pdf_pictures import PdfPictureError, max_pages, pdf_to_picture_links

samples_folder = Path(__file__).parent / "samples"


def test_each_page_becomes_one_jpeg_picture_link():
    pdf_bytes = (samples_folder / "order_gupta.pdf").read_bytes()

    picture_links = pdf_to_picture_links(pdf_bytes)

    assert len(picture_links) >= 1
    assert picture_links[0].startswith("data:image/jpeg;base64,")


def test_a_broken_pdf_is_refused():
    with pytest.raises(PdfPictureError):
        pdf_to_picture_links(b"this is not a pdf")


def test_the_page_limit_is_five():
    assert max_pages == 5