# Decision 0006: Keep RepoMind single-agent

## Status

Accepted for Assignment 6. The experimental split remains on `lab-06-split` and is not merged.

## Context and prediction

The proposed topology used parallel read-only investigators, serial write-only publishers and a coordinator. Before construction, the single-issue task failed gate 1 because publication depends on the investigation handoff. A five-issue batch provisionally passed all four gates because its investigations are independent, separately checkable and potentially parallel.

Prediction commit `8426681` expected M to cost 1.4x S on single issues and 1.3x on batches; S to lead M by about 5 percentage points on single issues; M to lead by about 15 points on batches; S-plus to match M on single issues but trail it slightly on batches.

## Evidence held constant

All 72 measured runs used `gemini-3.5-flash-lite`, tool-schema hash `703c0002892f27ec`, evaluator/answer hash `55abcd67e6a3b208`, `scripted:approve-all`, the same eight task IDs and `--jobs 1`. S and M shared a ceiling of 250,000 tokens per issue; each S-plus task received M's measured mean spend for that task.

For single issues, S passed 11/18 at 54,132 mean tokens and 8.0s; M passed 12/18 at 26,571 tokens and 8.1s; S-plus passed 12/18 at 24,851 tokens and 8.1s. M's multiplier over S was 0.49x. The split did not spend more, spending more did not raise the score, and the equal-spend one-agent rival did as well.

For five-issue batches, S passed 3/6 at 336,670 mean tokens and 30.9s; M passed 0/6 at 135,012 tokens and 22.6s; S-plus passed 0/6 at 127,057 tokens and 37.4s. M's multiplier was 0.40x. The split did not spend more; higher spend correlated with the better S score; and the equal-spend one-agent rival did as well as M. M bought a 27% wall-clock reduction against S, but not a usable whole-batch result.

## Decision

Keep one agent for a single issue. The task failed gate 1, M did not improve wall-clock, and S-plus reproduced M's pass count at the same actual spend without a role boundary.

Keep one agent for a batch of five. The split was faster and cheaper, but its grounded pass rate was 0/6 versus S's 3/6. Its failures were semantic investigation errors or missing returns, not deadlock, lost updates or broken handoffs. The combined structural check made missing work visible but could not verify semantic correctness without an answer key.

## Revisit condition

Reopen this decision on a preregistered larger set of batches of at least five independent issues if a split beats sequential S-plus in grounded whole-batch pass rate at matched actual spend across repeated runs, while also retaining a material wall-clock improvement and returning every required contract before its limit.

Splitting would gain batch parallelism and capability isolation but lose evidence across contracts and add stopping and verification seams. Not splitting gives up the observed batch speed and token reductions, but preserves the only topology in this experiment that produced successful batches.

`ARCHITECTURE.md` remains unchanged because RepoMind remains single-agent.
