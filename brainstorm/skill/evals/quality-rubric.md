# Quality Eval Rubric (v1.1)

**Purpose:** Agent-as-judge rubric for evaluating brainstorm QUALITY. The coding agent reads this rubric, reads the brainstorm output, and scores each dimension inline. No external API needed.

**Context:** v1.0 evals check structural correctness (fields present, types valid). v1.1 evals check whether the brainstorm is actually GOOD -- whether it would help a data scientist make better decisions about their analysis plan.

**Judge pattern:** The agent evaluating the output reads this rubric + the test case's quality expectations, then scores each dimension 1-5 with a one-sentence justification. This happens inline in the agent's context -- no pip installs, no API calls, no external tools.

---

## How to Use This Rubric (Agent-as-Judge)

When evaluating a brainstorm output against this rubric:

1. Read the full brainstorm output (all perspectives, synthesis, dialogue)
2. Read the test case's `## Quality Checks (v1.1)` section for case-specific expectations
3. Score each of the 5 dimensions below on 1-5
4. Compute the weighted average
5. Report PASS if weighted average >= 3.5, FAIL otherwise
6. For each dimension, write ONE sentence explaining the score

**Scoring discipline:** A score of 3 means "adequate but unremarkable." A 4 means "genuinely good -- this added value the user wouldn't have gotten alone." A 5 means "exceptional -- this changed how the user thinks about the problem." Do NOT default to 4s. Most outputs should land between 2-4. A run of all 4s and 5s means the rubric is too lenient.

---

## Dimension 1: Perspective Independence (Weight: 30%)

**Question:** Do the 3 perspectives make meaningfully DIFFERENT points? Or are they 3 variations of the same generic advice?

| Score | Description | What to look for |
|-------|-------------|------------------|
| 1 | Near-identical | All 3 personas raise the same concerns in slightly different language. You could swap their labels and nothing changes. |
| 2 | Mostly overlapping | 2 of 3 personas are redundant. One adds a distinct point, the others echo it. |
| 3 | Somewhat distinct | Each persona has at least 1 unique concern, but there's significant overlap in their recommendations. |
| 4 | Genuinely independent | Each persona raises concerns the others don't. Their findings reflect their distinct lenses (rigor vs. impact vs. feasibility). Some natural overlap exists but it's the minority. |
| 5 | Independent and conflicting | Perspectives are clearly distinct AND they sometimes disagree with each other. The Methodology Critic wants more rigor while the Pragmatist says that's too slow. The tensions are real, not manufactured. |

**Red flags for low scores:**
- All 3 personas mention "data quality" without different specifics about WHAT data quality means from their lens
- All 3 personas recommend the same next step
- You could remove one persona's output and lose nothing

**What discriminates 3 from 4:** At score 3, each persona has a unique finding but their next_actions lists overlap heavily. At score 4, even the next_actions are distinct -- the Methodology Critic wants a statistical validation, the Stakeholder Advocate wants a framing exercise, the Pragmatist wants a data audit.

---

## Dimension 2: Domain Grounding (Weight: 20%)

**Question:** When `--domain` is specified, do personas reference domain-specific concepts naturally? When no domain is specified, do personas still use relevant general DS vocabulary (not penalized, but also not rewarded)?

| Score | Description | What to look for |
|-------|-------------|------------------|
| 1 | Domain-blind | Personas give completely generic advice that could apply to any analysis. Domain file was loaded but ignored. |
| 2 | Surface-level name-dropping | Domain terms appear but are used superficially -- listed but not reasoned about. "You should consider NDCG" without explaining why it matters here. |
| 3 | Moderate grounding | At least 2 personas use domain concepts to shape their specific challenges. The domain vocabulary appears in findings, not just in domain_references. |
| 4 | Strong grounding | Every persona uses domain vocabulary naturally in their reasoning. Domain concepts drive the challenge, not decorate it. |
| 5 | Domain-expert fluency | Personas reason WITH domain concepts, not just ABOUT them. They connect domain-specific concerns to their lens (e.g., Pragmatist asks about click log availability because position debiasing requires it, not because "click logs" was in the domain file). |

