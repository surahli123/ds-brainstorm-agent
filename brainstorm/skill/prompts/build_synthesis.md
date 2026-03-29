# Cross-Persona Challenge Synthesis — Orchestrator Instructions

## How to Use This Template

This is **NOT dispatched to a subagent.** The SKILL.md orchestrator (you) follows these
instructions directly to synthesize the 3 persona outputs into a structured challenge
for the user. You do this in Phase 2, after all 3 subagent responses are collected.

## Variable Reference

| Variable | Source | Example |
|----------|--------|---------|
| `{ANALYSIS_QUESTION}` | The user's original analysis question, verbatim | `"I want to measure the impact of query rewriting..."` |
| `{CRITIC_OUTPUT}` | Full JSON response from Methodology Critic subagent | See persona output format |
| `{ADVOCATE_OUTPUT}` | Full JSON response from Stakeholder Advocate subagent | See persona output format |
| `{PRAGMATIST_OUTPUT}` | Full JSON response from Pragmatist subagent | See persona output format |
| `{STAKEHOLDER_NAMES}` | List of stakeholder names if `--stakeholder` was used, empty list otherwise | `["Peter Yang", "Jane Doe"]` |
| `{MISSING_PERSONAS}` | Comma-separated list of personas that failed, or empty string | `Pragmatist` or empty |

---

## Step 1: Parse the 3 Subagent Outputs

Each subagent returned a JSON block. Extract these key fields from each:

**From ALL personas:**
- `assessment` — SOUND, CONCERNS, or MAJOR_ISSUES
- `summary` — one-line assessment
- `findings[]` — array of typed, severity-tagged findings
- `next_actions[]` — what the user should address
- `domain_references[]` — domain concepts referenced

**From Stakeholder Advocate only:**
- `narrative_hook` — the 30-second pitch
- `key_metrics_for_audience` — metrics execs track
- `decision_this_enables` — what decision this analysis unlocks

**From Pragmatist only:**
- `feasibility` — HIGH, MEDIUM, or LOW
- `eighty_twenty` — the simplest valuable version
- `scope_recommendation` — what to cut or defer

If a persona is missing (listed in `{MISSING_PERSONAS}`), note it explicitly:
> "**Note:** {PERSONA_NAME} assessment was unavailable. This synthesis is based on
> {N} of 3 perspectives."

---

## Step 2: Identify Agreements

Scan all 3 persona outputs for findings where **2 or more personas raise the same concern**
(even if they frame it differently or assign different severity).

Agreements are strong signals — if the Methodology Critic AND the Pragmatist both flag
the same data quality issue, that's not a coincidence.

**Rules for agreements:**
- Must be substantively the same concern, not just surface-level similar wording
- State the agreement as a clear, actionable finding
- Note which personas agree and their severity ratings
- If all 3 agree, call it out explicitly — triple agreement is the strongest signal

**Format each agreement as:**

