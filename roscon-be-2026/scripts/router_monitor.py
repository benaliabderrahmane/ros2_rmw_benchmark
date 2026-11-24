#!/usr/bin/env python3
"""Watch every Zenoh router (rmw_zenohd) and the host's memory once a second, from the host, while a campaign runs.

Per router: CPU % (100 = one core), RSS MB and the established TCP connections in its network namespace (client mode:
about one per node; peer mode: a mesh). Host: MemAvailable. Rows go to --out (CSV) with the label the driver writes to
--label-file. Watchdog: when MemAvailable falls under --min-avail-gb, every container labelled zc-campaign is killed
(the run fails, the desktop survives). Stops when --stop-file appears.
RSS, not PSS: the router runs as root in a container and smaps_rollup is root-only; one process, so they are close.
"""
import argparse
import os
import subprocess
import time

CLK = os.sysconf("SC_CLK_TCK")


def read(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return ""


def routers():
    return [int(p) for p in os.listdir("/proc") if p.isdigit() and read(f"/proc/{p}/comm").strip() == "rmw_zenohd"]


def ticks(pid):
    s = read(f"/proc/{pid}/stat")
    f = s[s.rfind(")") + 2:].split()
    return int(f[11]) + int(f[12]) if len(f) > 12 else None


def rss_mb(pid):
    for line in read(f"/proc/{pid}/status").splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024
    return None


def tcp(pid):
    ends = sum(1 for path in ("net/tcp", "net/tcp6") for line in read(f"/proc/{pid}/{path}").splitlines()[1:]
               if line.split()[3:4] == ["01"])
    return ends // 2


def mem_avail_mb():
    for line in read("/proc/meminfo").splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) // 1024
    return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--label-file", required=True)
    ap.add_argument("--stop-file", required=True)
    ap.add_argument("--min-avail-gb", type=float, default=3.0)
    a = ap.parse_args()
    new = not os.path.exists(a.out)
    out = open(a.out, "a", buffering=1)
    if new:
        out.write("time,label,mem_avail_mb,router_pid,router_cpu_pct,router_rss_mb,router_tcp,event\n")
    prev, prev_t, last_idle = {}, time.monotonic(), 0.0
    while not os.path.exists(a.stop_file):
        time.sleep(1.0)
        now, stamp = time.monotonic(), time.strftime("%Y-%m-%dT%H:%M:%S")
        label, avail = read(a.label_file).strip(), mem_avail_mb()
        cur = {p: ticks(p) for p in routers()}
        for p, t in cur.items():
            if t is None:
                continue
            cpu = "" if p not in prev or prev[p] is None else f"{100 * (t - prev[p]) / CLK / (now - prev_t):.1f}"
            out.write(f"{stamp},{label},{avail},{p},{cpu},{rss_mb(p) or 0:.1f},{tcp(p)},\n")
        if not cur and now - last_idle >= 5:  # keep the memory trace between router runs
            out.write(f"{stamp},{label},{avail},,,,,\n")
            last_idle = now
        if 0 <= avail < a.min_avail_gb * 1024:
            ids = subprocess.run(["docker", "ps", "-q", "--filter", "label=zc-campaign"], capture_output=True,
                                 text=True).stdout.split()
            if ids:
                subprocess.run(["docker", "kill", *ids], capture_output=True)
            out.write(f"{stamp},{label},{avail},,,,,WATCHDOG killed {len(ids)} container(s)\n")
        prev, prev_t = cur, now


if __name__ == "__main__":
    main()
