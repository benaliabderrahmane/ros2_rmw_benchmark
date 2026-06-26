# Results

The full writeup behind the README. If you want the headline, the README has it. This file is the methodology, every table, and a per-RMW reading of what happened.

All of it is a single SERVER run on one host, ROS 2 Jazzy. The 256-byte run lives in `results/jazzy/`, the 64 KB run in `results/jazzy_shm/`. The two graphs below come out of those directories via `scripts/plot.py`.

![256-byte ring, 1 to 200 nodes](results/graphs/jazzy.png)

![64 KB FixedMsg ring, 1 to 200 nodes](results/graphs/jazzy_shm.png)

Headline: at 200 nodes on one host, `rmw_unix_socket_cpp` is the only stack where all 200 nodes come up and stay healthy. 99.8% delivery, p50 123 us, p99 242 us, flat from 1 to 200, at 438 MB PSS and 318% CPU. The DDS stacks either don't bring their nodes up at all (Cyclone default 14% up, Fast DDS default 27% up, Fast DDS tuned 0% up) or pay for staying up with seconds-scale tail latency and gigabytes of RAM (Cyclone tuned, Zenoh). The rest of this document is the evidence for that sentence, and the places where it's messier than one sentence allows.

## Methodology

### Workload

A ring of N processes, one ROS node each. Node *i* publishes a monotonic-timestamped message on `/bench/t<i>` at a fixed rate and subscribes to node *i-1*. Node 0 closes the ring by subscribing to node *N-1*. Every node is its own OS process, so N=200 means 200 processes plus whatever discovery daemon the RMW needs.

QoS is identical for every RMW and every run: reliable, keep-last-10. The message is identical too. Two message modes:

- **string run** — 256-byte `std_msgs/String`. The ordinary small-message case, the kind of traffic a control graph actually carries.
- **shm run** — fixed 64 KB `bench_nodes/FixedMsg`. Fixed size and plain layout so the DDS zero-copy paths (Fast DDS data-sharing, Cyclone+Iceoryx, Zenoh SHM) can engage. The shared-memory section explains why this run isn't a fair fight and what we got out of it anyway.

Same ring, same rate, same QoS, same payload across all four RMWs. The only thing that changes between variants is the middleware and its config.

### Metrics

**nodes up** — the fraction of N nodes that *ever* received a message from their ring neighbour. This is the trust metric, and it's first for a reason. If a node's process launched but never received anything, its discovery never completed, and every other number for it (RAM, latency, delivery) is either missing or measured on a node that isn't doing the job. A stack that brings up 14% of its nodes can post a lovely p50 — on the 14% that came up. So before reading any latency or RAM column, read the nodes-up column. Where nodes-up is below 1.0 the row is marked **survivors-only**: the remaining numbers describe the nodes that lived, not the graph you asked for.

**msg delivery** — received divided by sent, counted only among nodes that ran. Catches the stacks that come up but then silently drop messages under load.

**discovery s** — wall-clock seconds from launch to every node having received at least once. With sub-1.0 nodes-up this never completes for the missing nodes; the number is the time for the survivors to converge.

**RAM (PSS) MB** — proportional set size, total across all processes including any discovery daemon. PSS counts each shared-library page once and splits it across the processes mapping it, which is the honest way to add up RAM for a many-process graph. RSS would count librclcpp, the RMW, and the DDS libraries once *per process* and report a number two-to-three times too large at 200 nodes. We report total PSS, and separately the daemon's own PSS where a stack runs one (the `daemon PSS` column), so you can see how much of the bill is fixed overhead.

**CPU %** — 100 equals one fully-used core. 318% is roughly three cores. Summed across all processes.

**p50 / p99 us** — median and 99th-percentile end-to-end latency in microseconds, publisher timestamp to subscriber receipt.

### Why CLOCK_MONOTONIC

Latency is measured in C++ inside the rclcpp nodes using `CLOCK_MONOTONIC`. On Linux that clock is system-wide: two processes reading it get values from the same monotonic base, so a timestamp written by the publisher and read by the subscriber compare directly with no clock-sync step. That only holds because everything is on one host, which is the entire scope of this benchmark. Nothing here measures or claims anything about cross-host timing.

### Environment

