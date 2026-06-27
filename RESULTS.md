# Results

This is the full writeup behind the README. If you only want the headline, the README has it. This file has the method, every table, and a short plain read of what each RMW did.

Everything here is one run on one host, ROS 2 Jazzy, localhost only. The 256-byte run is in `results/jazzy/`. The 64 KB run is in `results/jazzy_shm/`. The two graphs below come from those directories.

![256-byte ring, 1 to 200 nodes](results/graphs/jazzy.png)

![64 KB FixedMsg ring, 1 to 200 nodes](results/graphs/jazzy_shm.png)

Short version: at 200 nodes on one host, `rmw_unix_socket_cpp` is the only stack where all 200 nodes start and stay healthy. All 200 up, 99.8% delivery, p50 123 us, p99 230 us, flat from 1 to 200 nodes, at 405 MB RAM and 318% CPU. The DDS stacks do one of two things. Either they fail to start their nodes (Cyclone default 14.5% up, both Fast DDS configs ~27% up at 200). Or they stay up but pay a high price: tail latency from hundreds of milliseconds up to seconds, and RAM in the gigabytes (Cyclone tuned, Zenoh). Zenoh comes closest on bring-up (98-99% up) but at single-digit-ms tails and ~8.5 GB. The rest of this file is the evidence.

## Methodology

### Workload

A ring of N processes, one ROS node each. Node *i* sends a message on `/bench/t<i>` at a fixed rate and subscribes to node *i-1*. Node 0 closes the ring by subscribing to node *N-1*. Each node is its own OS process. So N=200 means 200 processes, plus any discovery daemon the RMW needs.

QoS is the same for every RMW and every run: reliable, keep-last-10. The message is the same too. There are two message sizes:

- The **string** run: a 256-byte `std_msgs/String`. This is the small-message case.
- The **shm** run: a fixed 64 KB `bench_nodes/FixedMsg`. This is a fixed-size type. The DDS zero-copy paths need a fixed-size type before they turn on. The point of this run is to be fair to the DDS stacks (see the shared-memory section).

Latency is measured in C++ (rclcpp) using `CLOCK_MONOTONIC`. That clock only moves forward and is not affected by NTP steps or wall-clock changes. The publisher stamps the message with the monotonic time. The subscriber reads the monotonic time when the message arrives and takes the difference. This only works because everything is on one host. Nothing here measures cross-host timing.

### Test host

All numbers were measured on one CI box:

| field | value |
|---|---|
| cpu | Intel Xeon Silver 4216 @ 2.10GHz |
| logical cpus | 32 |
| ram | 45 GiB |
| os | Ubuntu 24.04.4 LTS |
| kernel | Linux 6.8 |
| /dev/shm | 23G |
| net.core.wmem_max | 212992 |

The full machine record is in `results/system.md`.

### Metrics

- **nodes up**: the share of the N nodes that ever got a message from their ring neighbour. Trust this one first. A stack whose nodes never started cannot be judged fairly on RAM or latency. Those numbers would then only describe the few nodes that did start. A stack that brings up 15% of its nodes can post a fine p50, on the 15% that came up. So read the nodes-up column before any latency or RAM column. When nodes-up is below 1.0, every other number for that cell is **survivors-only**: it describes the nodes that came up, not all N.
- **msg delivery**: received divided by sent, counted only among the nodes that ran. This catches stacks that come up but then drop messages under load.
- **RAM (PSS)**: Proportional Set Size. When many processes share the same library pages, PSS counts those shared pages once and splits them across the processes that share them. This is the fair number for a system made of many processes. RSS would count the shared pages once per process. RSS would report a total two to three times too big at 200 nodes. The table shows total PSS for the whole run, then the daemon's PSS on its own (0 when the RMW has no daemon).
- **CPU %**: 100 means one full core busy. The host has 32 logical CPUs, so the limit is 3200%.
- **discovery time**: seconds from launch until every node that comes up is receiving.
- **p50 / p99 latency**: the median and the 99th-percentile one-way latency, in microseconds (us). p99 means 99% of messages arrived faster than this number. When p99 lands in the millions of microseconds, the table also gives it in seconds in parentheses.

## The 256-byte string run

Node counts are 1 / 10 / 50 / 100 / 200. Variants: `unix_socket`, `cyclonedds_default`, `cyclonedds_tuned`, `fastdds_default`, `fastdds_tuned` (simple discovery + mutation_tries=1000), `zenoh_default`, `zenoh_tuned` (shared memory on). The tuned configs are explained in `CONFIGS.md`.

