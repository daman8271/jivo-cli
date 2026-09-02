# Build log

| Time (IST) | Phase | Event |
|---|---|---|
| 2026-08-24 20:15 | 0 | SAP bridge up; HANA + Service Layer both verified live |
| 2026-08-24 20:35 | 0 | `profile.py` built — per-field fill rates + value vocabularies |
| 2026-08-24 20:44 | 0 | Bridge dropped mid-test → `bridge.sh` + retry-on-transient added to every miner |
| 2026-08-24 20:47 | 0 | `watchdog.sh` running (20s checks) |
| 2026-08-24 20:50 | 0 | `gl.py` built — GL fingerprint per document type |
| 2026-08-24 20:52 | 0 | `sample.py` built — real documents + their journal |
| 2026-08-24 20:54 | 0 | Census written: 28 document types with rows, 15 draft types, 21 posting sources |
| 2026-08-24 21:00 | 1 | Wave 1 launched — 17 foundation topics, 34 agents (mine + adversarial verify) |
| 2026-08-24 21:07 | 1 | Wave 1 (17 Claude agents) LOST — session quota exhausted in 6.4 min, 916k tokens, resets 01:10 |
| 2026-08-24 21:15 | 1 | Re-planned: mining moved out of the model entirely. `sweep.py` launched, 234 jobs, 5 workers |
| 2026-08-24 21:20 | 1 | `flow.py` built — copied-from vs keyed-from-scratch, drafted-first ratio |
| 2026-08-24 21:28 | 1 | Codex path abandoned on Daman's instruction (no OpenAI plan). It had written nothing — nothing to distrust |
| 2026-08-24 21:31 | 1 | **Mining complete: 219/234 jobs, 221 files, 2.6 MB.** Zero model tokens spent |
