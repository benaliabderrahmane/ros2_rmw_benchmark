# Sourced by the benchmark drivers. wait_quiet: before each test, wait 15 s after the previous one, then until no
# container is running and the whole machine is under 10% busy (3 s sample from /proc/stat), so tests never overlap
# or inherit each other's load. Gives up waiting after 30 min.
cpu_busy_pct() {
  local a b i total=0 idle
  read -r -a a < /proc/stat; sleep 3; read -r -a b < /proc/stat
  idle=$(( (b[4] + b[5]) - (a[4] + a[5]) ))
  for i in 1 2 3 4 5 6 7 8; do total=$(( total + b[i] - a[i] )); done
  echo $(( 100 * (total - idle) / (total > 0 ? total : 1) ))
}

wait_quiet() {
  sleep 15
  local waited=0 others busy
  while :; do
    # .bench-hold (benchmarks/): other heavy work (a deck build, a render) is running; start no test meanwhile.
    # BENCH_HOLD_EXEMPT=1: a driver run on purpose while the others are held.
    while [ -z "${BENCH_HOLD_EXEMPT:-}" ] && [ -e "$(dirname "${BASH_SOURCE[0]}")/../.bench-hold" ]; do sleep 5; done
    others=$(docker ps -q | wc -l)
    busy=$(cpu_busy_pct)
    if [ "$others" -eq 0 ] && [ "$busy" -lt 10 ]; then return 0; fi
    if [ "$waited" -ge 1800 ]; then
      echo "WARN: not quiet after 30 min (containers: $others, CPU busy: $busy%); going on"
      return 0
    fi
    sleep 5; waited=$((waited + 8))
  done
}
