# MedRound — 60-Second Judge Demo Script

## Setup (before judges arrive)
- Backend running: `uvicorn main:app --reload` in `backend/`
- Frontend running: `npm run dev` in `frontend/`
- `sarah_chen_chart.pdf` pre-loaded in the upload panel
- Browser open to `http://localhost:5173`

---

## The Pitch (15 seconds)

> "Every year, medication errors from mismatched patient history kill thousands.
> MedRound catches those mismatches in real time — before the doctor signs off."

---

## Demo Flow (45 seconds)

**Step 1 — Upload Chart (10s)**
> "Here's Sarah Chen's chart. She's listed as having no known allergies and is prescribed amoxicillin."

*Click upload → chart appears in left column*

**Step 2 — Start Voice Session (15s)**
> "Now the nurse asks Sarah about her history verbally."

*Click Start Session → ElevenLabs agent begins*
> Agent: "Do you have any medication allergies?"
> (demo response or live): "Yes, I'm allergic to penicillin."

**Step 3 — Flags Appear (10s)**
> "MedRound catches it immediately."

*RED flag appears in center column:*
> ⚠️ HIGH — Allergies | Chart: (none) | Spoken: penicillin
> "Amoxicillin is a penicillin-class antibiotic — cross-reactivity risk."

**Step 4 — Closing (10s)**
> "One button adds it directly to the clinical note. No manual charting.
> That's MedRound — your AI safety net for bedside medicine."

---

## Key Stats to Mention
- Processes a chart in < 3 seconds via Mistral OCR
- LLM entity extraction with JSON schema enforcement (no hallucinated structure)
- 3-step matching: exact → abbreviation → LLM synonym check
