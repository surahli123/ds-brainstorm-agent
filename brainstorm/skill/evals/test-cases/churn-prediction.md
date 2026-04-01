# Test Case: Churn Prediction Model

**ID:** eval-002-churn-prediction
**Difficulty:** Medium
**Domain:** None (no `--domain` flag)

## Input

```
/ds-brainstorm

I want to build a churn prediction model. We have 2 years of user activity logs and payment data. The VP wants to reduce churn by 15% this quarter.
```

## Why This Is "Medium"

- Single analysis question (scope check passes), but with embedded complexity:
  - The VP's "15% reduction this quarter" is an aggressive, time-bound target that should trigger Pragmatist and Stakeholder Advocate concerns
  - "Build a churn prediction model" conflates prediction with intervention — predicting churn doesn't reduce it
  - No domain file loaded, so personas must work from general DS knowledge + search grounding only
- Tests that the skill produces complete structural output even without domain enrichment

## Expected Phase Flow

1. **Phase 0 (Scope Check):** PASS — single question about churn prediction, despite multiple data sources mentioned
2. **Phase 0 (Domain Load):** SKIP — no `--domain` flag specified
3. **Phase 0 (Search Grounding):** Search for churn prediction best practices, common pitfalls, ML approaches
4. **Phase 1 (Dispatch):** All 3 subagents dispatched (parallel by default, sequential fallback)
5. **Phase 2 (Synthesis):** Cross-persona synthesis with agreements and tensions
6. **Phase 3 (Socratic):** At least 1 round of challenger dialogue
7. **Phase 4 (Output):** Human-readable summary + machine-readable JSON

## Expected Persona Behavior

### Methodology Critic
Should challenge:
- Prediction vs intervention gap: a model that predicts churn doesn't tell you how to reduce it. Causal inference is needed for intervention design.
- Label definition: what counts as "churned"? 30-day inactive? Cancelled subscription? The definition drives everything.
- Feature leakage risk: payment failure events may be both features AND labels
- Survivorship bias in 2 years of historical data
- Evaluation strategy: how will you validate the model actually reduces churn, not just predicts it?

### Stakeholder Advocate
Should challenge:
- The VP said "reduce churn by 15%" — that's an intervention goal, not a prediction goal. The analysis needs to be framed around actions, not model accuracy.
- What decision does the model enable? If you identify at-risk users, what's the intervention? Without a clear action plan, the model is shelf-ware.
- Success metric alignment: VP cares about churn rate reduction, not AUC or precision. Frame results in VP language.
- Risk: delivering a model that predicts well but doesn't drive action will erode DS credibility

### Pragmatist
Should challenge:
- "This quarter" timeline: building a production churn model from scratch in one quarter is aggressive. What's the 80/20 version?
- Data quality: 2 years of activity logs — is this clean, consistent data? Or does it have schema changes, missing periods, tracking gaps?
- Do you have an intervention channel? Even if the model works, can you actually reach at-risk users (email, in-product, CS team)?
- Scope recommendation: start with a simple rules-based segmentation, validate the intervention channel, THEN build the ML model

## Structural Checks (Pass/Fail Criteria)

### Observation Contract (per persona)
Each of the 3 subagent outputs must contain:

| Field | Type | Constraint |
|-------|------|------------|
| `status` | string | One of: `success`, `warning`, `error` |
| `summary` | string | Non-empty |
| `perspective` | string | Matches the persona key (`methodology_critic`, `stakeholder_advocate`, `pragmatist`) |
| `assessment` | string | One of: `SOUND`, `CONCERNS`, `MAJOR_ISSUES` |
| `findings` | array | Length >= 1 |
| `next_actions` | array | Length >= 1 |
| `domain_references` | array | May be empty — no domain file loaded. Presence of the field is still required. |

### Key Difference from Test Case 1
- `domain_references` arrays may be empty since no `--domain` flag is specified
- This is structurally valid — the field must exist but can be `[]`
- Personas may still reference general DS concepts, but the check is that the field exists, not that it's populated

### Synthesis
| Field | Type | Constraint |
|-------|------|------------|
| `agreements` | array | Length >= 1 |
| `tensions` | array | Length >= 1 (Methodology Critic should tension with Pragmatist on rigor vs timeline; Stakeholder Advocate should tension with both on prediction vs intervention) |
| `key_question` | string | Non-empty |

### Socratic Dialogue
| Field | Type | Constraint |
|-------|------|------------|
| `dialogue_history` | array | Length >= 2 (at minimum: 1 challenger message + 1 user response) |

Each dialogue entry must have:
| Field | Type | Constraint |
|-------|------|------------|
| `role` | string | `user` or `challenger` |
| `references_persona` | string or null | One of the 3 persona keys, or null |
| `round` | integer | >= 1 |
| `content` | string | Non-empty |

### Overall JSON
- The complete Phase 4 structured output must be valid, parseable JSON
- Must contain top-level keys: `brainstorm_id`, `created_at`, `question`, `perspectives`, `synthesis`, `dialogue_history`

## Quality Checks (v1.1)

Quality evals use the rubric in `evals/quality-rubric.md`. This section defines case-specific expectations per dimension.

### Dimension 1: Perspective Independence (minimum: 4)

**Why 4 is expected:** This test case has natural persona divergence built into the question:
- Methodology Critic should challenge the prediction-intervention gap (predicting churn != reducing it) and push for causal methods
- Stakeholder Advocate should reframe around the VP's "15% reduction" target -- that's an intervention goal, not a prediction goal
- Pragmatist should challenge the "this quarter" timeline and push for an 80/20 version (rules-based segmentation first)

