import os
from mistralai import Mistral


def run_ocr(pdf_bytes: bytes) -> str:
    """Send PDF bytes to Mistral OCR and return raw extracted text."""
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    # TODO: implement Mistral OCR API call
    raise NotImplementedError
