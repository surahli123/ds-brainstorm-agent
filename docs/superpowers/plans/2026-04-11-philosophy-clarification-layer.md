# Philosophy-Based Clarification Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Wittgenstein-Socrates-Polanyi clarification framework to ds-brainstorm-agent — Phase 3 pushback tools first (zero friction), then Phase 0.5 pre-debate clarification (light touch).

**Architecture:** Two integration points into existing SKILL.md. (1) Three new pushback tools added inline to Phase 3 Socratic dialogue. (2) A new `prompts/build_clarification.md` file containing the full clarification protocol, referenced by a new Step 0.1.5. Phase 3 tools are higher priority (improve every session without friction). Phase 0.5 adds 1-2 dialogue turns for vague inputs only.

**Tech Stack:** Pure markdown prompt engineering. No Python, no dependencies. Two files changed: `brainstorm/skill/SKILL.md` (modified), `brainstorm/skill/prompts/build_clarification.md` (new).

**Spec:** `docs/superpowers/specs/2026-04-11-philosophy-clarification-layer-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `brainstorm/skill/SKILL.md` | MODIFY | Add Phase 3 pushback tools (Steps 3.2 changes + new Step 3.2.3), add Step 0.1.5 reference, make Step 0.4 conditional, update Step 0.5 evidence block |
| `brainstorm/skill/prompts/build_clarification.md` | CREATE | Full Wittgenstein-Socrates-Polanyi clarification protocol with DS-specific adaptations |
| `brainstorm/skill/evals/test-cases/vague-input-clarification.md` | CREATE | Eval test case for vague input triggering clarification |
| `brainstorm/skill/evals/test-cases/phase3-philosophy-pushback.md` | CREATE | Eval test case for Phase 3 philosophy tools |

---

### Task 1: Add Wittgenstein Response Decomposition to Phase 3 (Step 3.2)

**Files:**
- Modify: `brainstorm/skill/SKILL.md` — Phase 3, Step 3.2 section

This is the highest-value change. When a user responds to a tension with vague words ("impact", "better", "significant"), the orchestrator decomposes before accepting.

- [ ] **Step 1: Read current Step 3.2 in SKILL.md**

Read `brainstorm/skill/SKILL.md` and locate the `### Step 3.2: Push Back (Targeted Adversarial)` section. Note the exact text of the opening paragraph and the first sub-section.

- [ ] **Step 2: Insert Wittgenstein check at the START of Step 3.2**

After the Step 3.2 heading and before the existing "If the user addressed some concerns but not others" paragraph, insert this new sub-section:

```markdown
**Wittgenstein Vague Word Check (run FIRST, before any other pushback):**

Before quoting persona findings, scan the user's response for DS vague words. If any
are found, decompose before proceeding — vague responses produce vague follow-ups.

**Lookup table access:** Re-read `prompts/build_clarification.md` Layer 1 Step 2 for
the DS-specific vague word table. Common triggers: "impact" (which metric? which segment?),
"better" (by what measure? compared to what baseline?), "significant" (statistically or
business-meaningful?), "optimize" (for speed, accuracy, coverage, or cost?),
"performance" (latency? throughput? quality? cost?).

**When triggered:**
> *"Two words need unpacking before I can accept this:*
> - *'[word 1]' — [clarification direction from lookup table]*
> - *'[word 2]' — [clarification direction from lookup table]*
>
> *Pick the specific measures and I'll check them against what the [persona name] raised."*

**Rules:**
- Surface at most 2 vague words per response. Don't turn pushback into a vocabulary quiz.
- If the user's response contains no vague words from the table, skip silently and
  proceed to verbatim persona quote.
- This check fires INSTEAD of other philosophy tools for this round (one philosophy
  intervention per round — Wittgenstein has highest priority).
```

- [ ] **Step 3: Verify the insertion point is correct**

Re-read the modified section to confirm the Wittgenstein check appears BEFORE the existing "If the user addressed some concerns but not others" paragraph and AFTER the Step 3.2 heading.

- [ ] **Step 4: Commit**

```bash
git add brainstorm/skill/SKILL.md
git commit -m "feat(brainstorm): add Wittgenstein vague word decomposition to Phase 3 pushback"
```

---

### Task 2: Add Socratic Hidden Premise Detection to Phase 3 (Step 3.2)

**Files:**
- Modify: `brainstorm/skill/SKILL.md` — Phase 3, Step 3.2 section

When a user commits to an approach ("we'll run an A/B test for two weeks"), surface the unstated assumptions.

