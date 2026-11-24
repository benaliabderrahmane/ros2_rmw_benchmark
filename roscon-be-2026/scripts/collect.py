#!/usr/bin/env python3
"""Medians across the campaign's runs, for the talk.

  python3 scripts/collect.py --results results --out results/summary
  python3 scripts/collect.py --selftest

**Ring** (results/ring/r*/<phase>/result_<variant>_n<N>.json, from the public ros2_rmw_benchmark):
- bring-up = discovery_time_s, launch to the last node's first message. It counts only runs where every
  node came up; the other runs are reported, not hidden;
- nodes up, CPU, PSS, and latency p50/p99.

**performance_test** (results/t5/r*/<case>/{sub*,pub}.json and result.json; latencies in seconds): mean latency;
tail = median of the per-second maximum latency (perf_test logs per-second aggregates, no percentiles);
delivered = received / (received + lost) from the subscribers' own sequence-gap count (the publisher's log covers
another time window, which pushed received/sent above 100 %); CPU and PSS summed over publisher and subscribers.

**iRobot** (results/t6/r*/<suite>/<topology>/<rmw>/<proc>_log/{latency_total,resources}.txt): mean latency,
lost %, CPU, RSS. In multi-client topologies the harness keeps statistics only for the first client node of the
client process (the others report 0 messages and nan), so that node's latency stands for the process.

**Variants** are <stack>_<config>: config default, tuned or shm (see CONFIGS.md); unix_socket has one config,
and iRobot's fastrtps_* folders are Fast DDS. The .md tables put each stack's configs side by side in one row
("default / tuned / shm"; "·" = that config isn't in this benchmark); the .csv files are long format with
stack and config columns.

Writes ring.md, ring.csv, perf_test.md, perf_test.csv, irobot.md, irobot.csv and deck_numbers.json (the numbers
slides 20-22 use).
"""
import argparse
import csv
import glob
import json
import math
import os
import re
import statistics as st
import tempfile


CONFIG_ORDER = ['default', 'tuned', 'shm']


def split_variant(name):
    """cyclonedds_tuned -> ('cyclonedds', 'tuned'). iRobot names Fast DDS by its RMW (fastrtps_*), and
    unix_socket has a single config. Names without a config part (older runs) count as default."""
    if name.startswith('unix_socket'):
        return 'unix_socket', 'default'
    stack, _, config = name.rpartition('_')
    if not stack:
        stack, config = name, 'default'
    return ('fastdds' if stack == 'fastrtps' else stack), config


def side_by_side(f, cells, metrics):
    """cells: {variant: {metric: value}}. One row per stack; each metric cell is 'default / tuned / shm'."""
    keys = {v: split_variant(v) for v in cells}
    configs = sorted({c for _, c in keys.values()},
                     key=lambda c: (CONFIG_ORDER.index(c) if c in CONFIG_ORDER else len(CONFIG_ORDER), c))
    stacks = sorted({st_ for st_, _ in keys.values()}, key=lambda x: (x != 'unix_socket', x))
    by = {keys[v]: c for v, c in cells.items()}
    cfg = ' / '.join(configs)
    f.write('| RMW | ' + ' | '.join(f'{label} ({cfg})' for _, label in metrics) + ' |\n')
    f.write('|---' * (len(metrics) + 1) + '|\n')
    for x in stacks:
        f.write(f'| {x} | ' + ' | '.join(' / '.join(fmt(by[(x, c)][m]) if (x, c) in by else '·' for c in configs)
                                       for m, _ in metrics) + ' |\n')
    f.write('\n')


def write_csv(path, head, rows):
    """rows: {(group..., variant): {col: value}}; the variant (last key part) is split into stack and config."""
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        cols = list(next(iter(rows.values())).keys()) if rows else []
        w.writerow(head + ['stack', 'config'] + cols)
        for k in sorted(rows, key=str):
            w.writerow(list(k) + list(split_variant(k[head.index('variant')])) + [rows[k][c] for c in cols])


def med(xs):
    return round(st.median(xs), 2) if xs else None


