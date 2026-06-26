# ros2_rmw_benchmark

The only RMW we tested that stays healthy at 200 nodes on one host.

This repo compares four ROS 2 RMW implementations on a single machine, localhost only, from 1 to 200 nodes, on ROS 2 Jazzy. The one under test is `rmw_unix_socket_cpp`: AF_UNIX datagram sockets for transport, plus a lock-free POSIX shared-memory registry for discovery. No DDS, no daemon, no master, no broker. We wrote it, so weigh the framing accordingly. The numbers below come out of one command, and you should run them yourself.

## What and why

A lot of ROS 2 deployments are really just many processes on one box talking to each other. On our boat that's 150+ nodes on a single host. The DDS stacks that ROS 2 ships were designed for distributed systems first, and on a dense single-host graph that design shows up as CPU burn, RAM growth, and discovery that quietly stops converging once you cross ~50–100 participants. ROS 1 had the master and TCPROS; the move to ROS 2 traded a single point of failure for a discovery protocol that, on one host at scale, costs more than people expect.

`rmw_unix_socket_cpp` takes the other route. Transport is plain AF_UNIX datagrams: the kernel loopback path without the TCP/IP stack on top of it. Discovery is a shared-memory registry that every process maps. There's no separate process to launch, nothing to keep alive, nothing to scout. That buys nothing on a multi-host network — it can't reach another machine, so cross-host goes through a bridge like Zenoh — and at small node counts the mature DDS stacks tie or beat it on raw 1:1 latency. The story here is what happens as N grows.

## The four RMWs and the matrix

| RMW | default | tuned | shm |
|---|---|---|---|
| `rmw_unix_socket_cpp` (under test) | yes | — | — |
| `rmw_cyclonedds_cpp` | yes | `cyclonedds_tuned.xml` | `cyclonedds_shm.xml` (Iceoryx + iox-roudi) |
| `rmw_fastrtps_cpp` (Fast DDS) | yes | `fastdds_tuned.xml` + Discovery Server | `fastdds_shm.xml` (data-sharing) |
| `rmw_zenoh_cpp` | yes | `zenoh_tuned` (SHM via `ZENOH_CONFIG_OVERRIDE`) | — (tuned is the SHM variant) |

Variant keys used by the scripts: `unix_socket`, `cyclonedds_default`, `cyclonedds_tuned`, `cyclonedds_shm`, `fastdds_default`, `fastdds_tuned`, `fastdds_shm`, `zenoh_default`, `zenoh_tuned`. Per-config provenance — what each flag does, why, and the source — is in [CONFIGS.md](CONFIGS.md).

## The workload

A ring of N processes, one ROS node each. Node *i* publishes a monotonic-timestamped message on `/bench/t<i>` at a fixed rate and subscribes to node *i-1*. Same QoS for everyone (reliable, keep-last-10) and the same message for every RMW. Latency is measured in C++ (rclcpp) with `CLOCK_MONOTONIC`, which is system-wide on Linux, so cross-process timestamps compare directly on one host.

Two message modes:
- **string run** — 256-byte `std_msgs/String`.
- **shm run** — fixed 64 KB `bench_nodes/FixedMsg`, sized so DDS zero-copy can engage.

The metrics we report, briefly:
- **nodes up** = fraction of N that ever received from their ring neighbour. The trust metric. A stack whose processes never came up can't be judged on RAM or latency.
- **msg delivery** = received/sent among the nodes that ran.
- **RAM as PSS** (proportional set size) — shared library pages counted once across processes. RSS double-counts shared libs in a many-process graph; PSS is the fair number.
- **CPU %** where 100 = one core.
- **discovery time** = launch to every node receiving.
- **p50 / p99 latency** in microseconds.

## Quickstart

One command. It builds the Docker image, runs both matrices, and writes the graphs and `results/system.md`:

```sh
bash scripts/run_benchmark.sh
```

Prereqs: Docker, internet (the build clones CycloneDDS, Zenoh, and `rmw_unix_socket_cpp` and compiles zenoh-c via cargo), and this repo present.

Quick run, just two node counts and the string phase:

