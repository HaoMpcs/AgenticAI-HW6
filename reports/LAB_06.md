# Assignment 6 · Split it, measure it, decide

Model: Google `gemini-3.5-flash-lite`, the same for every run.

## Part A · The gates, before you build

**The roles you considered, and what each would need from the others mid-task.**

| Two roles | What one needs from the other while the task runs | How it would get it | What that costs |
|---|---|---|---|
| Investigator and publisher | The publisher needs the issue number, proposed label and responsible file, plus the investigation's coverage and uncertainty. The investigator needs no publisher output. | The investigator returns one schema-validated contract to the coordinator; the coordinator gives only a valid result to the publisher. | Evidence omitted from the contract is lost; validation and a second prompt consume tokens; the publisher cannot repair a weak investigation with read tools. |
| Coordinator and investigator | The coordinator needs a complete return and the investigator needs its issue brief and budget share. | Brief before the round, then a structured return; a recorded wait joins them. | The coordinator waits for the slowest required worker and must reserve enough budget for publishing. |
| Coordinator and publisher | The publisher needs the coordinator's accepted findings; the coordinator needs confirmation that each requested write completed. | A publisher brief after the investigation round, followed by the shared tracker state and combined check. | This serial seam limits speed-up and a bad accepted finding can be written faithfully. |

- For one issue: one investigator searches and reads, then returns `{label, file}` with its coverage and uncertainty. The publisher cannot start meaningful writes until that return is accepted, so the work is a sequential pipeline. The investigator can say what it searched and could not determine, but cannot say that its candidate is correct; the publisher can say which calls it attempted, but cannot independently assess the finding because it has no read tools.
- For a batch of five: five investigators can work independently, one per issue. Each returns the same contract and cannot make claims about another issue or about the final combined state. The publisher receives the accepted contracts and performs writes serially. Its completion does not establish that the five parts agree with the system rules, so the coordinator checks the tracker after all writes.

**The sketch** (text, or an image in `reports/`):

```
one issue (sequential):
coordinator -> investigator-issue -> validated return -> publisher -> tracker -> combined check
                    ^ recorded wait                  ^ no read tools

batch of five (parallel investigation, serial publication):
                 +-> investigator-1 --+
                 +-> investigator-2 --+
coordinator -----+-> investigator-3 --+-> validated returns -> publisher -> tracker
                 +-> investigator-4 --+                         |
                 +-> investigator-5 --+                         +-> combined check
```

**The four gates** (slide 46), in order, stopping at the first no.

| Gate | One issue | Why | A batch of five | Why |
|---|---|---|---|---|
| 1. The parts work mostly without talking | Fail | Investigation must precede publication; the only useful worker result is needed mid-task by the publisher. Stop here. | Pass | The five issues are unrelated, so five investigations need no cross-worker communication; only their bounded returns cross into the publication round. |
| 2. Each part's result can be checked on its own | Not reached | Gate 1 failed. | Pass | Each issue has its own structural end-state check, and the combined tracker check remains necessary after all five parts. |
| 3. A team buys what one agent cannot get more cheaply | Not reached | Gate 1 failed. | Pass | Five independent investigations can run concurrently. Fresh sequential contexts could buy isolation more cheaply, but cannot buy the same wall-clock reduction. |
| 4. The result is worth the multiplier | Not reached | Gate 1 failed. | Pass, provisionally | A whole batch fails when any issue fails, so reduced interference and shorter elapsed time could justify the predicted 1.3x token cost. Part C must overturn this verdict if equal-spend S-plus matches M or the speed-up does not appear. |

- The benefit you are trying to buy, and the condition it needs: primarily parallelism, which requires the five issue investigations to be truly independent and wall-clock time to fall in the measurements. Context isolation is secondary and requires the return contract to carry enough evidence without recreating a shared large context. Tool-surface specialisation limits accidental writes by investigators, but prompt-only specialisation is not claimed as a benefit because every role uses the same model.
- Your prediction, as committed in `reports/PREDICTIONS_06.md`, and its commit: single M/S token multiplier 1.4x, with S ahead by about 5 percentage points and S-plus at least matching M; batch multiplier 1.3x, with M ahead of S by about 15 points and S-plus trailing M by about 5 points. Prediction commit: `8426681`.

