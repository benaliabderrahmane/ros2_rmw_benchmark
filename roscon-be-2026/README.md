# ROSCon Belgium 2026: the talk's benchmarks

The benchmarks behind the talk *rmw_unix_socket_cpp: A Custom ROS 2 Middleware for Complex Single-Host Systems*
(ROSCon Belgium, Nivelles, 26 November 2026). One script per benchmark slide: run it and you get the slide's figure
from your own machine. We wrote `rmw_unix_socket_cpp` and this benchmark, so keep that in mind, and please tell us
what you measure.

| Slide | Script | As on the slide | Quick look |
|---|---|---|---|
| We hoped Zenoh would fix it (ROS 2 Jazzy) | [`reproduce/zenoh-jazzy.sh`](reproduce/zenoh-jazzy.sh) | ~1 h 45 min | `PARTS="2 3"`: ~15 min |
| 200 nodes started at once (ROS 2 Lyrical) | [`reproduce/200-nodes.sh`](reproduce/200-nodes.sh) | ~2.7 h | `RUNS=1 VARIANTS="unix_socket zenoh_default"` |
| Latency, and CPU at the same load (ROS 2 Lyrical) | [`reproduce/latency-cpu.sh`](reproduce/latency-cpu.sh) | ~4.5 h | `RUNS=1`: ~55 min |

```bash
git clone https://github.com/benaliabderrahmane/ros2_rmw_benchmark && cd ros2_rmw_benchmark/roscon-be-2026
reproduce/200-nodes.sh            # or zenoh-jazzy.sh, latency-cpu.sh; results land in results-local/
```

Each script builds its images, runs every case in its own container, and draws the slide's figure inside the image.
`DISTRO=jazzy` (or `lyrical`) switches the distro where it makes sense; the header of each script lists its knobs.

## What is built

- **Benchmark image** ([`docker/Dockerfile.ring`](docker/Dockerfile.ring)): `ros:<distro>-ros-base`, every competitor
  from the distro's own apt (Lyrical: Fast DDS 3.6.2 / rmw_fastrtps_cpp 9.4.10, Cyclone DDS 11.0.1 / rmw_cyclonedds_cpp
  4.1.5 + iceoryx 2.0.6, rmw_zenoh_cpp 0.10.6; Jazzy: Fast DDS 2.14.7 / 8.4.5, Cyclone DDS 0.10.5 / 2.2.4,
  rmw_zenoh_cpp 0.2.13), and `rmw_unix_socket_cpp` from source at the talk's commit (`bench/v0.6.0-rc`, e9847f5; set
  `UNIX_SOCKET_REF=v0.6.0 UNIX_SOCKET_VERSION=0.6.0 UNIX_SOCKET_SHA=` for the release).
- **performance_test image** ([`docker/Dockerfile.perf`](docker/Dockerfile.perf)): the benchmark image plus Apex
  performance_test, 2.4.0 from source on Lyrical (no release there), the apt package on Jazzy (2.3.0).
- **The 200-node node** ([`scripts/ts200/src`](scripts/ts200/src)): one ROS node per process with 5 publishers and 5
  subscriptions, built inside the image.

Configs ([`configs/lyrical`](configs/lyrical), [`configs/jazzy`](configs/jazzy)): each competitor in its default
configuration and in its tuned or shared-memory one (Cyclone DDS tuned XML; Cyclone DDS + iceoryx; Fast DDS
`mutation_tries=1000`; Fast DDS data sharing with loaned messages; Zenoh with shared memory; Zenoh in client mode
behind its router). `rmw_unix_socket_cpp` has no configuration.

## Method

- **200 nodes** ([`scripts/ts200.py`](scripts/ts200.py), [`scripts/run_ts200.sh`](scripts/run_ts200.sh)): 200
  processes started at once; a node that is not receiving on all 5 topics within 120 s is restarted, 3 times at most;
  every RMW runs 10 min; CPU and memory read from the host, from the container's cgroup
  ([`scripts/cgroup_sampler.py`](scripts/cgroup_sampler.py)); medians of 3 runs.
- **Latency and CPU** ([`scripts/gen_t5_specs.py`](scripts/gen_t5_specs.py), [`runners/run_case.py`](runners/run_case.py)):
  performance_test with the rclcpp single-threaded executor, publisher and subscribers in separate processes, 30 s per
  case with the first 5 s dropped, fixed rates (1-64 KiB at 1 kHz, 256 KiB at 500 Hz, 1 MiB at 100 Hz, 4-8 MiB at
  30 Hz); medians of 5 runs. The CPU figure is the cost of carrying that fixed load, not a maximum throughput.
- **Ring** (the repository's own harness, [`../scripts`](../scripts)): N processes in a ring; the slide uses its 64 KB
  phase at 100 processes.

## Host

The talk's numbers come from an AMD Ryzen 7 5700X (8 cores, 16 threads, 31 GB), Linux 6.8, with
`net.core.rmem_max` 2 GB and `net.core.wmem_max` 48 MB (`sudo sysctl -w net.core.rmem_max=2147483647
net.core.wmem_max=50331648`); `net.unix.max_dgram_qlen` 4096 is set inside every container. The Lyrical campaign
(17-21 Nov) ran on a tuned host (CPU governor `performance`, deep idle states off, other services paused); the Jazzy
quick runs (24 Nov) ran with the host's defaults, so their absolute CPU is higher. Each container is capped at 22 GB.

## The talk's results

Summaries only, in [`results/`](results): `lyrical-200-nodes/` and `jazzy-200-nodes/` (summary.json and the slide
figures), `performance_test-lyrical/` (perf_test.csv/.md, ring.csv/.md, the iRobot suite's tables and the slide
figures), `jazzy-quick/summary.json` (the Zenoh slide's big-message and shared-memory numbers) and
`fastdds-screen-jazzy/` (Fast DDS tunings tried at 200 nodes on Jazzy: none brought all 200 up).

## Caveats

- On Jazzy, Fast DDS 2.x reads its XML profile only from `FASTRTPS_DEFAULT_PROFILES_FILE`; the harness sets Fast DDS 3's
  `FASTDDS_DEFAULT_PROFILES_FILE`, so Fast DDS's tuned and shared-memory variants run with its defaults on Jazzy (the
  Jazzy figure labels it "Fast DDS (default)"). Lyrical's Fast DDS 3 reads the variable the harness sets.
- One machine, one kernel, our harness: treat the numbers as a starting point and measure your own system.
