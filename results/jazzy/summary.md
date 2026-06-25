# RMW benchmark summary

Node counts: 1, 10, 50, 100, 200

## Nodes up (recv/N)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_default | 1.0 | 1.0 | 0.6 | 0.3 | 0.14 |
| cyclonedds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.975 |
| fastdds_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.27 |
| fastdds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| zenoh_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.98 |
| zenoh_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

## Msg delivery (survivors)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 0.998 |
| cyclonedds_default | 1.0 | 1.0 | 0.937 | 0.937 | 0.874 |
| cyclonedds_tuned | 1.0 | 1.0 | 0.998 | 0.988 | 0.799 |
| fastdds_default | 1.0 | 1.0 | 0.978 | 0.971 | 0.123 |
| fastdds_tuned | 1.0 | 0.965 | 0.851 | 0.297 | 0.0 |
| zenoh_default | 1.0 | 1.0 | 0.999 | 0.992 | 0.937 |
| zenoh_tuned | 1.0 | 1.0 | 0.998 | 0.99 | 0.952 |

## Discovery (s)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 0.1 | 0.08 | 0.14 | 0.23 | 0.55 |
| cyclonedds_default | 0.07 | 0.08 | 0.27 | 0.26 | 0.27 |
| cyclonedds_tuned | 0.07 | 0.08 | 0.31 | 1.53 | 27.18 |
| fastdds_default | 0.09 | 0.22 | 1.74 | 3.29 | 76.46 |
| fastdds_tuned | 0.09 | 1.19 | 5.09 | 22.85 | — |
| zenoh_default | 0.08 | 0.09 | 0.32 | 1.06 | 6.06 |
| zenoh_tuned | 0.08 | 0.09 | 0.38 | 1.14 | 6.17 |

## RAM PSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 46.9 | 65.5 | 141.7 | 238.6 | 438.2 |
| cyclonedds_default | 14.4 | 51.3 | 202.5 | 202.5 | 202.0 |
| cyclonedds_tuned | 14.4 | 51.1 | 372.8 | 1113.2 | 4509.7 |
| fastdds_default | 25.5 | 108.6 | 741.1 | 2135.5 | 3605.4 |
| fastdds_tuned | 39.6 | 120.7 | 736.1 | 876.2 | 1506.0 |
| zenoh_default | 43.1 | 91.4 | 696.0 | 2300.0 | 8400.8 |
| zenoh_tuned | 42.5 | 91.6 | 706.8 | 2310.8 | 8482.5 |

## RAM RSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 48.2 | 481.7 | 2410.3 | 4818.9 | 9647.8 |
| cyclonedds_default | 15.7 | 166.3 | 600.7 | 600.6 | 599.6 |
| cyclonedds_tuned | 15.7 | 166.7 | 1001.7 | 2386.1 | 7224.9 |
| fastdds_default | 26.9 | 298.7 | 2107.5 | 5700.4 | 10494.7 |
| fastdds_tuned | 27.1 | 298.0 | 2074.0 | 2786.2 | 5410.3 |
| zenoh_default | 22.0 | 241.0 | 1610.3 | 4173.4 | 12179.3 |
| zenoh_tuned | 21.9 | 241.5 | 1624.2 | 4189.3 | 12275.6 |

## CPU (%)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.7 | 16.0 | 80.3 | 157.3 | 318.3 |
| cyclonedds_default | 0.7 | 10.0 | 26.0 | 29.0 | 26.0 |
| cyclonedds_tuned | 0.7 | 10.0 | 48.0 | 95.7 | 3324.7 |
| fastdds_default | 1.0 | 13.7 | 79.7 | 196.0 | 3096.7 |
| fastdds_tuned | 1.0 | 12.0 | 67.3 | 163.3 | 254.7 |
| zenoh_default | 0.7 | 14.3 | 66.3 | 131.7 | 237.3 |
| zenoh_tuned | 1.0 | 14.0 | 67.0 | 130.0 | 247.7 |

## Latency p50 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 126.8 | 189.8 | 169.0 | 135.2 | 123.1 |
| cyclonedds_default | 68.4 | 216.0 | 211.4 | 214.8 | 203.4 |
| cyclonedds_tuned | 76.9 | 240.5 | 242.3 | 216.3 | 3724.9 |
| fastdds_default | 113.9 | 310.4 | 291.9 | 288.3 | 32634.5 |
| fastdds_tuned | 113.7 | 321.8 | 287.6 | 279.3 | — |
| zenoh_default | 91.1 | 483.1 | 424.4 | 360.4 | 296.0 |
| zenoh_tuned | 90.3 | 477.3 | 421.4 | 351.7 | 295.7 |

## Latency p99 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 164.8 | 255.0 | 237.3 | 238.9 | 242.2 |
| cyclonedds_default | 69.9 | 325.3 | 318.7 | 323.7 | 318.3 |
| cyclonedds_tuned | 112.8 | 401.3 | 338.0 | 345.7 | 452673.7 |
| fastdds_default | 179.1 | 367.5 | 397.8 | 466.6 | 1229407.6 |
| fastdds_tuned | 115.8 | 421.5 | 404.3 | 161728.0 | — |
| zenoh_default | 110.2 | 571.1 | 580.9 | 563.9 | 4081.6 |
| zenoh_tuned | 107.8 | 579.8 | 571.5 | 569.4 | 8197.9 |
