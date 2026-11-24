## ring, shm

Bring-up counts only runs where every node came up (all-up / runs; min-max in ring.csv). Medians across runs.

### N = 1

| RMW | all-up / runs (default / tuned / shm) | bring-up s (default / tuned / shm) | nodes up (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | p50 µs (default / tuned / shm) | p99 µs (default / tuned / shm) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · / · | 0.09 / · / · | 1 / · / · | 0 / · / · | 49.1 / · / · | 44.7 / · / · | 57.3 / · / · |
| cyclonedds | · / 5/5 / 5/5 | · / 0.07 / 0.08 | · / 1 / 1 | · / 0 / 0 | · / 15.5 / 663.9 | · / 24.2 / 32.6 | · / 31.9 / 42.7 |
| fastdds | 5/5 / · / 5/5 | 0.08 / · / 0.08 | 1 / · / 1 | 0.3 / · / 0 | 31.6 / · / 32.4 | 38 / · / 39.9 | 51.6 / · / 52.9 |
| zenoh | 5/5 / 5/5 / · | 0.07 / 0.1 / · | 1 / 1 / · | 0.3 / 0.3 / · | 62 / 120.5 / · | 29.5 / 34.8 / · | 39.6 / 45.7 / · |

### N = 10

| RMW | all-up / runs (default / tuned / shm) | bring-up s (default / tuned / shm) | nodes up (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | p50 µs (default / tuned / shm) | p99 µs (default / tuned / shm) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · / · | 0.07 / · / · | 1 / · / · | 3 / · / · | 42.3 / · / · | 44.5 / · / · | 76.6 / · / · |
| cyclonedds | · / 5/5 / 5/5 | · / 0.09 / 0.1 | · / 1 / 1 | · / 3 / 3 | · / 82.8 / 714.3 | · / 85.5 / 48 | · / 113.8 / 57.8 |
| fastdds | 5/5 / · / 5/5 | 1.15 / · / 1.16 | 1 / · / 1 | 5 / · / 5 | 163.9 / · / 165 | 99.7 / · / 87.6 | 118 / · / 101.5 |
| zenoh | 5/5 / 5/5 / · | 0.09 / 0.13 / · | 1 / 1 / · | 5 / 5.3 / · | 112.5 / 717.6 / · | 132 / 120.4 / · | 165.1 / 140.1 / · |

### N = 50

| RMW | all-up / runs (default / tuned / shm) | bring-up s (default / tuned / shm) | nodes up (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | p50 µs (default / tuned / shm) | p99 µs (default / tuned / shm) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · / · | 0.13 / · / · | 1 / · / · | 16.3 / · / · | 166.9 / · / · | 48.6 / · / · | 63.2 / · / · |
| cyclonedds | · / 5/5 / 5/5 | · / 0.65 / 0.67 | · / 1 / 1 | · / 23 / 15 | · / 527.2 / 1113.9 | · / 95.9 / 54.3 | · / 119.7 / 75.1 |
| fastdds | 5/5 / · / 5/5 | 1.51 / · / 1.51 | 1 / · / 1 | 32.3 / · / 30.3 | 1062.4 / · / 1066.6 | 124.1 / · / 105 | 160.9 / · / 137.9 |
| zenoh | 4/5 / 5/5 / · | 0.39 / 0.9 / · | 1 / 1 / · | 32 / 31.3 / · | 724.9 / 4815.1 / · | 158.8 / 136.5 / · | 199.2 / 169.5 / · |

### N = 100

| RMW | all-up / runs (default / tuned / shm) | bring-up s (default / tuned / shm) | nodes up (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | p50 µs (default / tuned / shm) | p99 µs (default / tuned / shm) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · / · | 0.22 / · / · | 1 / · / · | 35.3 / · / · | 322.3 / · / · | 54.3 / · / · | 69.3 / · / · |
| cyclonedds | · / 5/5 / 0/5 | · / 4.27 / - | · / 1 / 0.29 | · / 46.7 / 55.3 | · / 1553.5 / 951.2 | · / 109.5 / 52.9 | · / 825.2 / 73.9 |
| fastdds | 5/5 / · / 5/5 | 6.61 / · / 7.37 | 1 / · / 1 | 87 / · / 75.3 | 2895.8 / · / 2895.6 | 174.7 / · / 142 | 2060 / · / 1568.2 |
| zenoh | 3/5 / 2/5 / · | 1.72 / 5.34 / · | 1 / 0.98 / · | 77.3 / 70 / · | 2745.3 / 20041.4 / · | 186.2 / 154.1 / · | 387.1 / 917 / · |

### N = 200

| RMW | all-up / runs (default / tuned / shm) | bring-up s (default / tuned / shm) | nodes up (default / tuned / shm) | CPU % (default / tuned / shm) | PSS MB (default / tuned / shm) | p50 µs (default / tuned / shm) | p99 µs (default / tuned / shm) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · / · | 0.44 / · / · | 1 / · / · | 70.3 / · / · | 633.1 / · / · | 61 / · / · | 78.5 / · / · |
| cyclonedds | · / 0/5 / 0/5 | · / - / - | · / 0.93 / 0.14 | · / 1708 / 48.7 | · / 5292.9 / 1028.2 | · / 831552 / 52.5 | · / 5.2774e+06 / 76.8 |
| fastdds | 0/5 / · / 0/5 | - / · / - | 0.2 / · / 0.34 | 1541.7 / · / 1561 | 4143.4 / · / 4934.4 | 134982 / · / 3074.7 | 2.45201e+06 / · / 4.38566e+06 |
| zenoh | 2/5 / 0/5 / · | 12.41 / - / · | 0.99 / 0.18 / · | 172.7 / 1198 / · | 10947.8 / 20694.9 / · | 211.8 / 141.6 / · | 99103.6 / 373719 / · |

## ring, string

Bring-up counts only runs where every node came up (all-up / runs; min-max in ring.csv). Medians across runs.

### N = 1

| RMW | all-up / runs (default / tuned) | bring-up s (default / tuned) | nodes up (default / tuned) | CPU % (default / tuned) | PSS MB (default / tuned) | p50 µs (default / tuned) | p99 µs (default / tuned) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · | 0.1 / · | 1 / · | 0.3 / · | 48.2 / · | 36.7 / · | 48.8 / · |
| cyclonedds | 5/5 / 5/5 | 0.08 / 0.07 | 1 / 1 | 0 / 0.3 | 15.3 / 15.4 | 19.9 / 19.9 | 28.7 / 28.1 |
| fastdds | 5/5 / 5/5 | 0.1 / 0.08 | 1 / 1 | 0 / 0 | 26.9 / 27.5 | 34.9 / 35.3 | 45.8 / 47.5 |
| zenoh | 5/5 / 5/5 | 0.07 / 0.07 | 1 / 1 | 0 / 0 | 62.1 / 62.5 | 24.8 / 22.9 | 34.8 / 34.4 |

### N = 10

| RMW | all-up / runs (default / tuned) | bring-up s (default / tuned) | nodes up (default / tuned) | CPU % (default / tuned) | PSS MB (default / tuned) | p50 µs (default / tuned) | p99 µs (default / tuned) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · | 0.07 / · | 1 / · | 2 / · | 31.4 / · | 36.2 / · | 61 / · |
| cyclonedds | 5/5 / 5/5 | 0.09 / 0.09 | 1 / 1 | 3 / 3.3 | 57.6 / 57.8 | 60.1 / 58.8 | 88.2 / 72.1 |
| fastdds | 5/5 / 5/5 | 1.15 / 1.15 | 1 / 1 | 4.3 / 5 | 111 / 111.2 | 83.3 / 81.5 | 105.1 / 95.8 |
| zenoh | 5/5 / 5/5 | 0.08 / 0.09 | 1 / 1 | 4 / 4.3 | 109.2 / 109.6 | 108.5 / 109.8 | 124.4 / 128.3 |

### N = 50

| RMW | all-up / runs (default / tuned) | bring-up s (default / tuned) | nodes up (default / tuned) | CPU % (default / tuned) | PSS MB (default / tuned) | p50 µs (default / tuned) | p99 µs (default / tuned) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · | 0.13 / · | 1 / · | 14 / · | 111.3 / · | 38.3 / · | 56.3 / · |
| cyclonedds | 0/5 / 5/5 | - / 0.62 | 0.54 / 1 | 9.3 / 14.7 | 229 / 402.9 | 62.4 / 62.4 | 76.4 / 79.1 |
| fastdds | 5/5 / 5/5 | 1.57 / 1.52 | 1 / 1 | 27.3 / 27.3 | 796.5 / 798.4 | 90.5 / 90.2 | 121.8 / 116.8 |
| zenoh | 5/5 / 4/5 | 0.39 / 0.38 | 1 / 1 | 23.7 / 26 | 671.2 / 676.6 | 112.5 / 113.1 | 134.3 / 133.1 |

### N = 100

| RMW | all-up / runs (default / tuned) | bring-up s (default / tuned) | nodes up (default / tuned) | CPU % (default / tuned) | PSS MB (default / tuned) | p50 µs (default / tuned) | p99 µs (default / tuned) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · | 0.22 / · | 1 / · | 28.3 / · | 210.9 / · | 38.8 / · | 55.8 / · |
| cyclonedds | 0/5 / 5/5 | - / 4.04 | 0.27 / 1 | 9.7 / 32 | 228.9 / 1276.4 | 62 / 63.1 | 75 / 649.2 |
| fastdds | 5/5 / 5/5 | 6.53 / 7.42 | 1 / 1 | 69.3 / 71 | 2359.3 / 2363.8 | 111.9 / 111.7 | 1077.8 / 1456.2 |
| zenoh | 3/5 / 5/5 | 1.52 / 1.51 | 1 / 1 | 50.7 / 52.3 | 2186.2 / 2245.6 | 116.4 / 115.7 | 244.4 / 228.7 |

### N = 200

| RMW | all-up / runs (default / tuned) | bring-up s (default / tuned) | nodes up (default / tuned) | CPU % (default / tuned) | PSS MB (default / tuned) | p50 µs (default / tuned) | p99 µs (default / tuned) |
|---|---|---|---|---|---|---|---|
| unix_socket | 5/5 / · | 0.43 / · | 1 / · | 61.7 / · | 409.9 / · | 38.8 / · | 59.5 / · |
| cyclonedds | 0/5 / 0/5 | - / - | 0.14 / 0.95 | 9.3 / 1707.3 | 229 / 3193.8 | 62.4 / 896094 | 79.2 / 5.54138e+06 |
| fastdds | 0/5 / 0/5 | - / - | 0.23 / 0.51 | 1524.3 / 1559 | 3113.2 / 4344.5 | 133132 / 108378 | 1.69464e+06 / 1.1267e+06 |
| zenoh | 1/5 / 4/5 | 8.26 / 8.49 | 0.99 / 1 | 108 / 109 | 7996.1 / 7980.1 | 129.3 / 128.3 | 35801.8 / 23640.6 |

