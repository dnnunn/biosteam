# BioSTEAM UI (Next.js)

Quick start (dev):
- Ensure API is running: `uvicorn app.api.main:app --reload --port 8000`
- In this folder:
  - Install deps: `npm i` (or `pnpm i` / `yarn`)
  - Run: `npm run dev`
  - Open: http://localhost:3000/designer

Pages:
- `/` — landing
- `/designer` — block-based canvas with Palette, Inspector, and Results Panel

Environment:
- `NEXT_PUBLIC_API_BASE` (optional) — defaults to `http://localhost:8000`

