# Philosophy-Based Clarification Layer for DS Brainstorm Agent

**Date:** 2026-04-11
**Status:** Design approved, pending implementation
**Inspiration:** [riiiku/clarify-skill](https://github.com/riiiku/clarify-skill), [Jaden's methodology post](https://x.com/Jaden_riku/status/2041013292005773507), [cellinlab's Polanyi deep-dive](https://x.com/cellinlab/status/2040428719206998507)

## Problem

The ds-brainstorm-agent is strong at *challenging* an analysis plan once stated, but weak
at *extracting what the user actually means* before the challenge begins. Phase 0 does a
scope check ("is this one question?") and jumps straight to search grounding. If the user
says "I want to analyze the impact of our new ranking model," we dispatch 3 personas
against that vague statement — producing generic challenges because the input was never
clarified.

Live user feedback confirmed this: "OK for coursework, not for real DS work." Domain
context was part of that gap, but input clarification is the other half.

## Philosophy Framework

Three philosophers, three cognitive layers — each handles a different type of
communication failure:

1. **Wittgenstein (Scan)** — Language is the boundary of thought. If you can't say it
   clearly, you haven't thought it clearly. Decompose vague compound statements into
   atomic propositions classified as F (fact), D (desire), or Q (confusion).

2. **Socrates (Excavate)** — The answer already exists in the person; targeted questions
   draw it out. Most people compress their real intent behind vague words — not out of
   laziness, but because the brain defaults to compression. Restore the compressed
   information with minimum questions.

3. **Polanyi (Sense)** — "We can know more than we can tell." Some knowledge is tacit —
   the user knows what they want but cannot verbalize it. When Socratic questioning
   stalls, switch to non-verbal extraction: demonstration, negation, behavioral patterns.

**Coverage:** These three layers are exhaustive for human expression failures:
- Things not yet thought through → Wittgenstein
- Things thought through but not expressed → Socrates
- Things that cannot be expressed in language → Polanyi

## Architecture: Approach B (Modular Clarify Layer)

Two integration points, matching the two sides of the dialogue:

### Integration Point A: Pre-Debate Clarification (New Phase 0.5)

A new file `prompts/build_clarification.md` containing the full clarification protocol.
SKILL.md references it as Step 0.1.5, between scope check and domain knowledge loading.
Light touch: max 2 dialogue turns, skip if input is already precise.

### Integration Point B: Enhanced Socratic Dialogue (Phase 3 Upgrade)

Inline additions to SKILL.md Phase 3. Three new pushback tools for the orchestrator
when processing user responses during the Socratic loop.

---

## Part 1: `prompts/build_clarification.md` — Specification

### Overview

The orchestrator follows this protocol after scope check (Step 0.1) and before domain
knowledge loading (Step 0.2). It transforms a vague user input into a clarified analysis
statement that feeds all downstream phases.

### Layer 1: Wittgenstein Scan

**Goal:** Decompose the user's input into atomic propositions.

**Step 1: F/D/Q Classification**

Classify every clause in the user's input into three types:

| Type | Definition | Example |
|------|-----------|---------|
| **F (Fact)** | Verifiable objective statement | "We launched a new ranking model 2 weeks ago" |
| **D (Desire)** | State the user wants to achieve | "I want to prove it's better than the old model" |
| **Q (Confusion)** | Something uncertain or unresolved | "Not sure whether to use offline eval or online A/B" |

**Output the classification to the user and ask:** "Did I get that right? Anything missing?"

**Skip condition:** If the input is already a single, clear type (e.g., a precise
hypothesis with metric and method), skip classification silently.

**Step 2: Vague Word Detection**

Scan the input for high-frequency vague words. If found, ask targeted clarification for
the 1-2 most critical ones only.

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

**Rule:** Only surface the 1-2 most critical vague words. Don't turn this into an
interrogation.

### Layer 2: Socratic Question (1 Targeted Question)

**Goal:** Draw out the single biggest piece of compressed intent.

After Layer 1 resolves surface ambiguity, ask ONE question from this bank — whichever
targets the biggest remaining gap:

**Three question types:**

| Type | Template | When to use |
|------|----------|-------------|
| **Definition check** | "When you say [X], what exactly do you mean?" | User used a term that could mean multiple things |
| **Success criterion** | "What would the output look like for you to feel it's right?" | User described what to do, but not what 'done' looks like |
| **Hidden premise** | "Is there anything you haven't said but really care about?" | User's plan has implicit constraints (timeline, politics, audience) |

**DS-specific question bank (examples):**

- "Who is going to act on this analysis, and what decision does it unlock?"
- "What's the smallest result that would still be worth presenting?"
- "If the data showed the opposite of what you expect, what would you do?"
- "Is there a deadline or decision meeting driving the timeline?"
- "Have you already tried something that didn't work?"

**Rules:**
- Ask only 1 question. Not 3. One.
- Skip if Layer 1 already resolved all ambiguity.
- Never ask more than 1 — the Phase 3 Socratic loop handles depth later.

### Layer 3: Polanyi Fallback (Tacit Knowledge Extraction)

**Goal:** Handle the "you know what I mean" problem — when the user knows what they want
but can't verbalize it.

**Trigger signals (any one triggers this layer):**
- User says "you know what I mean", "that kind of thing", "hard to explain"
- User uses a metaphor they can't unpack: "like what we did last quarter"
- User directly says "I can't explain it but I know it when I see it"
- User keeps revising the same answer without converging

**Three DS-adapted extraction strategies (use 1-2, not all 3):**

| Strategy | Generic version | DS-adapted version |
|---|---|---|
| **Demonstration** | "Show me an example that's right" | "Show me a past analysis or dashboard that captured what you're looking for — I'll extract the pattern" |
| **Negation** | "Tell me what you don't want" | "What outcome would make this analysis useless? What metric would be misleading here?" |
| **Behavioral extraction** | "Send me past work you liked" | "Link me to a previous analysis doc or notebook where you nailed the framing — I'll extract your implicit rules" |

**Rules:**
- Never use all three — pick the most fitting 1-2.
- If user has no examples on hand, use only Negation.
- Always surface extracted preferences for user confirmation — never assume.
- Never continue verbal questioning on a stalled point; that IS the signal Socrates
  has hit its limit.
- This layer is a FALLBACK. Most inputs resolve at Layer 1-2. Polanyi fires maybe
  20% of the time.

### Output: Clarified Analysis Statement

After clarification completes (1-2 dialogue turns max), produce a structured block:

```markdown
### Clarification Output

**Original input:** {user's verbatim input}

**Clarified question:** {the sharpened analysis question, reflecting all clarification}

**F/D/Q breakdown:**
- F: {facts established}
- D: {desires identified}  
- Q: {confusions remaining — these feed the persona debate}

**Tacit preferences:** {Polanyi extractions, if any — otherwise "None extracted"}

**Constraints surfaced:** {timeline, audience, political, methodological constraints
that emerged during clarification}
```

This block is added to the evidence block (Step 0.5) as a new top-level section called
"Clarification Context." All personas see both the original vague input AND the clarified
version — they can challenge the clarification itself.

### Search Grounding Gate

After clarification, search grounding behavior depends on domain context:

| Scenario | Behavior |
|---|---|
| `--domain` specified | Run Phase 0.4 search grounding automatically (domain file guides queries) |
| No `--domain`, user provided rich context | Skip search. Ask: "Want me to search for external context, or is your description sufficient?" |
| No `--domain`, vague input clarified | After clarification, ask: "I have your clarified question. Do you want me to search for domain context and prior art, or do you have specific references to share?" |

### Hard Rules for Clarification

1. **Lightness first.** If the input already contains a specific metric, a clear
   comparison/hypothesis, and a defined scope — skip the entire protocol. Say:
   "Your question is already sharp — moving to the debate."
2. **Max 2 dialogue turns** for the whole clarification phase. After 2 turns, proceed
   with whatever you have.
7. **Multi-topic discovery.** If F/D/Q decomposition reveals the input is actually
   multi-topic (multiple independent D's or Q's addressing different subjects), loop
   back to Step 0.1 (scope check) with the decomposed propositions. Tell the user:
   "Your question unpacks into N distinct analyses: [list]. Which one should we
   brainstorm first?" Do not proceed until the user picks one.
3. **Never teach the user about the framework.** Don't say "I'm applying Wittgenstein's
   proposition decomposition." Just do it. The user sees F/D/Q classification, targeted
   questions, and extraction strategies — not philosophy lectures.
4. **Never paraphrase.** Show the F/D/Q classification, don't say "what you said is..."
   and repeat everything back.
5. **Zero filler.** No "Got it," "Great question," "Let me think about that." Every
   sentence advances clarification.
6. **Polanyi is a fallback, not a mandatory step.** Don't force tacit knowledge
   extraction on users who are being perfectly clear.

---

## Part 2: SKILL.md Phase 0.5 Integration — Specification

### New Step 0.1.5 in SKILL.md

Insert after Step 0.1 (Scope Check), before Step 0.2 (Domain Knowledge Loading):

> **Step 0.1.5: Input Clarification (Wittgenstein-Socrates-Polanyi)**
>
> Follow the clarification protocol in `prompts/build_clarification.md`.
>
> **Skip condition:** If the user's input already contains: (a) a specific metric or
> measure, (b) a clear comparison or hypothesis, and (c) a defined scope — skip
> clarification and proceed to Step 0.2. Tell the user: "Your question is already
> sharp — moving to the debate."
>
> **Output:** A `clarified_statement` block that replaces the raw user input in all
> downstream phases. The original input is preserved as `original_input` for reference.
>
> **Search grounding gate:** If `--domain` is NOT specified, after clarification ask the
> user whether to run web search, accept user-provided references, or proceed without
> external context. If `--domain` IS specified, proceed to search grounding automatically.

### Evidence Block Update (Step 0.5)

Add a new section at the TOP of the evidence block (before Confluence Context):

```markdown
### Clarification Context
- **Original input:** {original_input}
- **Clarified question:** {clarified_statement}
- **Tacit preferences:** {polanyi_extractions, if any — otherwise "None extracted"}
- **Constraints surfaced:** {constraints from F/D/Q classification}
```

Personas see both original and clarified versions, allowing them to challenge the
clarification itself if they disagree with how the question was sharpened.

### Updated Phase Flow

```
Phase 0 (upgraded):
  Step 0.1:   Scope Check                    [unchanged]
  Step 0.1.5: Input Clarification            [NEW — prompts/build_clarification.md]
  Step 0.2:   Domain Knowledge Loading       [unchanged]
  Step 0.2b:  External Knowledge Directory   [unchanged]
  Step 0.3:   Stakeholder Profile Loading    [unchanged]
  Step 0.3b:  Confluence Search              [unchanged]
  Step 0.4:   Search Grounding               [CONDITIONAL — gated on domain/user choice]
  Step 0.5:   Evidence Block Assembly         [UPDATED — includes Clarification Context]
  Step 0.6:   Fallback Handling              [unchanged]
```

---

## Part 3: Phase 3 Socratic Dialogue Upgrade — Specification

### Three New Pushback Tools

Added to the orchestrator's toolkit in Phase 3. These are inline modifications to
SKILL.md, not a separate file.

#### Tool 1: Wittgenstein Response Decomposition

**When:** User response to a tension contains vague words from the lookup table.

**Lookup table access:** Re-read `prompts/build_clarification.md` Layer 1 Step 2 for
the DS-specific vague word table. The table is defined once in that file and referenced
here — do not duplicate it inline.

**Action:** Decompose the vague words before accepting the response.

**Example:**
> User: "We'll just look at the impact on relevance"
>
> Orchestrator: "Two words need unpacking before I can accept this:
> - 'impact' — on which metric? NDCG@10, session success rate, click-through?
> - 'relevance' — relevance as judged by whom? Human raters, user behavior signals, both?
>
> Pick the specific measures and I'll check them against what the Methodology Critic raised."

**Integration point:** Added as a new check at the START of Step 3.2, before verbatim
persona quote. If vague words are detected, decompose first — the persona quote follows
after the user clarifies.

#### Tool 2: Socratic Hidden Premise Detection

**When:** User makes a decision or commits to an approach in their response.

**Action:** Surface 2-3 unstated assumptions baked into that decision.

**Example:**
> User: "We'll run an A/B test for two weeks"
>
> Orchestrator: "That decision assumes three things:
> 1. Two weeks gives you enough traffic for statistical power — have you checked?
> 2. The effect is immediate (no novelty/learning curve needing a longer window)
> 3. You can hold everything else constant for two weeks (no other launches)
>
> Which of these have you verified?"

**Integration point:** Added as a check AFTER verbatim persona quote in Step 3.2. If the
user's response contains a commitment, surface the hidden premises.

#### Tool 3: Polanyi Stall Detection + Extraction (New Step 3.2.3)

**When:** User stalls on a specific concern.

**Trigger signals:**
- User says "you know what I mean", "that kind of thing", "hard to explain"
- User uses metaphor they can't unpack: "like what we did last quarter"
- User goes silent on a specific tension (addresses others, skips one)
- User keeps revising the same answer without converging

**Action:** Stop verbal questioning. Switch to extraction strategy.

**Template:**
> "Sounds like you have a feel for this but it's hard to pin down. Let me try a
> different angle:
> - Can you point me to a past analysis that got this right? I'll extract the pattern.
> - Or tell me what outcome would make this analysis useless — sometimes the negative
>   is easier to articulate."

**Integration point:** New Step 3.2.3 (after existing Step 3.2.2 Quantitative Threshold
Push). Uses the same DS-adapted extraction strategies from `prompts/build_clarification.md`.

**Dual Polanyi guard:** If Polanyi extracted preferences in Phase 0.5 (stored in the
`clarified_statement` block's "Tacit preferences" field), reference those extractions
first before re-triggering extraction in Phase 3. Say: "Earlier you showed me [example]
and I extracted [preferences]. Does that still apply here, or is this a different kind
of stall?" Only re-trigger full extraction if the Phase 0.5 preferences don't cover it.

### Updated Phase 3 Step Structure

```
Step 3.1:   Process User Response            [unchanged]
Step 3.2:   Push Back (Targeted Adversarial)
  ├── [NEW]      Wittgenstein check: scan response for vague words → decompose
  ├── [existing] Verbatim quote from persona findings
  ├── [NEW]      Socratic check: scan response for hidden premises → surface
  ├── [existing] Deflection detection
  └── [existing] Contradiction detection
Step 3.2.1: Blind Spot Escalation            [unchanged]
Step 3.2.2: Quantitative Threshold Push      [unchanged]
Step 3.2.3: Polanyi Stall Detection          [NEW]
  ├── Trigger signal detection
  ├── Strategy switch (demonstration / negation / behavioral)
  └── Max 1 Polanyi intervention per dialogue round
Step 3.3:   Re-invoke Subagent               [unchanged]
Step 3.4:   Check Termination Conditions     [unchanged]
```

### Hard Rule: One Philosophy Intervention Per Round

At most ONE philosophy-framework tool fires per pushback round. Priority order:

1. **Wittgenstein decomposition** — if vague words detected, decompose first (blocks
   everything else until resolved)
2. **Socratic hidden premise** — if user committed to an approach, surface assumptions
3. **Polanyi stall detection** — if user stalled, switch strategy

If multiple triggers fire in the same round, pick the highest-priority one. The others
can fire in subsequent rounds.

This prevents overwhelm — the orchestrator already has persona quotes, blind spots, and
threshold pushes. Adding all three philosophy tools in one round would be too much.

---

## Files Changed

| File | Change type | Description |
|------|-------------|-------------|
| `brainstorm/skill/prompts/build_clarification.md` | **NEW** | Full Wittgenstein-Socrates-Polanyi clarification protocol |
| `brainstorm/skill/SKILL.md` | **MODIFIED** | Add Step 0.1.5, make Step 0.4 conditional, update Step 0.5 evidence block, add Phase 3 tools |

## Files NOT Changed

- `prompts/build_debate_query.md` — persona dispatch is unchanged
- `prompts/build_synthesis.md` — synthesis is unchanged  
- `references/*.md` — persona definitions are unchanged
- `tests/` — new tests needed but scope TBD during implementation planning

## Testing Strategy

1. **Clarification skip test** — precise input ("Measure NDCG@10 delta between model A
   and model B on navigational queries over 2 weeks") should skip clarification entirely
2. **F/D/Q classification test** — vague input should produce correct F/D/Q breakdown
3. **Vague word detection test** — inputs containing lookup table words trigger decomposition
4. **Polanyi trigger test** — simulated stall signals trigger extraction strategies
5. **Search grounding gate test** — no `--domain` + clarified input asks user about search
6. **Phase 3 integration test** — vague user responses during Socratic loop trigger
   Wittgenstein decomposition
7. **Multi-topic discovery test** — input that appears single-topic but F/D/Q reveals
   multiple independent analyses should loop back to scope check
8. **Philosophy priority test** — input triggering both Wittgenstein and Socratic in
   Phase 3 should fire only Wittgenstein (highest priority)

## Implementation Priority (from CEO review)

**Ship order:** Phase 3 pushback tools FIRST, then Phase 0.5 clarification layer.

Phase 3 upgrades improve every session without adding friction. Phase 0.5 adds 1-2
dialogue turns that risk feeling patronizing to expert users. Implementation should:

1. Implement Phase 3 tools (Wittgenstein decomposition, hidden premise detection,
   Polanyi stall detection) — zero-friction improvement
2. Implement Phase 0.5 with aggressive skip condition — only fires on genuinely
   vague inputs
3. Make F/D/Q classification conversational, not academic — avoid "F: you launched
   a model" format for expert users

## Breaking Change Note

The conditional search grounding gate (Phase 0.4) changes behavior for users who
don't use `--domain`. Previously, web search ran automatically. Now, users without
`--domain` are asked whether they want web search. This is intentional — unsolicited
search on vague inputs produces noise. Document in CHANGELOG when shipped.

## Attribution

Framework inspired by:
- **Michael Polanyi** — *Personal Knowledge* (1958), *The Tacit Dimension* (1966)
- **riiiku/clarify-skill** — Claude Code implementation of the three-layer framework
- **Jaden (@Jaden_riku)** — Original synthesis of Wittgenstein + Socrates + Polanyi
  for AI interaction
- **cellinlab (@cellinlab)** — Deep analysis of Polanyi's tacit knowledge theory
