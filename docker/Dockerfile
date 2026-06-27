# syntax=docker/dockerfile:1.7
# ============================================================================
# ROS 2 Jazzy image with four RMW implementations, for the scaling benchmark.
# Everything is built into one overlay (/bench_ws) so a single
# `source /bench_ws/install/setup.bash` exposes all four, picked at runtime via
# RMW_IMPLEMENTATION:
#
#   1. rmw_fastrtps_cpp    apt, from the base image (Jazzy sync)        [default]
#   2. rmw_cyclonedds_cpp  source: CycloneDDS 0.10.5 + rmw_cyclonedds jazzy
#   3. rmw_zenoh_cpp       source: rmw_zenoh jazzy (vendors zenoh-c via cargo)
#   4. rmw_unix_socket_cpp source: cloned from GitHub at UNIX_SOCKET_REF
#
# Fast DDS comes from apt on purpose: the benchmark nodes and rmw_unix_socket_cpp
# link the apt fastcdr / rosidl_typesupport_fastrtps_*, and a source Fast DDS
# would risk ABI skew against them. The apt build is pinned to the Jazzy sync and
# ships the `fastdds` CLI (Discovery Server).
#
# docker run flags this image expects (set by run_benchmark.sh):
#   --ipc=host --shm-size=2g          SHM transports + the unix-socket registry
#   --ulimit nofile=1048576:1048576   ~200 node processes open a lot of fds
# ============================================================================

ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base

ARG ROS_DISTRO=jazzy
ENV ROS_DISTRO=${ROS_DISTRO}
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

# Pinned refs. Branch/tag are the active pins; known-good SHAs are noted for
# byte-exact rebuilds (uncomment the checkout lines to use them).
#   CycloneDDS core  tag 0.10.5
#   rmw_cyclonedds   branch jazzy
#   rmw_zenoh        branch jazzy   (zenoh_cpp_vendor 0.2.9; Rust pinned to 1.75)
#   rmw_unix_socket  branch main
ARG CYCLONEDDS_REF=0.10.5
ARG RMW_CYCLONEDDS_REF=jazzy
ARG RMW_ZENOH_REF=jazzy
ARG UNIX_SOCKET_REF=main
ARG UNIX_SOCKET_REPO=https://github.com/benaliabderrahmane/rmw_unix_socket_cpp.git
ARG RUST_VERSION=1.75.0

WORKDIR /bench_ws

RUN apt-get update && apt-get install -y --no-install-recommends \
      git build-essential cmake curl ca-certificates \
      clang libclang-dev procps \
      python3 python3-colcon-common-extensions python3-rosdep python3-matplotlib \
    && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rust/rustup \
    CARGO_HOME=/opt/rust/cargo \
    PATH=/opt/rust/cargo/bin:${PATH}
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
      | sh -s -- -y --no-modify-path --default-toolchain ${RUST_VERSION} --profile minimal \
    && rustc --version && cargo --version

RUN rosdep init 2>/dev/null || true && rosdep update --rosdistro "${ROS_DISTRO}"

# --- CycloneDDS core + rmw_cyclonedds (heavy, stable -> early & cached) -------
RUN mkdir -p /bench_ws/src \
    && git clone -b ${CYCLONEDDS_REF} https://github.com/eclipse-cyclonedds/cyclonedds.git \
         /bench_ws/src/cyclonedds \
    && git clone -b ${RMW_CYCLONEDDS_REF} https://github.com/ros2/rmw_cyclonedds.git \
         /bench_ws/src/rmw_cyclonedds

RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
    && apt-get update \
    && rosdep install --from-paths /bench_ws/src --ignore-src -y \
         --rosdistro "${ROS_DISTRO}" --skip-keys "cyclonedds" \
    && rm -rf /var/lib/apt/lists/*

RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
    && colcon build --merge-install --packages-up-to rmw_cyclonedds_cpp \
         --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_IDLC=NO \
           -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF -DBUILD_DDSPERF=OFF

# --- rmw_zenoh_cpp (heavy: cargo builds zenoh-c -> early & cached) -----------
RUN git clone -b ${RMW_ZENOH_REF} https://github.com/ros2/rmw_zenoh.git /bench_ws/src/rmw_zenoh

RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
    && apt-get update \
    && rosdep install --from-paths /bench_ws/src/rmw_zenoh --ignore-src -y \
         --rosdistro "${ROS_DISTRO}" \
    && rm -rf /var/lib/apt/lists/*

RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
    && source /bench_ws/install/setup.bash \
    && colcon build --merge-install --packages-up-to rmw_zenoh_cpp \
         --cmake-args -DCMAKE_BUILD_TYPE=Release

# --- rmw_unix_socket_cpp + the benchmark nodes (these change most, so build last) -
# The RMW under test lives in its own repo; we clone it (rather than vendor a copy)
# so this benchmark repo stays self-contained. To benchmark your own fork or pin a
# commit, build with --build-arg UNIX_SOCKET_REPO=<url> and/or UNIX_SOCKET_REF=<branch|tag|sha>.
RUN git clone -b ${UNIX_SOCKET_REF} ${UNIX_SOCKET_REPO} \
      /bench_ws/src/rmw_unix_socket_cpp
COPY bench_nodes /bench_ws/src/bench_nodes

RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
    && apt-get update \
    && rosdep install --from-paths \
         /bench_ws/src/rmw_unix_socket_cpp /bench_ws/src/bench_nodes \
         --ignore-src -y --rosdistro "${ROS_DISTRO}" \
    && rm -rf /var/lib/apt/lists/*

RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
    && source /bench_ws/install/setup.bash \
    && colcon build --merge-install \
         --packages-select rmw_unix_socket_cpp bench_nodes \
         --cmake-args -DCMAKE_BUILD_TYPE=Release

# Benchmark scripts + configs, baked in so the image is self-contained.
COPY scripts /benchmarks/scripts
COPY configs /benchmarks/configs
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
