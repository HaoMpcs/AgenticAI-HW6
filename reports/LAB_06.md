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

- The coordinator and the roles, and the tools each holds:
- Why they split by tool surface:
- The return contract, field by field, and which fields come from the worker's tool calls:
- Each worker's share of the budget, and what is held back:
- The five checks, where each is in your code:

## Part C · Measured

**The five constants** (slide 59): model, tools, budget, evaluator, task set.

**The results.**

| Arm | Kind | Passes / runs | Lowest and highest sweep | Tasks all three passed | Mean tokens | Mean wall-clock (s) |
|---|---|---|---|---|---|---|
| S | single | | | | | |
| S | batch | | | | | |
| M | single | | | | | |
| M | batch | | | | | |
| S-plus | single | | | | | |
| S-plus | batch | | | | | |

- Your multiplier (M over S), single and batch, beside the lecture's 15×:
- Whether S-plus's spend matched M's in fact, task by task:

**Slide 18's three questions**, for each kind of task.

| Question | One issue | A batch of five |
|---|---|---|
| Did the split spend more? | | |
| Does spending more raise the score? | | |
| Given the same budget, did one agent do as well? | | |

- What you would have claimed from arms S and M alone, and what you claim now:

**Every arm M run that failed.**

| Run | What each agent read, wrote and waited on | The first thing that went wrong | Anomaly | MAST category |
|---|---|---|---|---|
| | | | | |

## Part D · The decision

- One issue:
- A batch of five:
- The condition that would reopen it:
- The record: `decisions/0006-topology.md`

## AI assistance

Which tool, what it wrote, and what you checked:
