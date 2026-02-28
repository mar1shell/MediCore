# Person 4 — Demo Lead

## Owns
- `demo/` (all of it)
- Integration testing across the full pipeline
- Judge presentation

## Responsibilities
1. Create synthetic patient chart PDFs in `demo/charts/`
   - Sarah Chen — penicillin allergy not in chart (main demo case)
   - Additional patients as backup
2. Run end-to-end integration tests using `ml/test_cases/` as expected outputs
3. Write and rehearse 60-second judge demo script (`demo/scripts/demo_script.md`)
4. Prepare judge Q&A responses (`demo/qa/judge_qa.md`)
5. Coordinate final UI polish with Person 2

## Demo Priority Order
1. Case 02 (penicillin conflict) — most dramatic, HIGH severity flag → use as primary demo
2. Case 04 (dose error) — good backup if case 02 has issues
3. Case 05 (clean, no flags) — show the baseline works too

## Integration Checklist
- [ ] Backend starts with no errors: `uvicorn main:app --reload`
- [ ] Frontend starts: `npm run dev`
- [ ] PDF upload works for Sarah Chen chart
- [ ] Voice session opens without errors
- [ ] Cross-reference returns correct flags for each test case
- [ ] Flag cards render with correct severity color

## Coordinate With
- Everyone: You are the integration point — test early and report blockers
