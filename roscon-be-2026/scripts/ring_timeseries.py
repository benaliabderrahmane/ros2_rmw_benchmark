#!/usr/bin/env python3
"""Ring bring-up as a time series: N ring nodes started at once, and every --interval seconds from that instant the
total CPU % and PSS of all node processes (plus the discovery daemon, if the variant has one) and the number of
established TCP connections. One JSON per run. Runs inside the rmw-bench image (the harness is at /benchmarks/scripts).

  python3 ring_timeseries.py --variant zenoh_client --nodes 100 --out /campaign/results/ts/zenoh_client_r1.json

Variants: the harness's (rmw_matrix.BUILDERS) plus zenoh_client, the default router with every node in client mode.
Bring-up is computed like run_one.py: launch to the last node's first received message.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, "/benchmarks/scripts")
import measure  # noqa: E402
import rmw_matrix  # noqa: E402
from run_one import find_load_node, mono_ns, stop_daemon  # noqa: E402


def _zenoh_client():
    s = rmw_matrix.get_spec("zenoh_default")
    s.key, s.config = "zenoh_client", "client"
    s.env = {"ZENOH_CONFIG_OVERRIDE": 'mode="client"'}  # the router keeps its default config
    s.notes = "every node in client mode: it connects only to rmw_zenohd, which also carries the data"
    return s


def _zenoh_client_shm():
    s = _zenoh_client()
    s.key, s.config = "zenoh_client_shm", "client_shm"
    s.env = {"ZENOH_CONFIG_OVERRIDE": 'mode="client";transport/shared_memory/enabled=true'}
    s.daemon_env = {**s.daemon_env, "ZENOH_CONFIG_OVERRIDE": "transport/shared_memory/enabled=true"}  # never mode
    s.notes = "every node in client mode with shared memory; the router has shared memory too"
    return s


rmw_matrix.BUILDERS["zenoh_client"] = _zenoh_client
rmw_matrix.BUILDERS["zenoh_client_shm"] = _zenoh_client_shm


# Fast DDS tuning screen (23 Nov 2026), run on a /dev/shm cleaned of Fast DDS segments.
# Fast DDS 2.x (Jazzy, 2.14) reads only FASTRTPS_DEFAULT_PROFILES_FILE; the harness sets Fast DDS 3's
# FASTDDS_DEFAULT_PROFILES_FILE, so on Jazzy fastdds_tuned's profile is never loaded. The screen sets both names
# (fixed=True), except fastdds_tuned_clean: the campaign's Jazzy fastdds_tuned as it ran, only on a clean /dev/shm.
FASTDDS_VARIANTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fastdds_variants")


def _fastdds_variant(key, xml=None, extra_env=None, notes="", fixed=True):
    def build():
        s = rmw_matrix.get_spec("fastdds_tuned")
        s.key, s.notes = key, notes
        path = os.path.join(FASTDDS_VARIANTS, xml) if xml else s.env["FASTDDS_DEFAULT_PROFILES_FILE"]
        if fixed:
            s.env = {**s.env, "FASTDDS_DEFAULT_PROFILES_FILE": path, "FASTRTPS_DEFAULT_PROFILES_FILE": path}
            s.config_files = {"FASTRTPS_DEFAULT_PROFILES_FILE": path}
        s.env = {**s.env, **(extra_env or {})}
        return s
    return build


rmw_matrix.BUILDERS["fastdds_tuned_clean"] = _fastdds_variant(
    "fastdds_tuned_clean", fixed=False,
    notes="control: the campaign's fastdds_tuned exactly (on Jazzy its profile is not loaded), on a clean /dev/shm")
rmw_matrix.BUILDERS["fastdds_tuned_fixed"] = _fastdds_variant(
    "fastdds_tuned_fixed", notes="fastdds_tuned with its profile really loaded on Jazzy (mutation_tries=1000)")
rmw_matrix.BUILDERS["fastdds_bigbuf"] = _fastdds_variant(
    "fastdds_bigbuf", "fastdds_bigbuf.xml", notes="tuned + 16 MiB UDP send/receive socket buffers")
rmw_matrix.BUILDERS["fastdds_shmonly"] = _fastdds_variant(
    "fastdds_shmonly", extra_env={"FASTDDS_BUILTIN_TRANSPORTS": "SHM"},
    notes="tuned + shared memory as the only transport (discovery too): no UDP ports")
rmw_matrix.BUILDERS["fastdds_announce"] = _fastdds_variant(
    "fastdds_announce", "fastdds_announce.xml", notes="tuned + 10 initial announcements x 500 ms, 1 s period")


def tcp_connections():
    """Established TCP connections in this network namespace (a loopback connection shows up once per end)."""
    ends = 0
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as f:
                next(f)
                ends += sum(1 for line in f if line.split()[3] == "01")
        except OSError:
            pass
    return ends // 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=list(rmw_matrix.BUILDERS))
    ap.add_argument("--nodes", type=int, default=100)
    ap.add_argument("--window", type=float, default=30.0, help="seconds sampled from launch")
    ap.add_argument("--interval", type=float, default=0.25)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    spec = rmw_matrix.get_spec(args.variant)
    load_node = find_load_node()
    env = {**os.environ, "RMW_IMPLEMENTATION": spec.rmw, **spec.env}
    raw = f"/tmp/ts_{spec.key}"
    os.makedirs(raw, exist_ok=True)

    daemon_pgid = None
    if spec.daemon_cmd:
        d = subprocess.Popen(spec.daemon_cmd, env={**os.environ, **spec.daemon_env}, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        daemon_pgid = os.getpgid(d.pid)
        time.sleep(spec.daemon_wait_s)
        if not measure.pgid_members(daemon_pgid):
            raise SystemExit("daemon failed to start")

    # Nodes run past the sampled window, so their shutdown never shows in it.
    duration = args.window + 5
    t0 = mono_ns()
    procs = [subprocess.Popen([load_node, "--id", str(i), "--total", str(args.nodes), "--rate", "20", "--size", "256",
                               "--duration", str(duration), "--warmup", "5", "--degree", "1",
                               "--out", f"{raw}/node_{i}.json"],
                              env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             for i in range(args.nodes)]
    launch_s = (mono_ns() - t0) / 1e9

    samples, prev, prev_t = [], {}, t0
    k = 1
    while True:
        target = t0 + int(k * args.interval * 1e9)
        if target > t0 + int(args.window * 1e9):
            break
        time.sleep(max(0.0, (target - mono_ns()) / 1e9))
        now = mono_ns()
        pids = [p.pid for p in procs if p.poll() is None]
        pids += measure.pgid_members(daemon_pgid) if daemon_pgid else []
        ticks = {p: measure.cpu_ticks(p) for p in pids}
        # A pid seen for the first time contributes everything it used since it started: the start-up burst counts.
        delta = sum(max(0, t - prev.get(p, 0)) for p, t in ticks.items())
        cpu = 100.0 * delta / measure.CLK_TCK / ((now - prev_t) / 1e9)
        pss = sum(measure.pss_kb(p) for p in pids) / 1024.0
        samples.append({"t": round((now - t0) / 1e9, 3), "cpu_pct": round(cpu, 1), "pss_mb": round(pss, 1),
                        "tcp": tcp_connections(), "pids": len(pids),
                        "sampler_ms": round((mono_ns() - now) / 1e6, 1)})
        prev, prev_t = ticks, now
        k += 1

    for p in procs:
        try:
            p.wait(timeout=max(1.0, duration + 30 - (mono_ns() - t0) / 1e9))
        except subprocess.TimeoutExpired:
            p.kill()
    stop_daemon(daemon_pgid)

    first = []
    for i in range(args.nodes):
        try:
            t = json.load(open(f"{raw}/node_{i}.json")).get("t_first_recv_ns", -1)
        except (OSError, ValueError):
            continue
        if t >= 0:
            first.append(t)
    result = {"variant": spec.key, "rmw": spec.rmw, "config": spec.config, "notes": spec.notes, "env": spec.env,
              "nodes": args.nodes, "interval_s": args.interval, "window_s": args.window, "launch_s": round(launch_s, 2),
              "nodes_received": len(first),
              "bringup_s": round((max(first) - t0) / 1e9, 2) if len(first) == args.nodes else None,
              "samples": samples}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f)
    peak = max(samples, key=lambda s: s["cpu_pct"])
    print(f"{spec.key}: up {len(first)}/{args.nodes}, bring-up {result['bringup_s']} s, peak CPU {peak['cpu_pct']}% "
          f"at {peak['t']} s, PSS end {samples[-1]['pss_mb']} MB, TCP end {samples[-1]['tcp']}, "
          f"sampler max {max(s['sampler_ms'] for s in samples)} ms")


if __name__ == "__main__":
    main()
