# RMW benchmark summary

Node counts: 1, 10, 50, 100, 200

## Nodes up (recv/N)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| cyclonedds_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 0.98 |
| cyclonedds_shm | 1.0 | 1.0 | 1.0 | 0.11 | 0.08 |
| fastdds_default | 1.0 | 1.0 | 1.0 | 1.0 | 0.315 |
| fastdds_shm | 1.0 | 1.0 | 1.0 | 1.0 | 0.235 |
| zenoh_default | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| zenoh_tuned | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

## Msg delivery (survivors)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.0 | 1.0 | 1.0 | 1.0 | 0.998 |
| cyclonedds_tuned | 1.0 | 1.0 | 0.999 | 0.986 | 0.817 |
| cyclonedds_shm | 1.0 | 1.0 | 0.999 | 0.782 | 0.758 |
| fastdds_default | 1.0 | 1.0 | 0.982 | 0.964 | 0.144 |
| fastdds_shm | 1.0 | 1.0 | 0.977 | 0.962 | 0.117 |
| zenoh_default | 1.0 | 1.0 | 0.998 | 0.99 | 0.941 |
| zenoh_tuned | 1.0 | 1.0 | 0.999 | 0.99 | 0.933 |

## Discovery (s)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 0.07 | 0.07 | 0.13 | 0.24 | 0.58 |
| cyclonedds_tuned | 0.07 | 0.08 | 0.31 | 1.64 | 20.86 |
| cyclonedds_shm | 0.08 | 0.09 | 0.33 | 0.78 | 1.9 |
| fastdds_default | 0.09 | 0.16 | 1.42 | 3.72 | 74.83 |
| fastdds_shm | 0.09 | 0.15 | 1.72 | 3.88 | 79.23 |
| zenoh_default | 0.08 | 0.09 | 0.34 | 1.12 | 6.99 |
| zenoh_tuned | 0.08 | 0.09 | 0.34 | 1.15 | 7.71 |

## RAM PSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 13.2 | 32.8 | 113.6 | 214.5 | 418.8 |
| cyclonedds_tuned | 14.2 | 76.3 | 479.1 | 1363.7 | 6791.2 |
| cyclonedds_shm | 662.2 | 705.8 | 1067.7 | 809.1 | 889.6 |
| fastdds_default | 29.6 | 159.9 | 1003.5 | 2660.7 | 3748.7 |
| fastdds_shm | 30.1 | 161.9 | 1009.1 | 2671.2 | 4024.6 |
| zenoh_default | 41.9 | 93.0 | 729.1 | 2640.2 | 11186.9 |
| zenoh_tuned | 42.2 | 93.7 | 727.1 | 2686.0 | 11268.9 |

## RAM RSS (MB)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 14.4 | 144.2 | 719.8 | 1439.6 | 2883.3 |
| cyclonedds_tuned | 15.6 | 188.7 | 1094.9 | 2608.6 | 9488.1 |
| cyclonedds_shm | 17.4 | 191.7 | 1207.2 | 363.0 | 553.6 |
| fastdds_default | 31.0 | 345.4 | 2353.0 | 6367.5 | 10383.8 |
| fastdds_shm | 31.4 | 354.2 | 2378.6 | 6250.1 | 10804.2 |
| zenoh_default | 21.4 | 238.1 | 1621.0 | 4457.2 | 14856.1 |
| zenoh_tuned | 21.6 | 240.4 | 1624.2 | 4519.8 | 14966.2 |

## CPU (%)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 1.7 | 18.3 | 93.0 | 188.7 | 385.7 |
| cyclonedds_tuned | 0.7 | 12.0 | 62.0 | 132.7 | 3345.7 |
| cyclonedds_shm | 1.0 | 9.3 | 54.7 | 108.7 | 333.0 |
| fastdds_default | 1.3 | 19.0 | 113.7 | 273.7 | 3055.7 |
| fastdds_shm | 1.0 | 15.0 | 83.7 | 205.7 | 3131.3 |
| zenoh_default | 0.7 | 16.7 | 85.3 | 172.3 | 335.0 |
| zenoh_tuned | 0.7 | 16.0 | 87.3 | 173.3 | 344.3 |

## Latency p50 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 230.8 | 284.9 | 281.8 | 245.4 | 242.7 |
| cyclonedds_tuned | 88.7 | 342.2 | 344.7 | 331.3 | 4490.1 |
| cyclonedds_shm | 216.3 | 248.9 | 251.9 | 290.7 | 285.9 |
| fastdds_default | 159.2 | 400.3 | 392.6 | 391.4 | 88879.6 |
| fastdds_shm | 138.1 | 346.1 | 319.4 | 329.1 | 24431.2 |
| zenoh_default | 114.1 | 561.4 | 521.9 | 466.1 | 425.0 |
| zenoh_tuned | 115.5 | 567.6 | 542.1 | 472.1 | 427.9 |

## Latency p99 (us)

| Variant | 1 nodes | 10 nodes | 50 nodes | 100 nodes | 200 nodes |
|---|---|---|---|---|---|
| unix_socket | 244.7 | 373.8 | 355.5 | 361.5 | 365.6 |
| cyclonedds_tuned | 91.2 | 534.0 | 531.1 | 469.4 | 456460.4 |
| cyclonedds_shm | 248.0 | 367.9 | 351.4 | 325.7 | 348.7 |
| fastdds_default | 169.7 | 595.7 | 565.0 | 573.5 | 1125793.8 |
| fastdds_shm | 166.4 | 376.0 | 422.8 | 487.8 | 1412231.3 |
| zenoh_default | 117.2 | 684.6 | 681.0 | 654.8 | 17586.2 |
| zenoh_tuned | 118.7 | 667.4 | 722.1 | 668.1 | 19995.0 |
