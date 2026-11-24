Medians across runs. tail = median of the per-second maximum latency (perf_test logs no percentiles); delivered = received / (received + lost), from the subscribers' sequence gaps; CPU % and PSS are summed over the publisher and subscriber processes.

## performance_test array16k 1->1

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 37.05 / · / · | 102.04 / · / · | 100 / · / · | 4.5 / · / · | 53.2 / · / · | 5 / · / · |
| cyclonedds | 48.01 / 40.18 / 28.47 | 73.89 / 62.47 / 41.1 | 100 / 100 / 100 | 5.6 / 4.2 / 3.4 | 24.2 / 22.4 / 1456.4 | 5 / 5 / 5 |
| fastdds | 52.65 / · / 38.44 | 79.83 / · / 53.39 | 100 / · / 100 | 5.9 / · / 4.7 | 40.4 / · / 61.4 | 5 / · / 5 |
| zenoh | 78.45 / 81.97 / · | 109.97 / 147.72 / · | 100 / 100 / · | 10.6 / 10.7 / · | 69.9 / 130.4 / · | 5 / 5 / · |

## performance_test array1k 1->1

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 24.12 / · / · | 36.98 / · / · | 100 / · / · | 3.4 / · / · | 53.1 / · / · | 5 / · / · |
| cyclonedds | 37.8 / 36.9 / 26.08 | 54.16 / 52.91 / 39.29 | 100 / 100 / 100 | 3.9 / 3.9 / 3.2 | 22.3 / 22.2 / 1456.3 | 5 / 5 / 5 |
| fastdds | 50.44 / · / 37.38 | 70.61 / · / 53.85 | 100 / · / 100 | 5.7 / · / 4.6 | 38.8 / · / 59.9 | 5 / · / 5 |
| zenoh | 74.09 / 79.78 / · | 118.31 / 141.71 / · | 100 / 100 / · | 9.9 / 10.5 / · | 70 / 130.9 / · | 5 / 5 / · |

## performance_test array1k 1->5

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 35.84 / · / · | 50.36 / · / · | 100 / · / · | 13.7 / · / · | 62.8 / · / · | 5 / · / · |
| cyclonedds | 41.67 / 51.11 / 30.55 | 60.24 / 70.89 / 45.96 | 100 / 100 / 100 | 16.1 / 15.9 / 12.3 | 40.8 / 40.7 / 1477.8 | 5 / 5 / 5 |
| fastdds | 61.5 / · / 46.32 | 86.05 / · / 67.01 | 100 / · / 100 | 22.1 / · / 18 | 75.2 / · / 135.3 | 5 / · / 5 |
| zenoh | 105.77 / 108.67 / · | 161.27 / 163.61 / · | 100 / 100 / · | 39.7 / 41.4 / · | 88.6 / 159.1 / · | 5 / 5 / · |

## performance_test array1m 1->1

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 110.63 / · / · | 125.26 / · / · | 100 / · / · | 1.2 / · / · | 59.3 / · / · | 5 / · / · |
| cyclonedds | 691.48 / 326.07 / 145.67 | 732.85 / 370.2 / 160.74 | 100 / 100 / 100 | 10.7 / 4.4 / 1.7 | 30.5 / 29.2 / 1459.5 | 5 / 5 / 5 |
| fastdds | 343.07 / · / 95.58 | 402.95 / · / 115.76 | 100 / · / 100 | 4.6 / · / 1.1 | 43.2 / · / 79.1 | 5 / · / 5 |
| zenoh | 593.95 / 255.18 / · | 764.91 / 286.84 / · | 100 / 100 / · | 11.4 / 2.8 / · | 79.1 / 135.5 / · | 5 / 5 / · |

## performance_test array1m 1->5

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 276.55 / · / · | 307.13 / · / · | 100 / · / · | 10.7 / · / · | 72.8 / · / · | 5 / · / · |
| cyclonedds | 7483.9 / 4503.7 / 850.77 | 8240.15 / 5768.52 / 1255.87 | 100 / 100 / 100 | 121.1 / 99 / 33.4 | 72.2 / 72.2 / 1488.8 | 5 / 5 / 5 |
| fastdds | 1656.48 / · / 248.35 | 2970.67 / · / 279.02 | 100 / · / 96.58 | 60.7 / · / 11.4 | 88.9 / · / 159.8 | 5 / · / 5 |
| zenoh | 2694.81 / 1240.31 / · | 3696.66 / 1654.77 / · | 100 / 100 / · | 107.8 / 48.4 / · | 126.7 / 170.9 / · | 5 / 5 / · |

