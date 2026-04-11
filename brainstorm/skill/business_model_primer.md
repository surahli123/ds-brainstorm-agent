# Business Model Primer Step

## When This Runs

Before any brainstorm begins — this is a pre-Phase 1 step that runs after scope check (Step 0.1)
but before search grounding and persona dispatch.

## Purpose

Analyses default to optimizing the free side of a marketplace when the business model is not
explicitly loaded. This step forces the business model context to be surface-level explicit so
the Stakeholder Advocate can enforce correct metric framing throughout the debate.

Without this step: metrics like Login Rate, Application Rate, and DAU are treated as
first-class outcomes even when the paying party (employers, advertisers, subscribers) is
entirely unaffected by them.

---

## Step: Load or Generate Business Model Primer

### Input Sources (in priority order)

1. **Stakeholder profile** (if `--stakeholder` was specified): extract revenue model, key metric,
   and decision frame from the profile if present.
2. **Domain knowledge** (if `--domain` was specified): extract any marketplace structure,
   revenue model, or paying-party description.
3. **Search grounding** (Step 0.2 evidence block): extract any relevant company/market context.
4. **User-provided context**: if the user's analysis description mentions revenue model,
   paying customers, or business objectives, extract those explicitly.
5. **Generated primer**: if none of the above sources provide sufficient context, generate
   the 5-bullet primer from available evidence and flag it as inferred (not confirmed).

### The 5-Bullet Primer

Produce this doc — either loaded from sources or generated — before dispatching personas:

```
BUSINESS MODEL PRIMER
─────────────────────
1. Revenue model: Who pays? (employers / advertisers / subscribers / marketplace fees / SaaS / usage-based)
   → [answer]

2. Key metric: What drives renewal/retention for the paying party?
   → [answer — e.g., "employer time-to-hire", "advertiser ROAS", "subscriber task completion rate"]

3. Stakeholder: Who decides based on this analysis?
   → [name/role + what they will do with the output]

4. Decision frame: What options does the stakeholder have?
   → [scale / hold / cut / kill / redesign / redirect budget]

5. Known context: Any published research, prior analyses, or industry benchmarks?
   → [sources if available; "none found" if not]
```

### Confidence Flag

If the primer was generated (not loaded from confirmed sources), prepend:

> **INFERRED PRIMER — not confirmed from stakeholder profile or domain knowledge.**
> Verify before treating these as ground truth.

---

## How Personas Use the Primer

### Stakeholder Advocate (mandatory enforcement)

The Stakeholder Advocate MUST load the primer and enforce:

- Every metric in the analysis must either connect to the paying party's key metric,
  or the analysis must explicitly justify why a free-side metric is the right proxy.
- If the analysis measures only free-side metrics (e.g., student engagement on a
  two-sided employer/student marketplace), this is a **MAJOR** finding: the analysis
  cannot drive the decisions that matter to the revenue-generating party.
- The "so what" statement must be answerable in terms of the paying party's decision frame.

### Methodology Critic (secondary use)

Use the primer to check whether the causal model is estimating the right outcome:
- Is the treatment designed to affect the paying party, the free party, or both?
- Is there a plausible mechanism from the measured metric to the revenue metric?

### Pragmatist (secondary use)

Use the primer to scope the data requirements:
- Does the analysis require data from the paying party's system (e.g., employer CRM,
  advertiser dashboard, subscriber activity logs)?
- Is that data available, or is the analysis limited to free-side signals?

---

## Output

Deliver the primer to the user before Phase 1 dispatch:

```
Before we brainstorm, here's the business model context I'm working from:

[5-bullet primer]

[INFERRED PRIMER flag if applicable]

Does this look right? Any corrections before I bring in the personas?
```

Wait for the user to confirm or correct. If the user corrects the primer, update it and
proceed. If the user says "looks right" or equivalent, proceed with the confirmed primer.

---

## Integration Note

The confirmed primer is passed to all personas as part of the evidence block (Phase 0.4).
The Stakeholder Advocate's MANDATORY FIRST ACTIONS are expanded to include:

> "Load the Business Model Primer. Identify which metrics in the analysis connect to the
> paying party's key metric. If none do, this is a MAJOR finding — flag it immediately
> before proceeding to framing recommendations."
