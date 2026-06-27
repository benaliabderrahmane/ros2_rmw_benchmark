# Tuned and shared-memory configs

Every RMW here is run with its out-of-the-box defaults, because that is what
anyone starts from. But "the DDS stacks fall over at 200 nodes" is a weak claim
if all you did was leave them on defaults. A reviewer will fairly say you did not
try. So for each stack we also built a tuned config aimed at the exact failure we
saw (discovery falling apart, ports not getting claimed, the shared-memory path
not turning on), set it up the way the upstream docs and issue trackers say to,
and report both. The defaults are the honest starting point. The tuned configs
are us doing the homework. Where a tuned config helped, we say so. Where it made
things worse, we say that too.

One note on the shared-memory variants first. Comparing zero-copy shared memory
(Cyclone with Iceoryx, Fast DDS data-sharing, Zenoh SHM) against an AF_UNIX RMW
on the 64 KB payload is not a fair fight. Zero-copy skips the data copy, so on a
big message it wins by design. That is expected and not the point. We include the
64 KB run to be fair to the DDS stacks, and the finding is narrower: even with
zero-copy on, the at-scale bring-up problem does not go away. Each SHM section
below says what it actually changed.

Files live in `configs/`. The variant keys (`cyclonedds_tuned`, `cyclonedds_shm`,
`fastdds_tuned`, `fastdds_shm`, `zenoh_tuned`) are the ones `scripts/rmw_matrix.py`
knows about. "PSS" is the memory number we use: shared library pages are counted
once, which is the fair figure when you have many processes. "Discovery" is the
time from launch until every node is receiving. "p50" and "p99" are the median
and 99th-percentile latency.

---

## cyclonedds_tuned — `configs/cyclonedds_tuned.xml`

**What it changes.** Bind to the loopback interface only, set
`AllowMulticast=spdp` (use multicast for participant discovery, unicast for
everything else), set `ParticipantIndex=none`, and raise `MaxMessageSize` to
65500 bytes.

**Why.** Default Cyclone on this host only brought up 15% of the 200 nodes at
the 256-byte message size. Most processes never received anything from their ring
neighbour. Two changes matter for scale. First, pin discovery to loopback: we are
localhost-only, so there is no reason to let SPDP touch other interfaces. Second,
drop the per-participant index work, which grows with the node count and is pure
overhead when you have 200 participants on one box.

**Source.** CycloneDDS configuration docs, https://cdds.io/config.

**Effect.** It works as a bring-up fix. On the 256-byte run, 99% of the 200 nodes
come up, against the default's 15% (and the default was already down to 60% up at
50 nodes and 28% at 100). That is the win. But it does not make Cyclone healthy at
200. Message delivery falls to 79%, p99 latency climbs to about 0.45 s (the raw
figure is 453589 us), PSS hits 4.6 GB, and CPU sits around 3335%. So tuned Cyclone
trades "most nodes never start" for "nodes start but a fifth of the traffic is
lost and the tail is half a second." On the 64 KB run the shape is the same: 86%
of nodes up at 200, 63% delivery, p99 about 0.52 s, 6.0 GB PSS.

---

## cyclonedds_shm — `configs/cyclonedds_shm.xml` (+ `configs/iox_roudi_config.toml`)

**What it changes.** Starts from `cyclonedds_tuned.xml` and adds
`<SharedMemory><Enable>true</Enable></SharedMemory>`. This needs the Iceoryx
`iox-roudi` daemon running, and gives zero-copy only for fixed-size types. That
is why the SHM run uses the 64 KB `bench_nodes/FixedMsg` and not a variable-length
String. `iox_roudi_config.toml` sizes the Iceoryx memory pools (128 KB chunks).

**Why.** To give Cyclone its best shot on the large-payload run: send 64 KB
through shared memory instead of copying it through the kernel for every message.

**Source.** rmw_cyclonedds `shared_memory_support` docs, plus the Iceoryx project.

**Effect.** Net negative for this workload. `iox-roudi` reserves a fixed pool the
moment the first node starts: about 640 MB of PSS at one node, before any real
traffic. Worse, bring-up collapses past about 50 nodes. All nodes are up at 50,
then 10% at 100 and 11% at 200. The shared-memory path was meant to help at scale,
and it is the one path that does not reach scale. For a many-process graph like
this one, plain tuned Cyclone is the better Cyclone.

---

## fastdds_tuned — `configs/fastdds_tuned.xml`

**What it changes.** Raise `mutation_tries` from the default 100 to 1000, on
plain simple (SPDP) discovery. Applied with `FASTDDS_DEFAULT_PROFILES_FILE` plus
`RMW_FASTRTPS_USE_QOS_FROM_XML=1`. No Discovery Server.

