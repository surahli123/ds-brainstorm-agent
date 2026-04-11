# Eval: Phase 3 Philosophy Pushback Tools

## Test Scenario 1: Wittgenstein Response Decomposition

**Setup:** User received 3-persona synthesis with tensions. User responds:

"We'll just look at the impact on relevance"

**Expected:** Orchestrator decomposes before accepting:
- "impact" → which metric?
- "relevance" → judged by whom?
Persona quote follows AFTER user clarifies.

**Anti-Pattern:** Orchestrator accepts the vague response and quotes persona finding.

## Test Scenario 2: Socratic Hidden Premise Detection

**Setup:** User responds to a tension with a commitment:

"We'll run an A/B test for two weeks"

**Expected:** Orchestrator surfaces 2-3 assumptions:
- Sufficient traffic for statistical power?
- Immediate effect (no novelty curve)?
- Can hold constant for 2 weeks?

**Anti-Pattern:** Orchestrator accepts the commitment without surfacing assumptions.

## Test Scenario 3: Polanyi Stall Detection

**Setup:** User responds to a tension with:

"I want it to feel like... you know, like what we did for the last launch"

**Expected:** Orchestrator detects stall signal ("you know", unexplained metaphor).
Switches to extraction: asks for an example OR asks what they DON'T want.
Does NOT continue verbal questioning.

**Anti-Pattern:** Orchestrator asks "what do you mean by 'like the last launch'?"
(this is still verbal questioning, not extraction)

## Test Scenario 4: Priority Rule

**Setup:** User response contains BOTH a vague word ("impact") AND a commitment
("we'll do it in two weeks").

**Expected:** Only Wittgenstein fires (highest priority). Socratic hidden premise
detection waits for the next round.

**Anti-Pattern:** Both Wittgenstein and Socratic fire in the same round.

## Test Scenario 5: Dual Polanyi Guard

**Setup:** Polanyi extracted preferences in Phase 0.5 ("user prefers short-paragraph
reports with data up front"). User stalls again in Phase 3.

**Expected:** Orchestrator references Phase 0.5 extractions first: "Earlier you
showed me [example] and I extracted [preferences]. Does that still apply here?"
Only re-triggers full extraction if Phase 0.5 preferences don't cover it.

**Anti-Pattern:** Orchestrator runs full Polanyi extraction again without
referencing Phase 0.5 findings.
