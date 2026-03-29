---
name: ds-autoresearch
description: Automated DS analysis improvement loop. Dispatches writer and judge subagents to iteratively improve analytical writing quality. Use when you want to polish a DS analysis, takehome, or report.
allowed-tools:
  - open_files
  - write_file
  - grep
  - bash
  - invoke_subagent
---

# DS AutoResearch

Iteratively improve a DS analysis document. A writer subagent makes one improvement per cycle, judge subagents score it, and the orchestrator keeps or reverts based on the score delta.

## Usage

```
/ds-autoresearch path/to/analysis.md
/ds-autoresearch path/to/analysis.md cycles=10
```

## Orchestrator Logic

### Step 1: Setup

1. Read the target analysis file.
2. Create state directory `autoresearch-state/` next to the file (if it doesn't exist).
3. Copy original to `autoresearch-state/backup.md`.
4. Copy original to `autoresearch-state/current-best.md`.
5. Set `cycles` (default 5, or from user arg).

### Step 2: Baseline Evaluation

Dispatch both judge subagents on the current text:

1. Invoke `ds-judge-substance` subagent with the analysis text. The subagent returns JSON with scores.
2. Invoke `ds-judge-communication` subagent with the analysis text. Returns JSON with scores.
3. Parse both JSON responses. Extract scores per dimension.
4. Compute composite score:
   ```
   substance_avg = weighted_mean(substance_scores, weights below)
   communication_avg = weighted_mean(communication_scores, weights below)
   composite = 0.55 * substance_avg + 0.45 * communication_avg
   ```
5. Save baseline critique text (from both judges) for feedback-forward.
6. Append to `autoresearch-state/scores.jsonl`:
   ```json
   {"cycle": 0, "action": "baseline", "composite": X.XX, "substance_avg": X.XX, "communication_avg": X.XX, "substance_scores": {...}, "communication_scores": {...}}
   ```
7. Print baseline scores.

### Step 3: Improvement Loop

For each cycle from 1 to `cycles`:

**Phase assignment:**
- Cycles 1 to 40% of total: `structural`
- Cycles 41% to 80%: `substance`
- Cycles 81% to 100%: `polish`

**3a. Write:**
Invoke `ds-writer` subagent with:
- The current analysis text
- Cycle number and phase
- Judge critiques from the previous cycle (feedback-forward)

The writer returns the complete improved markdown. Save it as the candidate.

**3b. Evaluate:**
Invoke both judge subagents on the candidate text (same as Step 2). Parse scores and compute composite.

**3c. Decide:**
```
improvement = new_composite - current_best_composite

if improvement >= 0.3:
    KEEP — write candidate to current-best.md and the original file
    Update current_best_composite
else:
    REVERT — discard candidate, keep current-best.md
```

**3d. Log:**
Append to `autoresearch-state/scores.jsonl`:
```json
{"cycle": N, "action": "keep|revert", "composite": X.XX, ...}
```

Save judge critiques for next cycle's feedback-forward.

**3e. Plateau check:**
If 3 consecutive cycles were reverted, print actionable gaps and stop:

```
PLATEAU DETECTED

SUBSTANCE GAPS:
  [lowest-scoring substance critique excerpt]

COMMUNICATION GAPS:
  [lowest-scoring communication critique excerpt]

Add these to your draft, then re-run /ds-autoresearch to continue.
```

### Step 4: Completion

Print final summary:
```
Baseline: X.XX -> Final: X.XX (+X.XX, +XX%)
Cycles: N (kept=K, reverted=R)
```

Copy `current-best.md` back to the original file path.

## Scoring Weights

### Substance Dimension Weights
| Dimension | Weight |
|-----------|--------|
| statistical_rigor | 1.2 |
| methodology_soundness | 1.0 |
| evidence_conclusion_alignment | 1.3 |
| data_interpretation_accuracy | 1.0 |

### Communication Dimension Weights
| Dimension | Weight |
|-----------|--------|
| narrative_flow | 1.0 |
| audience_calibration | 1.1 |
| visualization_effectiveness | 0.9 |
| executive_summary_clarity | 1.2 |

### Computing Weighted Mean

```
weighted_mean(scores, weights) =
  sum(score[dim] * weight[dim] for dim in scores) / sum(weight[dim] for dim in scores)
```

## Subagent Dispatch Format

When invoking judge subagents, pass the analysis text as the message. The subagent's system prompt (from its SKILL.md) contains the rubric and output format instructions.

When invoking the writer subagent, format the message as:
```
CYCLE: {N} of {total}
PHASE: {structural|substance|polish}

JUDGE FEEDBACK FROM PREVIOUS CYCLE:
SUBSTANCE JUDGE:
{substance critique}

COMMUNICATION JUDGE:
{communication critique}

ANALYSIS TO IMPROVE:

{full analysis text}
```

For cycle 1 (no previous feedback), omit the JUDGE FEEDBACK section.

## Score Parsing

Judge subagents return JSON. Parse it to extract scores:

**Hybrid format** (binary dims return dict, numeric dims return float):
```json
{
  "statistical_rigor": {"has_confidence_intervals": true, ...},
  "methodology_soundness": 6.5,
  "critique": "..."
}
```

**Binary to numeric conversion:**
```
binary_score = (count of true values / total checkpoints) * 10
```

Extract `critique` field separately for feedback-forward. All other fields are scores.
