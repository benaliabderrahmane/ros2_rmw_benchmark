#!/usr/bin/env bash
# Print the machine's hardware/OS so a result set records where it was measured.
# Run this on the same machine you ran the benchmark on, so the output records
# what hardware produced the numbers:
#   bash scripts/sysinfo.sh > results/system.md
set -e

# `|| os=""` so a missing /etc/os-release doesn't trip set -e and blank the file;
# the ${os:-unknown} fallback below then fills it in.
os="$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME")" || os=""
cpu="$(LC_ALL=C lscpu 2>/dev/null | sed -n 's/^Model name:[[:space:]]*//p' | head -1)"

cat <<EOF
# Test system

| field | value |
|---|---|
| date | $(date -u '+%Y-%m-%d %H:%M UTC') |
| cpu | ${cpu:-unknown} |
| logical cpus | $(nproc 2>/dev/null) |
| ram | $(free -h 2>/dev/null | awk '/^Mem:/{print $2}') |
| kernel | $(uname -sr) |
| os | ${os:-unknown} |
| /dev/shm | $(df -h /dev/shm 2>/dev/null | awk 'NR==2{print $2}') |
| net.core.wmem_max | $(cat /proc/sys/net/core/wmem_max 2>/dev/null) |
| net.core.rmem_max | $(cat /proc/sys/net/core/rmem_max 2>/dev/null) |
EOF
