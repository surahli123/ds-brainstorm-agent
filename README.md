# DS AutoResearch

Automatically improve data science analysis writing through iterative edit-evaluate-keep/revert cycles. Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) pattern.

Feed it a rough analysis. Walk away. Come back to a polished write-up that scores 25-30% higher on analytical rigor and communication clarity.

**Validated:** eBay marketing channel analysis went from 6.10 to 7.77 composite (+27%) in 5 automated cycles.

## How It Works

```
┌──────────────────────────────────────────────────────┐
│                  AUTORESEARCH LOOP                    │
│                                                      │
│  ┌──────────┐   ┌──────────┐   ┌────────────────┐   │
│  │  Writer   │──>│  Commit  │──>│  Judge (x2)    │   │
│  │ (Model A) │   │  to git  │   │  (Model B)     │   │
│  │           │   │          │   │                │   │
│  │ Makes ONE │   │          │   │  Substance +   │   │
│  │ focused   │   │          │   │  Communication │   │
│  │ edit      │   │          │   │  = Composite   │   │
│  └─────▲─────┘   └──────────┘   └───────┬────────┘   │
│        │                                │            │
│        │   ┌──────────────────┐         │            │
│        │   │  Keep if +0.3    │◄────────┘            │
│        └───│  Revert if not   │  feedback-forward    │
│            └──────────────────┘  (critiques → writer)│
└──────────────────────────────────────────────────────┘
```

**Key design choices:**
- Writer and judges use **different models** (cross-model independence)
- Judge feedback is passed to the writer each cycle (**feedback-forward**)
- **Hybrid scoring:** binary yes/no for objective dimensions (stdev 0.0), numeric 1-10 for subjective dimensions
- Git-based state management in an isolated temp directory
- Plateau detection with **actionable gaps** (tells you exactly what substance to add)

## Two Deployment Modes

### Mode 1: Python Orchestrator (personal use, API-based)

A Python script (`loop_runner.py`) calls model APIs directly. Works with Novita AI, Anthropic, or Claude Code CLI.

```bash
# Quick start with Novita AI (cheapest)
export NOVITA_API_KEY="your-key"
python3 loop_runner.py --input analysis.md --cycles 5 --provider novita --auto-approve

# With 3-run judge averaging for more stable scoring
python3 loop_runner.py --input analysis.md --cycles 10 \
  --provider novita --judge-provider novita \
  --judge-model minimax/minimax-m2.7 \
  --judge-format hybrid --auto-approve --runs 3

# Use Anthropic API
export ANTHROPIC_API_KEY="your-key"
python3 loop_runner.py --input analysis.md --cycles 5 --provider anthropic
```

### Mode 2: RovoDev Skill (team deployment, no API keys)

A pure-markdown skill that dispatches native subagents. Zero Python dependency. Works with any coding agent that supports subagents (RovoDev, Claude Code, etc.).

```bash
# Install
cp -r rovodev-skill/skills/* ~/.rovodev/skills/
cp -r rovodev-skill/subagents/* ~/.rovodev/subagents/

# Run
/ds-autoresearch analysis.md
```

The skill orchestrates: writer subagent (Opus 4.6) makes improvements, judge subagents (GPT 5.4) score them, keep/revert logic runs inside the session.

## Project Structure

```
ds-brainstorm-agent/
├── loop_runner.py              # Python orchestrator (Mode 1)
├── evaluate.py                 # Judge harness — Codex, Novita, hybrid format routing
├── program.md                  # Writer system prompt
├── review_config.yaml          # Scoring weights, thresholds, dimension format config
├── calibrate_hybrid.py         # Compare numeric vs hybrid scoring, recommend weights
├── dashboard.html              # Chart.js live dashboard (serve with python3 -m http.server)
├── test_smoke.py               # 65 unit tests (decision logic, providers, parsing)
├── test_hybrid_calibration.py  # 5 calibration tests
│
├── skills/ds-autoresearch/
│   ├── SKILL.md                # Claude Code skill definition
│   └── references/
│       ├── substance-judge.md          # Numeric judge template
│       ├── substance-judge-binary.md   # Binary judge template
│       ├── substance-judge-hybrid.md   # Hybrid judge template (recommended)
│       ├── communication-judge.md
│       ├── communication-judge-binary.md
│       └── communication-judge-hybrid.md
│
└── rovodev-skill/              # RovoDev deployment (Mode 2)
    ├── skills/ds-autoresearch/
    │   └── SKILL.md            # Orchestrator skill (loop logic)
    └── subagents/
        ├── ds-writer/
        │   └── SKILL.md        # Writer subagent prompt
        ├── ds-judge-substance/
        │   ├── SKILL.md        # Substance judge
        │   └── references/     # 5 per-dimension rubric files
        └── ds-judge-communication/
            ├── SKILL.md        # Communication judge
            └── references/     # 5 per-dimension rubric files
```

