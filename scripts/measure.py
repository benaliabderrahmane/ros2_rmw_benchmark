#!/usr/bin/env python3
"""Resource sampling helpers (stdlib only).

PSS is the fair RAM metric for a many-process comparison: shared library pages
(librclcpp, the RMW .so, libc, ...) are counted once, split proportionally
across the processes that map them, so summing PSS across N nodes does not
double-count what they share. RSS is reported alongside for reference.
"""

import os
import time

CLK_TCK = os.sysconf("SC_CLK_TCK")


def _read_int_field(path, key):
    """Return the integer value (kB) of a `Key:  <n> kB` line, or 0."""
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(key):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return 0


def pss_kb(pid):
    return _read_int_field(f"/proc/{pid}/smaps_rollup", "Pss:")


def rss_kb(pid):
    return _read_int_field(f"/proc/{pid}/status", "VmRSS:")


def cpu_ticks(pid):
    """utime + stime in clock ticks for the whole process (all its threads)."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            data = f.read()
        # comm may contain spaces/parens; split after the closing ')'.
        fields = data[data.rfind(")") + 2:].split()
        return int(fields[11]) + int(fields[12])  # utime, stime (0-based after comm)
    except (OSError, ValueError, IndexError):
        return 0


def pgid_members(pgid):
    """All live pids in process group `pgid`.

    Discovery daemons are launched via wrappers (`fastdds discovery` is a python
    script; `ros2 run` is a launcher) that fork the real server as a child, so
    measuring/killing the launcher pid alone misses (or orphans) the server.
    Running the daemon in its own session lets us address the whole group.
    """
    members = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat") as f:
                fields = f.read().rsplit(")", 1)[1].split()
            if int(fields[2]) == pgid:  # state(0) ppid(1) pgrp(2)
                members.append(int(entry))
        except (OSError, ValueError, IndexError):
            continue
    return members


def sample_memory(pids):
    """Point-in-time PSS/RSS totals (MB) across the given pids."""
    total_pss = sum(pss_kb(p) for p in pids)
    total_rss = sum(rss_kb(p) for p in pids)
    return {
        "pss_mb": round(total_pss / 1024.0, 1),
        "rss_mb": round(total_rss / 1024.0, 1),
    }


def sample_cpu(pids, interval_s):
    """Aggregate CPU percent across pids over `interval_s` (100% == one core)."""
    before = {p: cpu_ticks(p) for p in pids}
    time.sleep(interval_s)
    delta = 0
    for p in pids:
        delta += cpu_ticks(p) - before.get(p, 0)
    cpu_seconds = delta / CLK_TCK
    return round(100.0 * cpu_seconds / interval_s, 1)