### Nodes up (share of N that ever received)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_default | 1.0 | 1.0 | 0.6 | 0.27 | 0.145 |
| cyclonedds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.97 |
| fastdds_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.265 |
| fastdds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.27 |
| zenoh_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.99 |
| zenoh_tuned | 1.0 | 1.0 | 1.0 | 0.98 | 0.98 |

### Message delivery (received / sent among nodes that ran)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 0.998 |
| cyclonedds_default | 1.0 | 1.0 | 0.937 (survivors-only) | 0.843 (survivors-only) | 0.906 (survivors-only) |
| cyclonedds_tuned | 1.0 | 1.0 | 0.998 | 0.987 | 0.794 (survivors-only) |
| fastdds_default | 1.0 | 0.999 | 0.98 | 0.971 | 0.108 (survivors-only) |
| fastdds_tuned | 1.0 | 1.0 | 0.983 | 0.962 | 0.141 (survivors-only) |
| zenoh_default | 1.0 | 1.0 | 0.998 | 0.992 | 0.957 (survivors-only) |
| zenoh_tuned | 1.0 | 1.0 | 0.999 | 0.969 (survivors-only) | 0.919 (survivors-only) |

### Discovery time (seconds)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 0.09 | 0.07 | 0.13 | 0.24 | 0.59 |
| cyclonedds_default | 0.08 | 0.08 | 0.24 (survivors-only) | 0.26 (survivors-only) | 0.27 (survivors-only) |
| cyclonedds_tuned | 0.07 | 0.08 | 0.33 | 1.59 | 24.47 (survivors-only) |
| fastdds_default | 0.09 | 0.39 | 1.62 | 3.61 | 88.58 (survivors-only) |
| fastdds_tuned | 0.08 | 0.22 | 1.48 | 3.62 | 91.41 (survivors-only) |
| zenoh_default | 0.08 | 0.09 | 0.33 | 1.13 | 6.03 (survivors-only) |
| zenoh_tuned | 0.08 | 0.09 | 0.34 | 10.66 (survivors-only) | 11.1 (survivors-only) |

"(survivors-only)" marks a cell where not all N nodes came up, so the figure describes only the nodes that did. Fast DDS at 200 nodes now reports a finite but very slow discovery (~88-91 s) where it used to report none at all.

### RAM, total PSS (MB, includes daemon)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 13.1 | 31.6 | 107.9 | 204.7 | 405.3 |
| cyclonedds_default | 14.2 | 51.1 | 202.2 (survivors-only) | 201.7 (survivors-only) | 202.1 (survivors-only) |
| cyclonedds_tuned | 14.1 | 50.7 | 371.4 | 1111.3 | 4617.0 (survivors-only) |
| fastdds_default | 24.8 | 108.1 | 740.2 | 2132.0 | 3418.5 (survivors-only) |
| fastdds_tuned | 24.4 | 108.2 | 740.9 | 2137.8 | 3405.2 (survivors-only) |
| zenoh_default | 42.1 | 90.8 | 692.5 | 2331.9 | 8553.9 (survivors-only) |
| zenoh_tuned | 42.4 | 90.8 | 692.1 | 2289.2 (survivors-only) | 8673.1 (survivors-only) |

Read the cyclonedds_default row next to the nodes-up table. Its RAM looks flat from 50 to 200 nodes (about 202 MB). That is because most of its nodes never started. It is the RAM of the survivors, not of 200 nodes.

### Daemon RAM, PSS on its own (MB)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cyclonedds_default | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cyclonedds_tuned | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| fastdds_default | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| fastdds_tuned | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| zenoh_default | 28.3 | 23.8 | 27.7 | 34.5 | 50.1 |
| zenoh_tuned | 28.5 | 23.7 | 27.7 | 34.8 | 50.0 |

`unix_socket` has no daemon, no DDS, and no master. The shared-memory registry it uses for discovery lives in `/dev/shm`, not in a process, so there is nothing to count here. Zenoh always needs its `rmw_zenohd` router (its default config turns off multicast scouting), which is why Zenoh shows a non-zero daemon. Fast DDS shows no daemon: both `fastdds_default` and `fastdds_tuned` now use simple discovery (the tuned config only raises `mutation_tries`).