ROS 2 Jazzy. CycloneDDS core 0.10.5 (tag) with `rmw_cyclonedds` jazzy branch built from source. `rmw_zenoh` jazzy branch (zenoh_cpp_vendor 0.2.9, Rust 1.75) built from source. `rmw_fastrtps_cpp` from the Jazzy apt package rather than source — building Fast DDS from source risks ABI skew against the apt fastcdr/typesupport that `bench_nodes` and `rmw_unix_socket_cpp` link against, and that skew produces failures that look like benchmark results but aren't. `rmw_unix_socket_cpp` is cloned from [github.com/benaliabderrahmane/rmw_unix_socket_cpp](https://github.com/benaliabderrahmane/rmw_unix_socket_cpp) at branch `main`.

The exact CPU model and RAM of the test host are in `results/system.md`, written by `scripts/sysinfo.sh` on the machine that ran the benchmark. We don't reprint them here because they're machine-specific; read that file for the hardware these numbers came off.

## The full tables

Both runs, one table per metric. Rows are variants, columns are node counts (1 / 10 / 50 / 100 / 200). Numbers are taken verbatim from `results/jazzy/` and `results/jazzy_shm/`. Cells in a row whose nodes-up dropped below 1.0 at that node count are **survivors-only** — the value describes the nodes that came up, not the full N. Where a p99 ran into the millions of microseconds we also render it as seconds in parentheses, because "452673.7" doesn't read as half a second at a glance.

### 256-byte run (`results/jazzy/`)

**nodes up** (recv/N)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_default | 1.0 | 1.0 | 0.6 | 0.3 | 0.14 |
| cyclonedds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.97 |
| fastdds_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.27 |
| fastdds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| zenoh_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.98 |
| zenoh_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

**msg delivery** (recv/sent among nodes that ran)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 0.998 |
| cyclonedds_default | 1.0 | 1.0 | 0.937 (survivors-only) | 0.937 (survivors-only) | 0.874 (survivors-only) |
| cyclonedds_tuned | 1.0 | 1.0 | 0.998 | 0.988 | 0.799 (survivors-only) |
| fastdds_default | 1.0 | 1.0 | 0.978 | 0.971 | 0.123 (survivors-only) |
| fastdds_tuned | 1.0 | 0.965 | 0.851 | 0.297 | 0.0 (survivors-only) |
| zenoh_default | 1.0 | 1.0 | 0.999 | 0.992 | 0.937 (survivors-only) |
| zenoh_tuned | 1.0 | 1.0 | 0.998 | 0.99 | 0.952 |

**discovery (s)**

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 0.1 | 0.08 | 0.14 | 0.23 | 0.55 |
| cyclonedds_default | 0.07 | 0.08 | 0.27 (survivors-only) | 0.26 (survivors-only) | 0.27 (survivors-only) |
| cyclonedds_tuned | 0.07 | 0.08 | 0.31 | 1.53 | 27.18 (survivors-only) |
| fastdds_default | 0.09 | 0.22 | 1.74 | 3.29 | 76.46 (survivors-only) |
| fastdds_tuned | 0.09 | 1.19 | 5.09 | 22.85 | None (survivors-only) |
| zenoh_default | 0.08 | 0.09 | 0.32 | 1.06 | 6.06 (survivors-only) |
| zenoh_tuned | 0.08 | 0.09 | 0.38 | 1.14 | 6.17 |

**RAM (total PSS, MB, daemon included)**

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 46.9 | 65.5 | 141.7 | 238.6 | 438.2 |
| cyclonedds_default | 14.4 | 51.3 | 202.5 (survivors-only) | 202.5 (survivors-only) | 202.0 (survivors-only) |
| cyclonedds_tuned | 14.4 | 51.1 | 372.8 | 1113.2 | 4509.7 (survivors-only) |
| fastdds_default | 25.5 | 108.6 | 741.1 | 2135.5 | 3605.4 (survivors-only) |
| fastdds_tuned | 39.6 | 120.7 | 736.1 | 876.2 | 1506.0 (survivors-only) |
| zenoh_default | 43.1 | 91.4 | 696 | 2300 | 8400.8 (survivors-only) |
| zenoh_tuned | 42.5 | 91.6 | 706.8 | 2310.8 | 8482.5 |

Cyclone default's RAM is flat from 50 nodes on because most of the nodes never came up — that 202 MB is the survivors, not 200 working nodes. Fast DDS tuned runs a Discovery Server; its daemon PSS is 18.8 / 15.4 / 27.2 / 43.8 / 20.6 MB at 1/10/50/100/200. Zenoh runs the `rmw_zenohd` router; its daemon PSS is 29 / 23.9 / 27.6 / 34.6 / 50.6 MB (default) and 28.8 / 23.9 / 27.8 / 34.6 / 50.8 MB (tuned). unix_socket and the Cyclone variants run no daemon (the daemon PSS column is 0).

