# Evaluator Demonstration Script — YGF News Intelligence Agent

Follow this structured script to conduct a live demonstration of the YGF News Intelligence Agent.

---

## Preparation & Prerequisites

1. Open PowerShell or Command Prompt.
2. Navigate to the project root:
   ```powershell
   cd "C:\Users\Anish Nilajkar\Desktop\YGF"
   ```

---

## Step 1: Start the Backend Server

Run the backend startup script:
```powershell
.\scripts\start_backend.bat
```
*(Alternatively: `.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` from `backend`)*

**Expected Observation:**
- Fast startup: Uvicorn running on `http://127.0.0.1:8000`.
- SQLite database initialized at `backend/news_intelligence.db` with WAL mode.
- 7 default curated RSS sources seeded.
- Interactive Swagger docs accessible at `http://127.0.0.1:8000/docs`.

---

## Step 2: Start the Frontend Client

In a second terminal window:
```powershell
.\scripts\start_frontend.bat
```
*(Alternatively: `npm run dev` from `frontend`)*

**Expected Observation:**
- Vite dev server starts on `http://localhost:5173`.
- Open your browser to `http://localhost:5173`.
- The editorial dashboard loads with live metrics, clean typography, and status indicators.

---

## Step 3: Verify Local Ollama Status

1. Look at the top navigation bar:
   - If Ollama is running and `qwen3:4b` is present, a green status indicator is shown.
   - If Ollama is offline or the model is not yet pulled, an amber status pill appears with setup guidance.
2. Click **Settings** in the navbar:
   - Observe the Ollama configuration card.
   - Click **Test Connection**.
   - Note the clear Windows command shown to pull the model:
     ```powershell
     ollama pull qwen3:4b
     ```

---

## Step 4: Trigger Live News Collection

1. In the top navigation bar, click the **"Run Collection"** button.
2. The agent executes the pipeline:
   - Fetches active RSS feeds with SSRF protection.
   - Normalizes URLs and content hashes.
   - Clusters related articles into event stories.
   - Extracts checkable claims and cross-validates evidence.
   - Generates grounded summaries.
3. Observe the notice banner confirming the number of articles collected and duplicates filtered.

---

## Step 5: Explore the Intelligence News Feed

1. Click **News Feed** in the navbar:
   - Observe the clustered stories.
   - Test the **Filter Pills**: Click *Corroborated*, *Conflicting*, or *Single-Source*.
   - Type a keyword in the **Search** box (e.g. `reasoning` or `Google`) and press Search.
   - Note the status badges, confidence scores, and source count indicators.

---

## Step 6: Deep Dive into Story Claims & Evidence

1. Click **"Inspect Claims"** on any story card.
2. In the Story Detail view:
   - **Grounded Summary:** Read *What Happened*, *Why It Matters*, *Key Facts & Stated Metrics*, and *What Remains Uncertain*.
   - **Extracted Claims & Cross-Source Evidence:** Inspect each claim. See the contributing publisher names, exact quotation snippets, and any numerical or date discrepancies flagged in red.
   - **Attributed Source Articles:** Click *"Read Original"* to open canonical URLs in a new tab.
   - Click **"Re-Verify"** or **"Re-Summarize"** to observe live on-demand reprocessing.

---

## Step 7: Experience the Social Studio

1. Click **"Open Social Studio"** from the story detail view or navbar.
2. Observe the 3 platform tabs:
   - **LinkedIn:** Editorial tone, hook, strategic impact, hashtags, and primary source URL.
   - **X (Twitter):** Concise text strictly respecting the 280-character limit with a live character gauge.
   - **Instagram:** Engaging structured caption with bulleted takeaways.
3. Edit any draft text directly in the editor.
4. Click **"Copy to Clipboard"** and observe the instant visual confirmation.
5. Click **"Save Draft"** to persist your edits.

---

## Step 8: Inspect Sources & Security Boundary

1. Click **Sources** in the navbar:
   - Review the table of configured feeds with reliability scores and official status flags.
   - Toggle a feed active/inactive using the checkbox.
   - Click **"Add Custom Source"** to view the SSRF-guarded feed registration form.

---

## Step 9: Audit Log & Diagnostics

1. Click **Run History** in the navbar:
   - Review the audit log of all manual and automated collection runs.
   - Observe duration, feeds attempted/succeeded, articles collected, and duplicate counts.
   - Click **"Logs"** to inspect diagnostic traces for any failed feed.

---

## Step 10: Run the Automated Test Benchmark

Open a terminal and run the automated test suite:
```powershell
.\scripts\run_tests.bat
```
**Expected Result:**
- **33 passed** in ~11 seconds.
- 100% test pass rate across SSRF guards, deduplication, cross-validation, and synthetic benchmark scenarios.