## Part B · The split

- The coordinator and the roles, and the tools each holds: the coordinator schedules work, validates returns and checks final tracker state without asking a model to choose an answer. One investigator per issue holds only `issues_read`, `code_search`, `code_read_file`, and the local `submit_investigation` return tool. One publisher per accepted issue holds only `issues_label`, `pulls_open` and `issues_comment`. Batch investigators run concurrently; publishers run serially.
- Why they split by tool surface: an investigator cannot accidentally write an unverified candidate, and a publisher cannot spend its round reopening investigation or substitute a new finding. This is a capability boundary, not a different persona: both roles use the same model.
- The return contract, field by field, and which fields come from the worker's tool calls: `result` has issue, label, file and evidence; `status` is `found`, `candidate` or `out_of_budget`; `not_searched` and `could_not_determine` state omissions and uncertainty. The harness replaces `searched` with the unique search queries and read paths from actual calls, and replaces `calls_used` with the count of actual registry calls. Every return is validated against `split/contract.schema.json`; an invalid or missing return is traced and never published.
- Each worker's share of the budget, and what is held back: 60% of the task budget is divided equally among investigators, 35% equally among publishers, and 5% remains as headroom under the one shared hard ceiling. For a five-issue batch this is 12%, 7% and 1% per issue respectively. An individual bound cannot enlarge the shared ceiling.
- The five checks, where each is in your code: schema validation runs in `ways/split.py`; `WaitGraph` detects wait cycles and chooses a non-coordinator victim; `check_combined` rereads tracker state after the final write; the registry retains Assignment 3's idempotency keys, while `SharedState.write` demonstrates compare-and-set refusal of stale versions; every agent uses `ctx.agent`, so its model/tool/wait/token lines share one trace. The three replay interfaces are in `split/guards.py` and all recorded guard replays passed.

## Part C · Measured

**The five constants** (slide 59): model `gemini-3.5-flash-lite`; tool schemas `703c0002892f27ec`; evaluator/answers `55abcd67e6a3b208` with reviewer `scripted:approve-all`; task IDs `batch-a`, `batch-b`, `one-4402`, `one-4403`, `one-4405`, `one-4406`, `one-4409`, `one-4413`; and the same ceiling for S and M (`250000` per issue, five times that for a batch). Every command used `--jobs 1`. S-plus used each task's measured M mean as its budget.

**The results.**

| Arm | Kind | Passes / runs | Lowest and highest sweep | Tasks all three passed | Mean tokens | Mean wall-clock (s) |
|---|---|---|---|---|---|---|
| S | single | 11 / 18 | 3–4 | 3 | 54,132 | 8.0 |
| S | batch | 3 / 6 | 1–1 | 1 | 336,670 | 30.9 |
| M | single | 12 / 18 | 3–5 | 3 | 26,571 | 8.1 |
| M | batch | 0 / 6 | 0–0 | 0 | 135,012 | 22.6 |
| S-plus | single | 12 / 18 | 4–4 | 4 | 24,851 | 8.1 |
| S-plus | batch | 0 / 6 | 0–0 | 0 | 127,057 | 37.4 |

- Your multiplier (M over S), single and batch, beside the lecture's 15×: **0.49× for single issues and 0.40× for batches**. This split spent less, unlike the lecture's cited typical multi-agent system at about 15× a chat (with one agent about 4× a chat); those vendor figures are different workloads and baselines, while these are the same tasks against arm S.
- Whether S-plus's spend matched M's in fact, task by task: yes within the required tolerance. M mean → S-plus mean (ratio): batch-a 131,697 → 125,676 (0.95×); batch-b 138,328 → 128,438 (0.93×); one-4402 32,154 → 23,956 (0.75×); one-4403 20,051 → 18,805 (0.94×); one-4405 29,696 → 29,128 (0.98×); one-4406 35,940 → 34,415 (0.96×); one-4409 21,826 → 22,596 (1.04×); one-4413 19,755 → 20,206 (1.02×).

**Slide 18's three questions**, for each kind of task.

