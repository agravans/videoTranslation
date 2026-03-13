# AI L&D Translation Platform

**BFSI compliance training in every language your team speaks.**

Translates, dubs, and delivers enterprise L&D video content across 11 Indian languages. Built for Indian BFSI (banking, financial services, insurance) companies — with a human review gate for compliance-critical content.

---

## Architecture

```
audioTranslation/
├── backend/               # FastAPI + Celery pipeline
│   ├── app/
│   │   ├── pipeline/      # 8-stage processing pipeline
│   │   │   ├── ingest.py       # FFmpeg audio extraction
│   │   │   ├── transcribe.py   # Whisper STT
│   │   │   ├── translate.py    # Sarvam Mayura translation
│   │   │   ├── qa.py           # Claude QA/glossary check
│   │   │   ├── tts.py          # Sarvam Bulbul TTS dubbing
│   │   │   ├── sync_audio.py   # Audio/video sync
│   │   │   ├── subtitle.py     # SRT generation + burn-in
│   │   │   └── orchestrator.py # Full pipeline runner
│   │   ├── glossary/
│   │   │   └── bfsi.py    # 150+ BFSI terms in Hindi + Tamil
│   │   ├── api/
│   │   │   └── jobs.py    # REST API (upload, status, review, download)
│   │   ├── models/
│   │   │   └── job.py     # Pydantic models
│   │   └── worker/
│   │       └── celery_app.py  # Async Celery worker
├── frontend/              # Next.js 15 portal
│   └── src/app/
│       ├── page.tsx            # Dashboard / job list
│       ├── jobs/new/page.tsx   # Upload + create job
│       ├── jobs/[id]/page.tsx  # Job detail + downloads
│       └── review/[jobId]/[lang]/page.tsx  # Human review interface
├── scripts/
│   └── process_video.py   # CLI for Week 1 testing (no UI needed)
└── docker-compose.yml
```

## Pipeline (8 Stages)

| # | Stage | Tool | Cost/min |
|---|-------|------|----------|
| 1 | Ingest & audio extract | FFmpeg | free |
| 2 | STT transcription | faster-whisper (local) | ~₹0.40 |
| 3 | Translation | Sarvam Mayura | ~₹1.50 |
| 4 | QA / glossary check | Claude Sonnet 4.6 | ~₹1.50 |
| 5 | TTS dubbing | Sarvam Bulbul v3 | ~₹2.00 |
| 6 | Audio sync | FFmpeg | free |
| 7 | Subtitle burn-in | FFmpeg | free |
| 8 | Delivery | FastAPI / S3 | free |

**Total COGS: ₹18–30/min/language** (vs. ₹800–1,500/min for traditional agencies)

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- FFmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg`
- Redis: `brew install redis` or `docker run -d -p 6379:6379 redis:alpine`

### 1. Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Celery Worker (separate terminal)

```bash
cd backend
celery -A app.worker.celery_app.celery worker --loglevel=info
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 4. Docker (all-in-one)

```bash
cp backend/.env.example backend/.env
# Edit backend/.env
docker-compose up
```

---

## Week 1: CLI Testing (No UI needed)

Test the full pipeline end-to-end from the command line:

```bash
# Install backend deps
cd backend && pip install -r requirements.txt

# Run with mock APIs (no real API keys needed)
python scripts/process_video.py \
  --input path/to/sample_training.mp4 \
  --languages hi-IN,ta-IN \
  --tier standard \
  --mock

# Run for real (requires .env with API keys)
python scripts/process_video.py \
  --input path/to/sample_training.mp4 \
  --languages hi-IN \
  --whisper-model base
```

Output files land in `./outputs/<job-id>/`.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/jobs` | Upload video + create job |
| GET | `/api/jobs` | List all jobs |
| GET | `/api/jobs/{id}` | Job status + progress |
| GET | `/api/jobs/{id}/download/{key}` | Download output file |
| GET | `/api/jobs/{id}/review/{lang}` | Get segments for review |
| PATCH | `/api/jobs/{id}/review/{lang}/segment/{id}` | Edit/approve segment |
| POST | `/api/jobs/{id}/review/{lang}/approve-all` | Bulk approve |
| POST | `/api/jobs/{id}/review/complete` | Finalize review |
| GET | `/api/languages` | List supported languages |
| GET | `/health` | Health check |

---

## Supported Languages (Sarvam Bulbul v3)

| Code | Language |
|------|----------|
| hi-IN | Hindi |
| ta-IN | Tamil |
| bn-IN | Bengali |
| gu-IN | Gujarati |
| kn-IN | Kannada |
| ml-IN | Malayalam |
| mr-IN | Marathi |
| od-IN | Odia |
| pa-IN | Punjabi |
| te-IN | Telugu |
| ur-IN | Urdu |

---

## API Keys Needed

1. **Sarvam AI** — [api.sarvam.ai](https://api.sarvam.ai) (free ₹1,000 credits on signup)
   - Saaras v3 (STT), Mayura (translation), Bulbul v3 (TTS)
2. **Anthropic** — Claude Sonnet 4.6 for BFSI QA
3. **OpenAI** (optional) — Whisper API fallback if not running locally

---

## Pricing Tiers

| Tier | Offering | Our Price | COGS | Margin |
|------|----------|-----------|------|--------|
| Starter | SRT subtitles only | ₹150/min/lang | ₹10–15 | ~88% |
| Standard | Subtitles + AI dubbing | ₹350–500/min/lang | ₹18–30 | ~85–94% |
| Premium | Dubbing + Lip Sync + Review | ₹700–1,000/min/lang | ₹50–60 | ~93% |

**Agency comparison: ₹800–1,500/min. We're 50–70% cheaper with 10x faster turnaround.**

---

## Build Plan (Week-by-Week)

- **Week 1** (done): Infra + end-to-end CLI pipeline ← you are here
- **Week 2**: Translation QA + BFSI glossary enforcement
- **Week 3**: TTS + dubbed video output
- **Week 4**: Upload portal (Next.js)
- **Week 5**: Human review interface
- **Week 6**: POC demo with real 10-min bank training video

---

*Prepared March 2026 — Subandhu × Debanshu — Confidential*
# videoTranslation