**CPU (%)**

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.7 | 16 | 80 | 157 | 318 |
| cyclonedds_default | 0.7 | 10 | 26 (survivors-only) | 29 (survivors-only) | 26 (survivors-only) |
| cyclonedds_tuned | 0.7 | 10 | 48 | 96 | 3324.7 (survivors-only) |
| fastdds_default | 1 | 14 | 80 | 196 | 3096.7 (survivors-only) |
| fastdds_tuned | 1 | 12 | 67 | 163 | 255 (survivors-only) |
| zenoh_default | 0.7 | 14 | 66 | 132 | 237 (survivors-only) |
| zenoh_tuned | 1 | 14 | 67 | 130 | 248 |

**p50 latency (us)**

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 127 | 190 | 169 | 135 | 123 |
| cyclonedds_default | 68 | 216 | 211 (survivors-only) | 215 (survivors-only) | 203 (survivors-only) |
| cyclonedds_tuned | 77 | 241 | 242 | 216 | 3724.9 (survivors-only) |
| fastdds_default | 114 | 310 | 292 | 288 | 32634.5 (survivors-only) |
| fastdds_tuned | 114 | 322 | 288 | 279 | None (survivors-only) |
| zenoh_default | 91 | 483 | 424 | 360 | 296 (survivors-only) |
| zenoh_tuned | 90 | 477 | 421 | 352 | 296 |

**p99 latency (us)**

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 165 | 255 | 237 | 239 | 242 |
| cyclonedds_default | 70 | 325 | 319 (survivors-only) | 324 (survivors-only) | 318 (survivors-only) |
| cyclonedds_tuned | 113 | 401 | 338 | 346 | 452673.7 (~0.45 s, survivors-only) |
| fastdds_default | 179 | 368 | 398 | 467 | 1229407.6 (~1.2 s, survivors-only) |
| fastdds_tuned | 116 | 422 | 404 | 161728 (~0.16 s) | None (survivors-only) |
| zenoh_default | 110 | 571 | 581 | 564 | 4081.6 (survivors-only) |
| zenoh_tuned | 108 | 580 | 572 | 569 | 8197.9 |

### 64 KB SHM run (`results/jazzy_shm/`)

This run swaps in the zero-copy variants where each stack has one: `cyclonedds_shm` (Cyclone tuned + Iceoryx/iox-roudi), `fastdds_shm` (data-sharing), `zenoh_tuned` (SHM). It is not apples-to-apples — see the shared-memory section. We collected the full sweep for unix_socket and the partial sweeps the other stacks managed before falling over; missing cells are runs that didn't complete or weren't collected.

**nodes up** (recv/N)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_tuned | — | — | — | — | 1.0 |
| cyclonedds_shm | 1.0 | 0.8 | 1.0 | 0.2 | 0.06 |
| fastdds_default | — | — | — | — | 0.31 |
| fastdds_shm | — | — | — | — | 0.23 |
| zenoh_default | — | — | — | — | 0.99 |
| zenoh_tuned | — | — | — | — | 0.96 |

**msg delivery**

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 0.999 | 0.998 |
| cyclonedds_tuned | — | — | — | — | 0.631 (survivors-only) |
| cyclonedds_shm | 1.0 | 0.889 (survivors-only) | 0.999 | 0.71 (survivors-only) | 0.73 (survivors-only) |
| zenoh_default | — | — | — | — | 0.765 (survivors-only) |
| zenoh_tuned | — | — | — | — | 0.717 (survivors-only) |

**discovery (s)**

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 0.07 | 0.07 | 0.13 | 0.3 | 0.7 |
| cyclonedds_tuned | — | — | — | — | 19.97 (survivors-only) |
| cyclonedds_shm | 0.07 | — | 0.46 | 1.03 (survivors-only) | 1.29 (survivors-only) |
| zenoh_default | — | — | — | — | 16.89 (survivors-only) |
| zenoh_tuned | — | — | — | — | 14.73 (survivors-only) |

