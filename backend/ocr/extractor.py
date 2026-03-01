"""OCR — extract structured medical data from patient charts using Mistral OCR API.

Uses Mistral's OCR model with JSON schema enforcement to ensure structured,
validated medical entity extraction.
"""

from __future__ import annotations

import base64
import json
from typing import Optional

from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model
from pydantic import BaseModel

from config import get_settings



# Pydantic Models for Structured Output


class Patient(BaseModel):
    """Patient demographic information."""
    name: Optional[str] = None
    age: Optional[int] = None
    date_of_birth: Optional[str] = None


class Diagnosis(BaseModel):
    """Clinical diagnosis with ICD coding."""
    name: str
    icd_code: Optional[str] = None
    date: Optional[str] = None


class MedicalChartAnnotation(BaseModel):
    """Complete structured medical chart extraction."""
    patient: Patient
    diagnoses: list[Diagnosis] = []
    allergies: list[str] = []
    medications: list[str] = []
    symptoms: list[str] = []
    doctor_notes: Optional[str] = None



# OCR Extraction Functions


def extract_structured_data(pdf_url: str) -> dict:
    """Extract structured medical data from a patient chart PDF via URL.

    Args:
        pdf_url: HTTPS URL to the PDF document.

    Returns:
        Dictionary matching MedicalChartAnnotation schema with extracted entities.

    Raises:
        ValueError: If OCR extraction fails or validation fails.
    """
    settings = get_settings()
    client = Mistral(api_key=settings.mistral_api_key)

    annotation_prompt = """
    Extract the following medical information from this document:
    - Patient name, age, date of birth
    - Diagnoses with ICD codes and dates
    - Allergies
    - Current medications
    - Symptoms reported
    - Doctor's notes or clinical observations
    
    Return valid JSON only.
    """

    document_annotation_format = response_format_from_pydantic_model(
        MedicalChartAnnotation
    )

    try:
        res = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "document_url": pdf_url,
                "type": "document_url",
            },
            document_annotation_prompt=annotation_prompt,
            document_annotation_format=document_annotation_format,
        )
    except Exception as e:
        raise ValueError(f"OCR processing failed: {str(e)}")

    if not res.document_annotation:
        raise ValueError("No structured annotation returned from OCR")

    # Parse and validate the response
    try:
        data = (
            json.loads(res.document_annotation)
            if isinstance(res.document_annotation, str)
            else res.document_annotation
        )
        validated = MedicalChartAnnotation.model_validate(data)
        return validated.model_dump()
    except Exception as e:
        raise ValueError(f"Failed to parse/validate OCR output: {str(e)}")


def extract_structured_data_from_bytes(
    pdf_bytes: bytes,
) -> dict:
    """Extract structured medical data from PDF bytes (local file upload).

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        Dictionary matching MedicalChartAnnotation schema with extracted entities.

    Raises:
        ValueError: If encoding or OCR extraction fails.
    """
    # Convert bytes to base64 data URI
    try:
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        data_uri = f"data:application/pdf;base64,{pdf_b64}"
    except Exception as e:
        raise ValueError(f"Failed to encode PDF: {str(e)}")

    # Use the URL-based extractor with data URI
    return extract_structured_data(data_uri)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Legacy fallback: extract plain text only (no structured output).

    For cases where structured extraction is not needed or as a
    backup if Mistral OCR is unavailable.

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        Extracted text as a single string.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return "(PyMuPDF not available)"

    text_parts: list[str] = []

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                page_text = page.get_text("text").strip()
                if page_text:
                    text_parts.append(page_text)
    except Exception:
        pass

    return "\n\n".join(text_parts) if text_parts else "(No text extracted)"