def ring(results):
    cells = {}
    for f in glob.glob(os.path.join(results, 'ring', 'r*', '*', 'result_*.json')):
        phase = os.path.basename(os.path.dirname(f))
        d = json.load(open(f))
        c = cells.setdefault((phase, d['variant'], d['nodes']),
                             {'runs': 0, 'bringup': [], 'nodes_up': [], 'cpu': [], 'pss': [], 'p50': [], 'p99': []})
        c['runs'] += 1
        up = d.get('delivery_ratio_nodes') or 0.0
        c['nodes_up'].append(up)
        if up >= 1.0 and d.get('discovery_time_s') is not None:
            c['bringup'].append(d['discovery_time_s'])
        for k, src in (('cpu', 'cpu_total_pct'), ('pss', 'ram_total_pss_mb'), ('p50', 'lat_p50_us'),
                       ('p99', 'lat_p99_us')):
            if d.get(src) is not None:
                c[k].append(d[src])
    return {k: {'runs': c['runs'], 'all_up_runs': len(c['bringup']), 'bringup_s': med(c['bringup']),
                'bringup_min_s': min(c['bringup'], default=None), 'bringup_max_s': max(c['bringup'], default=None),
                'nodes_up': med(c['nodes_up']), 'cpu_pct': med(c['cpu']), 'pss_mb': med(c['pss']),
                'lat_p50_us': med(c['p50']), 'lat_p99_us': med(c['p99'])} for k, c in cells.items()}


def perf(results):
    cases = {}
    for d in glob.glob(os.path.join(results, 't5', 'r*', '*')):
        m = re.match(r'(array\w+?)_s(\d+)_(.+)$', os.path.basename(d))
        if not m or not os.path.exists(os.path.join(d, 'result.json')):
            continue
        msg, nsub, rmw = m.group(1), int(m.group(2)), m.group(3)
        recv = lost = n = 0
        s = 0.0
        maxima = []
        for f in glob.glob(os.path.join(d, 'sub*.json')):
            try:
                rows = json.load(open(f))['analysis_results']
            except (OSError, ValueError, KeyError):
                continue
            for r in rows:
                recv += r['num_samples_received']
                lost += r.get('num_samples_lost', 0)
                if r['latency_n']:
                    n += r['latency_n']
                    s += r['latency_mean'] * r['latency_n']
                    if r.get('latency_max') is not None:
                        maxima.append(r['latency_max'])
        res = json.load(open(os.path.join(d, 'result.json')))
        c = cases.setdefault((msg, nsub, rmw), {'runs': 0, 'mean_us': [], 'tail_us': [], 'delivered_pct': [],
                                                'cpu_pct': [], 'pss_mb': []})
        c['runs'] += 1
        if n:
            c['mean_us'].append(s / n * 1e6)
        if maxima:
            c['tail_us'].append(st.median(maxima) * 1e6)
        if recv + lost:
            c['delivered_pct'].append(100.0 * recv / (recv + lost))
        for k, src in (('cpu_pct', 'cpu_total_pct'), ('pss_mb', 'pss_mb_total')):
            if res.get(src) is not None:
                c[k].append(res[src])
    return {k: {'runs': c['runs'], **{m: med(c[m]) for m in ('mean_us', 'tail_us', 'delivered_pct', 'cpu_pct', 'pss_mb')}}
            for k, c in cases.items()}


def node_rows(path):
    """latency_all.txt: per-node CSV rows, each section after its own 'node,topic,...' header."""
    rows, head = [], None
    for line in open(path):
        line = line.strip()
        if line.startswith('node,'):
            head = line.split(',')
        elif head and line and not line.endswith(':'):
            rows.append(dict(zip(head, line.split(','))))
    return rows