**RAM (total PSS, MB)**

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 46.7 | 66.2 | 146.9 | 247.9 | 451.7 |
| cyclonedds_tuned | — | — | — | — | 4912.4 (survivors-only) |
| cyclonedds_shm | 662.4 | ~700 | 1061 | 926 (survivors-only) | 817 (survivors-only) |
| zenoh_default | — | — | — | — | 11108.9 (survivors-only) |
| zenoh_tuned | — | — | — | — | 11987 (survivors-only) |

The Iceoryx daemon (iox-roudi) carries a fixed memory pool: its PSS is ~648 / 645 / 636 / 636 / 642 MB at 1/10/50/100/200. That ~640 MB is there from the first node and barely moves — it's the cost of having Iceoryx at all, before any payload flows.

**latency (us), 200 nodes**

| variant | p50 | p99 |
|---|---|---|
| unix_socket (200) | 103 | 494 |
| cyclonedds_tuned (200) | 198 | 963978.7 (~0.96 s, survivors-only) |
| zenoh_default (200) | — | 2247848 (~2.25 s, survivors-only) |
| zenoh_tuned (200) | — | 1772443 (~1.77 s, survivors-only) |

unix_socket's full p50/p99 across the SHM sweep: 202/534, 118/453, 100/348, 88/276, 103/494 at 1/10/50/100/200. Cyclone tuned's CPU at 200 was 1777%.

## What the numbers say

### rmw_unix_socket_cpp

The latency curve is flat. p50 sits between 123 and 190 us and p99 between 165 and 255 us across the entire sweep, in both runs, regardless of node count. That flatness is the whole point. There's no discovery storm and no per-participant index that grows with N, because discovery is a lock-free shared-memory registry and transport is one AF_UNIX datagram socket per link. RAM grows linearly and stays modest — 438 MB total PSS for 200 processes, no daemon. CPU at 200 is 318%, about three cores, which is real work but not the runaway the tuned DDS stacks hit. Delivery is 1.0 everywhere except 0.998 at 200 nodes, a handful of dropped messages out of the whole ring.

At N=1 it does *not* win on latency. Cyclone's 68 us p50 beats unix_socket's 127 us, and Zenoh and Fast DDS sit in the same neighbourhood. The mature stacks are well-optimised for the small-graph case. The unix_socket advantage is entirely a scaling story: it's the only stack whose 200-node numbers look like its 1-node numbers.

### cyclonedds_default

Fine to 10 nodes, then it falls off a cliff. At 50 nodes only 60% of nodes come up, at 100 nodes 30%, at 200 nodes 14%. Every number past 50 is survivors-only, which is why its RAM and CPU look deceptively flat (~202 MB, ~26% CPU) from 50 nodes on — those are the few dozen nodes that made it, not 200 working nodes. The default loopback discovery does not survive ~100+ participants on one host.

### cyclonedds_tuned

The tuning (`cyclonedds_tuned.xml`: lo-only, SPDP multicast only, no participant index, 65500-byte max message — see CONFIGS.md) does fix the bring-up: 100% of nodes up through 100, 97% at 200. The cost is steep. Discovery at 200 takes 27.18 s. RAM climbs to 4.5 GB. CPU hits 3324%. Delivery drops to 80%. And the tail is gone — p99 at 200 is 452673.7 us, about 0.45 s. So the choice Cyclone offers at 200 nodes is "most nodes never start" (default) or "they start, but a fifth of messages are lost and the worst case is half a second" (tuned). Neither is a healthy 200-node graph.

### fastdds_default

Holds delivery and bring-up cleanly to 100 nodes — 100% up, ~97% delivery, p99 under 500 us — then collapses at 200: only 27% of nodes up, 12% delivery on those, p99 1229407.6 us (~1.2 s). Simple discovery has a hard ceiling around 119 participants per domain on one host, and 200 nodes runs straight into it.

### fastdds_tuned

