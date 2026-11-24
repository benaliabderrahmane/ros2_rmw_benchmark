#!/bin/bash
# Slide "We hoped Zenoh would fix it: each fix moved the cost somewhere else" (ROS 2 Jazzy, rmw_zenoh_cpp from its
# apt). Three parts, 3 runs each, ours against Zenoh:
#   1. peer and client mode: the 200-node benchmark (reproduce/200-nodes.sh) with ours, Zenoh peer, Zenoh client;
#   2. big messages: performance_test, 4 MB to 5 subscribers (ours, Zenoh, Zenoh + shared memory);
#   3. then shared memory: the ring's 64 KB phase at 100 processes (ours, Zenoh, Zenoh + shared memory).
#
#   reproduce/zenoh-jazzy.sh                 # all three, ~1 h 45 min (part 1 is 3 x 3 x 10 min)
#   PARTS="2 3" reproduce/zenoh-jazzy.sh     # the quick parts only, ~15 min
#
# Output: results-local/zenoh-jazzy-<date>/: 200-nodes/ (part 1), t5/ and ring/ (parts 2-3) and summary/.
export DISTRO=jazzy
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
RUNS="${RUNS:-3}"
PARTS="${PARTS:-1 2 3}"
OUT="${OUT:-$HERE/results-local/zenoh-jazzy-$STAMP}"
mkdir -p "$OUT"
host_check
build_ring
if [[ " $PARTS " == *" 1 "* ]]; then
  build_ts200
  log "part 1: 200 nodes, peer and client mode"
  OUT="$OUT/200-nodes" VARIANTS="unix_socket zenoh_default zenoh_client" TS200_ARGS="--tail 100000" \
    RING_IMAGE="$RING_IMAGE" bash "$HERE/scripts/run_ts200.sh" "$RUNS"
  inimage "$OUT" scripts/plot_timeseries.py "$OUT/200-nodes"
fi
if [[ " $PARTS " == *" 2 "* ]]; then
  build_perf
  python3 "$HERE/scripts/gen_t5_specs.py" "$RUNS" >/dev/null
  for k in $(seq 1 "$RUNS"); do
    for v in unix_socket zenoh_default zenoh_tuned; do
      log "part 2: r$k 4 MB to 5 subscribers, $v"
      perf_case "$OUT" "$k" "array4m_s5_$v"
    done
  done
fi
if [[ " $PARTS " == *" 3 "* ]]; then
  for k in $(seq 1 "$RUNS"); do
    log "part 3: r$k ring, 64 KB messages, 100 processes"
    docker run --rm --ipc=host --entrypoint bash "$RING_IMAGE" -c 'rm -f /dev/shm/ros2_uds_* /dev/shm/*.zenoh'
    docker run --rm --sysctl net.unix.max_dgram_qlen=4096 --ipc=host --shm-size=2g --ulimit nofile=1048576:1048576 \
      --ulimit memlock=-1 -e NODES=100 -e RATE=20 -e SIZE=256 -e DURATION=30 -e WARMUP=5 -e SETTLE=10 -e CPU_WINDOW=3 \
      -e DEGREE=1 -e "VARIANTS=unix_socket zenoh_default zenoh_tuned" -e FIXED=1 -e "OUTDIR=/benchmarks/results/ring/r$k/shm" \
      -v "$OUT:/benchmarks/results" "$RING_IMAGE" bash /benchmarks/scripts/run_benchmark.sh --native | tail -1
  done
fi
chown_back "$OUT"
[[ " $PARTS " == *" 2 "* ]] && inimage "$OUT" scripts/summarize.py perf "$OUT" "$OUT/summary"
[[ " $PARTS " == *" 3 "* ]] && inimage "$OUT" scripts/summarize.py ring "$OUT" "$OUT/summary"
log "done: $OUT"
