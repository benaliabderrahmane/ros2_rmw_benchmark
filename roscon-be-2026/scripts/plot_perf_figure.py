#!/usr/bin/env python3
"""Latency / CPU figures for the benchmark slides, from the 17-18 Nov Lyrical campaign's summaries:
  perf_test.csv (Apex performance_test, separate processes, medians of 5 runs) -> latency_step*.png, cpu_step*.png
  irobot.csv (iRobot ros2-performance suite, medians of 3 runs, optional)       -> irobot_step*.png

Each figure is built in four steps for a slide build-up (DDS defaults; + Zenoh default; + ours; + the tuned and
shared-memory configs). Every series is drawn in every step, the ones not shown yet invisible, so axes and legend never
move. Each legend label says whether that config moves data through shared memory ("shm on") or not ("shm off").

  ~/.venvs/plot/bin/python scripts/plot_perf_figure.py results/summary <out_dir>
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator  # noqa: E402

NAVY, BLUE_DK, BLUE, GREY = "#002060", "#1F5FA8", "#6FA8DC", "#5F6B7A"
INK, LGREY, GRID = "#1A2433", "#5F6B7A", "#D5DCE6"
DASH, DOT = (0, (5, 2.5)), (0, (1, 1.6))
# key, legend label (with the shared-memory state), colour, line style, width, marker. Legend order: ours, the
# defaults, then the tuned and shared-memory configs. Fast DDS's default transports include shared memory (copied,
# serialized); our payloads from 64 KiB go through a shared-memory ring (serialized); only Fast DDS data sharing
# lends the buffer (loaned messages, no serialization).
SERIES = [("unix_socket", "rmw_unix_socket_cpp · shm ≥ 64 KiB", NAVY, "-", 3.6, None),
          ("cyclonedds_default", "Cyclone DDS · default · shm off", BLUE_DK, "-", 2.2, None),
          ("fastdds_default", "Fast DDS · default · shm on", BLUE, "-", 2.2, None),
          ("zenoh_default", "Zenoh · default · shm off", GREY, "-", 2.2, None),
          ("cyclonedds_tuned", "Cyclone DDS · tuned · shm off", BLUE_DK, DASH, 2.0, None),
          ("cyclonedds_shm", "Cyclone DDS + iceoryx · shm on", BLUE_DK, DOT, 2.4, "o"),
          ("fastdds_shm", "Fast DDS data sharing · shm on, loaned", BLUE, DOT, 2.4, "o"),
          ("zenoh_tuned", "Zenoh · shm on", GREY, DOT, 2.4, "o")]
STEPS = [{"cyclonedds_default", "fastdds_default"}, {"zenoh_default"}, {"unix_socket"},
         {"cyclonedds_tuned", "cyclonedds_shm", "fastdds_shm", "zenoh_tuned"}]
IROBOT_KEY = {"unix_socket_default": "unix_socket", "fastrtps_default": "fastdds_default", "fastrtps_shm": "fastdds_shm"}
NAME = {"array1k": "1 KiB", "array16k": "16 KiB", "array64k": "64 KiB", "array256k": "256 KiB", "array1m": "1 MiB",
        "array4m": "4 MiB", "array8m": "8 MiB"}
RATE = {"array1k": 1000, "array16k": 1000, "array64k": 1000, "array256k": 500, "array1m": 100, "array4m": 30,
        "array8m": 30}  # Hz, scripts/gen_t5_specs.py SIZES
PT_1, PT_5 = list(NAME), ["array1k", "array1m", "array4m"]


def us_label(v):
    return f"{v / 1000:g} ms" if v >= 1000 else f"{v:g} µs"


def figure(panels, val, ylab, ylim, ticks, fmt, steps_shown, out, ratios):
    """panels: [(title, [(x tick label, lookup)])]; val(lookup, key) -> value or None (series absent there)."""
    plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": 15,
                         "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})
    fig, ax = plt.subplots(1, 2, figsize=(18.2, 5.4), dpi=200, sharey=True,
                           gridspec_kw={"width_ratios": ratios, "wspace": 0.05})
    shown = set().union(*STEPS[:steps_shown])
    present = [s for s in SERIES if any(val(lk, s[0]) is not None for _, pts in panels for _, lk in pts)]
    for a, (title, pts) in zip(ax, panels):
        x = list(range(len(pts)))
        for k, label, colr, ls, lw, mk in present:
            a.plot(x, [val(lk, k) for _, lk in pts], color=colr, ls=ls, lw=lw, marker=mk, ms=7, mfc="white", mew=1.8,
                   alpha=1 if k in shown else 0, zorder=5 if k == "unix_socket" else 3, label=label if a is ax[0] else None)
        a.set_yscale("log")
        a.set_xticks(x)
        a.set_xticklabels([t for t, _ in pts], fontsize=14 if "\n" in pts[0][0] else 15)
        a.set_xlim(-0.35, len(pts) - 0.65)
        a.grid(True, which="major", color=GRID, lw=0.9)
        a.set_axisbelow(True)
        for side in ("top", "right"):
            a.spines[side].set_visible(False)
        a.set_title(title, fontsize=15, color=LGREY, loc="left")
    ax[0].set_ylabel(ylab, fontsize=16)
    ax[0].set_ylim(*ylim)
    ax[0].yaxis.set_major_locator(FixedLocator(ticks))
    ax[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt(v)))
    ax[0].yaxis.set_minor_locator(NullLocator())
    handles, labels = ax[0].get_legend_handles_labels()
    leg = fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False, fontsize=14, bbox_to_anchor=(0.5, 1.0),
                     handlelength=2.4, columnspacing=1.4)
    for txt, (k, *_) in zip(leg.get_texts(), present):
        txt.set_alpha(1 if k in shown else 0)
    two_line = any("\n" in t for _, pts in panels for t, _ in pts)
    fig.subplots_adjust(left=0.075, right=0.995, top=0.8, bottom=0.17 if two_line else 0.11)
    fig.savefig(out)


def main(summary, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    pt = {(r["msg"], int(r["subs"]), r["variant"]): r for r in csv.DictReader(open(os.path.join(summary, "perf_test.csv")))}
    ir_csv = os.path.join(summary, "irobot.csv")  # optional: the iRobot figure is drawn only when it exists
    ir = {(r["suite"], r["topology"], IROBOT_KEY.get(r["variant"], r["variant"])): r
          for r in csv.DictReader(open(ir_csv))} if os.path.exists(ir_csv) else {}
    rate = lambda m: f"{RATE[m] / 1000:g} kHz" if RATE[m] >= 1000 else f"{RATE[m]} Hz"
    for f, stem, ylab, ylim, ticks, fmt in [
            ("mean_us", "latency", "mean latency (log)", (18, 36000), [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000],
             us_label),
            ("cpu_pct", "cpu", "CPU, % of one core (log)", (0.9, 180), [1, 2, 5, 10, 20, 50, 100], lambda v: f"{v:g}%")]:
        lab = (lambda m: NAME[m]) if f == "mean_us" else (lambda m: f"{NAME[m]}\n{rate(m)}")
        panels = [("1 publisher → 1 subscriber", [(lab(m), (m, 1)) for m in PT_1]),
                  ("1 publisher → 5 subscribers", [(lab(m), (m, 5)) for m in PT_5])]
        val = lambda lk, k, f=f: float(pt[(lk[0], lk[1], k)][f]) if (lk[0], lk[1], k) in pt else None
        for n in range(1, 5):
            figure(panels, val, ylab, ylim, ticks, fmt, n, os.path.join(out_dir, f"{stem}_step{n}.png"), [2.4, 1])
    # iRobot: 1 publisher at 200 Hz -> 1 subscriber (separate processes); N topics of 1 MB in two processes.
    scal = [("1 topic\n450 Hz", "1_process"), ("2 topics\n739 Hz", "2_process"), ("5 topics\n1.2 kHz", "5_process"),
            ("10 topics\n5.6 kHz", "10_processes")]
    panels = [("1 publisher at 200 Hz → 1 subscriber", [(f"{s}\n ", ("pub-sub_multi_process", t)) for s, t in
                                                        [("10 B", "10b"), ("100 KB", "100kb"), ("1 MB", "1mb"), ("4 MB", "4mb")]]),
              ("N topics of 1 MB · total publish rate", [(s, ("pub-sub_multi_process_scalability", t)) for s, t in scal])]
    val = lambda lk, k: float(ir[(lk[0], lk[1], k)]["mean_us"]) if (lk[0], lk[1], k) in ir else None
    for n in range(1, 5) if ir else ():
        figure(panels, val, "mean latency (log)", (25, 5000), [30, 50, 100, 200, 500, 1000, 2000], us_label, n,
               os.path.join(out_dir, f"irobot_step{n}.png"), [1, 1])
    print("wrote", out_dir)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
