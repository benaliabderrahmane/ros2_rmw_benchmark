#!/usr/bin/env python3
"""The 200-node figure for the benchmark slide, from plot_timeseries.py's summary.json (0.5 s median curves).

Two rows (CPU, memory) by two columns (the first 30 s, where the bursts are; the whole 10 minutes). Same axes for every
RMW, log scales with human ticks (CPU in cores, memory in MB/GB), a dot where all 200 nodes are up, and each RMW's
steady value (median of the last 60 s) written at the end of its line. The full-length column uses 5 s averages.
Drawn at the slide's size (inches = slide inches), so font sizes are slide points.

  ~/.venvs/plot/bin/python scripts/plot_slide_figure.py results/timeseries200-2026-11-21 [out.png [key,key,...]]

With a key list, only those RMWs are drawn; the others stay invisible in place (legend slots, label positions and
axes unchanged), so the figures for successive key lists form a slide build-up without anything moving.
"""
import json
import math
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, NullLocator  # noqa: E402

# The deck's palette and chart convention (memory slide): ours NAVY and thick, Zenoh GREY, Cyclone BLUE_DK, Fast DDS BLUE.
STYLE = [("unix_socket", "rmw_unix_socket_cpp", "#002060", "-", 3.6),
         ("zenoh_default", "Zenoh, peer (default)", "#5F6B7A", "-", 2.2),
         ("zenoh_client", "Zenoh, client + router", "#5F6B7A", (0, (5, 2.5)), 2.2),
         ("cyclonedds_tuned", "Cyclone DDS (tuned)", "#1F5FA8", "-", 2.2),
         ("fastdds_tuned", "Fast DDS (tuned)", "#6FA8DC", "-", 2.2)]
INK, GREY, GRID = "#1A2433", "#5F6B7A", "#D5DCE6"
CPU_TICKS = [0.5, 1, 2, 4, 8, 16]
MEM_TICKS = [250, 500, 1000, 2000, 4000, 8000, 16000]  # decimal, like the slide text


def mem_label(mb):
    return f"{mb:.0f} MB" if mb < 1000 else f"{mb / 1000:.1f} GB".replace(".0 GB", " GB")


def cores_label(c):
    return f"{c:g} core" + ("" if c == 1 else "s") if c >= 1 else f"{c:g}"


def smooth(t, y, width):
    """Mean over consecutive `width`-second windows (the full-length view)."""
    out_t, out_y, step = [], [], t[1] - t[0] if len(t) > 1 else 0.5
    n = max(1, round(width / step))
    for i in range(0, len(y) - n + 1, n):
        out_t.append(t[i + n - 1])
        out_y.append(sum(y[i:i + n]) / n)
    return out_t, out_y


def spread(values, gap):
    order = sorted(range(len(values)), key=lambda i: values[i])
    pos, last = [0.0] * len(values), None
    for i in order:
        pos[i] = values[i] if last is None else max(values[i], last + gap)
        last = pos[i]
    return pos


