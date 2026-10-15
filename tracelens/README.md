# TraceLens

**Turn API request logs into actionable incident insights.** Open-source developer observability with a FastAPI backend, React/TypeScript dashboard, and the original Python CLI.

![TraceLens mark](frontend/public/tracelens-mark.png)

## Features

- Upload CSV, JSONL, or NDJSON logs directly from your browser.
- Overview dashboard: request volume, server error rate, p95 latency, and incident findings.
- Endpoint health table, HTTP status breakdown, hourly request chart.
- Searchable request explorer with status filtering.
- Evidence-backed incident findings and suggested troubleshooting steps.
- Download JSON reports. Demo mode requires no file or account.
- Original dependency-free CLI preserved: `python -m tracelens samples/requests.csv`.
- In-memory analysis only: uploaded files are not saved by the server.

## Run in GitHub Codespaces

From the **repository root**, start the backend:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

In a **second terminal**:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

In Codespaces open the forwarded **port 5173** in your browser (Ports tab → 5173 → Open in Browser). The Vite dev server forwards `/api` requests to FastAPI on port 8000.

Alternatively build the frontend and serve both from FastAPI on port 8000:

```bash
cd frontend && npm install && npm run build && cd ..
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Then open forwarded port **8000**. API documentation is at `/docs`.

## Expected log schema

Required fields: `timestamp` (timezone-aware ISO 8601), `method`, `path`, `status`, `latency_ms`. Optional `request_id`.

```csv
timestamp,method,path,status,latency_ms,request_id
2026-10-15T12:00:00Z,GET,/api/users,200,54,req-001
2026-10-15T12:01:00Z,POST,/api/payments,503,1450,req-002
```

**Limits:** 5 MB upload, 25,000 records, UTF-8 only. Uploaded content is processed in memory; reports exist in your browser session until you reload. The demo uses synthetic logs. Avoid uploading production logs with secrets or personal data to an untrusted deployment.

## API

- `GET /api/health` — health check
- `GET /api/demo` — sample analysis
- `POST /api/analyze` — multipart `file` with optional `latency_threshold` (milliseconds) and `error_threshold` (fraction) query parameters

## Tests

```bash
python -m pip install -r backend/requirements.txt
python -m unittest discover -s tests -v
cd frontend && npm install && npm run build
```

GitHub Actions validates Python tests and TypeScript/Vite build on each push.

## Architecture

`React + TypeScript (Vite)` → `/api` → `FastAPI` → `tracelens.core` (original CLI analysis engine). No database, login, paid API, or cloud credentials required.

## Roadmap

- [x] Phase 1 — CLI log parser and incident triage
- [x] Phase 2 — Browser dashboard, upload, visualizations, reports
- [ ] Phase 3 — Request correlation, time-window anomaly detection, optional PostgreSQL storage
- [ ] Phase 4 — Secure hosted demo, deployment and expanded integrations

## License

MIT — see [LICENSE](LICENSE).
