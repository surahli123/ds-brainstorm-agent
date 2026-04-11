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
