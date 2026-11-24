#!/bin/bash
# Slide "200 nodes started at once" (ROS 2 Lyrical). 200 processes, one ROS node each with 5 publishers and 5
# subscriptions (1,000 topics, 256 B at 20 Hz), all started at once; a node not receiving on all 5 within 120 s is
# restarted, 3 times at most; every RMW runs the full 10 min; 3 runs. CPU and memory come from each container's cgroup.
#
#   reproduce/200-nodes.sh                                           # as on the slide: 5 RMWs x 3 runs x 10 min, ~2.7 h
#   RUNS=1 VARIANTS="unix_socket zenoh_default" reproduce/200-nodes.sh  # a quicker look
#   DISTRO=jazzy reproduce/200-nodes.sh                              # the same on ROS 2 Jazzy
#
# Output: results-local/200-nodes-<distro>-<date>/: one JSON and one cgroup CSV per run, summary.json, timeseries.png
# and slide_figure.png (the slide's figure).
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
RUNS="${RUNS:-3}"
export VARIANTS="${VARIANTS:-unix_socket zenoh_default zenoh_client cyclonedds_tuned fastdds_tuned}"
export TS200_ARGS="${TS200_ARGS:---tail 100000}"  # run the full 10 min even once all 200 are up, as on the slide
export OUT="${OUT:-$HERE/results-local/200-nodes-$DISTRO-$STAMP}"
# Jazzy's Fast DDS 2.x reads only FASTRTPS_DEFAULT_PROFILES_FILE, which the harness does not set: label it honestly.
[ "$DISTRO" = jazzy ] && export SLIDE_LABELS="${SLIDE_LABELS:-fastdds_tuned=Fast DDS (default)}"
host_check
build_ring
build_ts200
RING_IMAGE="$RING_IMAGE" bash "$HERE/scripts/run_ts200.sh" "$RUNS"
inimage "$OUT" scripts/plot_timeseries.py "$OUT"
inimage "$OUT" scripts/plot_slide_figure.py "$OUT"
log "done: $OUT/slide_figure.png"
