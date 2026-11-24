#!/usr/bin/env python3
"""Sample one container's cgroup from the host every --interval s until the container is gone.

CPU: cpu.stat usage_usec (every process in the container, kernel-accounted). Memory: memory.stat anon + shmem +
file_mapped, each page counted once by the kernel, like a PSS total; memory.current and memory.events (max, oom_kill)
show whether the --memory cap was reached. Time: CLOCK_MONOTONIC ns, the clock the container's processes use, so rows
align with ts200.py's t0_ns. Reading a few small files from outside takes no lock in the measured processes, and the
reader is in another cgroup, so the container's load cannot starve it.

  python3 cgroup_sampler.py --cidfile run.cid --out run.cgroup.csv
"""
import argparse
import glob
import os
import time


def kv(path):
    out = {}
    try:
        with open(path) as f:
            for line in f:
                k, _, v = line.partition(" ")
                out[k] = int(v)
    except (OSError, ValueError):
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cidfile", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", type=float, default=0.5)
    a = ap.parse_args()
    for _ in range(600):  # docker writes the cidfile once the container exists
        if os.path.exists(a.cidfile) and open(a.cidfile).read().strip():
            break
        time.sleep(0.1)
    cid = open(a.cidfile).read().strip()
    cg = None
    for _ in range(100):
        hits = glob.glob(f"/sys/fs/cgroup/system.slice/docker-{cid}.scope") + glob.glob(f"/sys/fs/cgroup/docker/{cid}")
        if hits:
            cg = hits[0]
            break
        time.sleep(0.1)
    assert cg, f"no cgroup for container {cid}"
    with open(a.out, "w", buffering=1) as out:
        out.write("mono_ns,cpu_usec,mem_mb,current_mb,events_max,oom_kill\n")
        nxt = time.monotonic()
        while os.path.isdir(cg):
            cpu, mem, ev = kv(f"{cg}/cpu.stat"), kv(f"{cg}/memory.stat"), kv(f"{cg}/memory.events")
            try:
                current = int(open(f"{cg}/memory.current").read())
            except (OSError, ValueError):
                break
            if not cpu:
                break
            used = mem.get("anon", 0) + mem.get("shmem", 0) + mem.get("file_mapped", 0)
            out.write(f"{time.monotonic_ns()},{cpu['usage_usec']},{used / 2**20:.1f},{current / 2**20:.1f},"
                      f"{ev.get('max', 0)},{ev.get('oom_kill', 0)}\n")
            nxt += a.interval
            time.sleep(max(0.0, nxt - time.monotonic()))


if __name__ == "__main__":
    main()
