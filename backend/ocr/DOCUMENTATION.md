# OCR Module — Technical Documentation

## Overview

The `ocr/` module is the core intelligence layer of MediCore's chart processing pipeline. It is responsible for three sequential tasks:

1. **PDF Text Extraction** — Converting a scanned or digital patient chart (PDF) into raw text using Mistral's OCR API.
2. **Medical Entity Extraction** — Parsing that raw text with a large language model to identify structured clinical data: allergies, medications, and diagnoses.
3. **Cross-Reference & Safety Flagging** — Comparing entities extracted from the written chart against entities extracted from a doctor's spoken summary to detect dangerous discrepancies.

The entire module is built asynchronously using `httpx.AsyncClient` and designed around clearly typed Python dataclasses. All AI calls go through **Mistral AI** endpoints.

---

## Module File Structure

```
ocr/
├── __init__.py              # Public interface of the module
├── config.py                # Environment-based configuration loader
├── models.py                # All dataclasses (domain types)
├── prompt_loader.py         # File utilities for prompts and data
├── chart_processor.py       # Stage 1: PDF → raw OCR text
├── entity_extractor.py      # Stage 2: Raw text → structured medical entities
├── cross_reference.py       # Stage 3: Chart entities ↔ Spoken entities comparison
├── prompts/
│   ├── extraction_system_prompt.txt   # System prompt for LLM entity extraction
│   └── extraction_user_template.txt   # User message template for LLM
└── data/
    ├── abbreviation_map.json          # Drug/condition name aliases lookup table
    └── cross_reactivity.json          # Known allergen → cross-reactive drug mappings
```

---

## The Full Pipeline

```
[ PDF bytes ]
      │
      ▼
┌─────────────────────┐
│   ChartProcessor    │   ← Mistral OCR API (mistral-ocr-latest)
│  (chart_processor)  │
└─────────────────────┘
      │
      ▼  OCRResult (per-page markdown text + metadata)
      │
      ▼
┌─────────────────────┐
│   EntityExtractor   │   ← Mistral LLM (mistral-large-latest)
│ (entity_extractor)  │   ← Uses extraction_system_prompt.txt
└─────────────────────┘
      │
      ▼  ExtractedEntities { allergies, medications, diagnosis }
      │                    (from CHART)
      │
      │   [ Also runs on SPOKEN text from voice module ]
      │
      ▼  ExtractedEntities (from SPOKEN SUMMARY)
      │
      ▼
┌──────────────────────────┐
│  CrossReferenceEngine    │   ← Mistral LLM (mistral-small-latest)
│   (cross_reference)      │   ← Uses abbreviation_map.json
│                          │   ← Uses cross_reactivity.json
└──────────────────────────┘
      │
      ▼
CrossReferenceResult { flags: [DiscrepancyFlag, ...] }
```

---

## Stage 1 — PDF to Text: `ChartProcessor`

**File:** `chart_processor.py`  
**Model used:** `mistral-ocr-latest`  
**API endpoint:** `https://api.mistral.ai/v1/ocr`

### What it does

`ChartProcessor` takes raw PDF bytes (the uploaded patient chart) and converts them into structured OCR output using Mistral's OCR model. The model returns the text content of each page rendered as **Markdown**.

### How it works — step by step

1. **PDF encoding:** The raw PDF bytes are Base64-encoded using `base64.standard_b64encode` to make them safe for JSON transport.
2. **Payload construction (`_build_payload`):** A JSON payload is assembled using the `document_url` type with an inline data URI (`data:application/pdf;base64,...`). Image base64 data is explicitly excluded (`include_image_base64: False`) since only text output is needed.
3. **API call (`_call_ocr_api`):** An async POST request is sent to the Mistral OCR endpoint. HTTP errors are caught as `httpx.HTTPError` and re-raised as `OCRProcessingError`. Network errors (`httpx.RequestError`) are also caught and wrapped.
4. **Response parsing (`_parse_response`):** The response's `pages` array is iterated. For each page, a `ChartPage` dataclass is created containing:
   - `page_number`: the page index from the API
   - `text`: the markdown-rendered text of that page
   - `width` / `height`: the page dimensions (if returned)
