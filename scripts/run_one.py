#!/usr/bin/env python3
"""Run ONE (variant, node-count) benchmark point and emit a result JSON.

  python3 run_one.py --variant cyclonedds_tuned --nodes 100 --outdir results/raw

Steps: start the variant's discovery daemon (if any) -> launch N ring nodes ->
let discovery settle -> sample steady-state RAM (PSS/RSS) + CPU -> wait for the
run to finish -> aggregate per-node JSONs into discovery time, delivery ratio,
and pooled latency percentiles.

CLOCK_MONOTONIC is shared across processes on Linux, so the orchestrator's t0
and each node's recorded timestamps are directly comparable.
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure          # noqa: E402
import rmw_matrix       # noqa: E402


def mono_ns():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC)


def find_load_node():
    if os.environ.get("BENCH_LOAD_NODE"):
        return os.environ["BENCH_LOAD_NODE"]
    try:
        prefix = subprocess.check_output(
            ["ros2", "pkg", "prefix", "bench_nodes"], text=True).strip()
        path = os.path.join(prefix, "lib", "bench_nodes", "load_node")
        if os.path.exists(path):
            return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    raise SystemExit(
        "cannot find the load_node benchmark binary. Build the workspace and "
        "source its install/setup.bash, or set BENCH_LOAD_NODE to the binary path.")


def percentile(values, p):
    # Linear interpolation between the two samples straddling rank p (p in 0..1).
    if not values:
        return None
    s = sorted(values)
    rank = (len(s) - 1) * p
    lo = int(rank)
    hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (rank - lo), 1)


def stop_daemon(pgid):
    if pgid is None:
        return
    for sig in (signal.SIGINT, signal.SIGKILL):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            return
        time.sleep(1.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=list(rmw_matrix.BUILDERS))
    ap.add_argument("--nodes", type=int, required=True)
    ap.add_argument("--rate", type=float, default=20.0)
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--duration", type=float, default=20.0)
    ap.add_argument("--warmup", type=float, default=3.0)
    ap.add_argument("--settle", type=float, default=6.0, help="wait before sampling RAM/CPU")
    ap.add_argument("--cpu-window", type=float, default=3.0)
    ap.add_argument("--fixed", action="store_true",
                    help="send a fixed-size 64 KB message instead of a string, so the "
                         "DDS zero-copy shared-memory paths can engage")
    ap.add_argument("--degree", type=int, default=1,
                    help="senders each node subscribes to (1 = ring, >1 = fan-out)")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    if args.duration < args.settle + args.cpu_window + 2:
        print(f"WARNING: duration={args.duration}s is tight vs settle+cpu_window; "
              f"sampling may overlap node shutdown", file=sys.stderr)

    spec = rmw_matrix.get_spec(args.variant)
    load_node = find_load_node()

    outdir = Path(args.outdir)
    raw_dir = outdir / f"raw_{spec.key}_n{args.nodes}"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Env passed to every node process: the RMW choice plus the variant's extra vars.
    node_env = os.environ.copy()
    node_env["RMW_IMPLEMENTATION"] = spec.rmw
    node_env.update(spec.env)

    print(f"=== {spec.key}  ({spec.rmw}, {spec.config})  N={args.nodes} ===")
    if spec.notes:
        print(f"  config: {spec.notes}")

    # 1. Optional daemon (Zenoh router, or Iceoryx iox-roudi for Cyclone SHM). Launch it
    #    in its own session so we can measure + kill the real server child, not
    #    just the wrapper/launcher that spawned it.
    daemon = None
    daemon_pgid = None
    if spec.daemon_cmd:
        daemon_env = os.environ.copy()
        daemon_env.update(spec.daemon_env)
        print(f"  daemon: {' '.join(spec.daemon_cmd)}")
        daemon = subprocess.Popen(spec.daemon_cmd, env=daemon_env, start_new_session=True,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        daemon_pgid = os.getpgid(daemon.pid)
        time.sleep(spec.daemon_wait_s)
        if not measure.pgid_members(daemon_pgid):
            raise SystemExit("daemon failed to start (no live process in its group)")

    # 2. Launch N ring nodes.
    t0 = mono_ns()
    procs = []
    for i in range(args.nodes):
        out = raw_dir / f"node_{i}.json"
        cmd = [load_node, "--id", str(i), "--total", str(args.nodes),
               "--rate", str(args.rate), "--size", str(args.size),
               "--duration", str(args.duration), "--warmup", str(args.warmup),
               "--degree", str(args.degree), "--out", str(out)]
        if args.fixed:
            cmd.append("--fixed")
        p = subprocess.Popen(cmd, env=node_env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(p)
    launch_elapsed = (mono_ns() - t0) / 1e9
    print(f"  launched {args.nodes} nodes in {launch_elapsed:.2f}s")

    # 3. Let discovery settle, then sample steady-state RAM + CPU.
    time.sleep(args.settle)
    alive = [p.pid for p in procs if p.poll() is None]
    daemon_pids = measure.pgid_members(daemon_pgid) if daemon_pgid else []
    cpu_total = measure.sample_cpu(alive + daemon_pids, args.cpu_window)
    cpu_daemon = measure.sample_cpu(daemon_pids, 0.5) if daemon_pids else 0.0
    mem_nodes = measure.sample_memory(alive)
    mem_daemon = measure.sample_memory(daemon_pids) if daemon_pids else {"pss_mb": 0.0, "rss_mb": 0.0}
    print(f"  steady-state: PSS={mem_nodes['pss_mb']}MB(+{mem_daemon['pss_mb']} daemon)  "
          f"CPU={cpu_total}%")

    # 4. Wait for the run to finish; kill stragglers.
    deadline = time.monotonic() + args.duration + 60
    for p in procs:
        try:
            p.wait(timeout=max(1.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            p.kill()
    stop_daemon(daemon_pgid)

    # 5. Aggregate per-node results.
    first_recv = []
    total_sent = total_recv = 0
    pooled_lat = []
    nodes_received = 0
    for i in range(args.nodes):
        try:
            d = json.loads((raw_dir / f"node_{i}.json").read_text())
        except (OSError, json.JSONDecodeError):
            continue
        total_sent += d.get("n_sent", 0)
        total_recv += d.get("n_recv", 0)
        pooled_lat.extend(d.get("latencies_us", []))
        if d.get("t_first_recv_ns", -1) >= 0:
            nodes_received += 1
            first_recv.append(d["t_first_recv_ns"])

    discovery_s = round((max(first_recv) - t0) / 1e9, 2) if first_recv else None
    n = args.nodes

    # If discovery took longer than the settle wait, the RAM/CPU sample may have
    # caught discovery still in progress rather than steady state.
    sampling_suspect = discovery_s is not None and discovery_s > args.settle
    if sampling_suspect:
        print(f"  discovery ({discovery_s}s) > settle ({args.settle}s); "
              f"RAM/CPU sample may include discovery transient", file=sys.stderr)
    # Expected receives per node = sent * eff_degree, since each node subscribes
    # to eff_degree senders. load_node applies this SAME clamp, so keep the two in
    # sync or the delivery ratio below comes out wrong.
    eff_degree = max(1, min(args.degree, n - 1))
    result = {
        "variant": spec.key, "rmw": spec.rmw, "config": spec.config,
        "msg": "fixed64k" if args.fixed else "string",
        "nodes": n, "rate_hz": args.rate, "degree": eff_degree,
        "size_bytes": 65536 if args.fixed else args.size,
        "duration_s": args.duration, "warmup_s": args.warmup,
        "launch_elapsed_s": round(launch_elapsed, 2),
        "discovery_time_s": discovery_s,
        "sampling_during_discovery": sampling_suspect,
        "nodes_received": nodes_received,
        "delivery_ratio_nodes": round(nodes_received / n, 3) if n else 0.0,
        "delivery_ratio_msgs": round(total_recv / (total_sent * eff_degree), 3) if total_sent else 0.0,
        "ram_node_pss_mb": mem_nodes["pss_mb"],
        "ram_node_rss_mb": mem_nodes["rss_mb"],
        "ram_daemon_pss_mb": mem_daemon["pss_mb"],
        "ram_total_pss_mb": round(mem_nodes["pss_mb"] + mem_daemon["pss_mb"], 1),
        "ram_pss_per_node_mb": round(mem_nodes["pss_mb"] / n, 2) if n else 0.0,
        "cpu_total_pct": cpu_total,
        "cpu_daemon_pct": cpu_daemon,
        # max(0,...): cpu_total and cpu_daemon come from separate sampling windows,
        # so the subtraction can go slightly negative; clamp it.
        "cpu_per_node_pct": round(max(0.0, cpu_total - cpu_daemon) / n, 2) if n else 0.0,
        "lat_p50_us": percentile(pooled_lat, 0.50),
        "lat_p99_us": percentile(pooled_lat, 0.99),
        "lat_mean_us": round(sum(pooled_lat) / len(pooled_lat), 1) if pooled_lat else None,
        "lat_max_us": round(max(pooled_lat), 1) if pooled_lat else None,
        "lat_samples": len(pooled_lat),
        "config_files": spec.config_files,
        "notes": spec.notes,
    }

    out_path = outdir / f"result_{spec.key}_n{n}.json"
    out_path.write_text(json.dumps(result, indent=2))
    shutil.rmtree(raw_dir, ignore_errors=True)

    print(f"  discovery={discovery_s}s  delivery={result['delivery_ratio_msgs']}  "
          f"p50={result['lat_p50_us']}us p99={result['lat_p99_us']}us  -> {out_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
