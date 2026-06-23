#!/usr/bin/env python3
"""Render benchmark result JSONs as a multi-panel dashboard PNG (matplotlib).

  python3 plot.py --indir results/jazzy --out results/graphs/jazzy.png --title "..."

One panel per metric: x = node count (log), y = metric, one line per variant.
The local Unix-socket RMW is drawn thick/black as the reference.
"""

import argparse
import glob
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Stable order + style. unix_socket is the reference line (thick, black).
ORDER = [
    "unix_socket",
    "cyclonedds_default", "cyclonedds_tuned", "cyclonedds_shm",
    "fastdds_default", "fastdds_tuned", "fastdds_shm",
    "zenoh_default", "zenoh_tuned",
]
COLORS = {
    "unix_socket": "#000000",
    "cyclonedds_default": "#1f77b4", "cyclonedds_tuned": "#4c9be8", "cyclonedds_shm": "#9ecae1",
    "fastdds_default": "#d62728", "fastdds_tuned": "#ff7f0e", "fastdds_shm": "#ffbb78",
    "zenoh_default": "#2ca02c", "zenoh_tuned": "#98df8a",
}
# (key, title, log-y?)
METRICS = [
    ("delivery_ratio_nodes", "Nodes up (recv / N)", False),
    ("delivery_ratio_msgs", "Message delivery", False),
    ("discovery_time_s", "Discovery time (s)", True),
    ("ram_total_pss_mb", "RAM PSS total (MB)", True),
    ("ram_pss_per_node_mb", "RAM PSS per node (MB)", True),
    ("cpu_total_pct", "CPU (%, 100=1 core)", True),
    ("lat_p50_us", "Latency p50 (us)", True),
    ("lat_p99_us", "Latency p99 (us)", True),
]


def load(indir):
    data = {}
    for f in glob.glob(os.path.join(indir, "result_*.json")):
        d = json.load(open(f))
        data.setdefault(d["variant"], {})[d["nodes"]] = d
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="RMW benchmark")
    args = ap.parse_args()

    data = load(args.indir)
    if not data:
        raise SystemExit(f"no result_*.json in {args.indir}")
    variants = [v for v in ORDER if v in data] + [v for v in data if v not in ORDER]
    nodes = sorted({n for v in data.values() for n in v})

    fig, axes = plt.subplots(3, 3, figsize=(16, 12))
    axes = axes.flatten()

    for ax, (key, title, logy) in zip(axes, METRICS):
        for v in variants:
            xs, ys = [], []
            for n in nodes:
                d = data[v].get(n)
                val = d.get(key) if d else None
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    continue
                if logy and val <= 0:
                    val = 1e-3  # keep on a log axis
                xs.append(n)
                ys.append(val)
            if not xs:
                continue
            lw = 2.8 if v == "unix_socket" else 1.6
            z = 5 if v == "unix_socket" else 2
            ax.plot(xs, ys, marker="o", ms=4, lw=lw, color=COLORS.get(v), label=v, zorder=z)
        ax.set_title(title, fontsize=11)
        ax.set_xscale("log")
        ax.set_xticks(nodes)
        ax.set_xticklabels([str(n) for n in nodes])
        ax.set_xlabel("nodes")
        if logy:
            ax.set_yscale("log")
        else:
            ax.set_ylim(-0.03, 1.05)
        ax.grid(True, which="both", ls=":", alpha=0.4)

    # Legend in the 9th panel.
    legend_ax = axes[len(METRICS)]
    legend_ax.axis("off")
    handles, labels = axes[0].get_legend_handles_labels()
    legend_ax.legend(handles, labels, loc="center", fontsize=11, frameon=False,
                     title="variant")
    for ax in axes[len(METRICS) + 1:]:
        ax.axis("off")

    fig.suptitle(args.title, fontsize=15, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, dpi=110)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
