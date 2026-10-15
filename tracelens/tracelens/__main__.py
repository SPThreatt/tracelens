import argparse
import json
from .core import analyze, load_events

def main():
    parser = argparse.ArgumentParser(description='Analyze API request logs and generate incident findings.')
    parser.add_argument('file', help='CSV or JSONL request log')
    parser.add_argument('--latency-threshold', type=float, default=1000)
    parser.add_argument('--error-threshold', type=float, default=0.05)
    parser.add_argument('--output', help='Write JSON report to file')
    args = parser.parse_args()
    if args.latency_threshold < 0 or not 0 <= args.error_threshold <= 1:
        parser.error('thresholds must be nonnegative; error threshold must be 0..1')
    try:
        report = analyze(load_events(args.file), args.latency_threshold, args.error_threshold)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    payload = json.dumps(report, indent=2)
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(payload + '\n', encoding='utf-8')
        print(f'Wrote {args.output}')
    else:
        print(payload)

if __name__ == '__main__':
    main()
