# YGF Local AI News Intelligence Agent

[![Automated Tests](https://img.shields.io/badge/tests-33%20passed%20%7C%20100%25-brightgreen)](file:///backend/tests)
[![Python](https://img.shields.io/badge/python-3.14-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb)](https://vitejs.dev)
[![Local LLM](https://img.shields.io/badge/inference-Ollama%20(Open--Weight)-purple)](https://ollama.com)
[![No Paid APIs](https://img.shields.io/badge/cost-$0%20%2F%20No%20Paid%20APIs-success)](https://ygf-ngo.org)

An autonomous, locally running AI news intelligence engine designed for the **YGF NGO evaluation task**. The agent continuously collects AI and technology news from accessible sources, filters duplicates, clusters related articles into event stories, extracts checkable factual claims, cross-validates claims across independent sources using a deterministic verification layer supported by a local Ollama LLM, generates grounded news summaries with traceable source URLs, produces platform-specific social media post drafts (LinkedIn, X, Instagram), and provides optional Telegram notifications.

---

## Key Features

1. **Accessible RSS & Research Ingestion**
   - Pre-configured with official AI labs (OpenAI, Google Research), research publications (ArXiv CS.AI), and reputable tech newsrooms (TechCrunch AI, Ars Technica, VentureBeat, MIT Tech Review).
   - Ingestion rate-limiting, timeout controls, and automated retries.
   - Built-in **SSRF Protection** blocking private RFC1918 subnets, loopbacks, cloud metadata (`169.254.169.254`), and redirect rebinding.

2. **Deduplication & Event Clustering**
   - Canonical URL normalization (cleans tracking parameters like `utm_*`, `fbclid`, `gclid`, and standard ports).
   - Title normalization and SHA-256 content hashing to eliminate syndicated duplicates.
   - Token-based event clustering that groups multi-source coverage into cohesive stories while identifying official primary announcements.

3. **Deterministic Cross-Validation Engine**
   - **Does not treat LLMs as proof of truth.**
   - Factual claims are extracted and cross-checked against independent source reporting.
   - Material discrepancies in numerical metrics, benchmark scores, or launch dates are flagged as **`CONFLICTING`**.
   - Single-source reports are strictly isolated as **`INSUFFICIENT_EVIDENCE`**.
   - Multiple copies of the same press release count as a single origin source.
   - Supported statuses: `CORROBORATED`, `PARTIALLY_CORROBORATED`, `CONFLICTING`, `UNVERIFIED`, `INSUFFICIENT_EVIDENCE`.
   - Heuristic confidence score calculated transparently from coverage, independence, and consistency.

4. **100% Local LLM Inference via Ollama**
   - Zero dependency on paid cloud APIs (no OpenAI, Anthropic, Gemini, or Groq API calls).
   - Default configurable open-weight model: `qwen3:4b` (supports `qwen2.5:3b`, `llama3.2`, etc.).
   - Structured JSON output schemas validated with Pydantic.
   - **Prompt Injection Defense:** External article texts are encapsulated inside `<UNTRUSTED_ARTICLE_EVIDENCE>` boundaries with instructions to ignore embedded malicious instructions.
   - **Graceful Offline Mode:** The full collection, clustering, deterministic verification, and SQLite persistence pipeline runs seamlessly even when Ollama is offline.

5. **Social Studio (Human-in-the-Loop Copywriting)**
   - **LinkedIn:** Editorial tone, hook, strategic impact, hashtags, and canonical source link.
   - **X (Twitter):** Strictly enforced $\le 280$ characters with interactive live character counter.
   - **Instagram:** Structured, engaging caption with key bullet points.
   - Editable drafts, 1-click clipboard copy with visual feedback, and regeneration.

6. **Notification Delivery (Telegram)**
   - Backend-only credentials with safe message length chunking and formatting.
   - Duplicate delivery prevention (10-minute cooldown per story/chat).
   - Built-in test message dispatch and graceful disabled state when unconfigured.

7. **Automation & In-Process Scheduling**
   - Background automation powered by APScheduler.
   - Single-instance mutex lock preventing overlapping collection runs.
   - Full diagnostic run history and error logging.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite 5, JavaScript, Tailwind CSS v3, Lucide React icons, Recharts |
| **Backend** | Python 3.14+, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite (WAL mode), httpx, feedparser, BeautifulSoup4, APScheduler |
| **Local AI** | Ollama HTTP API (`http://localhost:11434`), structured JSON format |
| **Messaging** | Telegram Bot API (HTTP via httpx) |
| **Testing** | pytest, pytest-asyncio, FastAPI TestClient (33 automated test cases) |

---

## System Architecture

```
YGF News Intelligence Agent
├── News Sources Registry (Curated RSS/Atom)
│     └── SSRF Safety Filter (Blocks private/loopback IPs & unsafe redirects)
├── Ingestion & Extraction Engine
│     ├── Canonical URL Normalization (Strips tracking parameters)
│     ├── Title Cleaning & Content Hashing
│     └── BeautifulSoup Readability Extractor (with RSS fallback)
├── Story Clustering Engine
│     ├── Informative Token Similarity (Retains model numbers like 4.5 & o3)
│     └── Primary Article Selection (Official announcements prioritized)
├── Cross-Validation Engine
│     ├── Claim Extraction (Factual & Metric checkables)
│     ├── Multi-Source Evidence Evaluation (SUPPORTS / CONTRADICTS / INSUFFICIENT)
│     └── Rule-Based Adjudication & Heuristic Confidence Score
├── Local LLM Service (Ollama HTTP)
│     ├── Grounded Factual Summarization
│     └── Social Studio Copywriter (LinkedIn, X <=280 chars, Instagram)
├── Delivery & Scheduling
│     ├── APScheduler Background Runner
│     └── Telegram Notification Dispatcher
└── Editorial Intelligence Dashboard (React + Tailwind CSS)
```

For complete technical specifications, see [docs/architecture.md](file:///docs/architecture.md).

---

## Prerequisites

1. **Windows 10/11** (or macOS / Linux).
2. **Python 3.11 - 3.14** installed.
3. **Node.js v18+ & npm** installed.
4. **Ollama** installed from [ollama.com](https://ollama.com).

---

## Quick Start on Windows

### 1. Clone or Open the Repository
```powershell
cd "C:\Users\Anish Nilajkar\Desktop\YGF"
```

### 2. Configure Environment Variables
Copy example files to `.env`:
```powershell
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```

### 3. One-Click Launch (Both Services)
Double click `scripts\start_all.bat` or run in PowerShell:
```powershell
.\scripts\start_all.bat
```
*(Or use PowerShell: `.\scripts\start.ps1`)*

The script opens two separate windows:
- **Backend:** `http://127.0.0.1:8000` (API Docs: `http://127.0.0.1:8000/docs`)
- **Frontend Dashboard:** `http://localhost:5173`

---

## Manual Step-by-Step Setup

### Backend Setup
1. Open a terminal in `backend/`:
   ```powershell
   cd backend
   ```
2. Create virtual environment and activate:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Start FastAPI server:
   ```powershell
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup
1. Open a second terminal in `frontend/`:
   ```powershell
   cd frontend
   ```
2. Install dependencies:
   ```powershell
   npm install
   ```
3. Start Vite development server:
   ```powershell
   npm run dev
   ```
4. Access the web dashboard at `http://localhost:5173`.

---

## Ollama Local Model Setup

1. Verify Ollama is running:
   ```powershell
   ollama --version
   ```
2. Download the recommended model (or model of your choice):
   ```powershell
   ollama pull qwen3:4b
   # Or for machines with lower RAM:
   ollama pull qwen2.5:3b
   ```
3. Update `OLLAMA_MODEL` in `backend/.env` or dynamically change it in the **Settings** page of the web UI.

> [!NOTE]
> If Ollama is offline or the model is not yet downloaded, the dashboard displays a clear setup banner. All news ingestion, deduplication, deterministic evidence cross-checking, and dashboard navigation remain 100% operational using built-in deterministic fallbacks.

---

## Optional: Telegram Configuration

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`, choose a name and username, and copy the **API Token**.
3. Send a message to your bot or add it to a channel.
4. Get your numeric **Chat ID** (e.g. from `@userinfobot`).
5. Set the values in `backend/.env`:
   ```env
   TELEGRAM_BOT_TOKEN="your_bot_token_here"
   TELEGRAM_CHAT_ID="your_chat_id_here"
   ```
6. Navigate to the **Settings** page and click **"Send Test Notification"** to verify connectivity.

---

## Running Automated Tests & Benchmark

Run the full automated test suite (33 tests, ~11 seconds):
```powershell
.\scripts\run_tests.bat
```
*(Or manually: `cd backend; .\.venv\Scripts\pytest -v`)*

### Test Suite Structure:
- `test_security_ssrf.py`: SSRF blocking of localhost, private RFC1918 IPs, IPv6 loopback, and HTML sanitization.
- `test_url_and_dates.py`: Canonical URL normalization, tracking parameter stripping, title cleaning, and safe timestamp parsing.
- `test_deduplication_clustering.py`: URL and content hash deduplication, token similarity, and official announcement prioritization.
- `test_cross_validation.py`: Single-source classification, conflicting numerical evidence detection, and multi-source corroboration.
- `test_ollama_and_telegram.py`: Ollama offline fallback, prompt injection wrapping, Telegram disabled state, and X $\le 280$ char limits.
- `test_api_endpoints.py`: FastAPI endpoints integration tests (`/api/health`, `/api/sources`, `/api/news`, `/api/stats`, `/api/settings`).
- `test_synthetic_evaluation.py`: Deterministic synthetic evaluation benchmark testing all 5 required evaluation scenarios.

For full benchmark methodology and metrics, see [docs/evaluation.md](file:///docs/evaluation.md).

---

## Building Frontend for Production

To verify or deploy the production build:
```powershell
cd frontend
npm run build
```
Output is generated cleanly in `frontend/dist/`.

---

## API Documentation

FastAPI provides interactive Swagger UI documentation at:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

Key Endpoints:
- `GET /api/health`: System health and component status.
- `GET /api/health/ollama`: Local LLM connectivity and installed model detection.
- `GET /api/stats`: Real-time dashboard metrics and verification breakdown.
- `GET /api/news`: Paginated, searchable, status-filtered stories.
- `GET /api/news/{id}`: Detailed story view with claims, evidence items, and source links.
- `POST /api/collect`: Triggers news ingestion, clustering, and AI verification pipeline.
- `POST /api/news/{id}/verify`: Re-runs claim extraction and cross-validation on demand.
- `POST /api/news/{id}/summarize`: Regenerates grounded summary with local LLM.
- `GET /api/social-posts`: Retrieves platform drafts.
- `POST /api/news/{id}/social-posts/generate`: Generates platform drafts.
- `POST /api/telegram/test`: Tests Telegram notification delivery.
- `POST /api/telegram/send`: Dispatches verified story summary to Telegram.

---

## Known Limitations & Honest Disclosure

1. **Hardware Dependent Inference Speed:** Local LLM inference speed depends on your local CPU/GPU and model quantization. On modest hardware, claim extraction and summarization may take 10–25 seconds per story.
2. **Deterministic Rules as Safety Shield:** The system uses deterministic rule checking for numbers, dates, and publisher independence. The LLM serves to assist with claim extraction and drafting, never as the final authority on factual truth.
3. **Paywalls & Cloudflare Blocks:** The article extractor respects publishers' terms and does not attempt to bypass paywalls or CAPTCHAs. When full article text is blocked, the engine transparently falls back to RSS description metadata.

---

## Future Improvements

1. **Local Vector Search:** Integrate local embeddings (e.g. `nomic-embed-text` via Ollama) for semantic clustering across multi-lingual feeds.
2. **WhatsApp Webhook:** Expand notifications to WhatsApp Business API.
3. **Community Fact-Checking Feedback:** Allow editors to flag false positives directly from the UI to continually refine source reliability scores.

---

## Evaluation Task Demonstration

Follow [docs/demo-script.md](file:///docs/demo-script.md) for a step-by-step walkthrough covering live ingestion, evidence inspection, Social Studio copywriting, and Telegram dispatch.
