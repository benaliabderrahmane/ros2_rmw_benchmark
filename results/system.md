# Test system

The numbers under `results/` were measured on a single host. Fill this in by
running, on that machine:

```bash
bash scripts/sysinfo.sh > results/system.md
```

It records CPU model, logical cores, RAM, kernel, OS, `/dev/shm` size, and
`net.core.{wmem,rmem}_max` — the context a reader needs to weigh the numbers.

<!-- placeholder until run on the benchmark host -->