### CPU %

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.3 | 15.0 | 81.0 | 161.3 | 318.0 |
| cyclonedds_default | 0.7 | 10.0 | 26.3 (survivors-only) | 26.0 (survivors-only) | 26.3 (survivors-only) |
| cyclonedds_tuned | 1.3 | 9.3 | 50.7 | 95.0 | 3335.0 (survivors-only) |
| fastdds_default | 0.7 | 13.7 | 78.3 | 193.0 | 3140.7 (survivors-only) |
| fastdds_tuned | 1.0 | 13.0 | 78.0 | 194.7 | 3140.3 (survivors-only) |
| zenoh_default | 0.3 | 13.3 | 68.7 | 127.7 | 242.0 (survivors-only) |
| zenoh_tuned | 0.7 | 14.7 | 69.7 | 163.7 (survivors-only) | 239.0 (survivors-only) |

The cyclonedds_default CPU is survivors-only from 50 nodes on, same as its RAM.

### p50 latency (us)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 128.2 | 173.7 | 185.5 | 136.3 | 122.6 |
| cyclonedds_default | 68.6 | 230.3 | 206.8 (survivors-only) | 207.9 (survivors-only) | 208.4 (survivors-only) |
| cyclonedds_tuned | 89.0 | 239.9 | 243.6 | 220.5 | 3822.6 (~4 ms, survivors-only) |
| fastdds_default | 113.1 | 275.8 | 292.1 | 288.2 | 350.3 (survivors-only) |
| fastdds_tuned | 116.0 | 320.7 | 291.1 | 282.6 | 356.9 (survivors-only) |
| zenoh_default | 90.7 | 488.4 | 429.0 | 364.4 | 295.3 (survivors-only) |
| zenoh_tuned | 90.9 | 457.1 | 424.2 | 353.9 (survivors-only) | 294.7 (survivors-only) |

At 1 node, Cyclone (88 us) and Zenoh (91 us) post a lower p50 than unix_socket (127 us). The small-count latency win goes to the DDS stacks. The point of this benchmark is what happens as N grows: unix_socket's p50 stays flat (127 down to 124), while the others climb or blow up.

### p99 latency (us)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 149.8 | 258.3 | 236.2 | 236.1 | 229.9 |
| cyclonedds_default | 69.7 | 317.1 | 320.5 (survivors-only) | 317.8 (survivors-only) | 323.3 (survivors-only) |
| cyclonedds_tuned | 98.3 | 373.3 | 342.6 | 344.2 | 453588.9 (~454 ms, survivors-only) |
| fastdds_default | 115.0 | 382.9 | 397.1 | 435.0 | 1880345.2 (~1.9 s, survivors-only) |
| fastdds_tuned | 128.6 | 426.6 | 388.3 | 450.3 | 868880.3 (~869 ms, survivors-only) |
| zenoh_default | 107.8 | 618.2 | 579.6 | 551.2 | 4983.8 (~5 ms, survivors-only) |
| zenoh_tuned | 107.9 | 570.2 | 583.7 | 574.6 (survivors-only) | 4058.1 (~4 ms, survivors-only) |

This is the table that tells the story. unix_socket's p99 is flat: 150 at 1 node, 230 at 200. Cyclone tuned and both Fast DDS configs still bring some nodes up at 200, but their p99 runs from hundreds of milliseconds to nearly two seconds. Zenoh stays in the single-digit milliseconds at the tail.

### Read per RMW, string run