5. **Output:** An `OCRResult` is returned, holding the list of `ChartPage` objects, the combined `full_text` (all pages joined with double newlines), the model name used, and the count of pages processed.

### Error handling

- If the API returns no pages at all, an `OCRProcessingError` is raised with a descriptive message explaining the possible causes (empty PDF, encrypted, unsupported content).
- `OCRProcessingError` is a custom exception defined in the same file.

### Async context manager support

`ChartProcessor` supports Python's `async with` pattern, ensuring the underlying `httpx.AsyncClient` is always properly closed:
```python
async with ChartProcessor(config) as processor:
    result = await processor.process_pdf(pdf_bytes, "patient_chart.pdf")
```

---

## Stage 2 — Entity Extraction: `EntityExtractor`

**File:** `entity_extractor.py`  
**Model used:** `mistral-large-latest`  
**API endpoint:** `https://api.mistral.ai/v1/chat/completions`

### What it does

`EntityExtractor` takes plain text (either from OCR output or from a transcribed spoken summary) and uses a Mistral large language model to parse out three categories of clinically relevant information: **allergies**, **medications**, and **primary diagnosis**.

### How it works — step by step

1. **Input validation:** If the input text is fewer than 10 characters after stripping, extraction is skipped and an empty `ExtractedEntities` object is returned immediately. This guards against blank or garbage inputs.
2. **Payload construction (`_build_payload`):** A chat completion payload is built. The source label is adjusted based on origin:
   - `"chart"` → labeled as `"patient"` in the prompt
   - anything else → labeled as `"doctor's spoken assessment"`
   
   The model is configured with:
   - `temperature: 0.0` — deterministic, no creativity
   - `response_format: {"type": "json_object"}` — forces strict JSON output
   - Text is truncated to **8000 characters** to stay within practical token budgets
   
3. **System prompt** (`extraction_system_prompt.txt`): This is the most critical component. The LLM is instructed with a strict set of clinical safety rules:
   - Extract **only** explicitly stated information — no inference or guessing
   - Return only the **patient's own allergies** (not family history or suspected ones)
   - Only include **active/current** medications (not discontinued ones)
   - Preserve exact substance names as written
   - Handle `"NKDA"` and `"patient denies allergies"` as empty allergy lists (never null)
   - Return strictly valid JSON with no Markdown fences or preamble

4. **User template** (`extraction_user_template.txt`): A minimal wrapper that injects the source label and the actual text into the conversation.

5. **API call (`_call_llm`):** Async POST to Mistral chat completions. `HTTPStatusError` and `RequestError` are caught and re-raised as `EntityExtractionError`.

6. **Response parsing (`_parse_response`):** The JSON string inside `choices[0].message.content` is parsed. The resulting `ExtractedEntities` object is built with:
   - `allergies`: list of lowercase-stripped allergy strings
   - `medications`: list of dicts with `"name"` (lowercase-stripped) and `"dose"` — invalid entries (missing name) are silently filtered out
   - `diagnosis`: the primary diagnosis string or `None`
   - `extraction_notes`: any notes the LLM flagged about ambiguous content

### Output type: `ExtractedEntities`

```python
@dataclass
class ExtractedEntities:
    source: str           # "chart" or "spoken"
    allergies: list       # e.g. ["penicillin", "sulfa"]
    medications: list     # e.g. [{"name": "lisinopril", "dose": "10mg"}]
    diagnosis: str | None # e.g. "NSTEMI"
    extraction_notes: str | None
```

Convenience properties:
- `.allergy_names` → returns the `allergies` list directly
- `.medication_names` → returns only the `"name"` field from each medication dict

---

