# Person 2 — Frontend Engineer

## Owns
- `frontend/` (all of it)

## Responsibilities
1. Build drag-drop PDF upload UI (`ChartUpload/`)
2. Build ElevenLabs WebSocket voice session UI (`VoiceSession/`)
3. Build 3-column comparison view (`ComparisonView/`)
4. Build flag card with Dismiss / Add to Note actions (`FlagCard/`)
5. Wire all components to backend via `api/client.ts`

## Key Components
- `ChartUpload` — accepts PDF, calls `POST /upload-chart`, stores raw text
- `VoiceSession` — opens WS to `/voice-session`, streams audio
- `ComparisonView` — shows chart | flags | spoken in 3 columns
- `FlagCard` — renders a `DiscrepancyFlag`, severity-colored border

## Types
All shared types live in `src/types/index.ts`. Keep these in sync with `shared/schemas/`.

## Coordinate With
- Person 1 (backend): Confirm API response shapes before building fetchers
- Person 4 (demo): Make sure the UI looks good for judge demo; priority is ComparisonView
