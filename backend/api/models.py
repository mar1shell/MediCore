from pydantic import BaseModel
from typing import Literal


class ChartUploadResponse(BaseModel):
    raw_text: str


class ExtractEntitiesRequest(BaseModel):
    text: str


class EntityData(BaseModel):
    allergies: list[str]
    medications: list[str]
    diagnosis: list[str]


class CrossReferenceRequest(BaseModel):
    chart_data: EntityData
    spoken_data: EntityData


class DiscrepancyFlag(BaseModel):
    severity: Literal["high", "medium", "low"]
    field: str
    chart_val: str
    spoken_val: str
    message: str


class CrossReferenceResponse(BaseModel):
    flags: list[DiscrepancyFlag]
