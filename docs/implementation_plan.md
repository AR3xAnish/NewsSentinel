# Implementation Plan & Checklist — YGF Local AI News Intelligence Agent

## Phase 1: Environment & Project Foundation
- [x] Inspect local tools and environment (Python 3.14.3, Node v22.17.1, npm 10.9.2, Ollama).
- [x] Backend virtual environment & dependency installation.
- [x] Frontend scaffolding (Vite + React + JavaScript + Tailwind CSS + Lucide Icons + Recharts).
- [x] Backend core setup: `config.py`, `database.py`, SQLite connection with WAL mode.
- [x] SQLAlchemy models: `NewsSource`, `Article`, `Story`, `StoryArticle`, `Claim`, `Evidence`, `VerificationResult`, `SocialPost`, `NotificationDelivery`, `CollectionRun`, `ApplicationSetting`.
- [x] Pydantic schemas for models and API payloads.
- [x] Health and status endpoints (`/api/health`, `/api/health/ollama`).

## Phase 2: News Collection, Ingestion & Deduplication
- [x] Curated default RSS sources (AI research blogs, official announcements, tech publications).
- [x] SSRF-safe HTTP client (blocks private/loopback IPs, verifies redirects, enforces timeouts).
- [x] RSS parser service (handles malformed timestamps, extraction errors, missing fields).
- [x] Article text & metadata extractor (readable content, fallbacks to RSS summary when blocked).
- [x] URL normalization and deduplication service (query param stripping, hash fingerprints).
- [x] Persistence of articles, sources, and collection runs.
- [x] Automated tests for RSS parsing, deduplication, URL normalization, and SSRF guardrails.

## Phase 3: Story Clustering, Claim Extraction & Cross-Validation Engine
- [x] Story clustering service (token-based entity & title similarity + deterministic fallback).
- [x] Ollama service client (model discovery, connectivity checks, prompt execution, timeout handling).
- [x] Claim extraction pipeline (identifies concrete factual claims with source links).
- [x] Deterministic verification engine (cross-validates claims across independent sources):
  - Statuses: `CORROBORATED`, `PARTIALLY_CORROBORATED`, `CONFLICTING`, `UNVERIFIED`, `INSUFFICIENT_EVIDENCE`.
  - Heuristic confidence score based on source independence, evidence coverage, and consistency.
  - Identification of single-source and conflicting reports.
- [x] Grounded news summarization service (traceable facts, primary and supporting URLs, publication dates).
- [x] Automated tests for clustering, claim extraction, contradiction detection, and single-source rules.

## Phase 4: Social Studio, REST API & React Dashboard
- [x] Social post generation service (tailored drafts for LinkedIn, X with char limit, Instagram).
- [x] Complete FastAPI endpoints:
  - Sources management (`GET`, `POST`, `PATCH /api/sources`)
  - Collection triggers and run history (`POST /api/collect`, `GET /api/runs`)
  - News and story inspection (`GET /api/news`, `GET /api/news/{id}`, `/verify`, `/summarize`)
  - Social drafts management (`GET /api/social-posts`, `POST /api/news/{id}/social-posts/generate`, `PATCH`, `POST /copy`)
  - Application settings (`GET`, `PATCH /api/settings`)
  - Telegram testing and delivery (`POST /api/telegram/test`, `POST /api/telegram/send`)
- [x] React frontend (editorial intelligence aesthetic):
  - Navigation & Layout (Sidebar, Topbar with Ollama & system status badge)
  - Dashboard (metrics, charts, recent stories, run status)
  - News Feed (search, date range, topic, verification status filters, article cards)
  - Story Details (grounded summary, claims breakdown, supporting/opposing evidence cards, source links)
  - Social Studio (tabbed drafts for LinkedIn, X, Instagram, character counter, copy-to-clipboard, regenerate)
  - Sources Manager (view, add, toggle sources, test fetch)
  - Run History (audit log of collection runs, duplicates detected, errors)
  - Settings (Ollama model selection, lookback window, scheduler interval, Telegram bot setup)

## Phase 5: Telegram Integration & Scheduler Automation
- [x] Telegram delivery service (token backend-only, message chunking, safe markdown/HTML escape, duplicate protection).
- [x] APScheduler background job service (configurable interval, single instance lock, duplicate job prevention).
- [x] Graceful degradation when Telegram or Ollama are unconfigured or offline.

## Phase 6: Testing, Evaluation Benchmark, Build & Documentation
- [x] Synthetic evaluation dataset & verification benchmark report.
- [x] Automated test suite execution (mocked HTTP, offline LLM mock, edge cases: 33/33 passed).
- [x] Frontend build verification (`npm run build` completed cleanly).
- [x] Comprehensive documentation:
  - `README.md`
  - `docs/architecture.md`
  - `docs/evaluation.md`
  - `docs/demo-script.md`
  - Windows startup scripts (`scripts/start.bat`, `scripts/start.ps1`)