- [ ] **Step 1: Locate the insertion point in Step 3.2**

The Socratic check goes AFTER the existing verbatim persona quote logic and AFTER the existing deflection detection. Find the paragraph starting with "**If the user deflected or gave a vague answer:**" — the Socratic check inserts AFTER that paragraph's closing code block.

- [ ] **Step 2: Insert Socratic hidden premise detection**

After the deflection detection paragraph and before the "**Verbatim quoting rules:**" section, insert:

```markdown
**Socratic Hidden Premise Check (after persona quote, if user committed to an approach):**

When the user's response contains a concrete commitment (a method choice, a timeline,
a metric selection), surface 2-3 unstated assumptions baked into that decision.

**When triggered:**
> *"That decision assumes three things:*
> 1. *[assumption about data/infrastructure]*
> 2. *[assumption about timing/external factors]*
> 3. *[assumption about scope/feasibility]*
>
> *Which of these have you verified?"*

**DS-specific premise patterns to check:**
- Timeline commitments → assumes sufficient traffic/data volume for power
- Metric choices → assumes the metric isn't confounded by other factors
- Methodology choices → assumes required infrastructure exists
- Audience framing → assumes stakeholder priorities haven't shifted
- Baseline comparisons → assumes the baseline period is representative

**Rules:**
- Only fire when the user makes a NEW commitment in their response, not when
  they restate an existing decision from the analysis plan.
- Surface exactly 2-3 premises. Not 1 (too light), not 5 (overwhelming).
- This check does NOT fire if Wittgenstein already fired this round (one
  philosophy intervention per round).
```

- [ ] **Step 3: Verify insertion is correct**

Re-read Step 3.2 to confirm the order is: (1) Wittgenstein check, (2) verbatim persona quote logic, (3) Socratic hidden premise check, (4) deflection detection, (5) contradiction detection.

Wait — re-check: the spec says Socratic goes AFTER verbatim quote. The existing structure has: addressed concerns → persona quote → deflection → contradiction. The Socratic check should go between persona quote and deflection. Verify and adjust if needed.

- [ ] **Step 4: Commit**

```bash
git add brainstorm/skill/SKILL.md
git commit -m "feat(brainstorm): add Socratic hidden premise detection to Phase 3 pushback"
```

---

### Task 3: Add Polanyi Stall Detection to Phase 3 (New Step 3.2.3)

**Files:**
- Modify: `brainstorm/skill/SKILL.md` — Phase 3, after Step 3.2.2

When a user stalls ("you know what I mean", uses unexplained metaphors, skips a tension), switch from verbal questioning to extraction strategies.

- [ ] **Step 1: Locate Step 3.2.2 (Quantitative Threshold Push)**

Find the end of `### Step 3.2.2: Quantitative Threshold Push` section in SKILL.md. The new Step 3.2.3 inserts immediately after.

- [ ] **Step 2: Insert new Step 3.2.3**

After Step 3.2.2's closing rules, insert:

```markdown
### Step 3.2.3: Polanyi Stall Detection + Extraction

**When to trigger:** Starting from round 1 onwards, check each user response for
stall signals. This step detects when the user KNOWS what they want but CANNOT
verbalize it — a fundamentally different problem than vagueness (Wittgenstein) or
compressed intent (Socratic).

**Trigger signals (any one triggers this step):**
- User says "you know what I mean", "that kind of thing", "hard to explain"
- User uses a metaphor they can't unpack: "like what we did last quarter",
  "that McKinsey-style thing"
- User goes silent on a specific tension (addresses others, skips one consistently)
- User keeps revising the same answer without converging (3+ revisions of the same point)
- User directly says "I can't explain it but I know it when I see it"

**When triggered, STOP verbal questioning. Switch to extraction:**

> *"Sounds like you have a feel for this but it's hard to pin down. Let me try a
> different angle:*
> - *Can you point me to a past analysis or dashboard that got this right? I'll
>   extract the pattern.*
> - *Or tell me what outcome would make this analysis useless — sometimes the
>   negative is easier to articulate."*

**Three DS-adapted extraction strategies (use 1-2, not all 3):**

| Strategy | When to use | Template |
|---|---|---|
| **Demonstration** | User references past work they liked | "Show me a past analysis or dashboard that captured what you're looking for — I'll extract the pattern" |
| **Negation** | User can't say what they want | "What outcome would make this analysis useless? What metric would be misleading here?" |
| **Behavioral extraction** | User has a body of prior work | "Link me to a previous analysis doc or notebook where you nailed the framing — I'll extract your implicit rules" |

**After extraction, surface findings for confirmation:**
> *"From your [example/negation/past work], I'm extracting these implicit preferences:*
> - *[preference 1]*
> - *[preference 2]*
>
> *Does that match what you were trying to say?"*

**Dual Polanyi guard:** If Polanyi extracted preferences in Phase 0.5 (stored in the
`clarified_statement` block's "Tacit preferences" field), reference those extractions
first before re-triggering extraction in Phase 3. Say: "Earlier you showed me [example]
and I extracted [preferences]. Does that still apply here, or is this a different kind
of stall?" Only re-trigger full extraction if the Phase 0.5 preferences don't cover it.

**Rules:**
- Max 1 Polanyi intervention per dialogue round.
- If user has no examples on hand, use only Negation.
- Never use all three strategies — pick the most fitting 1-2.
- Always surface extracted preferences for user confirmation — never assume.
- Never continue verbal questioning on a stalled point; the stall IS the signal
  that Socratic questioning has hit its limit.
- This step does NOT fire if Wittgenstein or Socratic already fired this round
  (one philosophy intervention per round — Polanyi has lowest priority).
```

