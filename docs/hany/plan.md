# Person 3 — ML / Prompt Engineer

## Owns
- `ml/` (all of it)
- `backend/cross_reference/engine.py` — core matching logic
- `backend/cross_reference/rules.py` — flag severity assignment

## Responsibilities
1. Write and iterate on extraction prompt (`ml/prompts/extraction_prompt.txt`)
2. Write synonym check prompt (`ml/prompts/synonym_prompt.txt`)
3. Expand medical abbreviation dictionary (`ml/abbreviations/medical_abbrev.json`)
4. Implement 3-step cross-reference engine:
   - Step 1: Exact string match
   - Step 2: Abbreviation expansion + match
   - Step 3: LLM synonym check (call `backend/llm/synonym_check.py`)
5. Define flag severity rules in `backend/cross_reference/rules.py`
6. Author all 5 test cases in `ml/test_cases/`

## Key Interfaces You Implement
```python
# backend/cross_reference/engine.py
def cross_reference(chart_data: dict, spoken_data: dict) -> list[dict]: ...
```

Output must match `shared/schemas/discrepancy_flag.json`.

## Coordinate With
- Person 1 (backend): They call `cross_reference()` from the API route
- Person 4 (demo): Test cases feed directly into demo prep
