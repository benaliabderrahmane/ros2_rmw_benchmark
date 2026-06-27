#!/usr/bin/env python3
"""The benchmark matrix: every (RMW, config) variant and how to run it.

Each variant resolves to a RunSpec describing the environment the node
processes need, an optional discovery daemon to start first (Zenoh router /
Fast DDS Discovery Server), and which config files were applied (for the
record). The local rmw_unix_socket_cpp has no tunables, so it has a single
"default" column; the three DDS/Zenoh stacks each get default + tuned.
"""

import os
from dataclasses import dataclass, field

# configs/ is always a sibling of scripts/ -- true in the repo and in the image
# (the Dockerfile copies both under /benchmarks), so this resolves in both.
CONFIGS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "configs"))


@dataclass
class RunSpec:
    key: str
    rmw: str
    config: str               # "default", "tuned", or "shm"
    env: dict                 # extra env for the node processes
    daemon_cmd: list = None   # discovery daemon argv, or None
    daemon_env: dict = field(default_factory=dict)
    daemon_wait_s: float = 2.0
    config_files: dict = field(default_factory=dict)  # label -> path (for the record)
    notes: str = ""


def _cyclone_tuned():
    xml = os.path.join(CONFIGS_DIR, "cyclonedds_tuned.xml")
    return RunSpec(
        key="cyclonedds_tuned", rmw="rmw_cyclonedds_cpp", config="tuned",
        env={"CYCLONEDDS_URI": "file://" + xml},
        config_files={"CYCLONEDDS_URI": xml},
        notes="lo-only, spdp multicast, ParticipantIndex=none, 65500B max msg",
    )


def _fastdds_tuned():
    xml = os.path.join(CONFIGS_DIR, "fastdds_tuned.xml")
    # mutation_tries=1000 is eProsima's recommended fix for participants going
    # "deaf" when they cannot claim a unicast listening port (Fast-DDS#6383,
    # which #5767 dedups to; posted by the maintainers in that thread).
    #
    # We deliberately do NOT use a Discovery Server here. It was supposed to get
    # past the ~119-participants/host simple-discovery ceiling, but it has a
    # documented collapse when many nodes start at once (#6383): it brought up
    # 0/200 in our run, worse than plain simple discovery. We also tested raising
    # domainIDGain to move the port-collision ceiling past 200; it did not help,
    # because the real bottleneck at 200 participants on one host is the O(N^2)
    # simple-discovery traffic storm (discovery ~150 s, ~1/3 of nodes up even
    # with a 3-minute window). So simple discovery + mutation_tries is the
    # fairer tuned config; Fast DDS at 200 simultaneous nodes on one host is a
    # real limitation, not a config we can tune away.
    return RunSpec(
        key="fastdds_tuned", rmw="rmw_fastrtps_cpp", config="tuned",
        env={
            "FASTDDS_DEFAULT_PROFILES_FILE": xml,
            "RMW_FASTRTPS_USE_QOS_FROM_XML": "1",
        },
        config_files={"FASTDDS_DEFAULT_PROFILES_FILE": xml},
        notes="simple discovery + mutation_tries=1000 (Discovery Server dropped: collapses at scale, Fast-DDS#6383)",
    )


def _cyclone_shm():
    xml = os.path.join(CONFIGS_DIR, "cyclonedds_shm.xml")
    roudi = os.path.join(CONFIGS_DIR, "iox_roudi_config.toml")
    # Iceoryx zero-copy: needs the iox-roudi daemon up first, and a fixed-size
    # type (run with --fixed) or Cyclone silently falls back to the network.
    return RunSpec(
        key="cyclonedds_shm", rmw="rmw_cyclonedds_cpp", config="shm",
        env={"CYCLONEDDS_URI": "file://" + xml},
        daemon_cmd=["iox-roudi", "-c", roudi],
        daemon_wait_s=4.0,
        config_files={"CYCLONEDDS_URI": xml, "iox-roudi -c": roudi},
        notes="Iceoryx shared memory (zero-copy for fixed-size types; iox-roudi required)",
    )


def _fastdds_shm():
    xml = os.path.join(CONFIGS_DIR, "fastdds_shm.xml")
    # data_sharing=AUTOMATIC: zero-copy via SHM for plain/bounded types
    # (--fixed). Simple discovery + raised mutation_tries; compared against
    # fastdds_default, which uses the SHM transport but copies.
    return RunSpec(
        key="fastdds_shm", rmw="rmw_fastrtps_cpp", config="shm",
        env={
            "FASTDDS_DEFAULT_PROFILES_FILE": xml,
            "RMW_FASTRTPS_USE_QOS_FROM_XML": "1",
        },
        config_files={"FASTDDS_DEFAULT_PROFILES_FILE": xml},
        notes="Fast DDS data-sharing zero-copy (fixed-size types only)",
    )


def _zenoh_base_env():
    return {"RMW_IMPLEMENTATION": "rmw_zenoh_cpp"}


def _zenoh_default():
    # Default config: multicast scouting is off, so the router daemon is required.
    return RunSpec(
        key="zenoh_default", rmw="rmw_zenoh_cpp", config="default",
        env={},
        daemon_cmd=["ros2", "run", "rmw_zenoh_cpp", "rmw_zenohd"],
        daemon_env=_zenoh_base_env(),
        notes="rmw_zenohd router required (default config disables multicast scouting)",
    )


def _zenoh_tuned():
    # Enable shared memory on both router and every session via a layered
    # override, instead of editing the version-specific default json5 in place.
    shm = "transport/shared_memory/enabled=true"
    return RunSpec(
        key="zenoh_tuned", rmw="rmw_zenoh_cpp", config="tuned",
        env={"ZENOH_CONFIG_OVERRIDE": shm},
        daemon_cmd=["ros2", "run", "rmw_zenoh_cpp", "rmw_zenohd"],
        daemon_env={**_zenoh_base_env(), "ZENOH_CONFIG_OVERRIDE": shm},
        config_files={"ZENOH_CONFIG_OVERRIDE": shm},
        notes="shared_memory enabled on router + all sessions (rmw_zenohd router required)",
    )


def _simple(key, rmw):
    return RunSpec(key=key, rmw=rmw, config="default", env={})


BUILDERS = {
    "unix_socket": lambda: _simple("unix_socket", "rmw_unix_socket_cpp"),
    "cyclonedds_default": lambda: _simple("cyclonedds_default", "rmw_cyclonedds_cpp"),
    "cyclonedds_tuned": _cyclone_tuned,
    "cyclonedds_shm": _cyclone_shm,
    "fastdds_default": lambda: _simple("fastdds_default", "rmw_fastrtps_cpp"),
    "fastdds_tuned": _fastdds_tuned,
    "fastdds_shm": _fastdds_shm,
    "zenoh_default": _zenoh_default,
    "zenoh_tuned": _zenoh_tuned,
}

# Default run order (local RMW first, then each stack default->tuned->shm).
ALL_VARIANTS = [
    "unix_socket",
    "cyclonedds_default", "cyclonedds_tuned", "cyclonedds_shm",
    "fastdds_default", "fastdds_tuned", "fastdds_shm",
    "zenoh_default", "zenoh_tuned",
]


def get_spec(key):
    if key not in BUILDERS:
        raise KeyError(f"unknown variant '{key}'; known: {', '.join(BUILDERS)}")
    return BUILDERS[key]()