**Scoring when no --domain flag:**
- When no domain file is loaded, this dimension is scored on a compressed 1-3 scale mapped to 1-5:
  - 1-2: Generic advice with no relevant DS vocabulary
  - 3: Uses general DS concepts appropriate to the question (this maps to a score of 3)
  - Score cannot exceed 3 without domain file -- the ceiling is "adequate general DS advice"
- This means test cases without --domain should set their expected minimum lower (2-3 range)

**Red flags for low scores:**
- Domain file contains rich vocabulary (NDCG, MRR, QSR, L1/L2 layers) but personas only mention "metrics"
- Domain concepts appear in domain_references array but not in the actual findings text
- Persona could have given the same advice for any domain

---

## Dimension 3: Synthesis Quality (Weight: 20%)

**Question:** Does the synthesis surface REAL tensions between personas AND identify what all three missed?

| Score | Description | What to look for |
|-------|-------------|------------------|
| 1 | Consensus summary | Synthesis says "all three personas agree that..." with no tensions. No blind spots identified. Just a bulleted summary of each persona's output. |
| 2 | Weak tensions | Tensions array is non-empty but trivial or manufactured. Blind spots section absent or generic ("consider more factors"). |
| 3 | Identified tensions | Real tensions exist and are named, but stated as summaries rather than staged exchanges. Blind spots may be present but generic. |
| 4 | Staged disagreements + basic blind spots | Tensions are presented as explicit back-and-forth. Blind spots section exists with at least 1 specific finding that names a concrete assumption or gap none of the 3 personas questioned. |
| 5 | Decision-forcing tensions + insightful blind spots | Tensions are staged AND decision-forcing. Blind spots are specific, non-obvious, and grounded — e.g., "none of the three asked whether your click logs include bot traffic, which inflates engagement metrics by 10-20%." The blind spots change how the user thinks about the problem. |

**Red flags for low scores:**
- Synthesis tensions array has items like "there are tradeoffs to consider"
- key_question is generic ("what approach should you take?") rather than specific to the analysis
- Agreements section is longer than tensions section (usually a sign of mush)
- Blind spots section says "consider additional factors" without naming which factors or why they matter
- Blind spots repeat concerns already raised by individual personas (these aren't blind spots — they're duplicates)

**What discriminates 3 from 4:** At score 3, the synthesis says "The Methodology Critic is concerned about position bias while the Pragmatist questions data availability." At score 4, it also includes a blind spot like "None of the three personas asked whether the evaluation labels were collected from the same user population as production traffic — if your judges are search quality experts but your users are general consumers, the labels may not reflect real user satisfaction."

**What discriminates 4 from 5:** At score 4, blind spots name a gap. At score 5, blind spots change the shape of the analysis — they surface an assumption so fundamental that addressing it would alter the entire approach. The user reads it and thinks "oh, I hadn't considered that at all."

---

## Dimension 4: Socratic Challenge (Weight: 15%)

**Question:** Does the Socratic loop push back on user responses? Or does it accept everything the user says?

| Score | Description | What to look for |
|-------|-------------|------------------|
| 1 | Rubber-stamp | Challenger says "great point" or "that makes sense" and moves on. No pushback. |
| 2 | Weak pushback | Challenger acknowledges the user's point and adds a vague follow-up ("have you also thought about...") without challenging what was said. |
| 3 | Generic pushback | Challenger pushes back but with generic questions that could apply to any analysis ("what about edge cases?"). |
| 4 | Specific pushback | Challenger references specific unaddressed concerns from the personas and pushes back on what the user DIDN'T address. Uses the persona's actual findings. |
| 5 | Adaptive challenge | Challenger tracks which persona concerns the user has addressed vs. ignored, escalates unaddressed concerns, and opens new threads when the user's response reveals a new gap. |