- [ ] **Step 3: Add the one-intervention-per-round priority rule**

After Step 3.2.3, before Step 3.3 (Re-invoke Subagent), insert:

```markdown
### Philosophy Intervention Priority (Steps 3.2 + 3.2.3)

At most ONE philosophy-framework tool fires per pushback round. Priority order:

1. **Wittgenstein decomposition** (Step 3.2, first check) — if vague words detected,
   decompose first. Blocks everything else until resolved.
2. **Socratic hidden premise** (Step 3.2, after persona quote) — if user committed
   to an approach, surface assumptions.
3. **Polanyi stall detection** (Step 3.2.3) — if user stalled, switch to extraction.

If multiple triggers fire in the same round, pick the highest-priority one. The others
can fire in subsequent rounds. This prevents overwhelm — the orchestrator already has
persona quotes, blind spots, and threshold pushes.
```

- [ ] **Step 4: Commit**

```bash
git add brainstorm/skill/SKILL.md
git commit -m "feat(brainstorm): add Polanyi stall detection + philosophy priority rule to Phase 3"
```

---

### Task 4: Create `prompts/build_clarification.md`

**Files:**
- Create: `brainstorm/skill/prompts/build_clarification.md`

The full Wittgenstein-Socrates-Polanyi clarification protocol. This file is the reference for Phase 0.5 and the lookup table source for Phase 3.

- [ ] **Step 1: Create the file**

Write `brainstorm/skill/prompts/build_clarification.md` with this exact content:

```markdown
# Input Clarification Protocol — Wittgenstein-Socrates-Polanyi

## How to Use This Template

The SKILL.md orchestrator follows this protocol at Step 0.1.5, after scope check
and before domain knowledge loading. It transforms vague user input into a clarified
analysis statement. Max 2 dialogue turns for the entire protocol.

## Skip Condition

If the user's input already contains ALL THREE of:
(a) a specific metric or measure,
(b) a clear comparison or hypothesis, and
(c) a defined scope (time range, user segment, or system component)

Then skip this entire protocol. Tell the user:
"Your question is already sharp — moving to the debate."

---

## Layer 1: Wittgenstein Scan

**Goal:** Decompose the user's input into atomic propositions.

### Step 1: F/D/Q Classification

Classify every clause in the user's input into three types:

| Type | Definition | Example |
|------|-----------|---------|
| **F (Fact)** | Verifiable objective statement | "We launched a new ranking model 2 weeks ago" |
| **D (Desire)** | State the user wants to achieve | "I want to prove it's better than the old model" |
| **Q (Confusion)** | Something uncertain or unresolved | "Not sure whether to use offline eval or online A/B" |

Present the classification conversationally (not as a formal table) and ask:
"Did I get that right? Anything missing?"

**Skip if:** Input is already a single, clear type (e.g., a precise hypothesis).

**Multi-topic discovery:** If F/D/Q decomposition reveals multiple independent D's
or Q's addressing different subjects, loop back to Step 0.1 (scope check) with the
decomposed propositions. Tell the user: "Your question unpacks into N distinct
analyses: [list]. Which one should we brainstorm first?"

### Step 2: Vague Word Detection

Scan the input for high-frequency vague words. Ask targeted clarification for the
1-2 most critical ones only.

**DS-specific vague word lookup table:**

| Vague phrase | Clarification direction |
|---|---|
| "impact" | On which metric? For which user segment? |
| "better" | By what measure? Compared to what baseline? |
| "optimize" | Optimize for speed, accuracy, coverage, or cost? |
| "significant" | Statistically significant or business-meaningful? At what threshold? |
| "improve relevance" | NDCG? Precision? User satisfaction? Session success? |
| "analyze" | Descriptive (what happened), diagnostic (why), or predictive (what if)? |
| "the model" | Which model? Which version? Production or candidate? |
| "performance" | Latency? Throughput? Quality? Cost? |
| "users" | All users? A segment? Power users? New users? |
| "test" | A/B test? Offline eval? Statistical test? Manual QA? |
| "data" | What table/source? What time range? What granularity? |
| "the metric" | Which specific metric? How is it computed? |

**Rule:** Only surface the 1-2 most critical vague words. Don't interrogate.

---

## Layer 2: Socratic Question (1 Targeted Question)

**Goal:** Draw out the single biggest piece of compressed intent.

After Layer 1 resolves surface ambiguity, ask ONE question — whichever targets
the biggest remaining gap:

| Type | Template | When to use |
|------|----------|-------------|
| **Definition check** | "When you say [X], what exactly do you mean?" | Term could mean multiple things |
| **Success criterion** | "What would the output look like for you to feel it's right?" | User described what to do, not what 'done' looks like |
| **Hidden premise** | "Is there anything you haven't said but really care about?" | Implicit constraints (timeline, politics, audience) |

**DS-specific question bank:**
- "Who is going to act on this analysis, and what decision does it unlock?"
- "What's the smallest result that would still be worth presenting?"
- "If the data showed the opposite of what you expect, what would you do?"
- "Is there a deadline or decision meeting driving the timeline?"
- "Have you already tried something that didn't work?"

**Rules:**
- Ask only 1 question. Not 3. One.
- Skip if Layer 1 already resolved all ambiguity.

---

## Layer 3: Polanyi Fallback (Tacit Knowledge Extraction)

**Goal:** Handle the "you know what I mean" problem.

**This layer is a FALLBACK — skip unless triggered.**

**Trigger signals (any one triggers this layer):**
- User says "you know what I mean", "that kind of thing", "hard to explain"
- User uses a metaphor they can't unpack: "like what we did last quarter"
- User directly says "I can't explain it but I know it when I see it"
- User keeps revising the same answer without converging

**Three DS-adapted extraction strategies (use 1-2, not all 3):**

| Strategy | Generic | DS-adapted |
|---|---|---|
| **Demonstration** | "Show me an example that's right" | "Show me a past analysis or dashboard that captured what you're looking for — I'll extract the pattern" |
| **Negation** | "Tell me what you don't want" | "What outcome would make this analysis useless? What metric would be misleading here?" |
| **Behavioral** | "Send me past work you liked" | "Link me to a previous analysis doc or notebook where you nailed the framing — I'll extract your implicit rules" |

**Rules:**
- Never use all three — pick the most fitting 1-2.
- If user has no examples, use only Negation.
- Always surface extracted preferences for user confirmation — never assume.
- Never continue verbal questioning on a stalled point.

---

## Output: Clarified Analysis Statement

After clarification completes (max 2 dialogue turns), produce:

**Original input:** {user's verbatim input}

**Clarified question:** {the sharpened analysis question}

**F/D/Q breakdown:**
- F: {facts established}
- D: {desires identified}
- Q: {confusions remaining — these feed the persona debate}

**Tacit preferences:** {Polanyi extractions, if any — otherwise "None extracted"}

**Constraints surfaced:** {timeline, audience, political, methodological constraints}

This block is added to the evidence block (Step 0.5) as "Clarification Context."

---

## Search Grounding Gate

After clarification, search grounding depends on domain context:

| Scenario | Behavior |
|---|---|
| `--domain` specified | Run Phase 0.4 search grounding automatically |
| No `--domain`, user provided rich context | Ask: "Want me to search for external context, or is your description sufficient?" |
| No `--domain`, vague input clarified | Ask: "Do you want me to search for domain context and prior art, or do you have specific references to share?" |

---

## Hard Rules

1. **Lightness first.** If input has metric + hypothesis + scope → skip entirely.
2. **Max 2 dialogue turns** for the whole protocol. After 2 turns, proceed.
3. **Never teach the framework.** Don't mention Wittgenstein or Polanyi. Just do it.
4. **Never paraphrase.** Show F/D/Q classification, don't restate everything.
5. **Zero filler.** No "Got it," "Great question." Every sentence advances clarification.
6. **Polanyi is a fallback,** not a mandatory step.
7. **Multi-topic discovery.** If F/D/Q reveals multiple analyses, loop to scope check.
```

