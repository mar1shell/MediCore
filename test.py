from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Define Pydantic models for structured output
class Patient(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    date_of_birth: Optional[str] = None

class Diagnosis(BaseModel):
    name: str
    icd_code: Optional[str] = None
    date: Optional[str] = None

class MedicalChartAnnotation(BaseModel):
    patient: Patient
    diagnoses: List[Diagnosis] = []
    allergies: List[str] = []
    medications: List[str] = []
    symptoms: List[str] = []
    doctor_notes: Optional[str] = None

with Mistral(api_key=os.getenv("MISTRAL_API_KEY", "")) as mistral:
    
    annotation_prompt = """
    Extract the following medical information from this document:
    - Patient name, age, date of birth
    - Diagnoses with ICD codes
    - Allergies
    - Current medications
    - Symptoms reported
    - Doctor's notes
    
    Return valid JSON only.
    """

    # Generate response format from Pydantic model
    document_annotation_format = response_format_from_pydantic_model(MedicalChartAnnotation)
    
    res = mistral.ocr.process(
        model="mistral-ocr-latest",
        document={
            "document_url": "https://raw.githubusercontent.com/mistralai/cookbook/refs/heads/main/mistral/ocr/hcls/patient-packet-completed.pdf",
            "type": "document_url",
        },
        document_annotation_prompt=annotation_prompt,
        document_annotation_format=document_annotation_format,
    )
    
    print(f"Pages processed: {res.usage_info.pages_processed}")
    print(f"Document size: {res.usage_info.doc_size_bytes / 1024 / 1024:.2f} MB")
    print(f"Model: {res.model}")
    
    if res.document_annotation:
        print("\nExtracted Structured Data:")
        data = json.loads(res.document_annotation) if isinstance(res.document_annotation, str) else res.document_annotation
        print(json.dumps(data, indent=2))
    else:
        print("No structured annotation returned")
