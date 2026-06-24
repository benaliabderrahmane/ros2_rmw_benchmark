#!/usr/bin/env bash
# Source ROS Jazzy + the benchmark overlay, then exec the requested command.
# `set -u` is avoided: ROS setup.bash references unbound vars internally.
set -e

ROS_DISTRO="${ROS_DISTRO:-jazzy}"
source "/opt/ros/${ROS_DISTRO}/setup.bash"
if [ -f /bench_ws/install/setup.bash ]; then
  source /bench_ws/install/setup.bash
fi

echo "[entrypoint] ROS_DISTRO=${ROS_DISTRO} RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-<unset>} nofile=$(ulimit -n)" >&2

exec "$@"
