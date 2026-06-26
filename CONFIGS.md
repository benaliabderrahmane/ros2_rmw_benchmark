# Tuned and shared-memory configs

Every RMW here is also run with its out-of-the-box defaults, because that's what
anyone actually starts from. But "the DDS stacks fall over at 200 nodes" is a
weak claim if all you did was leave them on defaults — a reviewer will reasonably
say you didn't try. So for each stack we also built a tuned config aimed at the
exact failure we saw (discovery falling apart, ports not getting claimed, the
shared-memory path not engaging), tuned it the way the upstream docs and issue
trackers say to, and report both. The defaults are the honest starting point;
the tuned configs are us doing the homework. Where a tuned config helped, we say
so. Where it made things worse, we say that too.

A note on the shared-memory variants before the details: comparing zero-copy SHM
(Cyclone+Iceoryx, Fast DDS data-sharing, Zenoh SHM) against an AF_UNIX RMW on the
64 KB payload is not apples-to-apples. Zero-copy skips the payload copy by
construction, so on a large message it will win on raw transfer — that's expected
and not the point of this benchmark. We include the SHM run to be fair to the DDS
stacks, and the finding there is narrower: even with zero-copy turned on, the
at-scale bring-up problem doesn't go away. Each SHM section below says what it
actually changed.

Files referenced live in `configs/`. The variant keys (`cyclonedds_tuned`,
`cyclonedds_shm`, `fastdds_tuned`, `fastdds_shm`, `zenoh_tuned`, etc.) are the
ones `scripts/rmw_matrix.py` knows about.

---

## cyclonedds_tuned — `configs/cyclonedds_tuned.xml`

**What it changes.** Bind to the loopback interface only, set
`AllowMulticast=spdp` (multicast for participant discovery, unicast for
everything else), `ParticipantIndex=none`, and raise `MaxMessageSize` to 65500
bytes.

