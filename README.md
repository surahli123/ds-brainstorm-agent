# DS Brainstorm Agent

Two AI-powered tools for data scientists: one helps you **plan** analyses, the other **polishes** your write-ups.

| Tool | What it does | How it works |
|------|-------------|--------------|
| **[Brainstorm](#brainstorm)** | Challenges your analysis plan before you execute | 3-persona Socratic debate (methodology, stakeholder, pragmatist) |
| **[AutoResearch](#autoresearch)** | Improves your analysis writing automatically | Edit-evaluate-keep/revert loop with cross-model judges |

Both tools run as coding agent skills (Claude Code, RovoDev, or any agent with subagent support). No web app, no infrastructure.

---

## AutoResearch

Feed it a rough DS analysis. Walk away. Come back to a polished write-up.

**Validated:** eBay marketing analysis went from 6.10 to 7.77 composite (+27%) in 5 automated cycles.

### How it works

```
   Writer (Model A)          Judges (Model B, x2)
   ┌────────────┐            ┌─────────────────┐
   │ Makes ONE  │───commit──>│ Substance score  │
   │ focused    │            │ Communication    │
   │ improvement│<──feedback─│ score            │
   └────────────┘            └────────┬────────┘
         ^                            │
         │    ┌──────────────┐        │
         └────│ Keep if +0.3 │<───────┘
              │ Revert if not│  composite
              └──────────────┘
```

- Writer and judges use **different models** for independence
- Judge feedback is passed to the writer each cycle (feedback-forward)
- **Hybrid scoring:** binary yes/no for objective dimensions, numeric 1-10 for subjective
- Plateau detection prints **actionable gaps** telling you what substance to add

### Quick start (Python orchestrator)

```bash
cd autoresearch/
export NOVITA_API_KEY="your-key"

# 5 cycles, auto-approve marginal improvements
python3 loop_runner.py --input ../examples/ebay_marketing_analysis.md \
  --cycles 5 --provider novita --auto-approve

# With hybrid judges and 3-run averaging
python3 loop_runner.py --input analysis.md --cycles 10 \
  --provider novita --judge-provider novita \
  --judge-model minimax/minimax-m2.7 \
  --judge-format hybrid --auto-approve --runs 3
```

### Quick start (RovoDev / coding agent)

```bash
# Install skill + subagents
cp -r rovodev-skill/skills/* ~/.rovodev/skills/
cp -r rovodev-skill/subagents/* ~/.rovodev/subagents/

# Run inside your agent session
/ds-autoresearch analysis.md
```

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | required | Analysis markdown file |
| `--cycles` | 10 | Improvement cycles |
| `--provider` | claude-code | Writer: `claude-code`, `anthropic`, `novita` |
| `--model` | per provider | Writer model ID |
| `--judge-provider` | codex | Judge: `codex` or `novita` |
| `--judge-model` | deepseek/deepseek-v3.2 | Judge model ID |
| `--judge-format` | hybrid | `numeric`, `binary`, or `hybrid` |
| `--runs` | 1 | Judge runs to average (3 recommended) |
| `--auto-approve` | false | Auto-keep marginal improvements |

### Live dashboard

```bash
cd autoresearch/
python3 -m http.server 8765 &
open http://localhost:8765/dashboard.html
```

Step chart showing score progression, bar chart for substance vs communication, dimension breakdown bars.

### Scoring dimensions

**Substance (55%)**

| Dimension | Format | What it measures |
|-----------|--------|-----------------|
| statistical_rigor | Binary | CIs, p-values, sample sizes, effect sizes |
| methodology_soundness | Numeric | Method clarity, assumptions, reproducibility |
| evidence_conclusion_alignment | Numeric | Conclusions trace to evidence, causal hedging |
| data_interpretation_accuracy | Binary | Numbers correct, baselines stated, outliers noted |

**Communication (45%)**

| Dimension | Format | What it measures |
|-----------|--------|-----------------|
| narrative_flow | Numeric | Logical structure, transitions, through-line |
| audience_calibration | Numeric | Jargon explained, consistent depth |
| visualization_effectiveness | Numeric | Charts serve purpose, labeled, annotated |
| executive_summary_clarity | Numeric | Leads with impact, standalone actionable |

Binary dimensions have near-zero noise (stdev 0.000). Numeric dimensions need `--runs 3` for stability.

---

## Brainstorm

Three independent perspectives challenge your analysis plan before you spend a day executing it.

### Personas

| Persona | Role | Key question |
|---------|------|-------------|
| **Methodology Critic** | Is this analysis sound? | "What confounders haven't you considered?" |
| **Stakeholder Advocate** | Will this influence decisions? | "What metric does your VP actually care about?" |
| **Pragmatist** | Can this ship? | "Do you have the data? Can you finish in a week?" |

### How it works

1. You describe your analysis plan
2. All 3 personas independently critique it (with search-grounded audience intelligence)
3. You enter a Socratic dialogue loop — the orchestrator pushes back until your plan is sharp
4. Structured output feeds into the report generator

### Usage

```bash
# In Claude Code
/ds-brainstorm "I want to measure the impact of search ranking changes on conversion rate"

# With domain knowledge
/ds-brainstorm --domain search-relevance "How should I set up an A/B test for NDCG improvements?"

# With stakeholder context
/ds-brainstorm --stakeholder "Jane Doe" "Quarterly search relevance report for leadership"
```

### Related tools

- `/ds-report-gen` — generates a structured DS report from brainstorm output
- `/build-stakeholder-profile` — builds audience intelligence profiles from web research

---

## Repo Structure

```
ds-brainstorm-agent/
│
├── autoresearch/                # AutoResearch loop engine
│   ├── loop_runner.py           #   Python orchestrator
│   ├── evaluate.py              #   Judge harness (Codex, Novita, hybrid)
│   ├── program.md               #   Writer system prompt
│   ├── review_config.yaml       #   Scoring weights + thresholds
│   ├── calibrate_hybrid.py      #   Compare numeric vs hybrid scoring
│   ├── dashboard.html           #   Chart.js live dashboard
│   ├── SKILL.md                 #   Claude Code skill wrapper
│   └── judges/                  #   Judge prompt templates
│       ├── *-judge.md           #     Numeric (1-10)
│       ├── *-judge-binary.md    #     Binary (yes/no)
│       └── *-judge-hybrid.md    #     Hybrid (recommended)
│
├── brainstorm/                  # Socratic debate engine
│   ├── skill/                   #   ds-brainstorm skill
│   │   ├── SKILL.md
│   │   ├── references/          #     Persona prompts + domain knowledge
│   │   ├── prompts/             #     Debate + synthesis prompts
│   │   └── evals/               #     Quality rubric + test cases
│   ├── report-gen/              #   ds-report-gen skill
│   └── stakeholder-profiles/    #   build-stakeholder-profile skill
│
├── rovodev-skill/               # RovoDev deployment package
│   ├── skills/ds-autoresearch/  #   Orchestrator (pure markdown, no Python)
│   └── subagents/               #   Writer + 2 judge subagents
│       ├── ds-writer/
│       ├── ds-judge-substance/  #     5 per-dimension rubric files
│       └── ds-judge-communication/
│
├── tests/                       # 70 unit tests
│   ├── test_smoke.py
│   └── test_hybrid_calibration.py
│
└── examples/
    └── ebay_marketing_analysis.md
```

## Supported Models

| Provider | Writer | Judge | Use case |
|----------|--------|-------|----------|
| **Novita AI** | DeepSeek V3.2 ($0.27/Mt) | MiniMax M2.7 ($0.30/Mt) | Personal, open source |
| **RovoDev** | Opus 4.6 | GPT 5.4 (medium effort) | Company deployment |
| **Claude Code** | Claude CLI | Codex CLI | Zero-config default |
| **Anthropic API** | Claude Sonnet | Codex CLI | Direct API access |

## Validated Results

| Test | Result |
|------|--------|
| Full loop (eBay analysis, 5 cycles) | 6.10 → 7.77 (+27%) |
| Hybrid calibration (5 runs) | No inflation vs numeric (7.02 vs 7.41) |
| Binary judge stability | Objective dims stdev 0.000 |
| Plateau + human pause | Prints actionable substance gaps |
