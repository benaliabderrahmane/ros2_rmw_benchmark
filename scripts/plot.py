#!/usr/bin/env python3
"""Render benchmark result JSONs as a multi-panel dashboard PNG (matplotlib).

  python3 plot.py --indir results/jazzy --out results/graphs/jazzy.png --title "..."

One panel per metric: x = node count (log), y = metric, one line per variant.
unix_socket (this project's RMW) is drawn thick and black, since it is the
baseline the other RMWs are being compared against.
"""

import argparse
import glob
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Draw order and per-variant color. The fixed order keeps the legend stable across
# runs; unix_socket (this project's RMW) is the thick black baseline.
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
        with open(f) as fh:
            d = json.load(fh)
        data.setdefault(d["variant"], {})[d["nodes"]] = d
    return data


def local_meminfo_mb():
    """Total RAM (MB) of the machine running this script, or None."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return round(int(line.split()[1]) / 1024.0, 1)
    except (OSError, ValueError, IndexError):
        pass
    return None


def figure_total_ram(data, variants, nodes, cli_total):
    """One denominator for the whole RAM%% figure, so a single line never mixes
    totals across node counts. The measuring machine's recorded mem_total_mb wins
    when the runs agree on it; then --total-ram-mb; then this machine's
    /proc/meminfo. Returns (mb_or_None, used_fallback)."""
    recorded = {data[v][n]["mem_total_mb"]
                for v in variants for n in nodes
                if data[v].get(n) and data[v][n].get("mem_total_mb")}
    if len(recorded) == 1:
        return recorded.pop(), False
    if cli_total:
        return cli_total, True
    # No single recorded total (old data, or runs from different machines): fall back.
    return local_meminfo_mb(), True


def _style(ax, nodes):
    ax.set_xscale("log")
    ax.set_xticks(nodes)
    ax.set_xticklabels([str(n) for n in nodes])
    ax.set_xlabel("nodes")
    ax.grid(True, which="both", ls=":", alpha=0.4)


def plot_ram_pct(data, variants, nodes, out, cli_total):
    """RAM (PSS) as a percentage of total system RAM, vs node count."""
    total, used_fallback = figure_total_ram(data, variants, nodes, cli_total)
    fig, ax = plt.subplots(figsize=(8, 6))
    if not total:
        ax.axis("off")
        ax.text(0.5, 0.5, "No total-RAM available to compute a percentage.\n"
                "Pass --total-ram-mb, or re-run so results record mem_total_mb.",
                ha="center", va="center", fontsize=12)
    else:
        for v in variants:
            xs, ys = [], []
            for n in nodes:
                d = data[v].get(n)
                pss = d.get("ram_total_pss_mb") if d else None
                if not d or pss is None:
                    continue
                xs.append(n)
                ys.append(round(100.0 * pss / total, 2))
            if not xs:
                continue
            lw = 2.8 if v == "unix_socket" else 1.6
            z = 5 if v == "unix_socket" else 2
            ax.plot(xs, ys, marker="o", ms=4, lw=lw, color=COLORS.get(v), label=v, zorder=z)
        ax.set_title("RAM PSS as % of total system RAM", fontsize=12)
        ax.set_ylabel("% of total RAM")
        _style(ax, nodes)
        ax.legend(fontsize=9, frameon=False)
        if used_fallback:
            ax.text(0.5, -0.13, "note: no recorded total RAM in these runs; "
                    "used --total-ram-mb or this machine's /proc/meminfo",
                    transform=ax.transAxes, ha="center", va="top", fontsize=8, color="#888")
    fig.tight_layout()
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(f"wrote {out}")


def plot_startup_cpu(data, variants, node_list, out):
    """CPU% vs time (startup curve) -- one subplot per requested node count."""
    present = [n for n in node_list
               if any(data[v].get(n, {}).get("cpu_timeseries") for v in variants)]
    fig, axes = plt.subplots(1, max(1, len(present)),
                             figsize=(7 * max(1, len(present)), 5.5), squeeze=False)
    axes = axes[0]
    if not present:
        axes[0].axis("off")
        axes[0].text(0.5, 0.5,
                     "No cpu_timeseries in these results.\n"
                     "Re-run the benchmark on this branch (run_one.py now records it)\n"
                     "to populate the startup CPU-vs-time graph.",
                     ha="center", va="center", fontsize=12)
    for ax, n in zip(axes, present):
        for v in variants:
            d = data[v].get(n)
            series = d.get("cpu_timeseries") if d else None
            if not series:
                continue
            xs = [s["t_s"] for s in series]
            ys = [s["cpu_pct"] for s in series]
            lw = 2.8 if v == "unix_socket" else 1.6
            z = 5 if v == "unix_socket" else 2
            ax.plot(xs, ys, lw=lw, color=COLORS.get(v), label=v, zorder=z)
        ax.set_title(f"Startup CPU vs time -- {n} nodes", fontsize=12)
        ax.set_xlabel("time since launch (s)")
        ax.set_ylabel("CPU (%, 100 = 1 core)")
        ax.grid(True, ls=":", alpha=0.4)
        ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="RMW benchmark")
    ap.add_argument("--total-ram-mb", type=float, default=None,
                    help="total system RAM (MB) for the RAM%% graph when a run did "
                         "not record it; defaults to this machine's /proc/meminfo")
    ap.add_argument("--startup-nodes", default="100,200",
                    help="comma-separated node counts for the startup CPU-vs-time graph")
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

    # Two extra figures, written alongside --out (the dashboard above is unchanged).
    base, ext = os.path.splitext(args.out)
    try:
        startup_nodes = [int(x) for x in args.startup_nodes.split(",") if x.strip()]
    except ValueError:
        startup_nodes = [100, 200]
    plot_ram_pct(data, variants, nodes, f"{base}_ram_pct{ext}", args.total_ram_mb)
    plot_startup_cpu(data, variants, startup_nodes, f"{base}_startup_cpu{ext}")


if __name__ == "__main__":
    main()