- [ ] **Step 2: Verify the file exists and is well-formed**

```bash
wc -l brainstorm/skill/prompts/build_clarification.md
head -5 brainstorm/skill/prompts/build_clarification.md
```

Expected: ~160 lines, header shows "# Input Clarification Protocol"

- [ ] **Step 3: Commit**

```bash
git add brainstorm/skill/prompts/build_clarification.md
git commit -m "feat(brainstorm): add Wittgenstein-Socrates-Polanyi clarification protocol"
```

---

### Task 5: Add Step 0.1.5 to SKILL.md (Phase 0.5 Integration)

**Files:**
- Modify: `brainstorm/skill/SKILL.md` — Phase 0, between Step 0.1 and Step 0.2

- [ ] **Step 1: Locate Step 0.1 (Scope Check) in SKILL.md**

Find the end of `### Step 0.1: Scope Check` section. The new Step 0.1.5 inserts immediately after, before `### Step 0.2: Domain Knowledge Loading`.

- [ ] **Step 2: Insert Step 0.1.5**

After the scope check section and before Step 0.2, insert:

```markdown
### Step 0.1.5: Input Clarification (Wittgenstein-Socrates-Polanyi)

Follow the clarification protocol in `prompts/build_clarification.md`.

**Skip condition:** If the user's input already contains: (a) a specific metric or
measure, (b) a clear comparison or hypothesis, and (c) a defined scope — skip
clarification and proceed to Step 0.2. Tell the user: *"Your question is already
sharp — moving to the debate."*

**Output:** A `clarified_statement` block that replaces the raw user input in all
downstream phases. The original input is preserved as `original_input` for reference.

**Search grounding gate:** If `--domain` is NOT specified, after clarification ask
the user whether to run web search, accept user-provided references, or proceed
without external context. If `--domain` IS specified, proceed to Step 0.4 (search
grounding) automatically.
```

- [ ] **Step 3: Verify insertion is correctly positioned**

Re-read Phase 0 to confirm the step order is: 0.1 (Scope Check) → 0.1.5 (Input Clarification) → 0.2 (Domain Knowledge Loading).

- [ ] **Step 4: Commit**

```bash
git add brainstorm/skill/SKILL.md
git commit -m "feat(brainstorm): add Step 0.1.5 input clarification to Phase 0"
```

---

### Task 6: Make Phase 0.4 Search Grounding Conditional

**Files:**
- Modify: `brainstorm/skill/SKILL.md` — Phase 0, Step 0.4

- [ ] **Step 1: Locate Step 0.4 (Search Grounding) in SKILL.md**

Find the `### Step 0.4: Search Grounding` section.

- [ ] **Step 2: Add conditional gate at the top of Step 0.4**

Insert at the very beginning of Step 0.4, before the existing "Execute three WebSearch calls" instruction:

```markdown
**Conditional execution:** This step runs automatically when `--domain` is specified
(domain knowledge guides search queries). When `--domain` is NOT specified, Step 0.1.5
(Input Clarification) already asked the user whether to run web search. If the user
declined search, skip this step entirely and proceed to Step 0.5 with whatever context
is available. If the user opted in to search, proceed below.
```

- [ ] **Step 3: Commit**

```bash
git add brainstorm/skill/SKILL.md
git commit -m "feat(brainstorm): make search grounding conditional on domain/user choice"
```

---

### Task 7: Update Evidence Block Assembly (Step 0.5)

**Files:**
- Modify: `brainstorm/skill/SKILL.md` — Phase 0, Step 0.5

- [ ] **Step 1: Locate Step 0.5 evidence block structure**

Find the `### Step 0.5: Evidence Block Assembly` section and the markdown template showing the evidence block structure.

- [ ] **Step 2: Add Clarification Context section to the evidence block template**

In the evidence block template, add a new section at the TOP (before "### Confluence Context"):

```markdown
### Clarification Context
- **Original input:** {original_input — the user's verbatim question before clarification}
- **Clarified question:** {clarified_statement — the sharpened question from Step 0.1.5}
- **Tacit preferences:** {polanyi_extractions from Step 0.1.5, if any — otherwise "None extracted"}
- **Constraints surfaced:** {constraints from F/D/Q classification in Step 0.1.5}

[Omit this section entirely if Step 0.1.5 was skipped (input was already precise).]
```

