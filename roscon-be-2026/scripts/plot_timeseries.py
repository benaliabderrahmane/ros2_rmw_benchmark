#!/usr/bin/env python3
"""Plot ring_timeseries.py results: total CPU % and total PSS against time since launch, log y, median of the runs.

  ~/.venvs/plot/bin/python scripts/plot_timeseries.py results/timeseries-2026-11-21
Writes timeseries.png and summary.json (per variant: median curves, bring-up, peaks, steady state) into that folder.
"""
import glob
import json
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# The deck's chart convention (memory slide): ours NAVY and thick, Fast DDS BLUE, Cyclone BLUE_DK, Zenoh GREY.
STYLE = {
    "unix_socket": ("rmw_unix_socket_cpp", "#002060", "-", 3.5),
    "zenoh_default": ("Zenoh, peer (default)", "#5F6B7A", "-", 2.0),
    "zenoh_client": ("Zenoh, client + router", "#5F6B7A", "--", 2.0),
    "cyclonedds_tuned": ("Cyclone DDS (tuned)", "#1F5FA8", "-", 2.0),
    "fastdds_tuned": ("Fast DDS (tuned)", "#6FA8DC", "-", 2.0),
}
CPU_FLOOR = 1.0  # % : a log axis cannot show 0


def from_cgroup(d, csv):
    """Replace a run's in-container samples by the host's cgroup samples (cgroup_sampler.py), aligned on t0_ns."""
    rows = [line.split(",") for line in open(csv).read().splitlines()[1:]]
    rows = [(int(r[0]), int(r[1]), float(r[2]), int(r[4]), int(r[5])) for r in rows if len(r) == 6]
    samples, prev = [], None
    for ns, usec, mem, ev_max, oom in rows:
        if prev and ns > d["t0_ns"]:
            dt = (ns - prev[0]) / 1e9
            samples.append({"t": round((ns - d["t0_ns"]) / 1e9, 3), "cpu_pct": round(100 * (usec - prev[1]) / 1e6 / dt, 1),
                            "pss_mb": mem, "tcp": 0})
        prev = (ns, usec)
    end = d["samples"][-1]["t"]  # the supervised window; the container's teardown comes after
    d["samples"] = [x for x in samples if x["t"] <= end]
    d["cap_hits"], d["oom_kills"] = rows[-1][3], rows[-1][4]
    return d


def load(folder):
    runs = {}
    for f in sorted(glob.glob(os.path.join(folder, "*_r*.json"))):
        d = json.load(open(f))
        csv = f[:-5] + ".cgroup.csv"
        if os.path.exists(csv) and "t0_ns" in d:
            d = from_cgroup(d, csv)
        runs.setdefault(d["variant"], []).append(d)
    return runs


BIN = 0.5  # s: the common grid every run is resampled onto


def interp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            return ys[i - 1] + (ys[i] - ys[i - 1]) * (x - xs[i - 1]) / (xs[i] - xs[i - 1])
    return ys[-1]


def resample(run):
    """CPU % per BIN and PSS on a fixed grid. Samples are irregular when the sampler stalls under load, so CPU comes
    from the cumulative core-seconds (exact whatever the spacing) and PSS is interpolated."""
    s = run["samples"]
    ts, core_s, prev = [0.0], [0.0], 0.0
    for x in s:
        core_s.append(core_s[-1] + x["cpu_pct"] / 100 * (x["t"] - prev))
        ts.append(x["t"])
        prev = x["t"]
    grid = [BIN * k for k in range(1, int(s[-1]["t"] / BIN) + 1)]
    cpu = [100 * (interp(ts, core_s, g) - interp(ts, core_s, g - BIN)) / BIN for g in grid]
    pss = [interp([x["t"] for x in s], [x["pss_mb"] for x in s], g) for g in grid]
    return grid, cpu, pss, core_s, ts


