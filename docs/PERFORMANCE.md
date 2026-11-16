# Core performance

Measured with `uv run --no-sync pytest tests/core_hardening/test_perf.py -m "slow or perf"`, using
`time.process_time` (CPU time, not wall clock).

- Python 3.13.16, macOS 27.2 (arm64), Apple M1 Pro (10 cores).
- Honest note: the machine was shared and heavily loaded by other jobs during the run. CPU time reduces but does not
  remove that noise. The numbers are indicative only; the test budgets have at least 5x slack.

| Measurement | Result |
| --- | --- |
| encode, 1.6 KB record entry | about 29,000 per second |
| decode (strict parse plus validation), same entry | about 22,000 per second |
| `sha256_hex`, same entry | about 28,000 per second |
| verify, 10,000 entries (3.5 MB), from bytes | 0.37 s CPU, about 27,000 entries per second |
| verify, 10,000 entries, from the ledger file | 0.37 s CPU |
| verify, 5,000 entries | 0.18 s CPU (10,000 / 5,000 ratio 2.02: linear) |
| append at about 100 entries | 2.5 ms CPU, about 400 per second |
| append at about 1,000 entries | 34 ms CPU, about 29 per second |

Appending re-verifies the whole ledger under the lock, so the cost of one append grows linearly with ledger size
(about 0.37 s per append at 10,000 entries). CPU time excludes time blocked in `fsync`. A 20,000-entry ledger verifies
(slow test). Eight processes appending 200 entries each produced one valid ledger with contiguous seq (about 66 s wall).
