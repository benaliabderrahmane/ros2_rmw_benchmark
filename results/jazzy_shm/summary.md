# RMW benchmark summary

Node counts: 1, 10, 50, 100, 200

## Nodes up (recv/N)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_shm | 1.0 | 0.8 | 1.0 | 0.2 | 0.055 |
| fastdds_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.31 |
| fastdds_shm | 1.0 | 1.0 | 1.0 | 1.0 | 0.23 |
| zenoh_default | 1.0 | 1.0 | 1.0 | 0.98 | 0.995 |
| zenoh_tuned | 1.0 | 1.0 | 1.0 | 0.98 | 0.96 |

## Msg delivery (survivors)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 0.999 | 0.998 |
| cyclonedds_tuned | 1.0 | 1.0 | 0.996 | 0.985 | 0.631 |
| cyclonedds_shm | 1.0 | 0.889 | 0.999 | 0.71 | 0.73 |
| fastdds_default | 1.0 | 0.999 | 0.98 | 0.94 | 0.154 |
| fastdds_shm | 1.0 | 0.998 | 0.982 | 0.942 | 0.129 |
| zenoh_default | 1.0 | 1.0 | 0.997 | 0.971 | 0.765 |
| zenoh_tuned | 1.0 | 1.0 | 0.997 | 0.964 | 0.717 |

## Discovery (s)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 0.07 | 0.07 | 0.13 | 0.3 | 0.7 |
| cyclonedds_tuned | 0.06 | 0.07 | 0.58 | 1.56 | 19.97 |
| cyclonedds_shm | 0.07 | 0.08 | 0.46 | 1.03 | 1.29 |
| fastdds_default | 0.07 | 0.34 | 1.67 | 5.54 | 81.08 |
| fastdds_shm | 0.07 | 0.35 | 1.55 | 6.19 | 94.43 |
| zenoh_default | 0.06 | 0.08 | 0.49 | 2.04 | 16.89 |
| zenoh_tuned | 0.12 | 0.09 | 0.52 | 10.68 | 14.73 |

## RAM PSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 46.7 | 66.2 | 146.9 | 247.9 | 451.7 |
| cyclonedds_tuned | 14.3 | 76.1 | 484.3 | 1392.4 | 4912.4 |
| cyclonedds_shm | 662.4 | 700.4 | 1061.0 | 926.3 | 817.4 |
| fastdds_default | 30.1 | 160.0 | 1000.4 | 2670.0 | 3990.2 |
| fastdds_shm | 30.3 | 161.5 | 1005.6 | 2671.0 | 3760.3 |
| zenoh_default | 42.2 | 94.3 | 751.4 | 2854.6 | 11108.9 |
| zenoh_tuned | 41.6 | 93.4 | 741.9 | 2753.0 | 11987.0 |

## RAM RSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 47.8 | 479.8 | 2396.6 | 4792.2 | 9589.6 |
| cyclonedds_tuned | 15.6 | 189.2 | 1098.4 | 2634.7 | 7417.8 |
| cyclonedds_shm | 17.3 | 171.1 | 1192.1 | 710.6 | 387.1 |
| fastdds_default | 31.5 | 344.9 | 2305.2 | 6617.6 | 10705.1 |
| fastdds_shm | 31.6 | 354.3 | 2366.5 | 6227.2 | 10220.1 |
| zenoh_default | 21.5 | 239.2 | 1636.4 | 4661.5 | 13731.6 |
| zenoh_tuned | 21.2 | 235.3 | 1612.6 | 4533.1 | 15525.0 |

## CPU (%)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 2.3 | 10.0 | 36.0 | 72.7 | 162.3 |
| cyclonedds_tuned | 0.3 | 6.3 | 29.0 | 58.0 | 1777.0 |
| cyclonedds_shm | 1.0 | 5.7 | 35.0 | 63.3 | 52.0 |
| fastdds_default | 0.7 | 9.7 | 51.7 | 126.7 | 1759.7 |
| fastdds_shm | 0.7 | 7.7 | 40.7 | 110.0 | 1702.3 |
| zenoh_default | 0.7 | 10.7 | 53.7 | 139.3 | 1451.0 |
| zenoh_tuned | 0.7 | 12.7 | 48.7 | 131.3 | 1425.3 |

## Latency p50 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 201.5 | 118.0 | 100.4 | 87.8 | 102.7 |
| cyclonedds_tuned | 46.3 | 210.6 | 183.4 | 150.6 | 198.3 |
| cyclonedds_shm | 216.9 | 197.3 | 177.2 | 194.2 | 185.5 |
| fastdds_default | 83.0 | 233.8 | 206.1 | 192.3 | 552.8 |
| fastdds_shm | 79.5 | 224.4 | 196.7 | 190.1 | 5715.6 |
| zenoh_default | 64.2 | 372.3 | 302.2 | 273.7 | 248.4 |
| zenoh_tuned | 71.8 | 374.8 | 301.9 | 228.3 | 217.7 |

## Latency p99 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 534.2 | 453.3 | 347.9 | 276.3 | 493.7 |
| cyclonedds_tuned | 139.4 | 560.4 | 504.8 | 505.6 | 963978.7 |
| cyclonedds_shm | 421.8 | 363.5 | 479.3 | 434.8 | 427.9 |
| fastdds_default | 396.1 | 435.3 | 430.2 | 4555.0 | 1117366.9 |
| fastdds_shm | 280.3 | 439.9 | 488.4 | 1255.0 | 811393.0 |
| zenoh_default | 371.0 | 910.4 | 734.1 | 1182.7 | 2247848.4 |
| zenoh_tuned | 365.9 | 986.8 | 695.7 | 887.5 | 1772443.7 |
