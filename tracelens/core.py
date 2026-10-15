import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = {'timestamp','method','path','status','latency_ms'}

def load_events(path):
    p = Path(path)
    if p.suffix.lower() == '.csv':
        with p.open(newline='', encoding='utf-8') as f:
            records = list(csv.DictReader(f))
    elif p.suffix.lower() in ('.jsonl', '.ndjson'):
        with p.open(encoding='utf-8') as f:
            records = [json.loads(line) for line in f if line.strip()]
    else:
        raise ValueError('Expected .csv, .jsonl, or .ndjson')
    events = []
    for line, record in enumerate(records, 1):
        try:
            missing = REQUIRED - record.keys()
            if missing:
                raise ValueError(f'missing {sorted(missing)}')
            ts = datetime.fromisoformat(str(record['timestamp']).replace('Z', '+00:00'))
            if ts.tzinfo is None:
                raise ValueError('timestamp must include timezone')
            status = int(record['status'])
            latency = float(record['latency_ms'])
            if not (100 <= status <= 599) or not math.isfinite(latency) or latency < 0:
                raise ValueError('invalid status or latency')
            events.append({'timestamp': ts.astimezone(timezone.utc).isoformat(), 'method': str(record['method']).upper(), 'path': str(record['path']).split('?')[0], 'status': status, 'latency_ms': latency, 'request_id': str(record.get('request_id') or '')})
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError(f'Invalid record {line}: {exc}') from exc
    return events

def percentile(values, percent):
    if not values:
        return 0
    values = sorted(values)
    rank = (len(values)-1)*percent/100
    lo, hi = math.floor(rank), math.ceil(rank)
    return round(values[lo] + (values[hi]-values[lo])*(rank-lo), 2)

def analyze(events, latency_threshold=1000, error_threshold=0.05):
    if not events:
        return {'summary': {'requests': 0, 'error_rate': 0, 'p95_ms': 0}, 'endpoints': [], 'findings': []}
    grouped = defaultdict(list)
    for event in events:
        grouped[(event['method'], event['path'])].append(event)
    endpoints, findings = [], []
    for (method, path), group in sorted(grouped.items()):
        total = len(group)
        errors = sum(e['status'] >= 500 for e in group)
        client_errors = sum(400 <= e['status'] < 500 for e in group)
        p95 = percentile([e['latency_ms'] for e in group], 95)
        rate = round(errors/total, 4)
        item = {'method': method, 'path': path, 'requests': total, 'server_errors': errors, 'client_errors': client_errors, 'error_rate': rate, 'p95_ms': p95, 'statuses': dict(sorted(Counter(str(e['status']) for e in group).items()))}
        endpoints.append(item)
        if rate > error_threshold:
            findings.append({'severity': 'high', 'endpoint': f'{method} {path}', 'issue': 'Elevated 5xx error rate', 'evidence': f'{errors}/{total} requests returned 5xx ({rate:.1%})', 'next_step': 'Inspect request IDs and upstream dependencies for failed requests.'})
        if p95 > latency_threshold:
            findings.append({'severity': 'medium', 'endpoint': f'{method} {path}', 'issue': 'High p95 latency', 'evidence': f'p95={p95} ms exceeds {latency_threshold} ms', 'next_step': 'Review slow traces, database queries, and downstream service timings.'})
    findings.sort(key=lambda f: (0 if f['severity']=='high' else 1, f['endpoint']))
    return {'summary': {'requests': len(events), 'error_rate': round(sum(e['status'] >= 500 for e in events)/len(events), 4), 'p95_ms': percentile([e['latency_ms'] for e in events],95)}, 'endpoints': endpoints, 'findings': findings}