def irobot(results):
    cells = {}
    for d in glob.glob(os.path.join(results, 't6', 'r*', '*', '*', '*', '')):
        suite, topo, rmw = d.rstrip(os.sep).split(os.sep)[-3:]
        recv, wsum, lost, cpu, rss = 0, 0.0, 0.0, 0.0, 0
        for lg in glob.glob(os.path.join(d, '*_log')):
            lt = os.path.join(lg, 'latency_total.txt')
            if os.path.exists(lt):
                for x in csv.DictReader(open(lt)):
                    k, mean = int(float(x['received_msgs'])), float(x['mean_us'])
                    if k > 0 and not math.isfinite(mean):
                        la = os.path.join(lg, 'latency_all.txt')
                        nodes = [(int(float(r['received_msgs'])), float(r['mean_us'])) for r in
                                 (node_rows(la) if os.path.exists(la) else [])
                                 if float(r.get('received_msgs') or 0) > 0 and math.isfinite(float(r['mean_us']))]
                        k = sum(nk for nk, _ in nodes)
                        mean = sum(nk * nm for nk, nm in nodes) / k if k else mean
                    if k > 0:
                        recv += k
                        wsum += mean * k
                        lost += min(float(x['lost_perc']), 100.0) * k
            rs = os.path.join(lg, 'resources.txt')
            if os.path.exists(rs):
                rows = list(csv.DictReader(open(rs)))[2:]  # the first samples are start-up
                if rows:
                    cpu += st.mean(float(x['cpu_perc']) for x in rows)
                    rss += max(int(x['rss_KB']) for x in rows)
        c = cells.setdefault((suite, topo, rmw), {'runs': 0, 'mean_us': [], 'lost_pct': [], 'cpu_pct': [], 'rss_mb': []})
        c['runs'] += 1
        if recv:
            c['mean_us'].append(wsum / recv)
            c['lost_pct'].append(lost / recv)
        c['cpu_pct'].append(cpu)
        c['rss_mb'].append(rss / 1024)
    return {k: {'runs': c['runs'], **{m: med(c[m]) for m in ('mean_us', 'lost_pct', 'cpu_pct', 'rss_mb')}}
            for k, c in cells.items()}


def fmt(v):
    return '-' if v is None else v if isinstance(v, str) else f'{v:g}'


