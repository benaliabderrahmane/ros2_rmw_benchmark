## iRobot cli-srv_multi_process / 100kb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 110.5 / · / · | 0 / · / · | 0.36 / · / · | 110.62 / · / · | 3 / · / · |
| cyclonedds | 205.5 / 152.5 / · | 0 / 0 / · | 0.66 / 0.45 / · | 117.77 / 117.71 / · | 3 / 3 / · |
| fastdds | 200 / · / 202.5 | 0 / · / 0 | 0.59 / · / 0.56 | 154.39 / · / 156.51 | 3 / · / 3 |
| zenoh | 247 / 219 / · | 0 / 0 / · | 0.99 / 0.7 / · | 128.3 / 347.62 / · | 3 / 3 / · |

## iRobot cli-srv_multi_process / 10b

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 71.5 / · / · | 0 / · / · | 1 / · / · | 106.37 / · / · | 3 / · / · |
| cyclonedds | 98.5 / 97.5 / · | 0 / 0 / · | 1.17 / 1.14 / · | 110.92 / 111.42 / · | 3 / 3 / · |
| fastdds | 119.5 / · / 131 | 0 / · / 0 | 1.56 / · / 1.59 | 138.89 / · / 138.26 | 3 / · / 3 |
| zenoh | 151 / 152.5 / · | 0 / 0 / · | 2.2 / 2.31 / · | 136.55 / 136.15 / · | 3 / 3 / · |

## iRobot cli-srv_multi_process / 1mb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 345.89 / · / · | 0 / · / · | 0.08 / · / · | 129.18 / · / · | 3 / · / · |
| cyclonedds | 1293.5 / 679.75 / · | 0 / 0 / · | 0.44 / 0.2 / · | 148.16 / 148.07 / · | 3 / 3 / · |
| fastdds | 890 / · / 496.8 | 0 / · / 0 | 0.27 / · / 0.12 | 153.92 / · / 187.88 | 3 / · / 3 |
| zenoh | 973.5 / 643.28 / · | 0 / 0 / · | 0.42 / 0.15 / · | 138.08 / 354.34 / · | 3 / 3 / · |

## iRobot cli-srv_multi_process / 1mb_multi

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 316 / · / · | 0 / · / · | 0.16 / · / · | 130.71 / · / · | 3 / · / · |
| cyclonedds | 1200.5 / 675.5 / · | 0 / 0 / · | 0.95 / 0.54 / · | 153.95 / 152.31 / · | 3 / 3 / · |
| fastdds | 6566.5 / · / 669.5 | 0 / · / 0 | 1.33 / · / 0.85 | 280.21 / · / 303.81 | 3 / · / 3 |
| zenoh | 1007 / 629 / · | 0 / 0 / · | 0.89 / 0.31 / · | 141.05 / 358.75 / · | 3 / 3 / · |

## iRobot cli-srv_multi_process / 4mb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 2395 / · / · | 0 / · / · | 0.09 / · / · | 198.06 / · / · | 3 / · / · |
| cyclonedds | 6453.5 / 6219.5 / · | 0 / 0 / · | 0.34 / 0.2 / · | 154.75 / 156.19 / · | 3 / 3 / · |
| fastdds | 5084 / · / 3067 | 0 / · / 0 | 0.3 / · / 0.18 | 176.82 / · / 335.62 | 3 / · / 3 |
| zenoh | 4670 / 3494.5 / · | 0 / 0 / · | 0.34 / 0.14 / · | 176.54 / 383.71 / · | 3 / 3 / · |

## iRobot cli-srv_multi_process_multiple_clients / 10_cli_srv_100kb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 100 / · / · | 0 / · / · | 0.36 / · / · | 113 / · / · | 3 / · / · |
| cyclonedds | 218 / 159 / · | 0 / 0 / · | 0.83 / 0.61 / · | 122.66 / 122.37 / · | 3 / 3 / · |
| fastdds | 302 / · / 268.5 | 0 / · / 0 | 1.41 / · / 1.52 | 236.85 / · / 240.89 | 3 / · / 3 |
| zenoh | 249 / 234.5 / · | 0 / 0 / · | 1.07 / 0.79 / · | 132.3 / 350.82 / · | 3 / 3 / · |

