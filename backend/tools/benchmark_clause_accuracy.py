import argparse
import json
import time
from collections import Counter

import requests


def load_dataset(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def run(args):
    dataset = load_dataset(args.dataset)
    headers = {"Authorization": f"Bearer {args.token}"}

    total = 0
    correct = 0
    latencies = []
    label_counts = Counter()
    error_rows = 0

    for row in dataset:
        contract_id = row["contract_id"]
        ground_truth = row.get("ground_truth_clause_types", [])
        ground_set = {x.strip().lower() for x in ground_truth if x}

        start = time.perf_counter()
        resp = requests.get(
            f"{args.base_url}/api/analysis/{contract_id}",
            headers=headers,
            timeout=args.timeout,
        )
        latency = time.perf_counter() - start
        latencies.append(latency)

        if resp.status_code != 200:
            error_rows += 1
            continue

        data = resp.json()
        predicted = [c.get("clause_type", "") for c in data.get("clauses", [])]
        pred_set = {x.strip().lower() for x in predicted if x}

        union = ground_set | pred_set
        if union:
            row_score = len(ground_set & pred_set) / len(union)
            total += 1
            if row_score >= args.match_threshold:
                correct += 1

        for g in ground_set:
            label_counts[g] += 1

    accuracy = (correct / total) * 100 if total else 0.0
    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0
    p95_latency = sorted(latencies)[int(0.95 * (len(latencies) - 1))] if latencies else 0.0

    print("=== Legalyze Benchmark Summary ===")
    print(f"Dataset rows: {len(dataset)}")
    print(f"Evaluated rows: {total}")
    print(f"Errored rows: {error_rows}")
    print(f"Clause detection accuracy (%): {accuracy:.2f}")
    print(f"Avg analysis fetch latency (s): {avg_latency:.3f}")
    print(f"P95 analysis fetch latency (s): {p95_latency:.3f}")
    print(f"Match threshold (Jaccard): {args.match_threshold}")
    print("Ground-truth label distribution:")
    for k, v in label_counts.most_common():
        print(f"  - {k}: {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark clause detection accuracy from analyzed contracts."
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--token", required=True, help="Bearer access token")
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to jsonl dataset with contract_id and ground_truth_clause_types",
    )
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--match-threshold", type=float, default=0.7)
    args = parser.parse_args()
    run(args)

