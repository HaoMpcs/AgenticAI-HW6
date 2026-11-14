# Assignment 6 predictions

These predictions were made before implementing or running the split. The proposed split has a coordinator, read-only investigators, and a write-only publisher. Investigators are assigned one issue each; the publisher acts only on validated investigator returns.

## Single-issue tasks

- I predict the split will spend about **1.4 times** as many tokens per task as arm S. The extra prompt, structured handoff, and coordinator decision add cost without creating useful parallel work.
- I predict arm S will pass about **5 percentage points more runs** than arm M. With only one issue, the handoff is another failure surface and the smaller tool surfaces do not offset it.
- I predict arm S-plus will do **at least as well as arm M** when given M's actual spend. A single agent can use the extra budget for another read-only attempt without losing evidence at a role boundary.

## Batch tasks

- I predict the split will spend about **1.3 times** as many tokens per task as arm S. Five worker prompts and returns add overhead, although their focused contexts should avoid repeatedly carrying evidence for the other issues.
- I predict arm M will pass about **15 percentage points more runs** than arm S. Separate investigator contexts should reduce interference between five unrelated issues, and one failed issue otherwise fails the whole batch.
- I predict arm S-plus will **not do as well as arm M**, trailing it by roughly **5 percentage points**. More attempts should help S-plus, but I expect context isolation across five issues and independent work to retain a small reliability advantage for M.

The most uncertain prediction is batch pass rate: the publisher is a serial seam, so malformed or incomplete worker returns could erase the expected benefit even if investigation itself parallelizes cleanly.