**Why.** Default Cyclone on this host only brought up 14% of the 200 nodes — most
processes never received anything from their ring neighbour. The two changes that
matter for scale are pinning discovery to loopback (we're localhost-only, so
there's no reason to let SPDP touch other interfaces) and dropping the
per-participant index bookkeeping, which grows with the participant count and is
pure overhead when you have 200 participants on one box.

**Source.** CycloneDDS configuration docs, https://cdds.io/config.

**How it helped (and where it didn't).** It works as a bring-up fix: 97% of the
200 nodes come up versus the default's 14%. That's the headline win. But it doesn't
make Cyclone healthy at 200 — message delivery drops to 80%, p99 latency climbs
to about 0.45 s (the raw figure is 452673.7 us), PSS hits 4.5 GB, and CPU sits
around 3300%. So tuned Cyclone trades "most nodes never start" for "nodes start
but a fifth of the traffic is lost and the tail latency is half a second." At the
64 KB payload it's the same shape, and there all 200 do come up: 63% delivery,
p99 ~0.96 s, 4.9 GB.

---

## cyclonedds_shm — `configs/cyclonedds_shm.xml` (+ `configs/iox_roudi_config.toml`)

**What it changes.** Starts from `cyclonedds_tuned.xml` and adds
`<SharedMemory><Enable>true</Enable></SharedMemory>`. This requires the Iceoryx
`iox-roudi` daemon to be running, and gives zero-copy only for fixed-size types —
which is why the SHM run uses the 64 KB `bench_nodes/FixedMsg` rather than a
variable-length String. `iox_roudi_config.toml` sizes the Iceoryx mempools
(128 KB chunks) for the test.

**Why.** To give Cyclone its best shot on the large-payload run: zero-copy through
Iceoryx instead of copying 64 KB through the kernel for every message.

**Source.** rmw_cyclonedds `shared_memory_support` docs, plus the Iceoryx project.

**How it didn't help.** Net negative for this workload. `iox-roudi` reserves a
fixed pool the moment the first node starts — about 640 MB of PSS at N=1, before
any real traffic. Worse, bring-up collapses past roughly 50 nodes (Iceoryx/RouDi
runtime limits): 100% up at 50 nodes, 20% at 100, 6% at 200. The SHM path that
was supposed to help at scale is the one path that can't reach scale. For a
many-process graph like this one, plain tuned Cyclone is the better Cyclone.

---

## fastdds_tuned — `configs/fastdds_tuned.xml` (+ Discovery Server)

**What it changes.** Raise `mutation_tries` from the default 100 to 1000, and run
a Fast DDS Discovery Server (`fastdds discovery`) instead of the default simple
discovery. Applied via `FASTDDS_DEFAULT_PROFILES_FILE` plus
`RMW_FASTRTPS_USE_QOS_FROM_XML=1`.

**Why.** Two separate problems show up with ~100+ participants on one host. First,
a new participant tries to claim a unique unicast listening port; if it can't, it
silently goes "deaf" and never receives — and in the ROS Release builds the
warning that would tell you this is compiled out, so it fails quietly. Raising
`mutation_tries` gives each participant more attempts to find a free port. Second,
simple (SPDP) discovery has a hard ceiling of roughly 119 participants per domain
on one host, so you physically cannot reach 200 nodes that way; the Discovery
Server replaces the all-to-all simple discovery to get past that ceiling.

**Source.** eProsima Fast-DDS issue #5767,
https://github.com/eProsima/Fast-DDS/issues/5767.

**How it backfired.** The Discovery Server itself became unresponsive past about
50 nodes (also documented in #5767). The result is that tuned Fast DDS was *worse*
than default beyond 50 nodes: at 200 it brought up 0 nodes (0% up, 0% delivery,
no measurable latency), where default Fast DDS at least got 27% up. So the tuning
that lets it clear the 119-participant ceiling introduces a different bottleneck —
the central server — that fails earlier than the thing it replaced. This is the
one case where the honest report is that the tuned config is the wrong choice for
this workload; default is the lesser evil.

---

## fastdds_shm — `configs/fastdds_shm.xml`

**What it changes.** Sets `data_sharing=AUTOMATIC`, enabling Fast DDS data-sharing
(zero-copy via shared memory for plain/bounded types). Like the Cyclone SHM case,
this needs the fixed-size `FixedMsg`, so it runs on the 64 KB payload.

**Why.** Same motivation as the other SHM variants — avoid copying the 64 KB
payload, on the run where that copy is largest.

**Source.** Fast DDS data-sharing docs.

**How it didn't help.** No measurable change versus default at 64 KB. Both
data-sharing and plain default behave like the 256 B run and both collapse at 200
nodes (nodes-up 0.23 with data-sharing, 0.31 default). Data-sharing doesn't move
the needle here because the bottleneck isn't the payload copy — it's discovery.
Zero-copy makes the transfer cheaper once a participant is talking, but
most participants never get that far at 200 nodes, so the transport optimization
has nothing to optimize.

---

## zenoh SHM — `zenoh_tuned` via `ZENOH_CONFIG_OVERRIDE`

**What it changes.** Enables `transport/shared_memory/enabled=true` on both the
`rmw_zenohd` router and the sessions, set through `ZENOH_CONFIG_OVERRIDE` rather
than editing the shipped JSON5 config.

**Why.** Give Zenoh zero-copy on the large-payload run, same as the others.

**Source.** rmw_zenoh README and the Zenoh config reference. Note that rmw_zenoh
always needs the `rmw_zenohd` router daemon running — the default config disables
multicast scouting, so without the router there's no discovery at all. That daemon
is why Zenoh carries a non-zero "daemon PSS" column even in the default run.

**How it helped, a little.** Zenoh is the one DDS-family stack that already brings
up nearly all nodes on defaults (98% up, 94% delivery on the 256 B run), so SHM
wasn't a bring-up fix here — it was a tail-latency fix. Enabling it trimmed p99
and CPU slightly at 200 nodes and gave no RAM relief: Zenoh still sits at roughly
8.5 GB PSS on the 256 B run, and around 11–12 GB on the 64 KB run, with p99 in the
single-digit-millisecond to ~2 s range depending on payload. So SHM moved Zenoh
from "works at scale but expensive" to "works at scale, slightly less expensive
tail, still 8+ GB."

---

## What to take from this

Tuning fixes the bring-up problem for Cyclone (14% → 97% up at 256 B, all 200 up
at 64 KB) and is a wash or a regression everywhere else. The shared-memory
variants are included for fairness on the large-payload run, and the result is
that zero-copy does not solve the at-scale problem on this workload:
Cyclone+Iceoryx collapses past ~50 nodes and adds a fixed
~640 MB pool, Fast DDS data-sharing changes nothing because discovery is the
bottleneck, and Zenoh SHM only trims the tail. The place where zero-copy genuinely
earns its keep is megabyte-scale messages (camera, lidar), which are past the
~200 KB AF_UNIX datagram cap and out of scope here. See `RESULTS.md` for the full
per-node-count tables and `results/system.md` for the exact host the numbers were
measured on.