def write(results, out, ref):
    os.makedirs(out, exist_ok=True)
    rg, pt, ir = ring(results), perf(results), irobot(results)
    write_csv(os.path.join(out, 'ring.csv'), ['phase', 'variant', 'nodes'], rg)
    write_csv(os.path.join(out, 'perf_test.csv'), ['msg', 'subs', 'variant'], pt)
    write_csv(os.path.join(out, 'irobot.csv'), ['suite', 'topology', 'variant'], ir)
    with open(os.path.join(out, 'ring.md'), 'w') as f:
        for phase in sorted({k[0] for k in rg}):
            f.write(f'## ring, {phase}\n\nBring-up counts only runs where every node came up '
                    '(all-up / runs; min-max in ring.csv). Medians across runs.\n\n')
            for n in sorted({k[2] for k in rg if k[0] == phase}):
                f.write(f'### N = {n}\n\n')
                side_by_side(f, {k[1]: {**rg[k], 'up': f"{rg[k]['all_up_runs']}/{rg[k]['runs']}"}
                                 for k in rg if k[0] == phase and k[2] == n},
                             [('up', 'all-up / runs'), ('bringup_s', 'bring-up s'), ('nodes_up', 'nodes up'),
                              ('cpu_pct', 'CPU %'), ('pss_mb', 'PSS MB'), ('lat_p50_us', 'p50 µs'),
                              ('lat_p99_us', 'p99 µs')])
    with open(os.path.join(out, 'perf_test.md'), 'w') as f:
        f.write('Medians across runs. tail = median of the per-second maximum latency (perf_test logs no percentiles); '
                'delivered = received / (received + lost), from the subscribers\' sequence gaps; CPU % and PSS are '
                'summed over the publisher and subscriber processes.\n\n')
        for g in sorted({(k[0], k[1]) for k in pt}):
            f.write(f'## performance_test {g[0]} 1->{g[1]}\n\n')
            side_by_side(f, {k[2]: pt[k] for k in pt if (k[0], k[1]) == g},
                         [('mean_us', 'mean µs'), ('tail_us', 'tail µs'), ('delivered_pct', 'delivered %'),
                          ('cpu_pct', 'CPU %'), ('pss_mb', 'PSS MB'), ('runs', 'runs')])
    with open(os.path.join(out, 'irobot.md'), 'w') as f:
        for g in sorted({(k[0], k[1]) for k in ir}):
            f.write(f'## iRobot {g[0]} / {g[1]}\n\n')
            side_by_side(f, {k[2]: ir[k] for k in ir if (k[0], k[1]) == g},
                         [('mean_us', 'mean µs'), ('lost_pct', 'lost %'), ('cpu_pct', 'CPU %'), ('rss_mb', 'RSS MB'),
                          ('runs', 'runs')])
    sha_file = os.path.join(results, 'RMW_UNDER_TEST_SHA')
    deck = {'rmw_unix_socket_cpp': {'ref': ref, 'sha': open(sha_file).read().strip() if os.path.exists(sha_file) else None},
            'ring_string': {'bringup_s_n200': {}, 'all_up_runs_n200': {}, 'runs_n200': {}, 'pss_mb': {}, 'cpu_pct': {}},
            'perf_test_mean_us': {}, 'perf_test_tail_us': {}, 'perf_test_delivered_pct': {}, 'perf_test_cpu_pct': {}}
    for (phase, variant, n), c in rg.items():
        if phase != 'string':
            continue
        r = deck['ring_string']
        if n == 200:
            r['bringup_s_n200'][variant] = c['bringup_s']
            r['all_up_runs_n200'][variant] = c['all_up_runs']
            r['runs_n200'][variant] = c['runs']
        r['pss_mb'].setdefault(variant, {})[str(n)] = c['pss_mb']
        r['cpu_pct'].setdefault(variant, {})[str(n)] = c['cpu_pct']
    for (msg, nsub, rmw), c in pt.items():
        deck['perf_test_mean_us'].setdefault(f'{msg}_s{nsub}', {})[rmw] = c['mean_us']
        deck['perf_test_delivered_pct'].setdefault(f'{msg}_s{nsub}', {})[rmw] = c['delivered_pct']
        deck['perf_test_tail_us'].setdefault(f'{msg}_s{nsub}', {})[rmw] = c['tail_us']
        deck['perf_test_cpu_pct'].setdefault(f'{msg}_s{nsub}', {})[rmw] = c['cpu_pct']
    with open(os.path.join(out, 'deck_numbers.json'), 'w') as f:
        json.dump(deck, f, indent=1, sort_keys=True)
    return rg, pt, ir