## CLI Reference (Mode 1)

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | (required) | Path to the analysis markdown file |
| `--cycles` | 10 | Number of improvement cycles |
| `--provider` | claude-code | Writer: `claude-code`, `anthropic`, or `novita` |
| `--model` | (per provider) | Writer model (e.g., `deepseek/deepseek-v3.2`) |
| `--judge-provider` | codex | Judge: `codex` or `novita` |
| `--judge-model` | deepseek/deepseek-v3.2 | Model for Novita judge |
| `--judge-format` | hybrid | Scoring format: `numeric`, `binary`, or `hybrid` |
| `--runs` | 1 | Judge runs to average per evaluation (3 recommended) |
| `--auto-approve` | false | Skip human gate for marginal improvements |
| `--max-total-cycles` | 20 | Hard budget cap including skipped cycles |
| `--keep-workdir` | false | Preserve temp directory for debugging |
| `--config` | review_config.yaml | Path to scoring config |

## Scoring Dimensions

### Substance (55% of composite)

| Dimension | Format | Weight | What it measures |
|-----------|--------|--------|-----------------|
| statistical_rigor | Binary | 1.2 | CIs, p-values, sample sizes, effect sizes |
| methodology_soundness | Numeric | 1.0 | Method description, assumptions, reproducibility |
| evidence_conclusion_alignment | Numeric | 1.3 | Conclusions trace to evidence, causal hedging |
| data_interpretation_accuracy | Binary | 1.0 | Numbers described correctly, baselines stated |

### Communication (45% of composite)

| Dimension | Format | Weight | What it measures |
|-----------|--------|--------|-----------------|
| narrative_flow | Numeric | 1.0 | Logical structure, transitions, through-line |
| audience_calibration | Numeric | 1.1 | Jargon explained, consistent depth |
| visualization_effectiveness | Numeric | 0.9 | Charts serve purpose, labeled, annotated |
| executive_summary_clarity | Numeric | 1.2 | Leads with impact, standalone actionable |

**Binary dimensions** have near-zero scoring noise (stdev 0.000). **Numeric dimensions** need multi-run averaging (stdev ~0.20 with `--runs 3`).

## Supported Models

### Novita AI (personal/open-source)

| Role | Model | Cost (input/output per Mt) |
|------|-------|---------------------------|
| Writer | `deepseek/deepseek-v3.2` | $0.27 / $0.40 |
| Judge | `minimax/minimax-m2.7` | $0.30 / $1.20 |
| Judge (cheap) | `zai-org/glm-4.7-flash` | $0.07 / $0.40 |

### RovoDev (company)

| Role | Model | Notes |
|------|-------|-------|
| Writer | Opus 4.6 | Best analytical writing quality |
| Judge | GPT 5.4 (medium effort) | Independent perspective, binary criteria don't need deep reasoning |

## Live Dashboard

Start the HTTP server and open the dashboard to watch the loop in real time:

```bash
python3 -m http.server 8765 &
open http://localhost:8765/dashboard.html
```

Shows: step chart (running best + kept/reverted), bar chart (substance vs communication per cycle), dimension breakdown bars, cycle history table with stdev.

## Tuning Guide

### Scores are noisy
Use `--runs 3` for 3-run judge averaging (stdev drops from ~0.75 to ~0.20). Or switch to `--judge-format hybrid` which uses binary checkpoints for objective dimensions (stdev 0.0).

### The loop plateaus early
Check the plateau output — it prints which dimensions and specific checkpoints are holding you back. The ceiling is usually substance-limited (the writer can't add data that doesn't exist). Add the missing substance yourself, then re-run.

### The writer makes only cosmetic edits
The phase system guides the writer: first 40% of cycles = structural, middle 40% = substance, final 20% = polish. If you want bolder moves, reduce total cycles so more time is spent in structural phase.

### Substance/communication balance is wrong
Edit `weights` in `review_config.yaml`. For technical audiences, try 0.65/0.35. For executive presentations, try 0.40/0.60.

### Cross-environment score drift
Different judge models produce different absolute scores (DeepSeek scores higher than MiniMax). Pick one judge model and stick with it for consistent tracking. Relative improvement within a run is reliable regardless of model.

## Validated Results

| Test | Setup | Result |
|------|-------|--------|
| Full loop (eBay marketing analysis) | DeepSeek writer + MiniMax judge, 5 cycles | 6.10 → 7.77 (+27%) |
| Manual improvement (same doc) | Claude Opus in-session | 5.79 → 7.32 (+26%) |
| Hybrid calibration (5 runs each) | MiniMax judge, same doc | Hybrid 7.02 vs Numeric 7.41 — no inflation |
| Binary judge stability | MiniMax, 5 runs | Objective dims stdev 0.000, subjective dims stdev 1.1-2.2 |
| Plateau continuation | 10 more cycles after 7.77 | No improvement — content ceiling confirmed |
