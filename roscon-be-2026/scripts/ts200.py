#!/usr/bin/env python3
"""Supervised time series: N processes, each one ROS node with P publishers and S subscriptions (bench_multi's
multi_node), all started at once. A node that exits, or is not up within --up-timeout s of its (re)start, is killed and
restarted (at most --max-restarts times), so the run reaches all N up whenever the RMW allows it. "Up" = every one of
its subscriptions has received a message (the node writes ready_<i>). Every --interval s from launch: total CPU %, PSS
and TCP connections of all node processes plus the discovery daemon. Stops --tail s after all N are up, or at
--max-window s. Runs inside the rmw-bench image with /ts200/install sourced.

  python3 ts200.py --variant unix_socket --out /out/unix_socket_r1.json
"""
import argparse
import json
import os
import shutil
import signal
import subprocess
import time

import ring_timeseries  # noqa: F401  registers zenoh_client / zenoh_client_shm in rmw_matrix
from ring_timeseries import measure, mono_ns, rmw_matrix, stop_daemon, tcp_connections

NODE_BIN = os.environ.get("TS200_NODE_BIN", "/ts200/install/bench_multi/lib/bench_multi/multi_node")  # override: tests only


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=list(rmw_matrix.BUILDERS))
    ap.add_argument("--nodes", type=int, default=200)
    ap.add_argument("--pubs", type=int, default=5)
    ap.add_argument("--subs", type=int, default=5)
    ap.add_argument("--interval", type=float, default=0.5)
    ap.add_argument("--up-timeout", type=float, default=120.0)
    ap.add_argument("--max-restarts", type=int, default=3)
    ap.add_argument("--tail", type=float, default=30.0)
    ap.add_argument("--max-window", type=float, default=600.0)
    ap.add_argument("--mem-every", type=int, default=4, help="read PSS and TCP every Nth sample (both are slow)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    spec = rmw_matrix.get_spec(a.variant)
    env = {**os.environ, "RMW_IMPLEMENTATION": spec.rmw, **spec.env}
    ready = f"/tmp/ready_{spec.key}"
    shutil.rmtree(ready, ignore_errors=True)
    os.makedirs(ready)

    daemon_pgid = None
    if spec.daemon_cmd:
        d = subprocess.Popen(spec.daemon_cmd, env={**os.environ, **spec.daemon_env}, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        daemon_pgid = os.getpgid(d.pid)
        time.sleep(spec.daemon_wait_s)
        if not measure.pgid_members(daemon_pgid):
            raise SystemExit("daemon failed to start")

    def start(i):
        return subprocess.Popen([NODE_BIN, "--id", str(i), "--total", str(a.nodes), "--pubs", str(a.pubs),
                                 "--subs", str(a.subs), "--rate", "20", "--size", "256", "--ready-dir", ready],
                                env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    t0 = mono_ns()
    procs = [start(i) for i in range(a.nodes)]
    started = [t0] * a.nodes
    restarts, events, up_at = [0] * a.nodes, [], {}
    samples, prev, prev_t, all_up_ns = [], {}, t0, None
    pss = tcp = None  # --mem-every 0: memory comes from the host (cgroup_sampler.py)
    k = 1
    while True:
        target = t0 + int(k * a.interval * 1e9)
        time.sleep(max(0.0, (target - mono_ns()) / 1e9))
        now = mono_ns()
        pids = [p.pid for p in procs if p.poll() is None]
        pids += measure.pgid_members(daemon_pgid) if daemon_pgid else []
        ticks = {p: measure.cpu_ticks(p) for p in pids}
        delta = sum(max(0, t - prev.get(p, 0)) for p, t in ticks.items())
        cpu = round(100.0 * delta / measure.CLK_TCK / ((now - prev_t) / 1e9), 1)
        prev, prev_t = ticks, now
        # Supervision: who is up, who died, who is late.
        for i, p in enumerate(procs):
            if i in up_at:
                continue
            f = f"{ready}/ready_{i}"
            if os.path.exists(f):
                try:
                    up_at[i] = int(open(f).read())
                    continue
                except ValueError:
                    pass  # being written; next tick
            dead, late = p.poll() is not None, (now - started[i]) / 1e9 > a.up_timeout
            if (dead or late) and restarts[i] < a.max_restarts:
                if not dead:
                    p.kill()
                    p.wait()
                restarts[i] += 1
                events.append({"t": round((now - t0) / 1e9, 2), "node": i,
                               "why": f"exited ({p.returncode})" if dead else "not up in time"})
                procs[i], started[i] = start(i), now
        if all_up_ns is None and len(up_at) == a.nodes:
            all_up_ns = max(up_at.values())
        if a.mem_every and (k % a.mem_every == 1 or not samples):
            pss, tcp = round(sum(measure.pss_kb(p) for p in pids) / 1024.0, 1), tcp_connections()
        samples.append({"t": round((now - t0) / 1e9, 3), "cpu_pct": cpu, "pss_mb": pss, "tcp": tcp,
                        "pids": len(pids), "up": len(up_at), "sampler_ms": round((mono_ns() - now) / 1e6, 1)})
        k += 1
        elapsed = (mono_ns() - t0) / 1e9
        if (all_up_ns is not None and (mono_ns() - all_up_ns) / 1e9 >= a.tail) or elapsed >= a.max_window:
            break

    for p in procs:
        if p.poll() is None:
            p.send_signal(signal.SIGINT)
    deadline = time.monotonic() + 10
    for p in procs:
        try:
            p.wait(timeout=max(0.1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            p.kill()
    stop_daemon(daemon_pgid)

    result = {"variant": spec.key, "rmw": spec.rmw, "config": spec.config, "notes": spec.notes, "env": spec.env,
              "t0_ns": t0, "nodes": a.nodes, "pubs": a.pubs, "subs": a.subs, "interval_s": a.interval,
              "up_timeout_s": a.up_timeout, "max_restarts": a.max_restarts,
              "nodes_up": len(up_at), "all_up_s": round((all_up_ns - t0) / 1e9, 2) if all_up_ns else None,
              "restarts": sum(restarts), "restart_events": events, "samples": samples}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(result, f)
    peak = max(samples, key=lambda s: s["cpu_pct"])
    print(f"{spec.key}: up {len(up_at)}/{a.nodes}, all up at {result['all_up_s']} s, restarts {sum(restarts)}, "
          f"peak CPU {peak['cpu_pct']}% at {peak['t']} s, "
          f"window {samples[-1]['t']} s, sampler max "
          f"{max(s['sampler_ms'] for s in samples)} ms")


if __name__ == "__main__":
    main()
