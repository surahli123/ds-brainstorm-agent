---
name: ds-autoresearch
description: Automated DS analysis improvement loop — Claude writes, Codex judges, git keeps/reverts
---

# DS AutoResearch

Automatically improve a DS analysis document through iterative edit→evaluate→keep/revert cycles. Claude Code writes improvements, Codex judges score them, git manages state.

## Prerequisites

1. **Claude Code CLI** (`claude`) — installed and authenticated (default writer)
2. **Codex CLI** (`codex`) — installed and authenticated (`npm install -g @openai/codex`)
3. **Python 3.10+** with `pyyaml` and `pytest` packages
4. **Git** — used for state management in isolated temp directory

Optional:
- `ANTHROPIC_API_KEY` — only if using `--provider anthropic`
- `anthropic` Python package — only if using `--provider anthropic`

## Usage

```bash
# Standard run: 10 improvement cycles
python3 loop_runner.py --input analysis.md --cycles 10

# Short test run
python3 loop_runner.py --input analysis.md --cycles 3

# Use Anthropic API instead of Claude Code CLI
python3 loop_runner.py --input analysis.md --cycles 10 --provider anthropic

# Keep the temp working directory for debugging
python3 loop_runner.py --input analysis.md --cycles 10 --keep-workdir

# Set a hard budget cap
python3 loop_runner.py --input analysis.md --cycles 10 --max-total-cycles 15
```

## CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | (required) | Path to the analysis markdown file |
| `--cycles` | 10 | Number of improvement cycles |
| `--config` | review_config.yaml | Path to rubric/weights config |
| `--provider` | claude-code | Writer: `claude-code` (zero keys) or `anthropic` |
| `--max-total-cycles` | 20 | Hard budget cap including skipped cycles |
| `--keep-workdir` | false | Don't delete temp directory after completion |
| `--model` | claude-sonnet-4-20250514 | Model for Anthropic API provider |

## How It Works

```
loop_runner.py --input analysis.md --cycles 10
  │
  ├── 1. Creates isolated /tmp/autoresearch-<timestamp>/
  ├── 2. Copies analysis.md, git init, baseline eval
  │
  └── For each cycle:
      ├── Writer (Claude) produces improved version
      ├── Judges (Codex × 2, parallel) score it
      ├── Decision: KEEP (>1.0), HUMAN GATE (0.3-1.0), REVERT (<0.3)
      ├── Regression blocker: revert if top dimension drops >0.5
      └── Stop: 3 non-improving cycles, budget exceeded, or target reached
```

## Scoring

Two judges evaluate independently:
- **Substance** (55% weight): statistical rigor, methodology, evidence-conclusion alignment, data interpretation
- **Communication** (45% weight): narrative flow, audience calibration, visualization effectiveness, exec summary clarity

Thresholds are configured in `review_config.yaml`.

## Output

Each run creates `runs/<timestamp>/` containing:
- `analysis-initial.md` — the input document
- `analysis-final.md` — the improved output
- `scores.jsonl` — per-cycle score log
- `diffs/` — what changed each cycle
- `critiques/` — full judge explanations (for calibration learning)
- `summary.json` — run metadata and final status

## Configuration

Edit `review_config.yaml` to adjust:
- Composite weights (substance vs communication)
- Per-dimension weights within each judge
- `min_improvement` threshold (default: 0.3)
- `target_score` ceiling (default: 9.0)
- `max_consecutive_reverts` (default: 3, minimum: 3)

## Running Tests

```bash
python3 -m pytest test_smoke.py -v
```

Tests cover: decision logic, phase detection, writer validation, stop rules, budget cap, judge failure handling.
