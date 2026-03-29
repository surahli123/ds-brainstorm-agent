# Test Case: Multi-Topic Scope Check Gate

**ID:** eval-003-multi-topic-scope-check
**Difficulty:** Hard
**Domain:** None

## Input

```
/ds-brainstorm

I want to analyze our search ranking quality, build a recommendation engine, and also look at user segmentation for marketing.
```

## Why This Is "Hard"

- Tests the Phase 0 scope check gate — the first line of defense against unfocused brainstorms
- The input contains 3 distinct analysis topics that require different methodologies, data, and stakeholders:
  1. **Search ranking quality** — evaluation metrics, ranking model performance, relevance analysis
  2. **Recommendation engine** — collaborative filtering, content-based, engagement optimization
  3. **User segmentation for marketing** — clustering, behavioral cohorts, targeting strategy
- The scope check must fire BEFORE any subagent dispatch. If subagents run, the eval fails.
- "Hard" because it tests error handling and gating, not the happy path. Many agents will try to be helpful and address all 3 topics rather than enforcing the one-question-per-session constraint.

## Expected Phase Flow

1. **Phase 0 (Scope Check):** FAIL — multiple distinct analysis topics detected
2. **All subsequent phases:** SKIPPED — no dispatch, no synthesis, no Socratic loop, no structured output

The agent should stop at Phase 0 and return control to the user.

## Expected Behavior

### What SHOULD Happen
1. Agent detects 3 distinct topics in the input
2. Agent surfaces the topics explicitly (e.g., numbered list)
3. Agent asks the user to choose ONE topic to brainstorm
4. Agent does NOT proceed to search grounding, subagent dispatch, or any downstream phase
5. Agent waits for user selection before continuing

### Example Expected Response Pattern
```
I see 3 distinct analysis topics in your question:

1. **Search ranking quality** — evaluating how well your ranking model performs
2. **Recommendation engine** — building a new system for content recommendations
3. **User segmentation for marketing** — clustering users into targetable cohorts

These are each substantial analyses that deserve focused brainstorming. Which one would you like to dig into first?
```

The exact wording doesn't matter — the structural check is about behavior, not prose.

### What SHOULD NOT Happen
- Agent attempts to brainstorm all 3 topics (violates one-question-per-session constraint)
- Agent picks one topic on behalf of the user without asking (violates user control)
- Agent dispatches any subagent (methodology_critic, stakeholder_advocate, or pragmatist)
- Agent produces a synthesis section
- Agent enters the Socratic dialogue loop
- Agent produces structured Phase 4 JSON output

## Structural Checks (Pass/Fail Criteria)

### Scope Check Gate
| Check | Expected |
|-------|----------|
| Scope check fires | Yes — before any other phase |
| Multiple topics surfaced | Yes — agent identifies >= 2 distinct topics |
| User asked to select | Yes — agent explicitly asks user to choose one |

### No Downstream Output
| Check | Expected |
|-------|----------|
| `perspectives` in output | NO — no subagent outputs should exist |
| `synthesis` in output | NO — no synthesis should be produced |
| `dialogue_history` in output | NO — no Socratic dialogue should occur |
| Structured JSON produced | NO — Phase 4 is not reached |

### Why This Matters
The scope check gate exists because multi-topic brainstorms produce shallow, unfocused output. The Error Recovery table in CLAUDE.md explicitly states:

> **Multi-topic input:** User's question is too broad → Scope-check gate: ask user to pick one → Don't attempt multi-topic brainstorm

This eval verifies that the gate actually works. Without it, users get a false sense of depth when the agent spreads thin across multiple topics.

## Edge Cases to Consider for Future Evals

These are NOT checked in v1 but are worth noting for v1.1:

- **Two related topics:** "I want to analyze search ranking quality and also understand how query understanding affects ranking." — This is arguably one topic with two angles. Should scope check pass or fail? (Leaning: pass, with a note that these are related.)
- **One topic, multiple sub-questions:** "For our churn model, should we use logistic regression or XGBoost, and how should we define the churn label?" — This is one topic with implementation details. Should pass.
- **Vague single topic:** "I want to improve things." — Passes scope check (single topic) but should trigger a clarification request in a different way.

## Quality Checks (v1.1)

Not applicable — this test case verifies Phase 0 rejection behavior, not brainstorm quality.
No subagent output is produced, so quality dimensions cannot be scored.