def selftest():
    with tempfile.TemporaryDirectory() as t:
        for r, (up, disc) in enumerate([(1.0, 2.0), (1.0, 4.0), (0.5, 9.0)], 1):
            p = os.path.join(t, 'ring', f'r{r}', 'string')
            os.makedirs(p)
            json.dump({'variant': 'unix_socket', 'nodes': 200, 'delivery_ratio_nodes': up, 'discovery_time_s': disc,
                       'cpu_total_pct': 50, 'ram_total_pss_mb': 100, 'lat_p50_us': 30, 'lat_p99_us': 90},
                      open(os.path.join(p, 'result_unix_socket_n200.json'), 'w'))
        for r, lat, recv, lost in ((1, 2e-5, 100, 0), (2, 4e-5, 99, 1)):
            p = os.path.join(t, 't5', f'r{r}', 'array1k_s1_unix_socket')
            os.makedirs(p)
            json.dump({'cpu_total_pct': 2.0 * r, 'pss_mb_total': 50.0}, open(os.path.join(p, 'result.json'), 'w'))
            json.dump({'analysis_results': [{'num_samples_received': recv, 'num_samples_lost': lost, 'latency_n': recv,
                                             'latency_mean': lat, 'latency_max': 2 * lat}]},
                      open(os.path.join(p, 'sub0.json'), 'w'))
            json.dump({'analysis_results': [{'num_samples_sent': 100}]}, open(os.path.join(p, 'pub.json'), 'w'))
        p = os.path.join(t, 't6', 'r1', 'suite', 'topo', 'unix_socket', 'node_log')
        os.makedirs(p)
        open(os.path.join(p, 'latency_total.txt'), 'w').write('received_msgs,mean_us,late_perc,lost_perc\n10,50,0,0\n')
        open(os.path.join(p, 'resources.txt'), 'w').write('cpu_perc,rss_KB\n5,1000\n5,1000\n10,2048\n20,4096\n')
        p = os.path.join(t, 't6', 'r1', 'suite', 'topo', 'unix_socket', 'cli_log')  # multi-client: nan total
        os.makedirs(p)
        open(os.path.join(p, 'latency_total.txt'), 'w').write('received_msgs,mean_us,late_perc,lost_perc\n10,nan,0,0\n')
        open(os.path.join(p, 'latency_all.txt'), 'w').write(
            '\nClients stats:\nnode,topic,size_b,received_msgs,late_msgs,too_late_msgs,lost_msgs,mean_us\n'
            'client_node,t,100,10,0,0,0,70\nmulti_node_1,t,0,0,0,0,0,nan\n')
        # default and tuned of one stack, in each benchmark, land side by side in one row
        for v, disc in (('cyclonedds_default', 8.0), ('cyclonedds_tuned', 5.0)):
            json.dump({'variant': v, 'nodes': 200, 'delivery_ratio_nodes': 1.0, 'discovery_time_s': disc},
                      open(os.path.join(t, 'ring', 'r1', 'string', f'result_{v}_n200.json'), 'w'))
        for v in ('zenoh_default', 'zenoh_tuned'):
            p = os.path.join(t, 't5', 'r1', f'array1k_s1_{v}')
            os.makedirs(p)
            json.dump({}, open(os.path.join(p, 'result.json'), 'w'))
        for v in ('fastrtps_default', 'fastrtps_shm'):
            os.makedirs(os.path.join(t, 't6', 'r1', 'suite', 'topo', v, 'node_log'))
        rg, pt, ir = write(t, os.path.join(t, 'summary'), 'v0.6.0')
        assert [split_variant(v) for v in ('unix_socket', 'unix_socket_default', 'fastrtps_shm', 'zenoh', 'fastdds_tuned')] \
            == [('unix_socket', 'default')] * 2 + [('fastdds', 'shm'), ('zenoh', 'default'), ('fastdds', 'tuned')]
        md = open(os.path.join(t, 'summary', 'ring.md')).read()
        assert '| cyclonedds | 1/1 / 1/1 | 8 / 5 |' in md and '| unix_socket | 2/3 / · | 3 / · |' in md, md
        assert '| zenoh | - / - |' in open(os.path.join(t, 'summary', 'perf_test.md')).read()
        assert '| fastdds | ' in open(os.path.join(t, 'summary', 'irobot.md')).read()
        assert 'phase,variant,nodes,stack,config,' in open(os.path.join(t, 'summary', 'ring.csv')).read()
        c = rg[('string', 'unix_socket', 200)]
        assert (c['runs'], c['all_up_runs'], c['bringup_s'], c['nodes_up']) == (3, 2, 3.0, 1.0), c
        assert pt[('array1k', 1, 'unix_socket')] == {'runs': 2, 'mean_us': 30.0, 'tail_us': 60.0, 'delivered_pct': 99.5,
                                                     'cpu_pct': 3.0, 'pss_mb': 50.0}, pt
        i = ir[('suite', 'topo', 'unix_socket')]
        assert (i['mean_us'], i['cpu_pct'], i['rss_mb']) == (60, 15, 4.0), i
        deck = json.load(open(os.path.join(t, 'summary', 'deck_numbers.json')))
        assert deck['ring_string']['bringup_s_n200'] == {'unix_socket': 3.0, 'cyclonedds_default': 8.0,
                                                         'cyclonedds_tuned': 5.0}, deck
    print('selftest ok')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results'))
    ap.add_argument('--out')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        selftest()
    else:
        env = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'campaign.env')).read()
        ref = re.search(r'^UNIX_SOCKET_REF=(\S+)', env, re.M).group(1)
        rg, pt, ir = write(a.results, a.out or os.path.join(a.results, 'summary'), ref)
        print(f'ring cells {len(rg)} · performance_test cases {len(pt)} · iRobot cells {len(ir)} -> {a.out}')