def summarize(runs):
    out = {}
    for v, rs in runs.items():
        res = [resample(r) for r in rs]
        n = min(len(g) for g, *_ in res)
        t = res[0][0][:n]
        cpu = [statistics.median(r[1][i] for r in res) for i in range(n)]
        pss = [statistics.median(r[2][i] for r in res) for i in range(n)]
        first10 = statistics.median(interp(r[4], r[3], 10.0) for r in res)  # core-seconds in the first 10 s
        steady = [c for tt, c in zip(t, cpu) if tt >= max(20, t[-1] - 20)]  # the last 20 s (100-node runs: 20-30 s)
        ups = [r.get("bringup_s", r.get("all_up_s")) for r in rs]
        ups = [u for u in ups if u is not None]
        # Burst end: the first bin back under 2x the steady level; a bin is labelled by its end time.
        calm = 2 * statistics.median(steady) if steady else 0
        burst_end = next((tt - BIN for tt, c in zip(t, cpu) if c < calm), None)
        out[v] = {"runs": len(rs), "all_up_runs": len(ups), "bringup_s": statistics.median(ups) if ups else None,
                  "burst_end_s": burst_end, "nodes": rs[0]["nodes"], "pubs": rs[0].get("pubs", 1),
                  "subs": rs[0].get("subs", 1), "restarts": statistics.median(r.get("restarts", 0) for r in rs),
                  "nodes_up_min": min(r.get("nodes_up", r.get("nodes_received", 0)) for r in rs),
                  "cap_hits": max(r.get("cap_hits", 0) for r in rs), "oom_kills": max(r.get("oom_kills", 0) for r in rs),
                  "nodes_up_runs": [r.get("nodes_up", r.get("nodes_received")) for r in rs],
                  "peak_cpu_pct": round(max(cpu)), "peak_cpu_t": t[cpu.index(max(cpu))],
                  "steady_cpu_pct": round(statistics.median(steady), 1) if steady else None,
                  "core_s_first10": round(first10, 1),
                  "core_s_first30": round(statistics.median(interp(r[4], r[3], 30.0) for r in res), 1),
                  "peak_pss_mb": round(max(pss)), "end_pss_mb": round(pss[-1]),
                  "end_tcp": statistics.median(r["samples"][-1]["tcp"] for r in rs),
                  "t": t, "cpu": [round(c, 1) for c in cpu], "pss": [round(p, 1) for p in pss]}
    return out


def spread(values, min_gap):
    """Label positions (log10 space) pushed apart by at least min_gap, in the input order."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    pos = [None] * len(values)
    last = None
    for i in order:
        pos[i] = values[i] if last is None else max(values[i], last + min_gap)
        last = pos[i]
    return pos


def main(folder):
    s = summarize(load(folder))
    assert s, f"no *_r*.json in {folder}"
    fig, axes = plt.subplots(1, 2, figsize=(16, 6.2), dpi=150)
    one = next(iter(s.values()))
    nodes = one["nodes"]
    each = f", each with {one['pubs']} publishers and {one['subs']} subscriptions" if one["pubs"] > 1 else ""
    import math
    cg = any(os.path.exists(f[:-5] + ".cgroup.csv") for f in glob.glob(os.path.join(folder, "*_r*.json")))
    mem_label = "total memory (cgroup: anon + shared + mapped), MB (log)" if cg else "total PSS, MB (log)"
    for ax, key, label in ((axes[0], "cpu", "total CPU, % of one core (log)"),
                           (axes[1], "pss", mem_label)):
        shown = [v for v in STYLE if v in s]
        for v in shown:
            name, col, ls, lw = STYLE[v]
            y = [max(CPU_FLOOR, c) for c in s[v][key]] if key == "cpu" else s[v][key]
            ax.plot(s[v]["t"], y, color=col, ls=ls, lw=lw, label=name, zorder=3 if v == "unix_socket" else 2)
        if key == "pss":  # five end labels, pushed apart so none overlaps; the CPU panel has the legend
            ends = [math.log10(s[v]["pss"][-1]) for v in shown]
            for v, e, p in zip(shown, ends, spread(ends, 0.045)):
                ax.annotate(STYLE[v][0], (s[v]["t"][-1], 10 ** e), xytext=(s[v]["t"][-1] + 0.6, 10 ** p),
                            va="center", fontsize=10, color="#1A2433")
        ax.set_yscale("log")
        ax.set_xlabel(f"seconds since all {nodes} processes were started")
        ax.set_ylabel(label)
        ax.grid(True, which="major", color="#D5DCE6", lw=0.8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.set_xlim(0, max(x["t"][-1] for x in s.values()) * 1.25)
    axes[0].legend(frameon=False, fontsize=10, loc="upper right")
    fig.suptitle(f"{nodes} ROS 2 nodes, one per process{each}, started at once: median of "
                 f"{min(x['runs'] for x in s.values())} runs, CPU in 0.5 s bins", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(folder, "timeseries.png"))
    json.dump(s, open(os.path.join(folder, "summary.json"), "w"), indent=1)
    for v, x in s.items():
        print(f"{v:17s} up {x['all_up_runs']}/{x['runs']} bring-up {x['bringup_s']} s · CPU peak {x['peak_cpu_pct']}% "
              f"at {x['peak_cpu_t']} s, steady {x['steady_cpu_pct']}% · PSS peak {x['peak_pss_mb']} MB, "
              f"end {x['end_pss_mb']} MB · TCP {x['end_tcp']} · restarts {x['restarts']} · burst end {x['burst_end_s']} s")


if __name__ == "__main__":
    main(sys.argv[1])
