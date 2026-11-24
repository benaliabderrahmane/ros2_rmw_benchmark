#!/usr/bin/env python3
"""Write the performance_test specs: specs/t5/r<k>/<case>.json for k = 1..RUNS (argv[1], default 5).

The rmw-showcase T5 sweep (its scripts/gen_t5.py), without the devel-only variants:
- sizes 1 KB to 8 MB;
- separate publisher and subscriber processes;
- 1->1 for every size, and 1->5 for 1 KB, 1 MB and 4 MB;
- every RMW in its default and tuned configs (keys of benchmarks/runners/run_case.py's RMWS, see CONFIGS.md).
  fastdds_shm publishes loaned samples (--zero-copy): performance_test refuses that unless the RMW can really
  loan, which is part of the proof that its config takes effect. cyclonedds_shm publishes by copy (see ZERO_COPY).

Each case runs in its own container through the campaign copy of rmw-showcase's run_case.py (runners/). Logs land in
/campaign/results/t5/r<k>/<case>, with performance_test latencies in seconds.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
SIZES = [('Array1k', 1000), ('Array16k', 1000), ('Array64k', 1000), ('Array256k', 500),
         ('Array1m', 100), ('Array4m', 30), ('Array8m', 30)]
FAN = {'Array1k', 'Array1m', 'Array4m'}
RMWS = ['unix_socket', 'fastdds_default', 'fastdds_shm', 'cyclonedds_default', 'cyclonedds_tuned', 'cyclonedds_shm',
        'zenoh_default', 'zenoh_tuned']  # keys of runners/run_case.py's RMWS
# Loaned samples only where the RMW offers them: rmw_cyclonedds 4.1.5 reports can_loan_messages() false for these
# types even with psmx_iox loaded (perf_test then refuses --zero-copy); its samples still cross iceoryx by copy.
ZERO_COPY = {'fastdds_shm'}
PT = '/pt_ws/install/lib/performance_test/perf_test'  # Apex performance_test 2.4.0, built from source (Dockerfile.perf)

shutil.rmtree(os.path.join(HERE, 'specs', 't5'), ignore_errors=True)  # no stale cases from an older variant set
n = 0
for k in range(1, RUNS + 1):
    d = os.path.join(HERE, 'specs', 't5', f'r{k}')
    os.makedirs(d, exist_ok=True)
    for msg, rate in SIZES:
        for nsub in (1, 5):
            if nsub == 5 and msg not in FAN:
                continue
            for rmw in RMWS:
                case = f'{msg.lower()}_s{nsub}_{rmw}'
                out = f'/campaign/results/t5/r{k}/{case}'
                zc = ' --zero-copy' if rmw in ZERO_COPY else ''
                common = f'-c rclcpp-single-threaded-executor -m {msg} -r {rate} -t perf_{msg} --ignore 5{zc}'
                infra = [{'role': f'sub{i}', 'delay_s': 0.3,
                          'cmd': f'{PT} {common} -p 0 -s 1 --expected-num-pubs 1 --max-runtime 32 -l {out}/sub{i}.json'}
                         for i in range(nsub)]
                infra.append({'role': 'pub', 'delay_s': 0.5,
                              'cmd': f'{PT} {common} -p 1 -s 0 --expected-num-subs {nsub} --max-runtime 30 '
                                     f'-l {out}/pub.json'})
                with open(os.path.join(d, f'{case}.json'), 'w') as f:
                    json.dump({'name': f't5_{msg}_s{nsub}', 'rmw': rmw, 'warmup_s': 6, 'measure_s': 28,
                               'infra': infra}, f, indent=1)
                n += 1
print(n)