> **All 3 agree:** [or "Methodology Critic + Pragmatist agree:", etc.]
> [Concrete statement of the shared concern, with specific references from each persona's findings]

### Example

> **All 3 agree:** The analysis plan lacks a clear null hypothesis. The Methodology Critic
> calls this a critical gap ("no falsifiability = no rigor"), the Stakeholder Advocate warns
> it will make the findings unactionable ("if you can't say what you expected, you can't say
> what surprised you"), and the Pragmatist notes it will cause scope creep ("without a null,
> you'll keep exploring indefinitely").

---

## Step 3: Surface Tensions

This is the most important step. Scan the 3 outputs for findings where **personas
genuinely disagree** — where one persona's recommendation conflicts with another's.

**Rules for tensions:**
- Do NOT average out disagreements. If the Methodology Critic says "this needs a controlled
  experiment" and the Pragmatist says "you don't have time for that," that's a real tension.
  Present BOTH sides at full strength.
- Do NOT resolve tensions for the user. Your job is to stage the debate, not settle it.
- Every tension must end with a concrete question the user needs to answer.
- Use direct quotes from the persona outputs (or close paraphrases referencing their findings).
- Tensions should feel like a real debate between smart people who disagree.

**Format each tension as:**

> **Tension {N}: {Brief label of the trade-off}**
>
> {Persona A} says: "{Specific concern or recommendation from their findings}"
>
> But {Persona B} counters: "{Specific counter-concern from their findings}"
>
> → **Question for you:** {The trade-off the user needs to resolve, framed as a direct question}

### Example Tensions

> **Tension 1: Rigor vs. timeline**
>
> Methodology Critic says: "Your click-through comparison needs position-debiased metrics.
> Raw CTR conflates ranking position with relevance — you'd need to implement IPW estimation
> or use interleaving, which adds 2-3 weeks of instrumentation work."
>
> But Pragmatist counters: "You have a quarterly review in 4 weeks. The interleaving
> infrastructure doesn't exist yet. A paired t-test on session-level success rate gets you
> 80% of the insight in 20% of the time."
>
> → **Question for you:** Is position bias likely large enough in your data to invalidate
> raw CTR comparisons? If you've seen position 1 vs position 3 CTR differences of 3x+,
> the Critic is right — raw CTR is misleading. If differences are smaller, the Pragmatist's
> shortcut may hold.

> **Tension 2: Depth vs. stakeholder attention**
>
> Methodology Critic says: "You should segment by query intent (navigational vs. informational)
> because aggregate metrics will mask Simpson's paradox — improvements in one segment could
> hide degradation in another."
>
> But Stakeholder Advocate counters: "Your VP tracks one number: overall QSR. If you lead
> with a 4-segment breakdown, you'll lose them in slide 2. Show the top-line first, keep
> segments in the appendix."
>
> → **Question for you:** Do you suspect the treatment effect varies by query type? If yes,
> the segmentation is load-bearing and you need to find a way to present it simply. If no,
> lead with the aggregate and mention segments as a robustness check.

---

## Step 4: Incorporate Stakeholder Context

If `{STAKEHOLDER_NAMES}` is not empty (i.e., one or more stakeholder profiles were loaded):

### Single Stakeholder (1 profile loaded)

1. **Check metric alignment:** Does the Methodology Critic's recommended metrics match what
   the stakeholder actually tracks (from their profile's Layer 3: Metric Vocabulary)?
   If there's a mismatch, surface it as a tension or agreement.

2. **Check framing fit:** Does the Stakeholder Advocate's narrative hook use language
   the stakeholder would actually use? Reference the stakeholder's known preferences
   (e.g., "Peter Yang values 'actionable insights' over 'dashboards'").

3. **Check feasibility against stakeholder's decision style:** Does the Pragmatist's
   timeline estimate align with the stakeholder's known decision pace? (e.g., a
   prototype-first stakeholder might accept directional results faster than a
   rigorous-evidence stakeholder).

4. **Add a stakeholder-specific callout** after the tensions section:

> **Stakeholder lens ({STAKEHOLDER_NAME}):** Based on their profile, {NAME} is likely to
> {care most about X / push back on Y / want to see Z first}. This means Tension {N}
> is probably the one that matters most for your presentation.

### Multiple Stakeholders (2-3 profiles loaded)

Perform checks 1-3 above for EACH stakeholder independently. Then add:

5. **Surface stakeholder-stakeholder tensions.** These are a SEPARATE tension type from
   persona-persona tensions (methodology vs. feasibility). Pull these from the Stakeholder
   Advocate's `stakeholder_tensions` field if available, and augment with your own analysis
   of the profiles.

   **Format each stakeholder tension as:**

   > **Stakeholder tension: {Stakeholder A} vs. {Stakeholder B}**
   >
   > {Stakeholder A} prioritizes {X}, but {Stakeholder B} needs {Y}.
   > You'll need to frame this analysis differently for each audience.
   >
   > → **Navigation:** {Concrete recommendation for handling the tension —
   > e.g., "Present the top-line metric to A first, then the methodology deep-dive to B."}

   Present stakeholder tensions AFTER persona tensions in the "Where They Clash" section,
   under a sub-heading:

   ```
   #### Stakeholder-to-Stakeholder Tensions

   [stakeholder tensions here]
   ```

6. **Add a multi-stakeholder callout** after the tensions section:

> **Multi-stakeholder lens:** You're presenting to {N} stakeholders with different priorities.
> {Stakeholder A} is likely to {care about X}; {Stakeholder B} is likely to {care about Y}.
> {If 3: Stakeholder C is likely to {care about Z}.}
> The biggest political risk is Tension {N} — resolve that framing before presenting.

---

## Step 5: Identify the Key Question

From all the tensions surfaced, pick the **single most important one** — the tension that,
if resolved, would most change the shape of the analysis plan.

**Rules:**
- It should be a genuine dilemma, not a question with an obvious answer
- Frame it as a direct question to the user
- Explain WHY this is the key question (what hinges on the answer)

**Format:**

> **The key question you need to resolve:**
>
> {Direct question}
>
> Why this matters: {1-2 sentences on what changes depending on the answer}

---

## Step 6: Determine Priority Perspective

Based on the user's context (their analysis question, where they are in the process,
and the severity of each persona's concerns), identify which persona's concerns are
most urgent RIGHT NOW.

- If the plan has fundamental methodology flaws → Methodology Critic is priority
- If the plan is sound but won't influence anyone → Stakeholder Advocate is priority
- If the plan is sound and well-framed but can't actually be executed → Pragmatist is priority

State this as: "**Most urgent perspective:** {Persona}, because {reason}."

---

## Output Structure

Present the full synthesis to the user in this order:

```markdown
## Three-Perspective Challenge

**Your analysis question:** {ANALYSIS_QUESTION}

**Assessment summary:**
- Methodology Critic: {assessment} — "{summary}"
- Stakeholder Advocate: {assessment} — "{summary}"
- Pragmatist: {assessment} — "{summary}"

{Note about missing personas if any}

### Where They Agree

{2-3 agreements, formatted per Step 2}

### Where They Clash

{2-3 tensions, formatted per Step 3}

{Stakeholder-specific callout if applicable, per Step 4}

### The Key Question

{Key question, formatted per Step 5}

### Most Urgent Perspective

{Priority perspective, per Step 6}

---

**Your turn.** Respond to the tensions above — especially the key question.
You can address them in any order. I'll push back on whatever you leave unaddressed.
```

---

## Anti-Patterns to Avoid

1. **Consensus mush.** "All three personas generally agree the plan has merit but suggest
   some improvements." This is useless. Find the disagreements.

2. **Severity averaging.** If the Methodology Critic flags a critical issue and the Pragmatist
   says it's minor, do NOT split the difference and call it "major." Present both severity
   ratings and let the user decide.

3. **Parroting without synthesis.** Don't just list Persona A said X, Persona B said Y,
   Persona C said Z. The value is in the CONNECTIONS — where they agree, where they clash,
   what the user needs to resolve.

4. **Resolving tensions yourself.** You are staging a debate, not settling one. The user is
   the product owner — they make the call.

5. **Ignoring stakeholder context.** If stakeholder profiles were loaded, the user explicitly
   asked for stakeholder-aware brainstorming. Don't treat it as optional decoration — weave
   it into the tensions and recommendations. When multiple stakeholders are loaded, surface
   stakeholder-to-stakeholder tensions as a distinct category — don't collapse them into
   persona tensions or ignore the political navigation required.

6. **Generic questions.** "How will you handle data quality?" is generic. "Your plan assumes
   clean click logs, but the Pragmatist flagged that bot traffic makes up 15% of clicks in
   your domain — have you verified your deduplication pipeline catches this?" is specific.
