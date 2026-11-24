#!/usr/bin/env python3
"""Run one showcase case for one RMW inside the showcase container.

Spec (JSON file, argv[1]) keys:
  name, rmw, warmup_s, measure_s,
  infra: [{role, cmd, delay_s}]          long-running processes started first
  subs:  {count, cmd, stagger_s}          N subscriber processes; '{i}' and '{out}' substituted
  probes: [{role, cmd, at_s}]             one-shot commands run during measurement (output saved)
Writes <outdir>/result.json with CPU, memory, per-role CPU and all subscriber JSON lines.
"""
import json, os, signal, subprocess, sys, time, glob, shutil

# Campaign copy of rmw-showcase scripts/run_case.py for ROS 2 Lyrical (benchmarks/runners/run_case.py).
# Changes: the variants below (default and tuned per RMW, Lyrical configs in /campaign/configs, see
# benchmarks/CONFIGS.md), a per-variant '_daemon' started before the case (zenoh router, iox-roudi), and SETUP
# for Lyrical (performance_test built from source in /pt_ws). Everything after the variant table is unchanged.
CFG = '/campaign/configs/'
ZENOHD = 'ros2 run rmw_zenoh_cpp rmw_zenohd'
ZENOH_SHM = 'transport/shared_memory/enabled=true'  # layered on Lyrical's installed default session/router configs
RMWS = {
  'unix_socket': {'RMW_IMPLEMENTATION': 'rmw_unix_socket_cpp'},
  'fastdds_default': {'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp'},
  'fastdds_shm': {'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp', 'FASTDDS_DEFAULT_PROFILES_FILE': CFG + 'fastdds_shm_perf.xml',
                  'FASTDDS_BUILTIN_TRANSPORTS': 'LARGE_DATA'},
  'cyclonedds_default': {'RMW_IMPLEMENTATION': 'rmw_cyclonedds_cpp'},
  'cyclonedds_tuned': {'RMW_IMPLEMENTATION': 'rmw_cyclonedds_cpp', 'CYCLONEDDS_URI': 'file://' + CFG + 'cyclonedds_tuned.xml'},
  'cyclonedds_shm': {'RMW_IMPLEMENTATION': 'rmw_cyclonedds_cpp', 'CYCLONEDDS_URI': 'file://' + CFG + 'cyclonedds_shm.xml',
                     '_daemon': 'iox-roudi -c ' + CFG + 'iox_roudi_perf.toml'},
  'zenoh_default': {'RMW_IMPLEMENTATION': 'rmw_zenoh_cpp', '_daemon': ZENOHD},
  'zenoh_tuned': {'RMW_IMPLEMENTATION': 'rmw_zenoh_cpp', 'ZENOH_CONFIG_OVERRIDE': ZENOH_SHM, '_daemon': ZENOHD},
  # Zenoh client-mode campaign (21 Nov 2026): nodes in client mode; the router gets its own override, never mode.
  'zenoh_client_default': {'RMW_IMPLEMENTATION': 'rmw_zenoh_cpp', 'ZENOH_CONFIG_OVERRIDE': 'mode="client"',
                           '_daemon': 'env -u ZENOH_CONFIG_OVERRIDE ' + ZENOHD},
  'zenoh_client_tuned': {'RMW_IMPLEMENTATION': 'rmw_zenoh_cpp', 'ZENOH_CONFIG_OVERRIDE': 'mode="client";' + ZENOH_SHM,
                         '_daemon': 'env ZENOH_CONFIG_OVERRIDE=' + ZENOH_SHM + ' ' + ZENOHD},
}
SETUP = 'source /opt/ros/$ROS_DISTRO/setup.bash; source /pt_ws/install/setup.bash; source /ws/install/setup.bash; ' \
        'source /show_ws/install/setup.bash; '

def cg_usage_us():
    for line in open('/sys/fs/cgroup/cpu.stat'):
        k, v = line.split()
        if k == 'usage_usec':
            return int(v)

def descendants(pid):
    out, todo = set(), [pid]
    kids = {}
    for p in os.listdir('/proc'):
        if p.isdigit():
            try:
                ppid = int(open(f'/proc/{p}/stat').read().rsplit(')', 1)[1].split()[1])
                kids.setdefault(ppid, []).append(int(p))
            except Exception:
                pass
    while todo:
        x = todo.pop()
        if x in out:
            continue
        out.add(x)
        todo += kids.get(x, [])
    return out

def proc_cpu_ticks(pid):
    try:
        f = open(f'/proc/{pid}/stat').read().rsplit(')', 1)[1].split()
        return int(f[11]) + int(f[12])
    except Exception:
        return 0

def pss_kb(pid):
    try:
        for line in open(f'/proc/{pid}/smaps_rollup'):
            if line.startswith('Pss:'):
                return int(line.split()[1])
    except Exception:
        pass
    return 0

