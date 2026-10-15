# TraceLens

**API log analyzer for incident triage.** Turn request logs into endpoint-level reliability metrics and actionable findings in seconds.

## Quick start

Requires Python 3.10+. No API keys, database, Docker, or pip installs.

```bash
python -m tracelens samples/requests.csv
python -m tracelens samples/requests.csv --output report.json
python -m unittest discover -s tests -v
```

## Input

CSV (with header) or JSONL. Required fields: `timestamp` (timezone-aware ISO 8601), `method`, `path`, `status` (100–599), `latency_ms` (nonnegative number). Optional: `request_id`.

## Output

JSON containing overall request count, 5xx error rate, p95 latency, per-endpoint metrics, and prioritized findings with evidence and investigation suggestions. Query parameters are stripped from paths to reduce accidental sensitive-data exposure.

## Options

- `--latency-threshold 1000` sets the p95 warning threshold in milliseconds.
- `--error-threshold 0.05` sets the 5xx error-rate threshold (fraction).
- `--output report.json` writes machine-readable results.

## Architecture

`CSV/JSONL → validation/normalization → endpoint grouping → percentile/error-rate analysis → JSON incident report`

## Limitations / roadmap

This is an offline, single-file triage utility, not a live monitoring platform. Endpoint paths with dynamic IDs are not normalized, and findings are deterministic heuristics, not verified root-cause diagnoses. Planned: streaming ingestion, OpenTelemetry support, path templating, time-window baselines, HTML dashboard, and CI integrations.

## Privacy

Analyze only logs you are authorized to access. Do not commit customer logs, credentials, or sensitive request data. The tool does not send data over the network.

## License

MIT. See LICENSE.
