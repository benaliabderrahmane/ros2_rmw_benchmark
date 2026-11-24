#!/usr/bin/env python3
"""Summaries for reproduce/*.sh, with the campaign's own medians (collect.py's perf() and ring()).

  summarize.py perf <results dir holding t5/r*/>   <out dir>  -> <out>/perf_test.csv (plot_perf_figure.py's input)
  summarize.py ring <results dir holding ring/r*/> <out dir>  -> <out>/ring.json
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect  # noqa: E402

FIELDS = ["msg", "subs", "variant", "stack", "config", "runs", "mean_us", "tail_us", "delivered_pct", "cpu_pct",
          "pss_mb"]


def main(kind, res, out):
    os.makedirs(out, exist_ok=True)
    if kind == "perf":
        rows = []
        for (msg, nsub, variant), v in sorted(collect.perf(res).items()):
            stack, config = ("unix_socket", "default") if variant == "unix_socket" else variant.rsplit("_", 1)
            rows.append({"msg": msg, "subs": nsub, "variant": variant, "stack": stack, "config": config, **v})
        with open(os.path.join(out, "perf_test.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        for r in rows:
            print(f"{r['msg']:>10s} 1->{r['subs']} {r['variant']:20s} mean {r['mean_us']} us  CPU {r['cpu_pct']} %  "
                  f"delivered {r['delivered_pct']} %  ({r['runs']} runs)")
    elif kind == "ring":
        d = {f"{p}/{v}/n{n}": x for (p, v, n), x in sorted(collect.ring(res).items())}
        json.dump(d, open(os.path.join(out, "ring.json"), "w"), indent=1)
        for k, x in d.items():
            print(f"{k:28s} all up {x['all_up_runs']}/{x['runs']}  CPU {x['cpu_pct']} %  PSS {x['pss_mb']} MB")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(*sys.argv[1:4])
