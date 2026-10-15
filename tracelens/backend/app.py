"""TraceLens v2 API. In-memory processing: uploaded logs are never stored."""
from __future__ import annotations
import csv
import io
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from tracelens.core import analyze, REQUIRED

MAX_BYTES = 5 * 1024 * 1024
MAX_EVENTS = 25000
ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="TraceLens API", version="2.0.0", description="Analyze request logs locally in memory")

class Thresholds(BaseModel):
    latency_threshold: float = Field(1000, ge=0, le=600000)
    error_threshold: float = Field(0.05, ge=0, le=1)


def parse_bytes(filename: str, data: bytes):
    ext = Path(filename).suffix.lower()
    if ext not in {'.csv', '.jsonl', '.ndjson'}:
        raise ValueError('Upload a .csv, .jsonl, or .ndjson file')
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('File must be UTF-8 encoded') from exc
    if ext == '.csv':
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError('CSV requires: timestamp, method, path, status, latency_ms')
        records = list(reader)
    else:
        records = []
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid JSON on line {number}: {exc.msg}') from exc
            records.append(record)
    if len(records) > MAX_EVENTS:
        raise ValueError(f'Maximum {MAX_EVENTS:,} events per upload')
    events = []
    for line, record in enumerate(records, 1):
        try:
            if not isinstance(record, dict):
                raise ValueError('record must be an object')
            missing = REQUIRED - record.keys()
            if missing:
                raise ValueError(f'missing {sorted(missing)}')
            ts = datetime.fromisoformat(str(record['timestamp']).replace('Z', '+00:00'))
            if ts.tzinfo is None:
                raise ValueError('timestamp must include timezone')
            status = int(record['status'])
            latency = float(record['latency_ms'])
            if not 100 <= status <= 599 or not math.isfinite(latency) or latency < 0:
                raise ValueError('invalid status or latency')
            events.append({'timestamp': ts.astimezone(timezone.utc).isoformat(),
                           'method': str(record['method']).upper(),
                           'path': str(record['path']).split('?')[0],
                           'status': status, 'latency_ms': latency,
                           'request_id': str(record.get('request_id') or '')})
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError(f'Invalid record {line}: {exc}') from exc
    return events


def build_dashboard(events, latency_threshold=1000, error_threshold=0.05):
    report = analyze(events, latency_threshold, error_threshold)
    buckets = {}
    for event in events:
        dt = datetime.fromisoformat(event['timestamp'])
        bucket = dt.replace(minute=0, second=0, microsecond=0).isoformat()
        row = buckets.setdefault(bucket, {'time': bucket, 'requests': 0, 'errors': 0, 'latency_sum': 0})
        row['requests'] += 1
        row['errors'] += int(event['status'] >= 500)
        row['latency_sum'] += event['latency_ms']
    timeline = [{'time': v['time'], 'requests': v['requests'], 'errors': v['errors'],
                 'avg_latency_ms': round(v['latency_sum'] / v['requests'], 1)}
                for _, v in sorted(buckets.items())]
    status_groups = Counter(f"{event['status']//100}xx" for event in events)
    recent = sorted(events, key=lambda e: e['timestamp'], reverse=True)[:100]
    return {**report, 'timeline': timeline, 'status_groups': dict(sorted(status_groups.items())),
            'recent_requests': recent, 'meta': {'total_events': len(events), 'time_buckets': len(timeline)}}

@app.get('/api/health')
def health():
    return {'status': 'ok', 'version': '2.0.0'}

@app.get('/api/demo')
def demo():
    data = (ROOT / 'samples' / 'requests.csv').read_bytes()
    return build_dashboard(parse_bytes('requests.csv', data))

@app.post('/api/analyze')
async def upload(file: UploadFile = File(...), latency_threshold: float = 1000, error_threshold: float = 0.05):
    if not 0 <= latency_threshold <= 600000 or not 0 <= error_threshold <= 1:
        raise HTTPException(422, 'Invalid thresholds')
    data = await file.read(MAX_BYTES + 1)
    await file.close()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, 'File exceeds 5 MB limit')
    try:
        return build_dashboard(parse_bytes(file.filename or '', data), latency_threshold, error_threshold)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

# Optional production mode: serve prebuilt React assets from FastAPI on one port.
DIST = ROOT / 'frontend' / 'dist'
if DIST.is_dir():
    from fastapi.responses import FileResponse
    app.mount('/assets', StaticFiles(directory=DIST / 'assets'), name='assets')
    @app.get('/')
    def index():
        return FileResponse(DIST / 'index.html')
    @app.get('/{path:path}')
    def spa(path: str):
        target = (DIST / path).resolve()
        if target.is_relative_to(DIST.resolve()) and target.is_file():
            return FileResponse(target)
        return FileResponse(DIST / 'index.html')
