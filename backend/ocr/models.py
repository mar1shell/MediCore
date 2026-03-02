from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChartPage:
    page_number: int
    text: str
    width: Optional[float] = None
    height: Optional[float] = None

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


@dataclass
class OCRResult:
    filename: str
    full_text: str
    pages: list
    model_used: str
    pages_processed: int

    @property
    def char_count(self) -> int:
        return len(self.full_text)

    @property
    def is_usable(self) -> bool:
        return self.char_count > 50

    def get_page(self, number: int) -> "ChartPage | None":
        for page in self.pages:
            if page.page_number == number:
                return page
        return None


@dataclass
class ExtractedEntities:
    source: str
    patient_name: Optional[str] = None
    allergies: list = field(default_factory=list)
    medications: list = field(default_factory=list)
    diagnosis: Optional[str] = None
    extraction_notes: Optional[str] = None
    diagrams: bool = False

    @classmethod
    def empty(cls, source: str) -> "ExtractedEntities":
        return cls(source=source)

    @property
    def allergy_names(self) -> list:
        return self.allergies

    @property
    def medication_names(self) -> list:
        return [m["name"] for m in self.medications]

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "patient_name": self.patient_name,
            "allergies": self.allergies,
            "medications": self.medications,
            "diagnosis": self.diagnosis,
            "extraction_notes": self.extraction_notes,
            "diagrams": self.diagrams,
        }