**Note on eval limitations:** This dimension requires a simulated user response in the dialogue. Test cases should define what the simulated user says so the eval can check whether the challenger's response is appropriate. If the test case only has 1 round of dialogue, score based on the initial challenge quality.

**Red flags for low scores:**
- Challenger repeats the synthesis verbatim instead of adapting to the user's response
- Challenger never references a specific persona by name
- All rounds feel the same -- no progression or deepening

---

## Dimension 5: Actionability (Weight: 15%)

**Question:** Does the output help the user make concrete decisions about their analysis?

| Score | Description | What to look for |
|-------|-------------|------------------|
| 1 | Vague advice | "Consider your methodology carefully" or "think about stakeholder needs." No specifics. |
| 2 | Named concerns without resolution path | Problems are identified but next_actions are generic ("investigate further", "discuss with team"). |
| 3 | Concrete next steps | next_actions include specific tasks (e.g., "validate click log coverage for Q3-Q4 2025"). At least some findings connect to actions. |
| 4 | Decision-ready | next_actions include specific tradeoffs the user can evaluate. Findings are connected to decisions: "IF you have position data, THEN debias; OTHERWISE, use editorial labels as ground truth." |
| 5 | Prioritized action plan | next_actions are specific, ordered by priority, and acknowledge dependencies. The user could start executing immediately after reading them. Tradeoffs are named with clear upside/downside. |

**Red flags for low scores:**
- next_actions lists contain items that sound good but don't tell the user what to DO
- Findings describe problems without suggesting approaches
- All 3 personas have the same next_actions

---

## Pass/Fail Calculation

**Weighted score = (D1 * 0.30) + (D2 * 0.20) + (D3 * 0.20) + (D4 * 0.15) + (D5 * 0.15)**

| Result | Threshold | Meaning |
|--------|-----------|---------|
| PASS | >= 3.5 | Brainstorm quality is acceptable -- it provides value beyond what the user would get from a single-perspective review |
| MARGINAL | >= 3.0, < 3.5 | Brainstorm has some quality but significant dimensions are weak. Investigate which dimensions drag the score down. |
| FAIL | < 3.0 | Brainstorm quality is insufficient -- the multi-persona structure isn't adding meaningful value |

**Design target:** A well-functioning brainstorm agent should pass 60-80% of quality evals on first run. Passing 90%+ means the evals are too easy and won't discriminate between good and mediocre outputs. Failing more than 40% means either the agent or the evals need calibration.

---

## Per-Dimension Minimum Overrides

Test cases can set per-dimension minimum scores that override the global pass threshold. For example, a test case with `--domain search-relevance` might require Dimension 2 (Domain Grounding) >= 4, even if the weighted average passes at 3.5.

**How overrides work:**
- If ANY per-dimension minimum is violated, the test case FAILS regardless of weighted average
- This catches cases where a brainstorm scores well overall but is catastrophically weak in one area
- Test cases should only set overrides for dimensions where the test case design creates a strong expectation

---

## Judge Output Format

The agent-as-judge produces this structured assessment:

```
## Quality Eval: [test-case-id]

### Scores
| Dimension | Score | Weight | Weighted | Justification |
|-----------|-------|--------|----------|---------------|
| Perspective Independence | X/5 | 0.30 | X.XX | [one sentence] |
| Domain Grounding | X/5 | 0.20 | X.XX | [one sentence] |
| Synthesis Quality | X/5 | 0.20 | X.XX | [one sentence] |
| Socratic Challenge | X/5 | 0.15 | X.XX | [one sentence] |
| Actionability | X/5 | 0.15 | X.XX | [one sentence] |

**Weighted Average:** X.XX / 5.0
**Per-Dimension Minimums:** [PASS/FAIL — list any violations]
**Overall:** PASS / MARGINAL / FAIL

### Dimension Details
[For any dimension scoring <= 2, provide a specific example from the output showing the weakness]
[For any dimension scoring >= 4, cite the specific output that earned the high score]
```
