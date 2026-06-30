#!/usr/bin/env python3
"""Aggregate result_*.json files into summary.csv + summary.md comparison tables.

  python3 aggregate.py --indir results/raw --outdir results
"""

import argparse
import csv
import json
from pathlib import Path

import rmw_matrix

# Each metric: JSON key -> markdown column header. One section per metric.
METRICS = [
    ("delivery_ratio_nodes", "Nodes up (recv/N)"),
    ("delivery_ratio_msgs", "Msg delivery (survivors)"),
    ("discovery_time_s", "Discovery (s)"),
    ("ram_total_pss_mb", "RAM PSS (MB)"),
    ("ram_node_rss_mb", "RAM RSS (MB)"),
    ("cpu_total_pct", "CPU (%)"),
    ("lat_p50_us", "Latency p50 (us)"),
    ("lat_p99_us", "Latency p99 (us)"),
]

CSV_FIELDS = [
    "variant", "rmw", "config", "nodes", "rate_hz", "size_bytes", "duration_s",
    "launch_elapsed_s", "discovery_time_s", "nodes_received",
    "delivery_ratio_nodes", "delivery_ratio_msgs",
    "ram_node_pss_mb", "ram_node_rss_mb", "ram_daemon_pss_mb", "ram_total_pss_mb",
    "ram_pss_per_node_mb", "cpu_total_pct", "cpu_daemon_pct", "cpu_per_node_pct",
    "lat_p50_us", "lat_p99_us", "lat_mean_us", "lat_max_us", "lat_samples",
    "mem_total_mb",
]


def load_results(indir):
    results = {}
    for path in sorted(Path(indir).glob("result_*.json")):
        d = json.loads(path.read_text())
        results[(d["variant"], d["nodes"])] = d
    return results


def variant_order(results):
    present = {v for (v, _) in results}
    ordered = [v for v in rmw_matrix.ALL_VARIANTS if v in present]
    ordered += sorted(present - set(ordered))
    return ordered


def fmt(v):
    return "—" if v is None else str(v)


def write_markdown(results, out_path):
    node_counts = sorted({n for (_, n) in results})
    variants = variant_order(results)
    lines = ["# RMW benchmark summary", ""]
    lines.append(f"Node counts: {', '.join(map(str, node_counts))}")
    lines.append("")
    for key, header in METRICS:
        lines.append(f"## {header}")
        lines.append("")
        lines.append("| Variant | " + " | ".join(f"{n} nodes" for n in node_counts) + " |")
        lines.append("|" + "---|" * (len(node_counts) + 1))
        for v in variants:
            row = [v]
            for n in node_counts:
                d = results.get((v, n))
                row.append(fmt(d.get(key)) if d else "—")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    Path(out_path).write_text("\n".join(lines))


def write_csv(results, out_path):
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for (_, _), d in sorted(results.items()):
            w.writerow(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    results = load_results(args.indir)
    if not results:
        raise SystemExit(f"no result_*.json found in {args.indir}")
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    write_markdown(results, out / "summary.md")
    write_csv(results, out / "summary.csv")
    print(f"wrote {out/'summary.md'} and {out/'summary.csv'} ({len(results)} runs)")


if __name__ == "__main__":
    main()
