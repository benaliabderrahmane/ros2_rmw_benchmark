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
# Override any setting via env, e.g. a quick smoke run:
#   NODES="1 10" PHASES=string VARIANTS="unix_socket cyclonedds_tuned" ./scripts/run_benchmark.sh
# (The variant names are the keys in scripts/rmw_matrix.py.)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$SCRIPT_DIR")"

ROS_DISTRO="${ROS_DISTRO:-jazzy}"
IMAGE="${IMAGE:-rmw-bench:jazzy}"
NODES="${NODES:-1 10 50 100 200}"
RATE="${RATE:-20}"
SIZE="${SIZE:-256}"
# Tuned for the 200-node case: DDS discovery can take several seconds, so settle
# long enough to reach steady state before the measurement window starts.
DURATION="${DURATION:-30}"
WARMUP="${WARMUP:-5}"
SETTLE="${SETTLE:-10}"
CPU_WINDOW="${CPU_WINDOW:-3}"
DEGREE="${DEGREE:-1}"   # senders each node subscribes to (1 = ring, >1 = fan-out)

# Phases the one-command run does, and the variants tested in each:
#   string: variable-length string messages over the default/tuned transports.
#   shm:    fixed-size messages over the shared-memory transports.
# Set PHASES to run a subset.
PHASES="${PHASES:-string shm}"
STRING_VARIANTS="${STRING_VARIANTS:-unix_socket cyclonedds_default cyclonedds_tuned fastdds_default fastdds_tuned zenoh_default zenoh_tuned}"
SHM_VARIANTS="${SHM_VARIANTS:-unix_socket cyclonedds_tuned cyclonedds_shm fastdds_default fastdds_shm zenoh_default zenoh_tuned}"

run_native() {
  # Runs one variants x nodes matrix. Reads VARIANTS, FIXED, OUTDIR from env.
  # 200 nodes open a lot of files and sockets, so raise the fd limit if we can.
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
        --degree "$DEGREE" \
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
  # The container runs with --ipc=host, so the SHM transports use the host's
  # /dev/shm reported here; that is why we check its size.
  echo "preflight: /dev/shm=$(( ${shm:-0} / 1024 / 1024 ))MB  net.core.wmem_max=${wmem:-?}"
  [ -n "$shm" ] && [ "$shm" -lt 1073741824 ] && \
    echo "  WARNING: /dev/shm < 1GB — Zenoh / Cyclone-Iceoryx SHM pools may not fit." >&2
  if [ -n "$wmem" ] && [ "$wmem" -lt 50331648 ]; then
    echo "  rmw_unix_socket_cpp asks for a 48 MiB socket buffer (50331648 bytes); the kernel clamps it to wmem_max=${wmem}. This benchmark's messages are small, so the clamp does not matter here." >&2
    echo "  To match what the RMW asks for (e.g. for larger messages): sudo sysctl -w net.core.wmem_max=50331648 net.core.rmem_max=50331648" >&2
  fi
}

# run_phase <results-subdir> <fixed 0|1> <variants>
run_phase() {
  echo "=== phase: $1 ==="
  docker run --rm \
    --ipc=host --shm-size=2g --ulimit nofile=1048576:1048576 \
    -e NODES -e RATE -e SIZE -e DURATION -e WARMUP -e SETTLE -e CPU_WINDOW -e DEGREE \
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

  # Guard each phase so one failing phase doesn't abort the script under set -e:
  # the other phase still runs, and the chown-back below always happens (otherwise
  # a crash here would leave root-owned result files the host user can't delete).
  for phase in $PHASES; do
    case "$phase" in
      string) run_phase "$ROS_DISTRO" 0 "${VARIANTS:-$STRING_VARIANTS}" || echo "  !! string phase failed (continuing)" >&2 ;;
      shm)    run_phase "${ROS_DISTRO}_shm" 1 "${VARIANTS:-$SHM_VARIANTS}" || echo "  !! shm phase failed (continuing)" >&2 ;;
      *) echo "  ?? unknown phase '$phase' (use: string shm)" >&2 ;;
    esac
  done

  # The container runs as root, so result files land root-owned. chown them back
  # to the invoking user so they can be read and deleted without sudo on the host.
  docker run --rm -v "$REPO/results:/r" "$IMAGE" \
    chown -R "$(id -u):$(id -g)" /r >/dev/null 2>&1 || true

  echo "=== done ==="
  echo "  results: $REPO/results/   (summary.md per phase, system.md, graphs/)"
}

# Two modes, one file. With --native we run a single matrix in place; that is what
# each phase runs inside the container (see run_phase). Without it we build the
# image and orchestrate the whole run through Docker.
if [ "${1:-}" = "--native" ]; then
  run_native
else
  run_docker
fi