```sh
NODES="1 10" PHASES=string bash scripts/run_benchmark.sh
```

## Results

256 B string run:

![256 B string run: nodes up, RAM, CPU, latency vs node count](results/graphs/jazzy.png)

64 KB SHM run:

![64 KB SHM run: nodes up, RAM, CPU, latency vs node count](results/graphs/jazzy_shm.png)

The headline is the 200-node column of the string run on the server host. Everything else in the curves leads here:

| RMW (200 nodes, server) | nodes up | msg delivery | total PSS MB | CPU % | p50 µs | p99 µs |
|---|---|---|---|---|---|---|
| `unix_socket` | 1.00 | 0.998 | 438.2 | 318 | 123 | 242 |
| `cyclonedds_default` | 0.14 | 0.874 | 202.0 | 26 | 203 | 318 |
| `cyclonedds_tuned` | 0.97 | 0.799 | 4509.7 | 3324.7 | 3724.9 | 452673.7 |
| `fastdds_default` | 0.27 | 0.123 | 3605.4 | 3096.7 | 32634.5 | 1229407.6 |
| `fastdds_tuned` | 0.00 | 0.00 | 1506.0 | 255 | — | — |
| `zenoh_default` | 0.98 | 0.937 | 8400.8 | 237 | 296 | 4081.6 |
| `zenoh_tuned` | 1.00 | 0.952 | 8482.5 | 248 | 296 | 8197.9 |

Cyclone's flat RAM and CPU at default are survivors-only: most of its nodes never came up, so there's little left running to measure. The Fast DDS tuned row is the Discovery Server variant, which reaches zero healthy nodes at 200 (it collapses past 50). For per-node-count tables, the 64 KB run, and the reasoning behind each row, see [RESULTS.md](RESULTS.md).

## Findings

Only `unix_socket` stays healthy at 200 nodes: all 200 up, 99.8% delivery, p50 123 µs and p99 242 µs — flat from 1 to 200 nodes — at 438 MB PSS and 318% CPU.

The DDS stacks each fail differently. Cyclone at default brings up 14% of nodes; tuned gets 195 of 200 up (97%) but delivery drops to 80%, p99 climbs to roughly 0.45 s, and it costs 4.5 GB and 3300% CPU. Fast DDS at default brings up 27% with a ~1.2 s p99; the tuned Discovery Server run reaches 0 nodes up at 200. Zenoh brings up 98% of nodes at default and all 200 when tuned, at 94–95% delivery, but p99 lands at 4–8 ms and RAM at ~8.5 GB.

At 1 and 10 nodes the picture flips in places. Cyclone and Fast DDS post lower p50 latency than `unix_socket`, and Cyclone uses far less RAM. That's the honest small-N result. The difference is that `unix_socket`'s curves stay flat while the others bend.

**The SHM caveat, plainly.** The 64 KB run lets the zero-copy paths engage: Cyclone + Iceoryx, Fast DDS data-sharing, Zenoh SHM. Comparing those against an AF_UNIX RMW on large messages is not apples-to-apples. Zero-copy avoids the payload copy by construction, so on big payloads it wins on raw transfer. That's expected and not the interesting part. We include the 64 KB run to be fair to the DDS stacks, and the finding is that SHM doesn't fix the at-scale problem. Cyclone + Iceoryx bring-up collapses past ~50 nodes and adds a fixed ~640 MB iox-roudi pool from the first node. Fast DDS data-sharing changed nothing measurable — discovery is the bottleneck, not the copy. Zenoh SHM only trimmed the tail. Where zero-copy genuinely matters is MB-scale payloads like camera and lidar frames, which are past the ~200 KB AF_UNIX datagram cap and out of scope here. We're not claiming `unix_socket` beats zero-copy on large transfers. It doesn't, and it isn't trying to.

## Related work

