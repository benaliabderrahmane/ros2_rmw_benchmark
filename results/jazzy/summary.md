# RMW benchmark summary

Node counts: 1, 10, 50, 100, 200

## Nodes up (recv/N)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_default | 1.0 | 1.0 | 0.56 | 0.28 | 0.15 |
| cyclonedds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.985 |
| fastdds_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.31 |
| fastdds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.385 |
| zenoh_default | 1.0 | 1.0 | 0.96 | 0.98 | 1.0 |
| zenoh_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.99 |

## Msg delivery (survivors)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 0.997 |
| cyclonedds_default | 1.0 | 1.0 | 0.875 | 0.874 | 0.937 |
| cyclonedds_tuned | 1.0 | 1.0 | 0.998 | 0.987 | 0.797 |
| fastdds_default | 1.0 | 1.0 | 0.978 | 0.964 | 0.127 |
| fastdds_tuned | 1.0 | 1.0 | 0.979 | 0.967 | 0.164 |
| zenoh_default | 1.0 | 1.0 | 0.948 | 0.974 | 0.954 |
| zenoh_tuned | 1.0 | 1.0 | 0.998 | 0.988 | 0.935 |

## Discovery (s)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 0.1 | 0.07 | 0.13 | 0.23 | 0.57 |
| cyclonedds_default | 0.07 | 0.08 | 0.25 | 0.26 | 0.23 |
| cyclonedds_tuned | 0.07 | 0.08 | 0.32 | 1.09 | 26.75 |
| fastdds_default | 0.08 | 0.16 | 1.69 | 3.57 | 99.61 |
| fastdds_tuned | 0.09 | 0.23 | 1.64 | 3.65 | 70.23 |
| zenoh_default | 0.08 | 0.09 | 10.61 | 10.63 | 6.31 |
| zenoh_tuned | 0.08 | 0.09 | 0.33 | 1.39 | 10.78 |

## RAM PSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 13.3 | 31.9 | 108.2 | 205.2 | 405.6 |
| cyclonedds_default | 14.4 | 51.5 | 202.1 | 202.2 | 202.6 |
| cyclonedds_tuned | 14.3 | 51.1 | 373.8 | 1106.1 | 4707.6 |
| fastdds_default | 25.7 | 108.4 | 741.4 | 2140.3 | 3675.3 |
| fastdds_tuned | 25.3 | 108.8 | 740.2 | 2135.3 | 3586.4 |
| zenoh_default | 42.6 | 91.4 | 683.2 | 2292.0 | 8611.4 |
| zenoh_tuned | 42.6 | 91.6 | 692.7 | 2363.0 | 8477.2 |

## RAM RSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 14.6 | 146.3 | 732.0 | 1461.7 | 2932.8 |
| cyclonedds_default | 15.7 | 167.2 | 600.2 | 600.7 | 600.3 |
| cyclonedds_tuned | 15.6 | 166.3 | 1005.0 | 2381.0 | 7450.1 |
| fastdds_default | 27.0 | 296.5 | 2060.2 | 5536.3 | 10285.6 |
| fastdds_tuned | 26.7 | 299.1 | 2101.8 | 5692.8 | 10371.7 |
| zenoh_default | 21.9 | 241.1 | 1599.2 | 4163.3 | 12398.9 |
| zenoh_tuned | 22.1 | 243.4 | 1610.0 | 4242.2 | 12274.0 |

## CPU (%)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.3 | 16.0 | 81.3 | 157.0 | 322.0 |
| cyclonedds_default | 0.3 | 9.7 | 28.0 | 25.3 | 29.0 |
| cyclonedds_tuned | 0.7 | 9.3 | 51.0 | 98.3 | 3326.0 |
| fastdds_default | 0.7 | 14.3 | 78.7 | 192.0 | 3172.7 |
| fastdds_tuned | 1.0 | 15.0 | 78.7 | 195.3 | 3149.7 |
| zenoh_default | 1.0 | 13.0 | 88.0 | 152.0 | 241.3 |
| zenoh_tuned | 0.7 | 14.3 | 66.3 | 126.0 | 239.0 |

## Latency p50 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 127.6 | 187.6 | 167.6 | 134.9 | 122.7 |
| cyclonedds_default | 67.2 | 241.2 | 215.0 | 214.3 | 209.0 |
| cyclonedds_tuned | 69.5 | 235.0 | 239.2 | 218.8 | 3612.8 |
| fastdds_default | 114.2 | 299.5 | 287.6 | 294.2 | 82690.3 |
| fastdds_tuned | 113.1 | 297.0 | 296.3 | 288.8 | 502.5 |
| zenoh_default | 91.6 | 514.2 | 423.6 | 355.1 | 296.7 |
| zenoh_tuned | 92.4 | 492.9 | 420.4 | 360.2 | 297.8 |

## Latency p99 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 164.7 | 253.7 | 230.5 | 234.0 | 230.4 |
| cyclonedds_default | 68.9 | 308.6 | 324.3 | 318.0 | 317.3 |
| cyclonedds_tuned | 94.2 | 346.5 | 342.8 | 347.7 | 452582.5 |
| fastdds_default | 179.4 | 408.9 | 388.0 | 448.1 | 1143955.1 |
| fastdds_tuned | 115.1 | 362.9 | 384.0 | 434.3 | 1055063.3 |
| zenoh_default | 93.4 | 559.9 | 575.1 | 555.4 | 7902.9 |
| zenoh_tuned | 108.0 | 610.8 | 564.5 | 558.3 | 6366.0 |
