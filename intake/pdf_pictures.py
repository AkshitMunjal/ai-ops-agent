import base64
from io import BytesIO

import pypdfium2 as pdfium

max_pages = 5
picture_scale = 1.5
jpeg_quality = 85


class PdfPictureError(Exception):
    pass


def page_to_picture_link(page):
    bitmap = page.render(scale=picture_scale)
    picture = bitmap.to_pil()
    picture = picture.convert("RGB")

    picture_bytes = BytesIO()
    picture.save(picture_bytes, format="JPEG", quality=jpeg_quality)
    jpeg_bytes = picture_bytes.getvalue()

    picture_as_text = base64.b64encode(jpeg_bytes).decode("ascii")
    return "data:image/jpeg;base64," + picture_as_text


def pdf_to_picture_links(pdf_bytes):
    try:
        document = pdfium.PdfDocument(pdf_bytes)
    except pdfium.PdfiumError as error:
        raise PdfPictureError(f"The PDF could not be turned into pictures: {error}")

    page_count = len(document)

    if page_count == 0:
        raise PdfPictureError("The PDF has no pages.")

    if page_count > max_pages:
        raise PdfPictureError(
            f"The PDF has {page_count} pages. Scanned PDFs over {max_pages} pages need a person."
        )

    picture_links = []
    for page_number in range(page_count):
        page = document[page_number]
        picture_link = page_to_picture_link(page)
        picture_links.append(picture_link)

    return picture_links