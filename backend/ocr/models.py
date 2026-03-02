from dataclasses import dataclass, field
from typing import Literal, Optional

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
    def char_count(self):
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
            "allergies": self.allergies,
            "medications": self.medications,
            "diagnosis": self.diagnosis,
            "extraction_notes": self.extraction_notes,
            "diagrams": self.diagrams
        }
    
@dataclass
class DiscrepancyFlag:
    severity: str # either high, medium, low
    category: str # either allergy missing, diagnosis missing
    chart_value: str
    spoken_value: str
    message: str
    dismissed: bool = False
    added_to_notes: bool = False
    
@dataclass
class CrossReferenceResult:
    flags: list = field(default_factory=list)
    chart_entities: Optional[ExtractedEntities] = None
    spoken_entities: Optional[ExtractedEntities] = None
    @property
    def critical_flags(self) -> list:
        return [f for f in self.flags if f.severity == "HIGH"]
    @property
    def has_critical_flags(self) -> bool:
        return len(self.critical_flags) > 0