## iRobot cli-srv_multi_process_multiple_clients / 20_cli_srv_100kb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 120.5 / · / · | 0 / · / · | 0.48 / · / · | 115.12 / · / · | 3 / · / · |
| cyclonedds | 232 / 169.5 / · | 0 / 0 / · | 1 / 0.77 / · | 128.86 / 127.93 / · | 3 / 3 / · |
| fastdds | 351 / · / 292.5 | 0 / · / 0 | 1.61 / · / 2.47 | 328.64 / · / 337.14 | 3 / · / 3 |
| zenoh | 262.5 / 234.5 / · | 0 / 0 / · | 1.2 / 0.86 / · | 135.93 / 355.01 / · | 3 / 3 / · |

## iRobot cli-srv_multi_process_multiple_clients / 2_cli_srv_100kb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 117 / · / · | 0 / · / · | 0.38 / · / · | 111.25 / · / · | 3 / · / · |
| cyclonedds | 210 / 152.5 / · | 0 / 0 / · | 0.71 / 0.46 / · | 117.71 / 117.91 / · | 3 / 3 / · |
| fastdds | 207.5 / · / 213.5 | 0 / · / 0 | 0.64 / · / 0.69 | 163.39 / · / 166.01 | 3 / · / 3 |
| zenoh | 253 / 225 / · | 0 / 0 / · | 1.03 / 0.71 / · | 129.05 / 347.84 / · | 3 / 3 / · |

## iRobot cli-srv_multi_process_multiple_clients / 5_cli_srv_100kb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 105.5 / · / · | 0 / · / · | 0.35 / · / · | 111.5 / · / · | 3 / · / · |
| cyclonedds | 209 / 159.5 / · | 0 / 0 / · | 0.75 / 0.52 / · | 119.22 / 119.43 / · | 3 / 3 / · |
| fastdds | 243 / · / 239 | 0 / · / 0.32 | 0.83 / · / 1.06 | 191.14 / · / 197.51 | 3 / · / 3 |
| zenoh | 256.5 / 223.5 / · | 0 / 0 / · | 1.05 / 0.73 / · | 130.05 / 349.05 / · | 3 / 3 / · |

## iRobot cli-srv_multi_process_multiple_clients / cli_srv_100kb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 110.5 / · / · | 0 / · / · | 0.36 / · / · | 110.62 / · / · | 3 / · / · |
| cyclonedds | 217 / 155.5 / · | 0 / 0 / · | 0.71 / 0.45 / · | 117.44 / 117.93 / · | 3 / 3 / · |
| fastdds | 206.5 / · / 213.5 | 0 / · / 0 | 0.62 / · / 0.59 | 155.01 / · / 156.89 | 3 / · / 3 |
| zenoh | 255.5 / 219.5 / · | 0 / 0 / · | 1.01 / 0.7 / · | 128.55 / 347.59 / · | 3 / 3 / · |

## iRobot pub-sub_multi_process / 100kb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 43 / · / · | 0 / · / · | 0.1 / · / · | 109.5 / · / · | 3 / · / · |
| cyclonedds | 113 / 73 / · | 0 / 0 / · | 0.23 / 0.14 / · | 116.08 / 115.97 / · | 3 / 3 / · |
| fastdds | 143 / · / 82 | 0 / · / 0 | 0.19 / · / 0.16 | 148.39 / · / 147.64 | 3 / · / 3 |
| zenoh | 134 / 118 / · | 0 / 0 / · | 0.31 / 0.22 / · | 126.05 / 235.65 / · | 3 / 3 / · |

## iRobot pub-sub_multi_process / 10b

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 31 / · / · | 0 / · / · | 0.08 / · / · | 179.37 / · / · | 3 / · / · |
| cyclonedds | 48 / 47 / · | 0 / 0 / · | 0.1 / 0.1 / · | 111.92 / 111.54 / · | 3 / 3 / · |
| fastdds | 63 / · / 77 | 0 / · / 0 | 0.15 / · / 0.16 | 139.39 / · / 138.76 | 3 / · / 3 |
| zenoh | 91 / 88 / · | 0 / 0 / · | 0.18 / 0.18 / · | 124.93 / 125.15 / · | 3 / 3 / · |

