#!/bin/bash
# Supervised 200-node time series (21 Nov 2026): 200 processes, one ROS node each with 5 publishers and 5
# subscriptions (scripts/ts200/src/bench_multi), started at once. A node that exits, or is not up (every subscription
# has received) within 120 s of its (re)start, is restarted, 3 times at most; 10 min at most per run (scripts/ts200.py). Each RMW variant and
# each run in its own container, one after the other, each after wait_quiet (scripts/quiet.sh). CPU and memory are
# read from the host (scripts/cgroup_sampler.py, the container's cgroup): <variant>_r<k>.cgroup.csv. Router CPU/RSS/TCP and
# host memory: router_monitor.csv; the watchdog kills the run's container under 3 GB available.
#   RING_IMAGE=<image> TS200_DIR=<built bench_multi workspace> OUT=<dir> bash scripts/run_ts200.sh [RUNS=3]
# reproduce/200-nodes.sh builds both and calls this; QUIET=0 skips the wait for an idle machine.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$HERE/scripts/quiet.sh"
QLEN="${QLEN:-4096}"  # net.unix.max_dgram_qlen inside each container (per network namespace)
RUNS=${1:-3}
: "${RING_IMAGE:?set RING_IMAGE (reproduce/200-nodes.sh does)}" "${TS200_DIR:?set TS200_DIR}" "${OUT:?set OUT}"
VARIANTS="${VARIANTS:-unix_socket zenoh_default zenoh_client cyclonedds_tuned fastdds_tuned}"
TS200_ARGS="${TS200_ARGS:-}"  # e.g. "--tail 100000": run the full --max-window (600 s) even once all are up
mkdir -p "$OUT"
rm -f "$OUT/monitor.stop"
python3 "$HERE/scripts/router_monitor.py" --out "$OUT/router_monitor.csv" --label-file "$OUT/current.txt" \
  --stop-file "$OUT/monitor.stop" --min-avail-gb 3 &
MON=$!
trap 'touch "$OUT/monitor.stop"; wait $MON 2>/dev/null || true' EXIT
for r in $(seq 1 "$RUNS"); do
  for v in $VARIANTS; do
    f="$OUT/${v}_r$r.json"; [ -f "$f" ] && continue
    [ "${QUIET:-1}" = 0 ] || wait_quiet
    echo "$v r$r" > "$OUT/current.txt"; echo "=== $(date +%T) $v r$r"
    # Fast DDS segments too (added 23 Nov, after both 21/23 Nov campaigns: their Fast DDS runs started among stale ones).
    docker run --rm --ipc=host --entrypoint bash "$RING_IMAGE" -c \
      'rm -f /dev/shm/ros2_uds_* /dev/shm/*.zenoh /dev/shm/iceoryx_* /dev/shm/fastrtps_* /dev/shm/fastdds_* /dev/shm/sem.fastrtps_* /dev/shm/sem.fastdds_*'
    rm -f "$OUT/${v}_r$r.cid"
    docker run --rm --cidfile "$OUT/${v}_r$r.cid" --label zc-campaign=1 --memory=22g --memory-swap=22g \
      --oom-score-adj=1000 --sysctl net.unix.max_dgram_qlen="$QLEN" --ipc=host --shm-size=2g \
      --ulimit nofile=1048576:1048576 --ulimit memlock=-1 -v "$HERE/scripts:/campaign/scripts:ro" \
      -v "${TS200_DIR:-$HERE/scripts/ts200}:/ts200:ro" -v "$OUT:/out" --entrypoint bash "$RING_IMAGE" -c \
      "source /opt/ros/\$ROS_DISTRO/setup.bash; source /bench_ws/install/setup.bash; source /ts200/install/setup.bash;
       python3 /campaign/scripts/ts200.py --variant $v --mem-every 0 $TS200_ARGS --out /out/${v}_r$r.json" \
      > "$OUT/${v}_r$r.log" 2>&1 &
    DR=$!
    # CPU and memory from the host: the container's cgroup counters, no lock taken in the measured processes.
    python3 "$HERE/scripts/cgroup_sampler.py" --cidfile "$OUT/${v}_r$r.cid" --out "$OUT/${v}_r$r.cgroup.csv" &
    SP=$!
    wait $DR || echo "WARN: $v r$r failed"
    wait $SP || echo "WARN: sampler $v r$r failed"
    grep -v entrypoint "$OUT/${v}_r$r.log" | tail -1
  done
done
docker run --rm --entrypoint chown -v "$OUT:/out" "$RING_IMAGE" -R "$(id -u):$(id -g)" /out
echo "done: $OUT"