## Stage 3 — Cross-Reference Engine: `CrossReferenceEngine`

**File:** `cross_reference.py`  
**Model used:** `mistral-small-latest` (for synonym/semantic matching only)  
**API endpoint:** `https://api.mistral.ai/v1/chat/completions`

### What it does

`CrossReferenceEngine` compares two `ExtractedEntities` objects — one from the **written chart**, one from the **doctor's spoken summary** — and produces a list of `DiscrepancyFlag` objects that represent patient safety concerns.

### The three safety checks

#### 1. Allergy Omissions (`_check_allergy_omissions`)
**Severity: HIGH**

For every allergy documented in the chart, the engine checks whether it was also mentioned in the spoken summary. If a chart allergy is absent from the spoken summary, a `HIGH`-severity flag is raised.

This is the most safety-critical check: if a doctor verbally prescribes a treatment without mentioning a documented allergy, a fatal drug reaction could occur.

#### 2. Contraindications (`_check_contraindications`)
**Severity: HIGH**

For every allergy in the chart, the engine looks up the `cross_reactivity.json` table to find all drugs known to have cross-reactive properties with that allergen. If any of those cross-reactive drugs appear in the spoken medication list, a `HIGH`-severity `"Contraindication"` flag is raised.

Example: If the chart documents a **penicillin allergy** and the doctor verbally mentions **amoxicillin** (a penicillin-family drug), a HIGH flag is generated.

#### 3. Diagnosis Mismatch (`_check_diagnosis_mismatch`)
**Severity: MEDIUM**

If both the chart and spoken summary contain a diagnosis and those diagnoses do not match each other semantically, a `MEDIUM`-severity flag is raised.

### Entity matching — 3-tier resolution

All entity comparisons go through a three-tier resolution strategy to correctly identify when two differently written names refer to the same thing:

**Tier 1 — Exact match:**  
Direct lowercase string equality. Fast, no external calls.

**Tier 2 — Abbreviation/alias lookup (`_canonicalize`):**  
Each name is looked up in `abbreviation_map.json`. The file maps canonical drug and condition names to lists of known aliases, brand names, abbreviations, and alternative spellings. Both names are canonicalized and then compared.

Example: `"asa"` → `"aspirin"`, `"tylenol"` → `"acetaminophen"`, `"nstemi"` → `"nstemi"`, `"non-stemi"` → `"nstemi"`

**Tier 3 — LLM semantic synonym check (`_llm_synonym_check`):**  
If the first two tiers fail, a targeted prompt is sent to `mistral-small-latest`:
```
"In a clinical context, do '{a}' and '{b}' refer to the exact same drug, allergy, or diagnosis? Reply with SAME or DIFFERENT only."
```
The model is limited to 10 output tokens and temperature `0.0`. The answer is parsed as `True` if the response equals `"SAME"`. Errors are caught silently and return `False` (i.e., assume not the same, which is the safer default).

### Data files used

#### `abbreviation_map.json`
A static lookup table mapping canonical medical names to all known aliases:
- Drugs: `"aspirin"` → `["asa", "acetylsalicylic acid", ...]`, `"morphine"` → `["ms", "msir", "ms contin"]`
- Diagnoses: `"nstemi"` → `["non-st elevation mi", "non-stemi", ...]`, `"chf"` → `["congestive heart failure", ...]`
- Allergy keywords: `"nkda"` → `["no known drug allergies", "no known allergies", "nka"]`

#### `cross_reactivity.json`
Maps a canonical allergen to a list of drugs that are cross-reactive with it:
```json
{
  "penicillin": ["amoxicillin", "ampicillin", "piperacillin", ...],
  "aspirin":    ["nsaid", "ibuprofen", "naproxen", ...],
  "sulfa":      ["sulfamethoxazole", "bactrim", "furosemide", ...],
  "contrast":   ["gadolinium"]
}
```

---

## Data Models (`models.py`)