The Discovery Server variant (`fastdds_tuned.xml` plus `fastdds discovery`, mutation_tries raised to 1000 — provenance and the eProsima #5767 reference are in CONFIGS.md). It was supposed to get past the simple-discovery ceiling. Instead the Discovery Server itself goes unresponsive past ~50 nodes, and tuned ended up *worse* than default beyond that point: delivery already down to 30% at 100 nodes with a 161728 us (~0.16 s) p99, and **0 nodes up at 200** — discovery never returns, latency is unmeasurable (None). The honest read is that the recommended fix for Fast DDS at scale didn't work for this workload.

### zenoh_default

Brings up the graph: 98% of nodes at 200, 94% delivery. One of only two configurations besides unix_socket that gets near-full bring-up at 200. The price is RAM and tail latency. RAM at 200 is 8.4 GB. p99 at 200 is 4081.6 us — about 4 ms, roughly 17x worse than unix_socket's 242 us tail, though far better than the seconds-scale tails on the collapsing stacks. Zenoh always needs the `rmw_zenohd` router daemon because its default config disables multicast scouting.

### zenoh_tuned

Same as default with shared memory enabled on the router and sessions (via `ZENOH_CONFIG_OVERRIDE`, no editing the shipped json5 — see CONFIGS.md). SHM nudged things slightly: 100% up at 200 (vs 98%), 95% delivery, but the p99 at 200 went the wrong way (8197.9 us, ~8 ms) and RAM was unchanged at 8.5 GB. On 256-byte messages there's nothing for zero-copy to save, so this is within run-to-run noise on a stack that's already RAM-bound.

## Shared memory

The 64 KB run exists to be fair to the DDS stacks, and it comes with a caveat that has to be stated plainly: **comparing zero-copy shared memory against an AF_UNIX datagram RMW on large messages is not apples-to-apples.** Zero-copy avoids the payload copy by construction. On a 64 KB (or larger) message it will win on raw transfer, because it isn't moving the bytes — it's handing over a pointer into a shared segment. That's expected and it's not the interesting result. We are not claiming, and the numbers do not show, that unix_socket beats zero-copy on large transfers. Where zero-copy genuinely earns its keep is megabyte-scale traffic — camera frames, lidar scans — and that's above the ~200 KB AF_UNIX datagram cap and out of scope for this benchmark entirely.

What the SHM run *does* show is that turning on zero-copy doesn't fix the problem the DDS stacks have at scale, because the bottleneck is discovery, not payload copying.

- **cyclonedds_shm** (Iceoryx + iox-roudi): adds a fixed ~640 MB iox-roudi memory pool that's present from the very first node, and the bring-up collapses past ~50 nodes — 20% of nodes up at 100, 6% at 200. For this many-small-process workload it's a net negative: you pay 640 MB up front and most of your nodes still don't start. `iox_roudi_config.toml` sizes the mempools (128 KB chunks) for the test; the limit is RouDi's runtime, not the pool sizing.
- **fastdds_shm** (data-sharing AUTOMATIC): no measurable difference from `fastdds_default` at 64 KB. Bring-up still collapses at 200 (31% up for default, 23% for data-sharing). Data-sharing changes how the payload is delivered; it does nothing for the discovery ceiling, which is what kills Fast DDS at 200.
- **zenoh_tuned** (SHM): trimmed the p99 tail and CPU a little versus zenoh_default at 200, and shaved nothing off RAM (~11 GB on the SHM run). Discovery time and bring-up are essentially unchanged.

So zero-copy is the right tool for big payloads, and none of these stacks is wrong to use it. It just isn't the thing standing between them and a healthy 200-node graph on one host. The thing standing in the way is discovery, and SHM doesn't touch discovery.

## Honest limits

`rmw_unix_socket_cpp` is alpha and single-maintainer. It is localhost-only by design — cross-host traffic has to go through a bridge such as Zenoh, and nothing in this benchmark says anything about multi-host behaviour. It passes the rmw conformance suite and about 90 of its own tests, but it is not safety-certified. It has a per-message size cap of roughly 200 KB (the AF_UNIX datagram limit; raise `net.core.wmem_max` / `net.core.rmem_max` for larger), which is why the SHM run tops out at 64 KB and why MB-scale messages are out of scope. And it does not aim to beat shared-memory DDS at raw 1:1 latency — at N=1 it doesn't.

The benchmark itself is synthetic: a ring of identical nodes publishing fixed-size messages at a uniform rate on one host. It's a scaling comparison, not an absolute verdict on any of these middlewares. Real graphs have uneven fan-out, mixed message sizes, and bursty traffic, and they may stress these stacks differently. Treat the 200-node result as what it is — evidence that on one host, with this workload, only one of these four stacks brings up and keeps healthy a 200-node graph — and not as a claim that it's the best RMW for every job.

For the hardware these numbers came off, see `results/system.md`. For the tuned-config provenance and the issue references behind each `*_tuned` / `*_shm` variant, see `CONFIGS.md`. To reproduce, `bash scripts/run_benchmark.sh`.