- [ ] **Step 3: Commit**

```bash
git add brainstorm/skill/SKILL.md
git commit -m "feat(brainstorm): add clarification context to evidence block assembly"
```

---

### Task 8: Add Eval Test Cases

**Files:**
- Create: `brainstorm/skill/evals/test-cases/vague-input-clarification.md`
- Create: `brainstorm/skill/evals/test-cases/phase3-philosophy-pushback.md`

- [ ] **Step 1: Create vague input clarification test case**

Write `brainstorm/skill/evals/test-cases/vague-input-clarification.md`:

```markdown
# Eval: Vague Input Triggers Clarification

## Test Input

"I want to analyze the impact of our new model on performance"

## Expected Behavior

1. Step 0.1.5 fires (input lacks specific metric, comparison, and scope)
2. F/D/Q classification produced:
   - F: A new model exists
   - D: User wants to measure its effect
   - Q: Which metric, which aspect of performance, compared to what
3. Vague words detected: "impact" (which metric?), "performance" (latency? quality?)
4. At most 1 Socratic question asked
5. Clarified statement produced with specific metric and scope

## Anti-Patterns (should NOT happen)

- Clarification skipped (input is clearly vague)
- More than 2 dialogue turns consumed
- Framework names mentioned ("Wittgenstein", "Polanyi")
- All 3 Polanyi strategies offered at once
- Generic F/D/Q shown to precise input (skip condition test):
  Input: "Measure NDCG@10 delta between model A and B on navigational queries over 2 weeks"
  → Should skip clarification entirely

## Edge Case: Multi-Topic Discovery

Input: "I want to analyze the impact of the new ranking model and also look into
why our query classification accuracy dropped last week"

Expected: F/D/Q reveals 2 independent analyses → loops back to scope check →
asks user which to brainstorm first
```

- [ ] **Step 2: Create Phase 3 philosophy pushback test case**

Write `brainstorm/skill/evals/test-cases/phase3-philosophy-pushback.md`:

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add brainstorm/skill/evals/test-cases/vague-input-clarification.md brainstorm/skill/evals/test-cases/phase3-philosophy-pushback.md
git commit -m "feat(brainstorm): add eval test cases for philosophy clarification layer"
```

---

## Parallelization Strategy

| Task | Touches | Depends on | Lane |
|------|---------|------------|------|
| Task 1 (Wittgenstein Step 3.2) | SKILL.md Phase 3 | — | A |
| Task 2 (Socratic Step 3.2) | SKILL.md Phase 3 | Task 1 (same section) | A |
| Task 3 (Polanyi Step 3.2.3) | SKILL.md Phase 3 | Task 2 (same section) | A |
| Task 4 (build_clarification.md) | NEW file | — | B |
| Task 5 (Step 0.1.5) | SKILL.md Phase 0 | Task 4 (references it) | C |
| Task 6 (Conditional 0.4) | SKILL.md Phase 0 | Task 5 | C |
| Task 7 (Evidence block) | SKILL.md Phase 0 | Task 6 | C |
| Task 8 (Eval test cases) | NEW files | — | D |

**Execution plan:**
- **Lane A** (Tasks 1-3): Phase 3 pushback tools — sequential within lane, touches same SKILL.md section
- **Lane B** (Task 4): New clarification protocol file — fully independent
- **Lane C** (Tasks 5-7): Phase 0 integration — sequential within lane, depends on Task 4
- **Lane D** (Task 8): Eval test cases — fully independent

**Launch:** Lanes A + B + D in parallel. After B completes, launch Lane C. After all lanes merge, final verification.

---

## Final Verification

After all tasks complete:

- [ ] Read `brainstorm/skill/SKILL.md` end-to-end and verify Phase 0 flow: 0.1 → 0.1.5 → 0.2 → ... → 0.4 (conditional) → 0.5 (with clarification context)
- [ ] Read `brainstorm/skill/SKILL.md` Phase 3 and verify tool order: Wittgenstein → persona quote → Socratic → deflection → contradiction → blind spots → thresholds → Polanyi
- [ ] Verify `prompts/build_clarification.md` lookup table matches the vague words referenced in Phase 3
- [ ] Run existing tests: `python3 -m pytest tests/ -q` — nothing should break (no Python changes)