def main(folder, out, show=None):
    global STYLE
    # SLIDE_LABELS="key=label;...": rename a series, e.g. Jazzy's fastdds_tuned, whose profile Fast DDS 2.14 never loaded
    over = dict(p.split("=", 1) for p in os.environ.get("SLIDE_LABELS", "").split(";") if "=" in p)
    STYLE = [(k, over.get(k, name), *rest) for k, name, *rest in STYLE]
    s = json.load(open(os.path.join(folder, "summary.json")))
    def shown(k):
        return show is None or k in show
    plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": 15,
                         "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})
    fig, ax = plt.subplots(2, 2, figsize=(18.2, 5.6), dpi=200, sharey="row",
                           gridspec_kw={"width_ratios": [1, 2.45], "wspace": 0.04, "hspace": 0.12})
    end = min(s[k]["t"][-1] for k, *_ in STYLE if k in s)
    for row, (key, ticks, fmt, lo, hi, ylab) in enumerate([
            ("cpu", CPU_TICKS, cores_label, 0.45, 20, "CPU"), ("pss", MEM_TICKS, mem_label, 200, 24000, "memory")]):
        for col in (0, 1):
            a = ax[row][col]
            ends = []
            for k, name, colr, ls, lw in STYLE:
                if k not in s:
                    continue
                t = s[k]["t"]
                y = [v / 100 for v in s[k]["cpu"]] if key == "cpu" else s[k]["pss"]
                if col == 0:
                    tt, yy = [x for x in t if x <= 30], y[:sum(1 for x in t if x <= 30)]
                else:
                    tt, yy = smooth([x for x in t if x <= end], y[:sum(1 for x in t if x <= end)], 5)
                yy = [max(v, lo * 1.01) for v in yy]
                a.plot(tt, yy, color=colr, ls=ls, lw=lw, zorder=4 if k == "unix_socket" else 3, alpha=1 if shown(k) else 0,
                       solid_capstyle="butt", label=name if (row, col) == (0, 1) else None)
                up = s[k].get("bringup_s") if s[k].get("all_up_runs") == s[k].get("runs") else None
                if up is not None and key == "cpu" and (col == 1 or up <= 30) and shown(k):
                    i = min(range(len(t)), key=lambda j: abs(t[j] - up))
                    a.plot([up], [max(y[i], lo * 1.01)], "o", ms=9, color=colr, mec="white", mew=1.5, zorder=6)
                if col == 1:  # steady value at the end of the line: median of the last 60 s
                    own = min(end, t[-1])
                    last = [v for x, v in zip(t, y) if own - 60 <= x <= own]
                    ends.append((k, statistics.median(last), colr))
            a.set_yscale("log", base=2)
            a.set_ylim(lo, hi)
            a.yaxis.set_major_locator(FixedLocator(ticks))
            a.yaxis.set_major_formatter(FuncFormatter(lambda v, _p, f=fmt: f(v)))
            a.yaxis.set_minor_locator(NullLocator())
            a.grid(True, which="major", color=GRID, lw=0.9)
            a.set_axisbelow(True)
            for side in ("top", "right"):
                a.spines[side].set_visible(False)
            if col == 0:
                a.set_xlim(0, 30)
                a.set_xticks(range(0, 31, 5))
                a.set_ylabel(ylab, fontsize=16, color=INK)
            else:
                a.set_xlim(0, end)
                a.set_xticks(range(0, round(end) + 1, 60))
                lg = [math.log2(v) for _, v, _ in ends]
                for (k, v, colr), p in zip(ends, spread(lg, 0.7)):  # spread over all, so labels never move
                    if not shown(k):
                        continue
                    txt = cores_label(round(v, 1)) if key == "cpu" else mem_label(v)
                    # a thin leader in the series colour carries identity; the text stays in ink
                    a.annotate(txt, (end, v), xytext=(end * 1.035, 2 ** p), va="center", fontsize=15,
                               color=INK, fontweight="bold" if k == "unix_socket" else "normal",
                               arrowprops=dict(arrowstyle="-", color=colr, lw=1.6, shrinkA=0, shrinkB=2),
                               annotation_clip=False)
            if row == 0:
                a.xaxis.set_major_formatter(NullFormatter())
            else:
                a.set_xlabel("seconds since the 200 processes were started" if col == 1 else "seconds", fontsize=15,
                             color=GREY)
    ax[0][0].set_title("first 30 s", fontsize=15, color=GREY, loc="left")
    ax[0][1].set_title("whole run (5 s averages) · steady value at the end of each line", fontsize=15, color=GREY,
                       loc="left")
    handles, labels = ax[0][1].get_legend_handles_labels()
    def note(x):
        return ("" if x["all_up_runs"] == x["runs"] else " · never all up" if not x["all_up_runs"]
                else f" · all up in {x['all_up_runs']} of {x['runs']} runs")
    present = [st for st in STYLE if st[0] in s]  # a run of only some RMWs: labels follow the series drawn
    labels = [lab + note(s[k]) for (k, *_), lab in zip(present, labels)]
    handles.append(plt.Line2D([], [], ls="", marker="o", ms=9, color=INK, mec="white"))
    labels.append("all 200 up")
    leg = fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, fontsize=15, bbox_to_anchor=(0.5, 1.0),
                     handlelength=2.6, columnspacing=2.2)
    for (k, *_), txt in zip([st for st in STYLE if st[0] in s], leg.get_texts()):
        txt.set_alpha(1 if shown(k) else 0)
    fig.subplots_adjust(left=0.07, right=0.9, top=0.8, bottom=0.11)
    fig.savefig(out)
    print("wrote", out)


if __name__ == "__main__":
    folder = sys.argv[1]
    main(folder, sys.argv[2] if len(sys.argv) > 2 else os.path.join(folder, "slide_figure.png"),
         set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None)