## iRobot pub-sub_multi_process / 1mb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 110 / · / · | 0 / · / · | 0.18 / · / · | 116.4 / · / · | 3 / · / · |
| cyclonedds | 724 / 357 / · | 0 / 0 / · | 1.53 / 0.67 / · | 131.64 / 130.3 / · | 3 / 3 / · |
| fastdds | 465 / · / 136 | 0 / · / 0 | 0.96 / · / 0.23 | 153.04 / · / 151.88 | 3 / · / 3 |
| zenoh | 605 / 271 / · | 0 / 0 / · | 1.64 / 0.4 / · | 134.2 / 238.81 / · | 3 / 3 / · |

## iRobot pub-sub_multi_process / 4mb

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 374 / · / · | 0 / · / · | 0.49 / · / · | 143.65 / · / · | 3 / · / · |
| cyclonedds | 3531 / 2168 / · | 0 / 0 / · | 5.85 / 3.07 / · | 231.5 / 226.47 / · | 3 / 3 / · |
| fastdds | 2004 / · / 323 | 0 / · / 0 | 4.22 / · / 0.45 | 231.79 / · / 187.44 | 3 / · / 3 |
| zenoh | 3035 / 801 / · | 0 / 0 / · | 8.22 / 1.02 / · | 160.24 / 249.29 / · | 3 / 3 / · |

## iRobot pub-sub_multi_process_scalability / 10_processes

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 298 / · / · | 0 / · / · | 5.04 / · / · | 194.12 / · / · | 3 / · / · |
| cyclonedds | 148 / 148 / · | 0 / 0 / · | 3.58 / 3.6 / · | 138.45 / 134.87 / · | 3 / 3 / · |
| fastdds | 194 / · / 174 | 0 / · / 0 | 4.3 / · / 4.76 | 186.01 / · / 278.32 | 3 / · / 3 |
| zenoh | 203 / 780 / · | 0 / 0 / · | 4.33 / 5.93 / · | 152.76 / 194.74 / · | 3 / 3 / · |

## iRobot pub-sub_multi_process_scalability / 1_process

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 136 / · / · | 0 / · / · | 0.46 / · / · | 118.75 / · / · | 3 / · / · |
| cyclonedds | 988 / 984 / · | 0 / 0 / · | 2.99 / 2.98 / · | 116.42 / 116.29 / · | 3 / 3 / · |
| fastdds | 129 / · / 112 | 0 / · / 0 | 0.45 / · / 0.06 | 148.14 / · / 156.06 | 3 / · / 3 |
| zenoh | 152 / 212 / · | 0 / 0 / · | 0.49 / 0.64 / · | 130.45 / 188.6 / · | 3 / 3 / · |

## iRobot pub-sub_multi_process_scalability / 2_process

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 122 / · / · | 0 / · / · | 0.67 / · / · | 127.12 / · / · | 3 / · / · |
| cyclonedds | 988 / 993 / · | 0 / 0 / · | 4.49 / 4.51 / · | 119.55 / 119.66 / · | 3 / 3 / · |
| fastdds | 118 / · / 103 | 0 / · / 0 | 0.67 / · / 0.71 | 150.88 / · / 168.97 | 3 / · / 3 |
| zenoh | 132 / 198 / · | 0 / 0 / · | 0.7 / 0.96 / · | 132.34 / 188.12 / · | 3 / 3 / · |

## iRobot pub-sub_multi_process_scalability / 5_process

| RMW | mean µs (default / tuned / shm) | lost % (default / tuned / shm) | CPU % (default / tuned / shm) | RSS MB (default / tuned / shm) | runs (default / tuned / shm) |
|---|---|---|---|---|---|
| unix_socket | 143 / · / · | 0 / · / · | 1.13 / · / · | 151 / · / · | 3 / · / · |
| cyclonedds | 120 / 120 / · | 0 / 0 / · | 0.97 / 0.97 / · | 123.54 / 123.29 / · | 3 / 3 / · |
| fastdds | 136 / · / 115 | 0 / · / 0 | 1.16 / · / 2.38 | 161.51 / · / 210.8 | 3 / · / 3 |
| zenoh | 144 / 229 / · | 0 / 0 / · | 1.13 / 1.58 / · | 134.83 / 191.34 / · | 3 / 3 / · |