| Question | One issue | A batch of five |
|---|---|---|
| Did the split spend more? | No: M used 0.49× S. | No: M used 0.40× S. |
| Does spending more raise the score? | No: the higher-spend S passed 11/18, while lower-spend S-plus and M each passed 12/18. | Yes in these runs: higher-spend S passed 3/6, while lower-spend S-plus and M each passed 0/6. |
| Given the same budget, did one agent do as well? | Yes: S-plus and M both passed 12/18; S-plus had four tasks pass all three runs versus M's three. | Yes: both passed 0/6, though M was faster (22.6s versus 37.4s). |

- What you would have claimed from arms S and M alone, and what you claim now: from S and M alone I might have credited the split on single issues for one extra pass at half the tokens, while rejecting it on batches because its 27% speed-up accompanied a fall from 3/6 to 0/6. S-plus removes the single-task architectural claim: one sequential agent at the split's spend also passed 12/18 and was at least as reliable by the all-three measure. The defensible claim is that focused contexts and lower spend helped, not that a second agent did.

**Every arm M run that failed.**

| Run | What each agent read, wrote and waited on | The first thing that went wrong | Anomaly | MAST category |
|---|---|---|---|---|
| `split-batch-a-s01-494401` | Five investigators read independently; publishers wrote accepted returns; coordinator waited and reread tracker. | 4412 returned a question with a file instead of `none`; 4414 returned `file:none` for a feature. | none | task_verification |
| `split-batch-a-s02-bc233b` | Same topology; all five contracts arrived and were published. | 4412 returned a question with `src/api/health.ts` instead of `none`. | none | task_verification |
| `split-batch-a-s03-f136ab` | Same topology; all five contracts arrived and were published. | 4412 again attached a file to a question requiring no change. | none | task_verification |
| `split-batch-b-s01-440c20` | Five independent reads, serial writes, then combined check. | 4426 attached `src/util/money.ts` to a question; 4431 labeled a feature as bug. | none | task_verification |
| `split-batch-b-s02-128b6a` | Four contracts were published; 4429 hit its turn limit, so its publisher was stopped; combined check reported the missing comment. | 4426's question named a file before 4429 failed to return and 4431 mislabeled a feature. | none | task_verification |
| `split-batch-b-s03-426cb0` | Five valid contracts were published and structurally agreed. | 4426 attached a code file to a question requiring `none`. | none | task_verification |
| `split-one-4402-s01-438112` | Investigator read/searched for 10 turns; coordinator waited; no publisher ran. | Investigator reached the turn limit without returning a contract. | none | task_verification |
| `split-one-4402-s02-4f8f8f` | Same: reads only, then invalid missing return and no writes. | Investigator reached the turn limit without returning a contract. | none | task_verification |
| `split-one-4402-s03-6de144` | Same: reads only, then invalid missing return and no writes. | Investigator reached the turn limit without returning a contract. | none | task_verification |
| `split-one-4403-s01-beaa2e` | Investigator read CSV code; publisher faithfully wrote its contract. | A deliberate-behavior question returned `src/export/csv.ts` instead of `none`. | none | task_verification |
| `split-one-4403-s03-afa125` | Same handoff and writes as sweep 1. | The question again returned a file instead of `none`. | none | task_verification |
| `split-one-4405-s01-91b6a9` | Investigator read ExportButton; publisher wrote the accepted label/file. | A requested behavior was labeled bug instead of feature. | none | task_verification |

## Part D · The decision

- One issue: keep one agent. Gate 1 failed before construction, and at equal actual spend S-plus matched M's 12/18 while passing more tasks in all three sweeps.
- A batch of five: keep one agent. M reduced mean time from 30.9s to 22.6s and tokens from 336,670 to 135,012, but fell from 3/6 grounded passes to 0/6; speed does not justify an unusable batch result.
- The condition that would reopen it: on a preregistered larger set of batches of at least five independent issues, a split must beat sequential S-plus in grounded whole-batch pass rate at matched actual spend across repeated runs, while also retaining a material wall-clock improvement and returning every required contract before its limit.
- The record: `decisions/0006-topology.md`.

## AI assistance

Codex wrote the split implementation, guards, evaluation script, reports and decision record. I checked its work with 107 starter tests, both development issues, all three recorded guard replays, grounded recomputation of all 72 measured runs, trace-by-trace failure review, and `make check-06`.