## performance_test array256k 1->1

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 50.57 / · / · | 63.07 / · / · | 100 / · / · | 3 / · / · | 55 / · / · | 5 / · / · |
| cyclonedds | 196.02 / 110.29 / 56.45 | 234.6 / 135.32 / 66.63 | 100 / 100 / 100 | 14.4 / 7 / 3.2 | 25.6 / 25.9 / 1457.1 | 5 / 5 / 5 |
| fastdds | 106.33 / · / 49.59 | 153.58 / · / 63.45 | 100 / · / 100 | 7.2 / · / 3 | 40.2 / · / 64.7 | 5 / · / 5 |
| zenoh | 195.79 / 121.21 / · | 275.56 / 188.54 / · | 100 / 100 / · | 17.6 / 7.3 / · | 72 / 132.1 / · | 5 / 5 / · |

## performance_test array4m 1->1

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 462.73 / · / · | 637.07 / · / · | 100 / · / · | 1.3 / · / · | 77.2 / · / · | 5 / · / · |
| cyclonedds | 2496.44 / 1244 / 544.33 | 2779.31 / 1568.1 / 698.25 | 100 / 100 / 100 | 11.6 / 5 / 1.7 | 50 / 49.6 / 1468.3 | 5 / 5 / 5 |
| fastdds | 1205.25 / · / 310.66 | 1344.53 / · / 354.48 | 100 / · / 100 | 4.9 / · / 1.1 | 54.8 / · / 136.1 | 5 / · / 5 |
| zenoh | 2156.83 / 830.32 / · | 2721.83 / 973.78 / · | 100 / 100 / · | 12.3 / 2.5 / · | 104.1 / 149.4 / · | 5 / 5 / · |

## performance_test array4m 1->5

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 1352.55 / · / · | 1860.63 / · / · | 100 / · / · | 13.3 / · / · | 102.8 / · / · | 5 / · / · |
| cyclonedds | 30642.1 / 7753.74 / 2925.36 | 32651.8 / 8575.91 / 3840.62 | 100 / 100 / 100 | 167.3 / 72.6 / 35.6 | 120.2 / 121.8 / 1521.7 | 5 / 5 / 5 |
| fastdds | 4029.05 / · / 946.09 | 4757.86 / · / 1243.26 | 100 / · / 100 | 46.1 / · / 13.2 | 124.7 / · / 228.7 | 5 / · / 5 |
| zenoh | 8698.47 / 3421.89 / · | 10625.2 / 4186.27 / · | 100 / 100 / · | 110.2 / 40.1 / · | 202.2 / 211.1 / · | 5 / 5 / · |

## performance_test array64k 1->1

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 30.34 / · / · | 43.69 / · / · | 100 / · / · | 4 / · / · | 54.3 / · / · | 5 / · / · |
| cyclonedds | 75.15 / 59.97 / 33.92 | 112.17 / 84.06 / 51.33 | 100 / 100 / 100 | 9.7 / 6.7 / 3.9 | 24.6 / 24.4 / 1456.6 | 5 / 5 / 5 |
| fastdds | 65.06 / · / 40.39 | 87.79 / · / 59.99 | 100 / · / 100 | 7.7 / · / 4.9 | 44.2 / · / 65.5 | 5 / · / 5 |
| zenoh | 101.63 / 87.76 / · | 129 / 130.85 / · | 100 / 100 / · | 14.4 / 11.2 / · | 70.4 / 130.6 / · | 5 / 5 / · |

## performance_test array8m 1->1

| RMW | mean µs (default / tuned / shm) | tail µs (default / tuned / shm) | delivered % (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|---|
| unix_socket | 1292.19 / · / · | 1506.08 / · / · | 100 / · / · | 3.5 / · / · | 101.3 / · / · | 5 / · / · |
| cyclonedds | 5873.82 / 3488.81 / 1379.59 | 6802.05 / 4169.86 / 2011.95 | 100 / 100 / 100 | 25.8 / 13.1 / 3.9 | 78.6 / 75.8 / 1480.3 | 5 / 5 / 5 |
| fastdds | 2642.68 / · / 575.87 | 3197.49 / · / 653.37 | 100 / · / 100 | 10.1 / · / 1.8 | 71 / · / 212 | 5 / · / 5 |
| zenoh | 9086.94 / 5254.24 / · | 10251.4 / 5659.47 / · | 100 / 100 / · | 36.7 / 14.1 / · | 134.1 / 150.4 / · | 5 / 5 / · |