ROS 1 had a Unix-domain-socket transport for `ros_comm`, contributed by Tomoya Fujita, a Sony engineer (developed at Sony, used on the aibo robot). The PR — [ros/ros_comm #1510, "Unix Domain Socket Support"](https://github.com/ros/ros_comm/pull/1510) — was closed and never merged; it lives on [his fork](https://github.com/fujitatomoya/ros_comm) on branch `topic-noetic-devel-uds-support`, and there's a ROSCon 2018 talk, "aibo with ROS" ([slides](https://roscon.ros.org/2018/presentations/ROSCon2018_Aibo.pdf), [video](https://vimeo.com/293292255)). That work bypassed the TCP/IP loopback stack but was not zero-copy (it still copied through the kernel and reused TCPROS framing) and still used the ROS master for discovery. Its micro-bench on Skylake showed UDS-stream at 1.82 µs vs TCP at 3.14 µs for a 100 B message, and roughly 8% lower average end-to-end latency on a HelloWorld. ROS 1 is EOL as of May 31 2025, so it's a citable precedent, not reusable code.

As far as we can tell there is no ROS 2 RMW that uses AF_UNIX sockets, and no ROS 2 talk that cites Fujita's work as prior art — the ROS 2 world converged on shared memory (Fast DDS SHM, Cyclone + Iceoryx, `rmw_iceoryx`, Zenoh) independently. So `rmw_unix_socket_cpp` (AF_UNIX datagram + SHM discovery) sits at a distinct point in the design space, with the ROS 1 UDS work as its closest ancestor. Worth a look if you're in this area: [ZeroDDS](https://github.com/zero-objects/zero-dds), a recent pure-Rust RMW for ROS 2 ([Discourse thread](https://discourse.openrobotics.org/t/zerodds-a-pure-rust-rmw-for-ros-2-rc-3-built-against-349-real-ros-dds-pain-reports/55581), Apache-2.0, a few weeks old, release candidate).

## Reproduce and layout

`bash scripts/run_benchmark.sh` is the whole thing. Underneath:

- `bench_nodes/` — the C++ ament package: `load_node` and `msg/FixedMsg.msg`.
- `configs/` — `cyclonedds_tuned.xml`, `cyclonedds_shm.xml`, `fastdds_tuned.xml`, `fastdds_shm.xml`, `iox_roudi_config.toml`.
- `docker/` — `Dockerfile`, `entrypoint.sh`.
- `scripts/` — `run_benchmark.sh`, `run_one.py`, `rmw_matrix.py`, `measure.py`, `aggregate.py`, `plot.py`, `sysinfo.sh`, `clean.sh`.
- `results/` — `jazzy/` (256 B), `jazzy_shm/` (64 KB), `graphs/`, `system.md`.

Versions, as tested: ROS 2 Jazzy. CycloneDDS core 0.10.5 (tag) with `rmw_cyclonedds` jazzy branch, from source. `rmw_zenoh` jazzy branch (zenoh_cpp_vendor 0.2.9, Rust 1.75), from source. `rmw_fastrtps_cpp` from the Jazzy apt package, not source, to avoid ABI skew with the apt fastcdr/typesupport that `bench_nodes` and `rmw_unix_socket_cpp` link against. `rmw_unix_socket_cpp` cloned from [GitHub](https://github.com/benaliabderrahmane/rmw_unix_socket_cpp) at branch `main`. The exact CPU and RAM of the test host are in [results/system.md](results/system.md), written by `scripts/sysinfo.sh` on the benchmark machine — we don't restate them here so the README can't drift from the run.

## Honest limits

`rmw_unix_socket_cpp` is alpha and single-maintainer. It's localhost-only by design; cross-host goes through a bridge. It passes the rmw conformance suite and ~90 of its own tests, but it is not safety-certified. It has a per-message size cap of about 200 KB (the AF_UNIX datagram limit; raise `net.core.wmem_max` and `net.core.rmem_max` for larger), and it does not aim to beat shared-memory DDS at raw 1:1 latency. This benchmark is synthetic ring traffic at uniform rate and size on one host — a scaling comparison, not an absolute verdict. Nothing here generalizes to multi-host.

## See also

- [RESULTS.md](RESULTS.md) — the full writeup, per-node-count tables, both runs.
- [CONFIGS.md](CONFIGS.md) — tuned-config provenance: what, why, source, effect.
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to add an RMW or a workload.
- [LICENSE](LICENSE) — Apache-2.0.