- **unix_socket.** All 200 nodes up, 99.8% delivery at 200. Every curve is flat from 1 to 200 nodes: p50 123 us, p99 230 us, 405 MB PSS, 318% CPU. No daemon. It is not the fastest at 1 node (Cyclone and Zenoh beat its p50 there), and it uses more RAM at small counts than Cyclone. The difference is that nothing bends as N grows.
- **cyclonedds_default.** Fine to 10 nodes. From 50 nodes it stops bringing nodes up: 60% up at 50, 27% at 100, 14.5% at 200. Its flat-looking RAM and CPU at scale are survivors-only and should not be read as efficiency.
- **cyclonedds_tuned.** The tuned config (see `CONFIGS.md`) gets nearly all nodes up (97% at 200) where the default got 14.5%. But staying up is expensive: delivery falls to 79% at 200, discovery takes 24 s, p99 is about 0.45 s, RAM is 4.6 GB, and CPU hits 3335% (most of 32 cores).
- **fastdds_default.** Holds up to 100 nodes, then falls apart at 200: 27% up, 11% delivery, p99 about 1.9 s.
- **fastdds_tuned.** Now simple discovery + `mutation_tries=1000` (see `CONFIGS.md`); the Discovery Server it used to run was dropped because it collapses when many nodes start at once (eProsima/Fast-DDS#6383) and brought up 0/200. The new config is clean to 100 nodes — 100% up, sub-millisecond p99 — then the O(N^2) simple-discovery storm hits at 200: discovery takes 91 s, only 27% of nodes come up, delivery 14%, p99 about 0.87 s. mutation_tries lifts the deaf-participant ceiling, but it cannot fix the discovery storm. Fast DDS at 200 simultaneous nodes on one host is a real limit, not a misconfiguration.
- **zenoh_default.** Stays up well: 99% up and 96% delivery at 200. The cost is the tail and the RAM: p99 about 5 ms, and about 8.5 GB at 200.
- **zenoh_tuned.** With shared memory on, 98% up, 92% delivery, p99 about 4 ms, about 8.7 GB. The shared-memory setting trimmed nothing useful at this message size. (Zenoh's tail is run-to-run variable: a prior run on this host gave a 200-node p99 nearer 32 ms; read it as "single-digit-to-tens of ms," not a fixed figure.)

## The 64 KB shm run

Same ring, same QoS, but the message is now a fixed 64 KB `bench_nodes/FixedMsg`. This is the message size where the DDS zero-copy paths can turn on. Variants here are `unix_socket`, `cyclonedds_tuned`, `cyclonedds_shm` (Iceoryx with the `iox-roudi` daemon), `fastdds_default`, `fastdds_shm` (data-sharing), `zenoh_default`, `zenoh_tuned`. Read the shared-memory caveat below before reading these tables.

The full sweep was collected for `unix_socket` and `cyclonedds_shm`. For the other variants the table below reports the 200-node result, which is the point of this run.

### Nodes up (share of N that ever received)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_shm | 1.0 | 1.0 | 1.0 | 0.11 | 0.08 |

### Message delivery (received / sent among nodes that ran)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 0.998 |
| cyclonedds_shm | 1.0 | 1.0 | 0.999 | 0.782 (survivors-only) | 0.758 (survivors-only) |

### Discovery time (seconds)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 0.07 | 0.07 | 0.13 | 0.24 | 0.58 |
| cyclonedds_shm | 0.08 | 0.09 | 0.33 | 0.78 (survivors-only) | 1.9 (survivors-only) |

### RAM, total PSS (MB, includes daemon)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 13.2 | 32.8 | 113.6 | 214.5 | 418.8 |
| cyclonedds_shm | 662.2 | 705.8 | 1067.7 | 809.1 (survivors-only) | 889.6 (survivors-only) |

cyclonedds_shm carries a fixed Iceoryx pool from the very first node: about 640 MB of `iox-roudi` at N=1. That is why even N=1 costs 662 MB here.

### Daemon RAM, PSS on its own (MB)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cyclonedds_shm | 647.9 | 644.4 | 636.5 | 641.6 | 640.1 |

The Iceoryx daemon pool is about 640 MB and barely moves with N. That is the cost of having Iceoryx at all, before any payload flows.

### CPU %

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 1.7 | 18.3 | 93.0 | 188.7 | 385.7 |
| cyclonedds_shm | 1.0 | 9.3 | 54.7 | 108.7 (survivors-only) | 333.0 (survivors-only) |

### p50 latency (us)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 230.8 | 284.9 | 281.8 | 245.4 | 242.7 |
| cyclonedds_shm | 216.3 | 248.9 | 251.9 | 290.7 (survivors-only) | 285.9 (survivors-only) |

### p99 latency (us)

| variant | 1 | 10 | 50 | 100 | 200 |
|---|---|---|---|---|---|
| unix_socket | 244.7 | 373.8 | 355.5 | 361.5 | 365.6 |
| cyclonedds_shm | 248.0 | 367.9 | 351.4 | 325.7 (survivors-only) | 348.7 (survivors-only) |

The other shm variants do the same thing at 200 nodes as they did in the string run, in some cases worse. From the run logs at 200 nodes:

- **cyclonedds_tuned**: 86% up, 63% delivery, discovery 28.64 s, 6.0 GB, p50 14696 us, p99 524228 us (~0.52 s).
- **fastdds_default**: 30% up, 12% delivery, discovery 33.38 s, 3.8 GB, p50 121956 us, p99 1068172 us (~1.07 s).
- **fastdds_shm** (data-sharing zero-copy): holds to 100 nodes (100% up, 97% delivery, p99 487 us at 100), then 34% up, 19% delivery, discovery 79.8 s, 4.4 GB, p99 539688 us (~0.54 s) at 200. No measurable gain over fastdds_default.
- **zenoh_default**: 100% up, 94% delivery, discovery 6.96 s, about 11 GB, p99 17346 us (~17 ms) at 200.
- **zenoh_tuned**: 99% up, 94% delivery, discovery 11.71 s, about 11 GB, p99 14857 us (~15 ms) at 200.

### Read per RMW, shm run

- **unix_socket.** Same as the string run: all 200 up, 99.8% delivery, flat p50 and p99, 419 MB, 386% CPU. The 64 KB message does not change the shape. unix_socket copies the message through the kernel, so it does not get the zero-copy free ride on the big payload. But its at-scale behaviour is the same.
- **cyclonedds_shm** (Iceoryx). Costs about 640 MB of `iox-roudi` from the first node, before any real traffic. Bring-up collapses past about 50 nodes: 11% up at 100, 8% at 200. The shared-memory daemon made the scaling worse here, not better.
- **cyclonedds_tuned, fastdds_default, fastdds_shm.** Same collapse at 200 nodes as in the string run. Fast DDS data-sharing did not move the result, because the thing that breaks at 200 is discovery, not the data copy.
- **zenoh_default, zenoh_tuned.** Stay up at 200 with about 94% delivery, but at about 11 GB of RAM and a tail in the tens of milliseconds.

## Shared memory: an apples-to-oranges note

The 64 KB run includes zero-copy shared-memory transports: Cyclone with Iceoryx, Fast DDS data-sharing, and Zenoh SHM. Comparing those to an AF_UNIX RMW on a large message is not a fair fight, and it is worth saying so plainly.

Zero-copy skips the data copy. On a large payload it wins by design, because it never moves the bytes. `rmw_unix_socket_cpp` is not zero-copy: it copies each message through the kernel (AF_UNIX is a kernel socket type that delivers datagrams between processes on the same host). So on big messages, zero-copy should beat it, and it does. That is expected and is not the point of this benchmark. We do not claim, and the numbers do not show, that unix_socket beats zero-copy on large transfers. It does not.

The reason the 64 KB run exists is to be fair to the DDS stacks: to give them the message size where their best transport turns on. The result is that the shared-memory path does not fix the at-scale problem, because the thing that breaks at 200 nodes is discovery, not the data copy.

- Cyclone with Iceoryx adds a fixed pool of about 640 MB from the first node, and its bring-up collapses past about 50 nodes (11% up at 100, 8% at 200). Net negative here.
- Fast DDS data-sharing changed nothing measurable versus the default. The limit at 200 nodes is discovery, not the copy.
- Zenoh SHM did not clearly help the tail (about 20 ms at 200, no better than default) and did not help the RAM (about 11 GB at 64 KB).

Zero-copy really pays off for megabyte-scale messages such as camera and lidar frames. Those are past the AF_UNIX datagram size limit (about 400 KB on this host — two times `net.core.wmem_max`) and are out of scope here.

## Honest limits

- `rmw_unix_socket_cpp` is alpha and has a single maintainer.
- It is localhost only by design. Cross-host traffic goes through a separate bridge, which is not part of this benchmark and not measured here. Nothing in this document says anything about multi-host.
- It passes the rmw conformance suite plus about 90 of its own tests. It is not safety certified.
- It has a per-message size limit of about 400 KB — two times `net.core.wmem_max` (the AF_UNIX datagram limit). For larger messages, raise `net.core.wmem_max` and `net.core.rmem_max`. This is why the shm run tops out at 64 KB.
- It does not try to beat shared-memory DDS at 1:1 latency, and at small node counts it does not (Cyclone and Zenoh post a lower p50 at 1 node).
- The benchmark is synthetic ring traffic at one rate and one size on one host. Real graphs have uneven fan-out, mixed message sizes, and bursty traffic. Treat this as a scaling comparison on one host with this workload, not a final verdict on any of these stacks.

## Versions

ROS 2 Jazzy. CycloneDDS core 0.10.5 (tag) with `rmw_cyclonedds` jazzy, built from source. `rmw_zenoh` jazzy (`zenoh_cpp_vendor` 0.2.9, Rust 1.75), built from source. `rmw_fastrtps_cpp` from the Jazzy apt package (not source, to avoid ABI skew with the apt fastcdr and typesupport that `bench_nodes` and `rmw_unix_socket_cpp` link against). `rmw_unix_socket_cpp` cloned from [github.com/benaliabderrahmane/rmw_unix_socket_cpp](https://github.com/benaliabderrahmane/rmw_unix_socket_cpp) (branch `main`). The tuned and shared-memory configs are documented in `CONFIGS.md`. To reproduce, run `bash scripts/run_benchmark.sh`.
