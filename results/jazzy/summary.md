# RMW benchmark summary

Node counts: 1, 10, 50, 100, 200

## Nodes up (recv/N)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_default | 1.0 | 1.0 | 0.6 | 0.27 | 0.145 |
| cyclonedds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.97 |
| fastdds_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.265 |
| fastdds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.27 |
| zenoh_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.99 |
| zenoh_tuned | 1.0 | 1.0 | 1.0 | 0.98 | 0.98 |

## Msg delivery (survivors)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 0.998 |
| cyclonedds_default | 1.0 | 1.0 | 0.937 | 0.843 | 0.906 |
| cyclonedds_tuned | 1.0 | 1.0 | 0.998 | 0.987 | 0.794 |
| fastdds_default | 1.0 | 0.999 | 0.98 | 0.971 | 0.108 |
| fastdds_tuned | 1.0 | 1.0 | 0.983 | 0.962 | 0.141 |
| zenoh_default | 1.0 | 1.0 | 0.998 | 0.992 | 0.957 |
| zenoh_tuned | 1.0 | 1.0 | 0.999 | 0.969 | 0.919 |

## Discovery (s)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 0.09 | 0.07 | 0.13 | 0.24 | 0.59 |
| cyclonedds_default | 0.08 | 0.08 | 0.24 | 0.26 | 0.27 |
| cyclonedds_tuned | 0.07 | 0.08 | 0.33 | 1.59 | 24.47 |
| fastdds_default | 0.09 | 0.39 | 1.62 | 3.61 | 88.58 |
| fastdds_tuned | 0.08 | 0.22 | 1.48 | 3.62 | 91.41 |
| zenoh_default | 0.08 | 0.09 | 0.33 | 1.13 | 6.03 |
| zenoh_tuned | 0.08 | 0.09 | 0.34 | 10.66 | 11.1 |

## RAM PSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 13.1 | 31.6 | 107.9 | 204.7 | 405.3 |
| cyclonedds_default | 14.2 | 51.1 | 202.2 | 201.7 | 202.1 |
| cyclonedds_tuned | 14.1 | 50.7 | 371.4 | 1111.3 | 4617.0 |
| fastdds_default | 24.8 | 108.1 | 740.2 | 2132.0 | 3418.5 |
| fastdds_tuned | 24.4 | 108.2 | 740.9 | 2137.8 | 3405.2 |
| zenoh_default | 42.1 | 90.8 | 692.5 | 2331.9 | 8553.9 |
| zenoh_tuned | 42.4 | 90.8 | 692.1 | 2289.2 | 8673.1 |

## RAM RSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 14.4 | 143.6 | 718.5 | 1439.5 | 2888.8 |
| cyclonedds_default | 15.5 | 164.0 | 593.8 | 592.8 | 593.7 |
| cyclonedds_tuned | 15.4 | 164.4 | 989.7 | 2361.4 | 7308.9 |
| fastdds_default | 26.2 | 293.2 | 2047.9 | 5533.3 | 9752.2 |
| fastdds_tuned | 25.7 | 295.1 | 2081.1 | 5663.1 | 9901.8 |
| zenoh_default | 21.5 | 236.6 | 1584.7 | 4159.4 | 12241.8 |
| zenoh_tuned | 22.0 | 238.3 | 1591.6 | 4125.5 | 12381.2 |

## CPU (%)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.3 | 15.0 | 81.0 | 161.3 | 318.0 |
| cyclonedds_default | 0.7 | 10.0 | 26.3 | 26.0 | 26.3 |
| cyclonedds_tuned | 1.3 | 9.3 | 50.7 | 95.0 | 3335.0 |
| fastdds_default | 0.7 | 13.7 | 78.3 | 193.0 | 3140.7 |
| fastdds_tuned | 1.0 | 13.0 | 78.0 | 194.7 | 3140.3 |
| zenoh_default | 0.3 | 13.3 | 68.7 | 127.7 | 242.0 |
| zenoh_tuned | 0.7 | 14.7 | 69.7 | 163.7 | 239.0 |

## Latency p50 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 128.2 | 173.7 | 185.5 | 136.3 | 122.6 |
| cyclonedds_default | 68.6 | 230.3 | 206.8 | 207.9 | 208.4 |
| cyclonedds_tuned | 89.0 | 239.9 | 243.6 | 220.5 | 3822.6 |
| fastdds_default | 113.1 | 275.8 | 292.1 | 288.2 | 350.3 |
| fastdds_tuned | 116.0 | 320.7 | 291.1 | 282.6 | 356.9 |
| zenoh_default | 90.7 | 488.4 | 429.0 | 364.4 | 295.3 |
| zenoh_tuned | 90.9 | 457.1 | 424.2 | 353.9 | 294.7 |

## Latency p99 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 149.8 | 258.3 | 236.2 | 236.1 | 229.9 |
| cyclonedds_default | 69.7 | 317.1 | 320.5 | 317.8 | 323.3 |
| cyclonedds_tuned | 98.3 | 373.3 | 342.6 | 344.2 | 453588.9 |
| fastdds_default | 115.0 | 382.9 | 397.1 | 435.0 | 1880345.2 |
| fastdds_tuned | 128.6 | 426.6 | 388.3 | 450.3 | 868880.3 |
| zenoh_default | 107.8 | 618.2 | 579.6 | 551.2 | 4983.8 |
| zenoh_tuned | 107.9 | 570.2 | 583.7 | 574.6 | 4058.1 |