def main():
    spec = json.load(open(sys.argv[1]))
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    env = dict(os.environ)
    env.update({k: v for k, v in RMWS[spec['rmw']].items() if not k.startswith('_')})
    extra = RMWS[spec['rmw']].get('_setup')
    env.update(spec.get('env', {}))
    env['ROS_DOMAIN_ID'] = str(spec.get('domain', 42))
    env['RCUTILS_LOGGING_BUFFERED_STREAM'] = '1'
    procs = []  # (role, Popen)
    logs = os.path.join(outdir, 'logs'); os.makedirs(logs, exist_ok=True)

    def start(role, cmd, idx=None):
        lf = open(os.path.join(logs, f'{role}{"" if idx is None else "_" + str(idx)}.log'), 'w')
        pre = SETUP + (f'source {extra}; ' if extra else '')
        p = subprocess.Popen(['bash', '-c', pre + 'exec ' + cmd], env=env, stdout=lf, stderr=subprocess.STDOUT,
                             start_new_session=True)
        procs.append((role, p))
        return p

    daemon = RMWS[spec['rmw']].get('_daemon')
    if daemon:
        start('daemon', daemon)
        time.sleep(1.5)
    t_launch = time.time()
    for inf in spec.get('infra', []):
        start(inf['role'], inf['cmd'])
        time.sleep(inf.get('delay_s', 0.5))
    subs_out = os.path.join(outdir, 'subs.jsonl')
    sp = spec.get('subs')
    t_subs = time.time()
    groups = sp if isinstance(sp, list) else ([sp] if sp else [])
    k = 0
    for g in groups:
        for i in range(g['count']):
            start('sub', g['cmd'].format(i=k, out=subs_out), k)
            k += 1
            if g.get('stagger_s'):
                time.sleep(g['stagger_s'])
    time.sleep(spec.get('warmup_s', 10))
    # measurement window
    roles = {}
    for role, p in procs:
        roles.setdefault(role, set()).update(descendants(p.pid))
    t0 = cg_usage_us(); w0 = time.time()
    tick0 = {pid: proc_cpu_ticks(pid) for s in roles.values() for pid in s}
    probe_res = {}
    probes = sorted(spec.get('probes', []), key=lambda x: x.get('at_s', 0))
    pss_samples = []
    end = w0 + spec.get('measure_s', 30)
    while time.time() < end:
        el = time.time() - w0
        while probes and probes[0].get('at_s', 0) <= el:
            pr = probes.pop(0)
            try:
                r = subprocess.run(['bash', '-c', SETUP + pr['cmd']], env=env, capture_output=True, text=True,
                                   timeout=pr.get('timeout', 60))
                probe_res[pr['role']] = (r.stdout + r.stderr)[-4000:]
            except subprocess.TimeoutExpired:
                probe_res[pr['role']] = 'TIMEOUT'
        if not pss_samples or el > spec.get('measure_s', 30) / 2 and len(pss_samples) < 2:
            pss_samples.append({role: sum(pss_kb(pid) for pid in s) for role, s in roles.items()})
        time.sleep(0.2)
    t1 = cg_usage_us(); w1 = time.time()
    tick1 = {pid: proc_cpu_ticks(pid) for pid in tick0}
    hz = os.sysconf('SC_CLK_TCK')
    role_cpu = {role: round(sum(tick1[p] - tick0[p] for p in s if p in tick0) / hz / (w1 - w0) * 100, 1)
                for role, s in roles.items()}
    alive = {role: sum(1 for r, p in procs if r == role and p.poll() is None) for role in roles}
    # stop subscribers first (they write their JSON on SIGINT), then infra
    for role, p in procs:
        if role == 'sub':
            try: os.killpg(p.pid, signal.SIGINT)
            except Exception: pass
    deadline = time.time() + 20
    for role, p in procs:
        if role == 'sub':
            try: p.wait(max(0.1, deadline - time.time()))
            except Exception: pass
    for role, p in reversed(procs):
        if role != 'sub':
            try: os.killpg(p.pid, signal.SIGINT)
            except Exception: pass
    time.sleep(3)
    for role, p in procs:
        try: os.killpg(p.pid, signal.SIGKILL)
        except Exception: pass
    subs = []
    if os.path.exists(subs_out):
        for line in open(subs_out):
            try: subs.append(json.loads(line))
            except Exception: pass
    res = {
        'name': spec['name'], 'rmw': spec['rmw'], 'measure_s': round(w1 - w0, 2),
        'cpu_total_pct': round((t1 - t0) / 1e6 / (w1 - w0) * 100, 1),
        'cpu_by_role_pct': role_cpu,
        'pss_mb_by_role': {k: round(v / 1024, 1) for k, v in pss_samples[-1].items()} if pss_samples else {},
        'pss_mb_total': round(sum(pss_samples[-1].values()) / 1024, 1) if pss_samples else 0,
        'alive_at_end': alive, 'n_subs_expected': sum(g['count'] for g in groups), 'n_subs_reported': len(subs),
        'subs': subs, 'probes': probe_res, 'spec': spec, 'rmw_env': RMWS[spec['rmw']],
    }
    json.dump(res, open(os.path.join(outdir, 'result.json'), 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('name', 'rmw', 'cpu_total_pct', 'pss_mb_total', 'n_subs_reported')}))

if __name__ == '__main__':
    main()