All data flowing through the pipeline is represented as Python `dataclass` objects.

### `ChartPage`
A single OCR-processed page from the PDF.
| Field | Type | Description |
|---|---|---|
| `page_number` | `int` | Page index (from OCR API) |
| `text` | `str` | Markdown-rendered text content |
| `width` | `float \| None` | Page width in points |
| `height` | `float \| None` | Page height in points |
| `.is_empty` | property | `True` if text is blank/whitespace |

### `OCRResult`
The complete result of processing a PDF through the OCR API.
| Field | Type | Description |
|---|---|---|
| `filename` | `str` | Original file name |
| `full_text` | `str` | All pages joined with double newlines |
| `pages` | `list[ChartPage]` | Per-page breakdown |
| `model_used` | `str` | Model name returned by the API |
| `pages_processed` | `int` | Number of pages billed/processed |
| `.char_count` | property | Length of `full_text` |
| `.is_usable` | property | `True` if `char_count > 50` |
| `.get_page(n)` | method | Returns the `ChartPage` for page number `n`, or `None` |

### `ExtractedEntities`
Structured clinical data extracted from text by the LLM.
| Field | Type | Description |
|---|---|---|
| `source` | `str` | `"chart"` or `"spoken"` |
| `allergies` | `list[str]` | List of allergy substance names |
| `medications` | `list[dict]` | Each dict has `"name"` and optional `"dose"` |
| `diagnosis` | `str \| None` | Primary diagnosis |
| `extraction_notes` | `str \| None` | LLM notes about ambiguities |
| `.allergy_names` | property | Returns `allergies` list directly |
| `.medication_names` | property | Returns only `name` from each medication |
| `.empty(source)` | classmethod | Creates a blank `ExtractedEntities` |

### `DiscrepancyFlag`
Represents a single patient safety concern detected during cross-referencing.
| Field | Type | Description |
|---|---|---|
| `severity` | `str` | `"HIGH"` or `"MEDIUM"` |
| `category` | `str` | `"Allergy Omission"`, `"Contraindication"`, or `"Diagnosis Mismatch"` |
| `chart_value` | `str` | The relevant value from the written chart |
| `spoken_value` | `str \| None` | The relevant value from the spoken summary (if applicable) |
| `message` | `str` | Human-readable clinical explanation |
| `dismissed` | `bool` | Whether a clinician has dismissed this flag |
| `added_to_notes` | `bool` | Whether this flag was added to clinical notes |

### `CrossReferenceResult`
The final aggregated output of the cross-reference engine.
| Field | Type | Description |
|---|---|---|
| `flags` | `list[DiscrepancyFlag]` | All detected discrepancies |
| `chart_entities` | `ExtractedEntities \| None` | The chart-extracted entities used |
| `spoken_entities` | `ExtractedEntities \| None` | The spoken-extracted entities used |
| `.critical_flags` | property | Filtered list of only `HIGH`-severity flags |
| `.has_critical_flags` | property | `True` if any HIGH-severity flags exist |

---

## Configuration (`config.py`)

`OCRConfig` is a dataclass loaded from environment variables via `OCRConfig.from_env()`.

| Variable | Default | Description |
|---|---|---|
| `MISTRAL_API_KEY` | *(required)* | Mistral AI API key. Raises `EnvironmentError` if missing. |
| `OCR_REQUEST_TIMEOUT` | `60.0` | HTTP timeout in seconds for all Mistral API calls |

The same config object is shared across all three engines (`ChartProcessor`, `EntityExtractor`, `CrossReferenceEngine`), since they all authenticate with the same Mistral API key.

---

## Prompt Loader (`prompt_loader.py`)

A lightweight utility module that provides two functions:

- **`_load_prompt(filename)`** — Reads a `.txt` file from the `prompts/` directory relative to the module. Used at module import time by `entity_extractor.py` to load the system prompt and user template into memory.
- **`_load_data(filename)`** — Reads and JSON-parses a file from the `data/` directory. Raises `FileNotFoundError` with a descriptive message if the file is missing. Used at module import time by `cross_reference.py`.

