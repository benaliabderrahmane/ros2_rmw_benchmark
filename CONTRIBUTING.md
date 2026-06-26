# Contributing

Thanks for looking. This is a small, single-maintainer project, so the bar for a useful contribution is low: a new RMW variant, a new metric, a bug in the harness, or a result set from hardware that isn't a developer laptop. What follows is the practical map. The story and the numbers live in `README.md` and `RESULTS.md`; this file is about the code.

The whole thing is Python (stdlib + matplotlib) driving one small C++ ROS node, packaged in Docker. There is no framework. If a change feels like it needs one, it probably belongs somewhere else.

## Code layout

The harness is eight files under `scripts/`, plus the load node and the configs.

`bench_nodes/` is an ament C++ package with one executable, `load_node` (`src/load_node.cpp`), and one message, `msg/FixedMsg.msg`. A `load_node` process is one ring node: given `--id i --total N`, it publishes a monotonic-timestamped message on `/bench/t<i>` at `--rate` Hz and subscribes to node `i-1`. With `--fixed` it sends the 64 KB `FixedMsg` (plain fixed-width fields, so DDS zero-copy can engage) instead of a `--size`-byte `std_msgs/String`. On exit it writes a per-node JSON with `t_first_recv_ns`, `n_sent`, `n_recv`, and the raw `latencies_us` array. Latency is `recv_ns - send_ns` in microseconds; both timestamps come from `CLOCK_MONOTONIC`, which is system-wide on Linux, so cross-process numbers compare directly on one host.

`configs/` holds the tuned/SHM config files referenced by the matrix: `cyclonedds_tuned.xml`, `cyclonedds_shm.xml`, `fastdds_tuned.xml`, `fastdds_shm.xml`, and `iox_roudi_config.toml` (Iceoryx mempools). Why each one exists and what it changed is in `CONFIGS.md` — read that before editing a config, the settings are load-bearing, not decoration.

`scripts/`:

- `rmw_matrix.py` — the source of truth for what a "variant" is. Each variant is a `RunSpec`: the RMW name, a config label, extra env for the node processes, an optional discovery daemon to start first (Zenoh router, Fast DDS Discovery Server, iox-roudi), and which config files were applied. `ALL_VARIANTS` is the run order; `BUILDERS` maps a key to its `RunSpec`.
- `run_one.py` — runs ONE `(variant, node-count)` point and emits one `result_*.json`. It starts the daemon (if any), launches N `load_node` processes, lets discovery settle, samples steady-state RAM/CPU, waits for the run to finish, then aggregates the per-node JSONs into the result. This is where the result schema is defined.
- `measure.py` — `/proc` sampling helpers, stdlib only. PSS from `smaps_rollup`, RSS from `status`, CPU from `stat` (utime+stime). `pgid_members()` finds every pid in a daemon's process group, because the daemons fork a real server behind a launcher.
- `aggregate.py` — reads all `result_*.json` in a directory, writes `summary.md` (one table per metric, variants × node counts) and `summary.csv` (one row per run, all fields).
- `plot.py` — renders the result JSONs as the multi-panel dashboard PNG. One panel per metric, x = node count (log), one line per variant, `unix_socket` drawn thick/black as the reference.
- `run_benchmark.sh` — the orchestrator. Builds the Docker image, runs each phase (`string`, then `shm`) in a container, writes `system.md` and the graphs. `--native` runs a single matrix in-place (this is what runs inside the container).
- `sysinfo.sh` — prints the host's CPU/RAM/kernel/shm as a markdown table; the orchestrator captures it to `results/system.md`.
- `clean.sh` — removes generated results and raw scratch dirs.

The data flow, end to end: `load_node` writes per-node JSON → `run_one.py` pools those into one `result_*.json` (using `measure.py` for RAM/CPU) → `aggregate.py` tabulates → `plot.py` charts. `rmw_matrix.py` sits to the side and tells `run_one.py` how to launch each variant.

## Adding a new RMW variant

Two edits in `scripts/rmw_matrix.py`:

1. Write a builder returning a `RunSpec`. For an RMW with no tunables, `_simple("mything", "rmw_mything_cpp")` is enough. If it needs config files or environment, set `env=` (merged into every node process's environment, on top of `RMW_IMPLEMENTATION`) and `config_files=` (recorded in the result, not interpreted). If discovery needs a daemon, set `daemon_cmd=` to its argv and, if the daemon needs its own environment, `daemon_env=`. The daemon runs in its own session so the harness can measure and kill the whole process group; bump `daemon_wait_s` if it's slow to come up. Use `notes=` for a one-line description of what the config does.
2. Register it: add the key to `BUILDERS` and put it in `ALL_VARIANTS` where it should appear in the run order and tables.

If you want it in the default one-command run, also add the key to `STRING_VARIANTS` and/or `SHM_VARIANTS` in `scripts/run_benchmark.sh`. If it draws its own line in the graphs, add it to `ORDER` and `COLORS` in `scripts/plot.py` (otherwise it still plots, just with a default color at the end). And if the RMW has to be compiled into the image, add it to `docker/Dockerfile`.

Look at `_zenoh_tuned()` for the env + daemon pattern and `_cyclone_shm()` for env + daemon + a daemon that needs extra warm-up.

## Adding a metric

A metric flows through four files, in this order:

1. `load_node.cpp` — if the metric is per-node (a new latency statistic, a drop counter), measure it and add the field to the JSON it writes.
2. `run_one.py` — pool or compute the metric across nodes and add it to the `result` dict. RAM/CPU-style metrics get sampled here via `measure.py`; add a helper there if you need a new `/proc` field.
3. `aggregate.py` — add the key to `METRICS` (for the per-metric markdown table) and to `CSV_FIELDS` (for the flat CSV).
4. `plot.py` — add `(key, title, log-y?)` to its `METRICS` list to get a panel. The grid is 3×3 with one cell spent on the legend, so eight metrics fit; past that, grow the `subplots` shape.

Keep the result JSON additive — old result sets should still load. `aggregate.py` and `plot.py` already render a missing field as `—` / a skipped point.

## Running a subset during development

Don't run the full 9-variant × 5-node-count × 2-phase matrix while iterating; it takes a long time and the 200-node DDS points are the slow part. Override via env:

```
# one variant, two small node counts, string phase only
NODES="1 10" PHASES=string VARIANTS="unix_socket cyclonedds_tuned" bash scripts/run_benchmark.sh
```

To skip Docker entirely — you have ROS 2 Jazzy and the RMWs you're testing sourced locally — drive a single matrix in place:

```
VARIANTS="unix_socket" NODES="1 10" OUTDIR=results/dev bash scripts/run_benchmark.sh --native
```

Or go one level down and run a single point directly:

```
python3 scripts/run_one.py --variant unix_socket --nodes 10 --outdir results/dev
```

`run_one.py` finds `load_node` via `ros2 pkg prefix bench_nodes`, or set `BENCH_LOAD_NODE` to its path.

## Contributing results from your own hardware

The numbers in `RESULTS.md` are from one machine (recorded in `results/system.md`). A second data point on different silicon is useful — the at-scale story should hold, but the crossover node count and the absolute latencies will move.

1. Run `bash scripts/sysinfo.sh` and eyeball the output — it's what identifies your run. Do not hand-edit CPU/RAM into it.
2. Run the matrix. The one-command path (`bash scripts/run_benchmark.sh`) needs Docker, internet for the build, and a few GB of `/dev/shm`. It writes results under `results/jazzy/` and `results/jazzy_shm/`.
3. Move the output into a host-named directory so it doesn't clobber the reference run: `results/<host>/` and `results/<host>_shm/`, with `system.md`, `summary.md`, `summary.csv`, and the `result_*.json` files. Point the runner there with `OUTDIR=results/<host> ...` if you want it written there directly.
4. Open a PR with the `results/<host>/` directory. In the description, say what the box is and call out anything unusual — a stack that came up here but not on the reference machine, a wildly different crossover point, an RMW version that differs from the one in `docker/Dockerfile`.

If a stack collapses differently than `RESULTS.md` reports, that's a finding, not a mistake — include it. The whole point of the "nodes up" metric is that a stack whose processes never came up can't be judged on its RAM or latency, and that boundary is exactly the kind of thing that shifts with hardware.

## Conventions

Match the surrounding style. Comments are one line and explain why, not what. The harness is stdlib Python plus matplotlib for the plot — keep new dependencies out of the sampling and aggregation path. Configs are checked in for reproducibility, so a config change without a matching note in `CONFIGS.md` (source, what it does, what it changed) isn't done.

Licensed Apache-2.0; by contributing you agree your contribution is under the same license.
