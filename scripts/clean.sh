#!/usr/bin/env bash
# Remove benchmark artifacts. SCOPED to this suite — it never touches other
# Docker images, containers, or anything you didn't create here. Safe anytime.
#
#   bash scripts/clean.sh         # image + stray containers + results
#   bash scripts/clean.sh --all   # also: build cache, base image, /dev/shm
#
# Don't use `docker system prune -a` for this; it would delete unrelated images too.
set -e
IMAGE="${IMAGE:-rmw-bench:jazzy}"
BENCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== stray $IMAGE containers =="
docker ps -aq --filter ancestor="$IMAGE" | xargs -r docker rm -f

echo "== image $IMAGE =="
docker rmi "$IMAGE" 2>/dev/null || echo "  (not present)"

echo "== generated results + native build dirs =="
rm -rf "$BENCH_DIR"/results/*/ "$BENCH_DIR"/build "$BENCH_DIR"/install "$BENCH_DIR"/log 2>/dev/null || true

if [ "${1:-}" = "--all" ]; then
  echo "== unused Docker build cache (shared across builds) =="
  docker builder prune -f
  echo "== base image (if unused elsewhere) =="
  docker rmi ros:jazzy-ros-base 2>/dev/null || echo "  (not present / in use)"
  echo "== host /dev/shm leftovers =="
  # SHM files left behind by the benchmarked RMWs: ros2_uds_* (unix_socket),
  # *.zenoh (Zenoh), iceoryx_* (Cyclone + iceoryx). Safe to remove when no run is live.
  rm -f /dev/shm/ros2_uds_* /dev/shm/*.zenoh /dev/shm/iceoryx_* 2>/dev/null \
    || echo "  need privileges: sudo rm -f /dev/shm/ros2_uds_* /dev/shm/*.zenoh /dev/shm/iceoryx_*"
else
  cat <<'EOF'

Heavier reclaim NOT done (re-run with --all, or do it manually):
  docker builder prune -f                                            # unused build cache (tens of GB)
  docker rmi ros:jazzy-ros-base                                      # base image (~1.5 GB)
  sudo rm -f /dev/shm/ros2_uds_* /dev/shm/*.zenoh /dev/shm/iceoryx_*  # SHM leftovers (when nothing is running)
EOF
fi
echo "done."
