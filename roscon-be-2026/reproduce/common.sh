#!/bin/bash
# Shared by reproduce/*.sh (sourced, not run): settings, image builds, one performance_test case, plotting.
# Needs Docker (with BuildKit), bash and python3 on the host; everything else runs in the images.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"  # roscon-be-2026/
REPO="$(cd "$HERE/.." && pwd)"                            # this repository (Dockerfile.ring's build context)
DISTRO="${DISTRO:-lyrical}"
BASE="${BASE:-ros:${DISTRO}-ros-base}"
# rmw_unix_socket_cpp as measured for the talk: the v0.6.0 release candidate, branch bench/v0.6.0-rc at e9847f5 (its
# package.xml still says 0.5.0). The release itself: UNIX_SOCKET_REF=v0.6.0 UNIX_SOCKET_VERSION=0.6.0 UNIX_SOCKET_SHA=
UNIX_SOCKET_REF="${UNIX_SOCKET_REF:-bench/v0.6.0-rc}"
UNIX_SOCKET_VERSION="${UNIX_SOCKET_VERSION:-0.5.0}"
UNIX_SOCKET_SHA="${UNIX_SOCKET_SHA-e9847f5e853ca3fde19b8ec2dd18e84eb12593ac}"
RING_IMAGE="${RING_IMAGE:-rmw-bench:${DISTRO}-roscon}"
PERF_IMAGE="${PERF_IMAGE:-rmw-perf:${DISTRO}-roscon}"
STAMP="$(date +%Y-%m-%d_%H%M)"
log() { echo "=== $(date +%T) $*"; }

host_check() {  # the talk's host limits (README, "Host"): warn, never fail
  local r w
  r=$(cat /proc/sys/net/core/rmem_max); w=$(cat /proc/sys/net/core/wmem_max)
  if [ "$r" -lt 50331648 ] || [ "$w" -lt 50331648 ]; then
    echo "NOTE: net.core.rmem_max=$r, wmem_max=$w; the talk's host had 48 MiB or more (see README, Host)." >&2
  fi
}

build_ring() {
  log "building $RING_IMAGE (base $BASE, rmw_unix_socket_cpp $UNIX_SOCKET_REF)"
  docker build --network=host -f "$HERE/docker/Dockerfile.ring" --build-context configs="$HERE/configs/$DISTRO" \
    --build-arg BASE="$BASE" --build-arg UNIX_SOCKET_REF="$UNIX_SOCKET_REF" \
    --build-arg UNIX_SOCKET_VERSION="$UNIX_SOCKET_VERSION" --build-arg UNIX_SOCKET_SHA="$UNIX_SOCKET_SHA" \
    -t "$RING_IMAGE" "$REPO"
}

build_ts200() {  # the 200-node benchmark node (scripts/ts200/src), built in the image, kept in .build/
  export TS200_DIR="$HERE/.build/ts200-$DISTRO"
  mkdir -p "$TS200_DIR" && cp -r "$HERE/scripts/ts200/src" "$TS200_DIR/"
  log "building the 200-node benchmark node in $TS200_DIR"
  docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$TS200_DIR:/ts200" -w /ts200 --entrypoint bash \
    "$RING_IMAGE" -c 'source /opt/ros/$ROS_DISTRO/setup.bash && colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release \
      >/dev/null && test -x install/bench_multi/lib/bench_multi/multi_node'
}

build_perf() {  # Lyrical: performance_test 2.4.0 from source (as on the slides); Jazzy: its apt package
  local from=source
  [ "$DISTRO" = jazzy ] && from=apt
  log "building $PERF_IMAGE (performance_test from $from)"
  docker build --network=host -f "$HERE/docker/Dockerfile.perf" --build-arg BASE="$RING_IMAGE" \
    --build-arg PT_FROM="$from" -t "$PERF_IMAGE" "$HERE/docker"
}

perf_case() {  # one performance_test case in its own container: perf_case <results dir> <run k> <case>
  local out=$1 k=$2 case=$3
  mkdir -p "$out/t5/r$k"
  docker run --rm --sysctl net.unix.max_dgram_qlen=4096 --shm-size=4g --ulimit nofile=1048576:1048576 \
    --ulimit rtprio=99 --ulimit memlock=-1 --cap-add=SYS_NICE --entrypoint bash \
    -v "$HERE/runners:/campaign/runners:ro" -v "$HERE/configs/$DISTRO:/campaign/configs:ro" \
    -v "$HERE/specs:/campaign/specs:ro" -v "$out:/campaign/results" "$PERF_IMAGE" \
    -c "python3 /campaign/runners/run_case.py /campaign/specs/t5/r$k/$case.json /campaign/results/t5/r$k/$case" | tail -1
}

chown_back() {  # the containers write as root
  docker run --rm --entrypoint chown -v "$1:/r" "$RING_IMAGE" -R "$(id -u):$(id -g)" /r
}

inimage() {  # run a python script of scripts/ inside the ring image (matplotlib is there): inimage <out dir> <args...>
  local out=$1; shift
  docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e MPLCONFIGDIR=/tmp -e SLIDE_LABELS="${SLIDE_LABELS:-}" \
    -v "$HERE:$HERE:ro" -v "$out:$out" -w "$HERE" --entrypoint python3 "$RING_IMAGE" "$@"
}
