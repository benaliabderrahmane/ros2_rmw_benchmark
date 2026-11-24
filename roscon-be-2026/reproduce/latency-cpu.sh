#!/bin/bash
# Slides "Latency: lowest of every default config..." and "At the same load, less CPU..." (ROS 2 Lyrical). Apex
# performance_test, publisher and subscribers in separate processes: 1 KiB to 8 MiB 1->1, and 1 KiB, 1 MiB, 4 MiB
# 1->5, at fixed rates (1-64 KiB at 1 kHz, 256 KiB at 500 Hz, 1 MiB at 100 Hz, 4-8 MiB at 30 Hz); every RMW in its
# default, tuned and shared-memory configs; 5 runs; each case in its own container (runners/run_case.py).
#
#   reproduce/latency-cpu.sh                    # as on the slides: 80 cases x 5 runs x ~40 s, ~4.5 h
#   RUNS=1 reproduce/latency-cpu.sh             # ~55 min
#   RUNS=1 ONLY="array1m_s1_unix_socket array1m_s1_fastdds_shm" reproduce/latency-cpu.sh   # chosen cases only
#
# Output: results-local/latency-cpu-<distro>-<date>/: raw runs in t5/, summary/perf_test.csv (medians) and
# figures/latency_step4.png, figures/cpu_step4.png (the slides' figures; steps 1-3 are the slide build-up).
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
RUNS="${RUNS:-5}"
ONLY="${ONLY:-}"
OUT="${OUT:-$HERE/results-local/latency-cpu-$DISTRO-$STAMP}"
if [ "$DISTRO" = jazzy ]; then
  echo "NOTE: on Jazzy, Fast DDS 2.x reads only FASTRTPS_DEFAULT_PROFILES_FILE; runners/run_case.py sets Fast DDS 3's" \
       "FASTDDS_DEFAULT_PROFILES_FILE, so fastdds_shm runs with Fast DDS defaults there." >&2
fi
host_check
build_ring
build_perf
mkdir -p "$OUT"
python3 "$HERE/scripts/gen_t5_specs.py" "$RUNS" >/dev/null  # writes specs/t5/r<k>/<case>.json
for spec in "$HERE"/specs/t5/r*/*.json; do
  k=$(basename "$(dirname "$spec")"); k=${k#r}; case=$(basename "$spec" .json)
  if [ -n "$ONLY" ] && [[ " $ONLY " != *" $case "* ]]; then continue; fi
  log "r$k $case"
  perf_case "$OUT" "$k" "$case"
done
chown_back "$OUT"
inimage "$OUT" scripts/summarize.py perf "$OUT" "$OUT/summary"
inimage "$OUT" scripts/plot_perf_figure.py "$OUT/summary" "$OUT/figures"
log "done: $OUT/figures/latency_step4.png, $OUT/figures/cpu_step4.png"
