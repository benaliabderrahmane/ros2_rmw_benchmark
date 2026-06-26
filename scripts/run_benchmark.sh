#!/usr/bin/env bash
# RMW benchmark runner.
#
#   ./scripts/run_benchmark.sh            # build the image, then run EVERYTHING:
#                                         #   the 256 B matrix, the 64 KB SHM
#                                         #   matrix, graphs, and system.md.
#   ./scripts/run_benchmark.sh --native   # run a single matrix in-place (used
#                                         #   inside the container, or on a host
#                                         #   with ROS + the four RMWs sourced).
#
# Override anything via env, e.g. a quick smoke run:
#   NODES="1 10" PHASES=string VARIANTS="unix_socket cyclonedds_tuned" ./scripts/run_benchmark.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$SCRIPT_DIR")"

ROS_DISTRO="${ROS_DISTRO:-jazzy}"
IMAGE="${IMAGE:-rmw-bench:jazzy}"
NODES="${NODES:-1 10 50 100 200}"
RATE="${RATE:-20}"
SIZE="${SIZE:-256}"
# Sized for the 200-node end: discovery for the DDS stacks can take seconds, so
# settle long enough to sample steady state, run long enough to clear it.
DURATION="${DURATION:-30}"
WARMUP="${WARMUP:-5}"
SETTLE="${SETTLE:-10}"
CPU_WINDOW="${CPU_WINDOW:-3}"

# Which phases the one-command run does, and the variant set for each. The SHM
# phase swaps in the shared-memory variants and a fixed-size message.
PHASES="${PHASES:-string shm}"
STRING_VARIANTS="${STRING_VARIANTS:-unix_socket cyclonedds_default cyclonedds_tuned fastdds_default fastdds_tuned zenoh_default zenoh_tuned}"
SHM_VARIANTS="${SHM_VARIANTS:-unix_socket cyclonedds_tuned cyclonedds_shm fastdds_default fastdds_shm zenoh_default zenoh_tuned}"

run_native() {
  # Drives one matrix from env: VARIANTS, FIXED, OUTDIR. Raise the open-file
  # limit for ~200 node processes (best effort).
  ulimit -n 1048576 2>/dev/null || ulimit -n 65536 2>/dev/null || true
  if ! command -v ros2 >/dev/null 2>&1; then
    [ -f "/opt/ros/$ROS_DISTRO/setup.bash" ] && source "/opt/ros/$ROS_DISTRO/setup.bash"
    [ -f "/bench_ws/install/setup.bash" ] && source "/bench_ws/install/setup.bash"
  fi

  local variants="${VARIANTS:-$STRING_VARIANTS}"
  local outdir="${OUTDIR:-$REPO/results/$ROS_DISTRO}"
  local fixed_flag=""; [ "${FIXED:-}" = "1" ] && fixed_flag="--fixed"
  mkdir -p "$outdir"

  echo "=== matrix: [$variants] x [$NODES] ${fixed_flag} -> $outdir ==="
  for v in $variants; do
    for n in $NODES; do
      python3 "$SCRIPT_DIR/run_one.py" \
        --variant "$v" --nodes "$n" \
        --rate "$RATE" --size "$SIZE" --duration "$DURATION" \
        --warmup "$WARMUP" --settle "$SETTLE" --cpu-window "$CPU_WINDOW" \
        $fixed_flag --outdir "$outdir" || echo "  !! $v n=$n failed (continuing)"
    done
  done
  python3 "$SCRIPT_DIR/aggregate.py" --indir "$outdir" --outdir "$outdir"

  if python3 -c "import matplotlib" 2>/dev/null; then
    local name; name="$(basename "$outdir")"
    python3 "$SCRIPT_DIR/plot.py" --indir "$outdir" \
      --out "$REPO/results/graphs/$name.png" --title "RMW scaling — $name" || true
  fi
  echo "=== done: $outdir/summary.md ==="
}

preflight() {
  command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not found." >&2; exit 1; }
  docker info >/dev/null 2>&1 || { echo "ERROR: cannot reach the Docker daemon (running? in the 'docker' group?)." >&2; exit 1; }
  local shm wmem
  shm=$(df -B1 --output=size /dev/shm 2>/dev/null | tail -1 | tr -d ' ')
  wmem=$(cat /proc/sys/net/core/wmem_max 2>/dev/null)
  echo "preflight: /dev/shm=$(( ${shm:-0} / 1024 / 1024 ))MB  net.core.wmem_max=${wmem:-?}  (run uses --ipc=host)"
  [ -n "$shm" ] && [ "$shm" -lt 1073741824 ] && \
    echo "  WARNING: /dev/shm < 1GB — Zenoh / Cyclone-Iceoryx SHM pools may not fit." >&2
  if [ -n "$wmem" ] && [ "$wmem" -lt 50331648 ]; then
    echo "  NOTE: rmw_unix_socket_cpp requests a 48 MiB socket buffer (SO_SNDBUF/SO_RCVBUF=50331648); net.core.wmem_max=${wmem} clamps it. Fine for this benchmark's message sizes." >&2
    echo "  To match what the RMW asks for (e.g. for larger messages): sudo sysctl -w net.core.wmem_max=50331648 net.core.rmem_max=50331648" >&2
  fi
}

# run_phase <results-subdir> <fixed 0|1> <variants>
run_phase() {
  echo "=== phase: $1 ==="
  docker run --rm \
    --ipc=host --shm-size=2g --ulimit nofile=1048576:1048576 \
    -e NODES -e RATE -e SIZE -e DURATION -e WARMUP -e SETTLE -e CPU_WINDOW \
    -e "VARIANTS=$3" -e "FIXED=$2" -e "OUTDIR=/benchmarks/results/$1" \
    -v "$REPO/results:/benchmarks/results" \
    "$IMAGE" bash /benchmarks/scripts/run_benchmark.sh --native
}

run_docker() {
  preflight
  echo "=== building $IMAGE (context: $REPO) ==="
  # --network=host: on networks that block public DNS from bridge containers,
  # build-time apt/git/cargo need the host resolver.
  docker build ${DOCKER_BUILD_NET:---network=host} \
    -f "$REPO/docker/Dockerfile" -t "$IMAGE" "$REPO"

  mkdir -p "$REPO/results"
  bash "$SCRIPT_DIR/sysinfo.sh" > "$REPO/results/system.md" 2>/dev/null || true

  for phase in $PHASES; do
    case "$phase" in
      string) run_phase "$ROS_DISTRO" 0 "${VARIANTS:-$STRING_VARIANTS}" ;;
      shm)    run_phase "${ROS_DISTRO}_shm" 1 "${VARIANTS:-$SHM_VARIANTS}" ;;
      *) echo "  ?? unknown phase '$phase' (use: string shm)" >&2 ;;
    esac
  done

  # Container wrote results as root; hand them back so they're usable sans sudo.
  docker run --rm -v "$REPO/results:/r" "$IMAGE" \
    chown -R "$(id -u):$(id -g)" /r >/dev/null 2>&1 || true

  echo "=== done ==="
  echo "  results: $REPO/results/   (summary.md per phase, system.md, graphs/)"
}

if [ "${1:-}" = "--native" ] || [ "${BENCH_IN_CONTAINER:-}" = "1" ]; then
  run_native
else
  run_docker
fi