Both are prefixed with `_` to signal they are internal utilities, not part of the public API.

---

## Public Interface (`__init__.py`)

The module exports exactly one symbol:

```python
from backend.ocr.entity_extractor import extract_text_from_pdf

__all__ = ["extract_text_from_pdf"]
```

This is the function consumed by the `/upload-chart` API route in `api/routes/chart.py`.

---

## Integration with the REST API

The OCR module integrates into the FastAPI application through the chart route:

**`POST /upload-chart`** (`api/routes/chart.py`)
- Accepts a PDF file upload
- Validates that the content type is `application/pdf`
- Reads the file bytes and passes them to `extract_text_from_pdf` (from `ocr/__init__.py`)
- Returns the extracted text as JSON: `{"filename": "...", "text": "..."}`

**`POST /extract-entities`** (`api/routes/chart.py`)
- Accepts `{"text": "..."}` in the request body
- Passes the text to `extract_entities` from the `llm/` module
- Returns structured entities as JSON

**`POST /cross-reference`** (`api/routes/cross_reference.py`)
- Accepts `{"chart_entities": {...}, "spoken_entities": {...}}`
- Passes both to `compare_entities` from `cross_reference/comparator.py`
- Returns a list of flags and a match score

---

## AI Models Summary

| Engine | Model | Purpose | Temperature |
|---|---|---|---|
| `ChartProcessor` | `mistral-ocr-latest` | PDF → markdown text | N/A |
| `EntityExtractor` | `mistral-large-latest` | Text → structured entities | 0.0 |
| `CrossReferenceEngine` | `mistral-small-latest` | Semantic synonym matching | 0.0 |

The choice of models is intentional: the most expensive/capable model (`mistral-large`) handles the nuanced clinical extraction, while the cheaper/faster `mistral-small` handles the narrow synonym-check task.

---

## Error Handling Strategy

| Error | Class | Where raised | Meaning |
|---|---|---|---|
| `OCRProcessingError` | `chart_processor.py` | `_call_ocr_api`, `_parse_response` | Mistral OCR API failure or empty response |
| `EntityExtractionError` | `entity_extractor.py` | `_call_llm`, `_parse_response` | Mistral LLM failure or malformed JSON response |
| `EnvironmentError` | `config.py` | `OCRConfig.from_env()` | Missing `MISTRAL_API_KEY` |
| `FileNotFoundError` | `prompt_loader.py` | `_load_data()` | Missing data file in `data/` directory |

In `CrossReferenceEngine._llm_synonym_check`, errors are caught silently and logged, returning `False` (not a match) — this is a deliberate conservative default: if we cannot confirm two names are the same, we treat them as different, which means we are more likely to flag a discrepancy than to miss one.

---

## Key Design Decisions

1. **All-async architecture:** Every external API call uses `httpx.AsyncClient`. This ensures the FastAPI event loop is never blocked when processing large PDFs or waiting on LLM responses.

2. **Dataclasses over dicts:** The entire data flow uses typed `@dataclass` objects rather than raw dictionaries. This makes every component self-documenting and eliminates a class of key-lookup bugs.

3. **Temperature 0.0 everywhere:** All LLM calls are deterministic. In a medical context, randomness in output is a safety liability.

4. **3-tier entity matching:** The ladder of exact match → abbreviation lookup → LLM check ensures both speed (most common matches are resolved locally) and accuracy (rare name variants are still caught via the LLM).

5. **Safety-biased defaults:** When uncertain (LLM synonym check error, missing data), the system defaults to the more conservative/alarming assumption rather than silently passing.

6. **Strict prompt engineering:** The system prompt for entity extraction has explicit clinical rules that prevent the LLM from inferring or hallucinating medical data — a critical requirement in patient safety contexts.