**Failure indicators:** All 3 personas focus on "churn prediction is hard" without diverging on WHY it's hard from their perspective. If Methodology Critic and Pragmatist both say "data quality is a concern" with the same specifics, they've collapsed into one voice.

### Dimension 2: Domain Grounding (minimum: 2, ceiling: 3)

**Why ceiling is 3:** No `--domain` flag is specified. Personas should use general DS vocabulary appropriate to churn prediction (AUC, survival analysis, causal inference, feature leakage, survivorship bias), but without a domain file, the grounding ceiling is capped per the rubric's compressed scale.

**Expected general vocabulary:**
- Methodology Critic: causal inference, prediction-intervention gap, label definition, feature leakage, survivorship bias
- Stakeholder Advocate: churn rate vs. model accuracy, intervention ROI, action plan
- Pragmatist: data quality, schema changes over 2 years, intervention channel availability

**Failure indicators:** Personas give advice so generic it could apply to any classification problem ("make sure your data is clean", "use cross-validation"). Churn-specific DS vocabulary should appear even without a domain file.

### Dimension 3: Synthesis Quality (minimum: 4)

**Why 4 is expected:** This test case has STRONG built-in tensions that the synthesis should surface:
- **Rigor vs. timeline:** Methodology Critic wants causal inference; Pragmatist says that won't ship this quarter
- **Prediction vs. intervention:** Methodology Critic and Stakeholder Advocate should both flag that a prediction model alone doesn't reduce churn, but for different reasons (methodological validity vs. stakeholder value)
- **Scope:** Pragmatist wants 80/20 rules-based; Methodology Critic wants proper causal analysis; Stakeholder Advocate wants something the VP can act on NOW

These are genuine, decision-forcing tensions. The synthesis should stage them as explicit exchanges, not summarize them.

**Failure indicators:** Synthesis says "all agree the timeline is aggressive" without staging the actual disagreement about WHAT to do about it. Or key_question is generic ("how should you approach churn?") instead of forcing a decision ("should you ship a simple rules-based segmentation this quarter and defer the ML model, or invest in the full pipeline and negotiate the timeline with the VP?").

### Dimension 4: Socratic Challenge (minimum: 3)

**Why 3 is the floor:** The embedded complexity (VP target, timeline pressure, prediction-intervention gap) gives the challenger rich material to push back on. Even in round 1, the challenger should force the user to choose between the VP's timeline and methodological rigor.

**Expected challenge areas:**
- If user says "I'll start with a simple model" -- challenger should push on whether a simple model can achieve 15% reduction
- If user says "I'll use causal methods" -- challenger should push on timeline feasibility
- If user ignores the intervention channel question -- challenger should escalate it

**Failure indicators:** Challenger accepts "I'll build a simple model first" without asking what the intervention plan is once at-risk users are identified.

### Dimension 5: Actionability (minimum: 4)

**Why 4 is expected:** The VP's concrete "15% this quarter" target creates strong actionability pressure. Every finding should connect to a decision:
- Methodology Critic: "IF you want causal claims, THEN you need X; OTHERWISE, frame it as correlation"
- Stakeholder Advocate: "Frame the deliverable as 'at-risk user segments + recommended interventions' not 'churn model accuracy'"
- Pragmatist: "Week 1: validate data quality + intervention channels. Week 2-4: build v1. This leaves 8 weeks for iteration."

**Failure indicators:** next_actions are "investigate data quality" or "align with stakeholders" without specifics about WHAT to investigate or HOW to align. The VP's 15% target should anchor the action plan.

### Pass Criteria

- **Weighted average:** >= 3.5
- **Per-dimension minimums:** D1 >= 4, D2 >= 2, D3 >= 4, D4 >= 3, D5 >= 4
- **Both conditions must hold.** A weighted average of 3.8 with D3 = 2 is a FAIL (synthesis should be strong on this case).

---

## Simulated User Response (for eval)

When the brainstorm reaches the Socratic loop and presents the synthesis, respond as:

```
Good points. I'll start with a logistic regression model using payment and activity
features. For the intervention, we'll flag at-risk users weekly and have the CS team
do personalized outreach calls. I think we can get a basic model deployed in 3-4 weeks,
which leaves enough runway to hit the VP's quarterly target. We'll use AUC to track
model quality and churn rate reduction as the business metric.
```

**Why this response is useful for eval:**
- Leaves the prediction-intervention gap open — CS outreach is a channel, not a
  designed intervention. What do they say? What offer do they make? How do you
  know it works?
- Timeline is optimistic — 3-4 weeks to deploy a model assumes clean data, clear
  label definition, and existing infrastructure. None verified.
- AUC as model metric is fine but doesn't address the Methodology Critic's causal
  concern — high AUC doesn't mean the intervention will reduce churn by 15%
- Doesn't address label definition (what is "churned"?) or survivorship bias
- Ignores the Pragmatist's 80/20 suggestion (rules-based segmentation first)

---

## What This Eval Does NOT Check (Structural -- v1.0)

- Whether the Methodology Critic correctly identifies the prediction-intervention gap
- Whether the Pragmatist's timeline concern is calibrated to a realistic engineering velocity
- Whether the Stakeholder Advocate's VP-framing advice is actually persuasive