**Why.** Past about 100 participants on one host, a new participant tries to claim
a free unicast listening port; if it cannot, it silently goes deaf and never
receives, and in ROS Release builds the warning that would tell you is compiled
out, so it fails quietly. Raising `mutation_tries` gives each participant more
attempts to find a free port. This is the mitigation the eProsima maintainers
recommend in the issue thread.

**Why not a Discovery Server.** An earlier version of this profile added a Fast
DDS Discovery Server to get past the ~119-participants/host port-collision
ceiling. It backfired: the Discovery Server collapses when many nodes start at
once (unresponsive, >100% CPU), and brought up 0 of 200 nodes — worse than plain
simple discovery, which at least got ~32% up. We also tested raising
`domainIDGain` (250→2000) to move the port-collision ceiling past 200; it did not
help either. The real bottleneck at 200 participants on one host is the O(N²)
simple-discovery traffic storm: discovery takes ~150 s and only about a third of
nodes come up even with a three-minute window. So no tuning makes Fast DDS scale
to 200 simultaneous participants on one host here — it is a real limitation, and
`mutation_tries=1000` on simple discovery is the least-bad honest choice (and the
maintainers' recommended one).

**Source.** eProsima Fast-DDS issue
[#6383](https://github.com/eProsima/Fast-DDS/issues/6383) (the Discovery Server
collapse, with the `mutation_tries=1000` recommendation), which
[#5767](https://github.com/eProsima/Fast-DDS/issues/5767) dedups to.

---

## fastdds_shm — `configs/fastdds_shm.xml`

**What it changes.** Sets `data_sharing=AUTOMATIC`, which turns on Fast DDS
data-sharing: zero-copy over shared memory for plain fixed-size types. Like the
Cyclone SHM case, this needs the fixed-size `FixedMsg`, so it runs on the 64 KB
payload.

**Why.** Same idea as the other SHM variants: avoid copying the 64 KB payload on
the run where that copy is largest.

**Source.** Fast DDS data-sharing docs.

**Effect.** No measurable change versus default at 64 KB. Both data-sharing and
plain default collapse at 200 nodes: 34% of nodes up with data-sharing, 30% with
default. Data-sharing does not change anything here because the bottleneck is not
the payload copy. It is discovery. Zero-copy makes the transfer cheaper once a
participant is talking, but at 200 nodes most participants never get that far, so
there is no transfer left to make cheaper.

---

## zenoh_tuned (SHM) — via `ZENOH_CONFIG_OVERRIDE`

**What it changes.** Sets `transport/shared_memory/enabled=true` on the
`rmw_zenohd` router and on every session, through `ZENOH_CONFIG_OVERRIDE` rather
than editing the shipped config.

**Why.** Give Zenoh zero-copy on the large-payload run, the same as the others.

**Source.** rmw_zenoh README and the Zenoh config reference. rmw_zenoh always
needs the `rmw_zenohd` router daemon running: its default config turns off
multicast scouting, so without the router there is no discovery at all. That
daemon is why Zenoh shows a non-zero daemon PSS column even on the default run.

**Effect.** Small. Zenoh is the one DDS-family stack that already brings up nearly
all nodes on defaults (97% up, 94% delivery on the 256-byte run), so SHM was not a
bring-up fix here. At 200 nodes on the 256-byte run, default Zenoh has a p99 of
about 12 ms and SHM-on Zenoh about 32 ms, so SHM did not help the tail there.
Neither one helps the RAM: Zenoh sits around 8.4 GB PSS at 200 nodes either way,
and around 11 GB on the 64 KB run. So Zenoh works at scale but stays expensive,
and turning SHM on does not change that.

---

## What to take from this

Tuning fixes the bring-up problem for Cyclone (15% to 99% up at 256 bytes, 86% up
at 64 KB) and is a wash or a regression everywhere else. The shared-memory
variants are here for fairness on the large-payload run, and the result is that
zero-copy does not solve the at-scale problem on this workload. Cyclone with
Iceoryx collapses past about 50 nodes and adds a fixed 640 MB pool. Fast DDS
data-sharing changes nothing, because discovery is the bottleneck. Zenoh SHM only
trims the tail. Zero-copy really pays off for megabyte-scale messages (camera,
lidar), which are past the ~400 KB AF_UNIX datagram cap (two times `net.core.wmem_max`) and out of scope here. See
`RESULTS.md` for the full per-node-count tables and `results/system.md` for the
exact host the numbers came from.
