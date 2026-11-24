# Benchmark image for the ROSCon Belgium 2026 runs (ROS 2 Lyrical or Jazzy: BASE=ros:<distro>-ros-base). Build context:
# this repository's root; named build context "configs" = roscon-be-2026/configs/<distro> (reproduce/common.sh).
# python3-matplotlib is added so the figures are drawn inside the image (nothing to install on the host).
#
# Every competitor is Lyrical's own apt binary: rmw_fastrtps_cpp 9.4.10 / Fast DDS 3.6.2 (in ros-base),
# rmw_cyclonedds_cpp 4.1.5 / Cyclone DDS 11.0.1 (+ its psmx_iox shared-memory plugin), rmw_zenoh_cpp 0.10.6,
# and iceoryx 2.0.6 for iox-roudi. Only rmw_unix_socket_cpp (at UNIX_SOCKET_REF) and the public harness's load
# node are built here. The Jazzy recipe (thin layer on rmw-bench:jazzy-devel) is Dockerfile.ring.jazzy.bak.
ARG BASE=ros:lyrical-ros-base
FROM ${BASE}
ARG UNIX_SOCKET_REF=v0.6.0
ARG UNIX_SOCKET_VERSION=0.6.0
ARG UNIX_SOCKET_REPO=https://github.com/benaliabderrahmane/rmw_unix_socket_cpp.git
# The commit UNIX_SOCKET_REF must resolve to (run_campaign.sh reads it with gh api). Also busts the clone's
# cache entry when the branch moves.
ARG UNIX_SOCKET_SHA=
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

# Upgrade first so every ROS package comes from the same apt sync (as rmw_unix_socket_cpp's CI does).
RUN apt-get update && apt-get -y upgrade && apt-get install -y --no-install-recommends \
      ros-${ROS_DISTRO}-rmw-cyclonedds-cpp ros-${ROS_DISTRO}-rmw-zenoh-cpp ros-${ROS_DISTRO}-iceoryx-posh \
      git build-essential cmake python3-colcon-common-extensions procps python3-matplotlib fonts-liberation \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /bench_ws/src \
 && git clone --depth 1 -b "${UNIX_SOCKET_REF}" "${UNIX_SOCKET_REPO}" /bench_ws/src/rmw_unix_socket_cpp \
 && sha=$(git -C /bench_ws/src/rmw_unix_socket_cpp rev-parse HEAD) \
 && { [ -z "${UNIX_SOCKET_SHA}" ] || [ "$sha" = "${UNIX_SOCKET_SHA}" ] \
      || { echo "rmw_unix_socket_cpp ${UNIX_SOCKET_REF} is at $sha, expected ${UNIX_SOCKET_SHA}" >&2; exit 1; }; } \
 && { grep -q "<version>${UNIX_SOCKET_VERSION}</version>" \
        /bench_ws/src/rmw_unix_socket_cpp/rmw_unix_socket_cpp/package.xml \
      || { echo "rmw_unix_socket_cpp at ${UNIX_SOCKET_REF} is not ${UNIX_SOCKET_VERSION}" >&2; exit 1; }; }

COPY bench_nodes /bench_ws/src/bench_nodes
# Lyrical removed ament_target_dependencies (deprecated since Kilted); link the same two packages through their
# CMake targets instead. Only the image's copy is changed; the harness clone stays as published.
RUN sed -i 's/^ament_target_dependencies(load_node rclcpp std_msgs)$/target_link_libraries(load_node rclcpp::rclcpp ${std_msgs_TARGETS})/' \
      /bench_ws/src/bench_nodes/CMakeLists.txt \
 && grep -q 'target_link_libraries(load_node rclcpp::rclcpp' /bench_ws/src/bench_nodes/CMakeLists.txt
RUN source /opt/ros/${ROS_DISTRO}/setup.bash && apt-get update \
 && { rosdep init 2>/dev/null || true; } && rosdep update --rosdistro "${ROS_DISTRO}" >/dev/null \
 && rosdep install --from-paths /bench_ws/src --ignore-src -y --rosdistro "${ROS_DISTRO}" \
 && rm -rf /var/lib/apt/lists/* \
 && cd /bench_ws && colcon build --merge-install --packages-select rmw_unix_socket_cpp bench_nodes \
      --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
 && rm -rf /bench_ws/build /bench_ws/log \
 && mkdir -p /benchmarks && git -C /bench_ws/src/rmw_unix_socket_cpp rev-parse HEAD > /benchmarks/RMW_UNDER_TEST_SHA

COPY scripts /benchmarks/scripts
COPY --from=configs . /benchmarks/configs
# The harness's entrypoint sources /opt/ros/$ROS_DISTRO and /bench_ws (run_benchmark.sh --native only sources
# the overlay when ros2 isn't on PATH yet, and ros:*'s own entrypoint puts it there).
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
