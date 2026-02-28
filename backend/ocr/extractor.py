"""OCR — extract plain text from a PDF file.

Uses PyMuPDF (fitz) for native text layer extraction and falls back to
Tesseract for scanned/image-only pages.
"""

from __future__ import annotations

import io

import fitz  # pymupdf


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Return all text from *pdf_bytes* as a single string.

    Native text is preferred; image-only pages are handled by Tesseract
    when pytesseract and Pillow are available.
    """
    text_parts: list[str] = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text("text").strip()

            if page_text:
                text_parts.append(page_text)
            else:
                # Fallback: render page to image and run Tesseract OCR
                page_text = _ocr_page(page)
                if page_text:
                    text_parts.append(page_text)

    return "\n\n".join(text_parts)


def _ocr_page(page: fitz.Page) -> str:
    """Render *page* to a PIL image and run Tesseract OCR on it."""
    try:
        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img).strip()
    except ImportError:
        return ""
