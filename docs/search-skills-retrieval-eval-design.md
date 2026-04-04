# Search Skills Retrieval Quality Eval — Design Decisions

**Date:** 2026-04-03
**Status:** Design phase (brainstorm complete, implementation not started)
**Related:** [Search Skills Eval Framework](search-skills-eval-framework.md) (broader context)
**Brainstorm method:** 4-persona ds-brainstorm with `--domain search-relevance`

---

## 1. Scope

**In scope:** Measuring whether the Search Skill returns the right documents when an AI
agent (not a human) issues the queries.

**Out of scope (v2):**
- Task-level success attribution (is search the bottleneck on agent task success?)
- Query generation quality (did the agent ask the right question?)
- End-to-end agent evaluation

**Why narrow:** The 4-persona brainstorm surfaced that "evaluating Search Skills in
agentic search" is actually 2-3 bundled problems — retrieval quality, query generation
quality, and task-level attribution — each requiring different data, metrics, and
infrastructure. All four personas flagged scope as a concern. Retrieval quality is the
foundation layer: you can't attribute task outcomes to retrieval until you can measure
retrieval independently.

---

## 2. Design Decisions

### 2.1 Relevance Definition: Level 1 (Query-Intent)

**Decision:** Define relevance as "is this document about what the query asked for?"
(standard IR definition).

**Known gap:** Level 1 misses agentic-specific failures where a document is topically
relevant but useless to the agent (right topic, wrong granularity, wrong aspect). A
Level 2 definition ("does this document help the agent complete its current reasoning
step?") would catch these but requires instrumenting task context into every eval.

**Upgrade path:** Ship Level 1 as v1 baseline. Design instrumentation now so Level 2
is achievable when the pipeline is proven. The construct validity gap between Level 1
and Level 2 is the primary known limitation of this eval.

**Query confound (accepted):** At Level 1, a bad agent query that retrieves nothing
relevant scores Precision@k=0 — but the fault is the query, not retrieval. This is
accepted by design: Level 1 evaluates the retrieval stack's response to whatever query
it receives, same as TREC. Query generation quality is a separate eval (out of scope).

**Relevance levels reference:**

| Level | Definition | Judge needs | Catches |
|-------|-----------|-------------|---------|
| 1 (chosen) | Query-intent: about what the query asked | Query + document | Topical misses |
| 2 (future) | Task-goal: helps complete the agent's task | Query + document + task context | Granularity/aspect misses |
| 3 (aspirational) | Step-level: contains info for current reasoning step | Query + document + task + agent plan | All retrieval failures |

### 2.2 Extractability: Separate Dimension

**Decision:** Measure answer extractability independently from retrieval quality.

**Rationale:** Retrieving the right document is necessary but not sufficient. If the
answer is in a table, PDF, or structured schema the LLM can't parse, retrieval
"succeeded" but the task fails. These are different failure modes requiring different
fixes (retrieval quality = ranking/recall improvements; extractability = parsing/chunking
improvements).

**Implication:** The eval produces two scores per query, not one:
1. Retrieval quality (Precision@k / Recall@k)
2. Extractability (can the LLM consumer actually use what's in the retrieved docs?)

**Extractability metric: Extraction Success Rate (ESR).**
For each retrieved document scored as relevant (UMBRELLA >= 2), a second judge pass
evaluates whether the answer is actually extractable by the LLM consumer:

| Score | Label | Definition |
|-------|-------|-----------|
| 0 | Unextractable | Answer exists but is locked in a format the LLM cannot parse (scanned PDF, image, complex nested table, binary attachment) |
| 1 | Partially extractable | Answer is present but requires multi-hop reasoning across document sections, or is embedded in noisy context that degrades extraction reliability |
| 2 | Fully extractable | Answer is in plain text, simple table, or structured field that an LLM can reliably extract in a single pass |

**ESR formula:** `count(score >= 1) / count(relevant docs)` — the fraction of relevant
documents from which the LLM can extract usable information.

**Judge approach:** Same UMBRELLA-style pointwise judge, separate prompt. Input: query +
document + target answer location. The judge assesses format parseability, not topical
relevance (that's already scored in the retrieval quality pass).

**Key failure modes this catches:**
- Confluence pages with answers inside attached spreadsheets
- Jira tickets where the answer is in a comment thread image
- PDF documents with tabular data that OCR/parsing degrades
- Structured schemas (JSON, YAML) where the answer requires key traversal

**Instrumentation:** Log `doc_format` (text/html/pdf/spreadsheet/image/structured) per
retrieved document. This enables decomposition: ESR by format type reveals which
content types are extraction bottlenecks.

### 2.3 Metrics: Precision@k and Recall@k (NDCG Retired)

**Decision:** Use set-based metrics. Do not use NDCG or MRR for this eval.

**Rationale (unanimous across all 4 personas):** NDCG's positional discount
(`1/log2(rank+1)`) models a human scanning a ranked list top-to-bottom. An LLM
consuming retrieved documents does not exhibit positional attention decay — it reads
all results within its context window. Applying positional discounting to LLM-consumed
results measures a phenomenon that doesn't exist.

**k selection:** Test at k=8 and k=20 until agent result consumption is instrumented.
Once we know how many results the agent actually reads per Search Skill call, that
number becomes k. See Section 4.2 for connection to PM's QSR discount function work.

### 2.4 Distribution Characterization: Eval-First (No BEIR/MTEB Prerequisite)

**Decision:** Do not require BEIR/MTEB benchmarking before building the eval. Let the
eval surface distribution gaps organically.

**Tradeoff documented:**

| | Benchmark first (BEIR/MTEB) | Build eval, let it surface the gap |
|---|---|---|
| **Pro** | Know if retrieval stack is fundamentally miscalibrated before investing in eval infra | Ship faster; eval becomes the diagnostic tool |
| **Con** | 1-2 day detour; results may be inconclusive if agent queries don't map to BEIR tasks | Risk building a judge that scores retrieval as "fine" while BM25 distribution mismatch silently degrades recall |
| **Mitigation** | — | Tag queries by source (human vs agent) from day one; systematic score gap between the two IS the distribution signal |

**Critical mitigation:** Every eval query must be tagged with `source=human|agent`. If
Precision@k for agent queries is systematically lower than for human queries on the same
retrieval stack, that gap is the distribution shift — discovered through the eval instead
of through BEIR.

### 2.5 Judge Framework: Adapted UMBRELLA

**Decision:** Use UMBRELLA-style pointwise LLM-as-Judge, adapted for agent queries.

**Requirement before deployment:** Re-measure inter-annotator agreement on 50-100
agent-generated query-document pairs. The existing 73.3% human agreement was validated
on WANDS (e-commerce, human-issued keyword queries). Agent-generated queries are
structurally different — longer, multi-constraint, domain-specific. Agreement rates
do not transfer across query distributions without re-validation.

**Acceptance threshold: IAA >= 65%.** This allows ~10pp degradation from UMBRELLA's
73.3% on WANDS to account for the distribution shift to agent queries. Below 65%,
judge variance is too high for reliable Precision@k scores or keep/revert decisions.
If recalibration falls below 65%, the judge prompt needs rework before the eval is
usable.

**Judge prompt adaptation:** For Level 1, the judge scores relevance given only query +
document (no task context). The prompt must be explicit that "relevant" means "contains
information responsive to what this query is asking for" — not "related to the same
broad topic."

### 2.6 Baseline Comparison: Agent vs Human Queries

**Decision:** Primary baseline is comparing Precision@k for agent-generated queries vs
human-issued queries on the same retrieval stack.

**Why this baseline:** The score gap between agent and human queries IS the distribution
shift signal. If agent queries score significantly lower, the retrieval stack is
miscalibrated for the agent distribution (likely BM25 lexical/semantic balance). If
scores are comparable, the retrieval stack generalizes and the eval can focus on judge
quality and extractability.

**Implementation:** Requires the `source=human|agent` tag on every eval query (already
in instrumentation plan, Section 5 Step 1). No additional infrastructure needed.

**Future baseline (v2):** Before/after regression detection for Search Skill changes.
This becomes the CI gate once the eval is stable.

---

## 3. Open Questions

| Question | Depends on | Impact if wrong |
|----------|-----------|-----------------|
| What is k? (8 or 20?) | Agent instrumentation — how many results does the agent read per call | Precision@k measured at wrong cutoff misrepresents retrieval quality |
| Does UMBRELLA agreement hold on agent queries? | 50-100 sample recalibration | If agreement drops below ~65%, judge signal is too noisy for keep/revert decisions |
| Is BM25 recall degraded on agent queries? | Query source tagging in eval | If yes, L1 lexical/semantic balance needs retuning — a retrieval stack fix, not an eval fix |
| ~~What's the baseline comparison?~~ | ~~Null hypothesis definition~~ | **Resolved:** Agent vs human queries on same retrieval stack (see 2.6) |

---

## 4. Connections to Existing Work

### 4.1 QSR / DLCTR Decomposition

The existing search metrics stack (QSR, DLCTR, AI Trigger Rate, AI Success Rate) was
designed for human-initiated search. This eval complements — not replaces — that stack
by covering the agent-initiated query distribution that QSR doesn't capture.

### 4.2 PM's QSR Discount Function Revision

The PM lead is independently revisiting the QSR positional discount function. This eval
work feeds directly into that decision:

- **This eval's k measurement** (how many results does the agent consume?) informs
  whether the discount function should apply at all for agent queries
- **If the agent reads all k results equally**, the discount function should be flat
  (no positional decay) for the agent cohort — same conclusion this eval reached for
  choosing Precision@k over NDCG
- **Recommendation:** Instrument agent result consumption once, use the data for both
  the eval k selection AND the discount function revision. Same data, two decisions.

### 4.3 UMBRELLA Framework

The existing UMBRELLA framework (pointwise 0-3 scale) provides the judge architecture.
This eval reuses the approach but requires recalibration on agent query distribution.
Any recalibration findings should be shared with the broader UMBRELLA team — they apply
to AI Search (SAIN) evaluation as well.

---

## 5. Next Steps (Priority Order)

1. **Instrument agent query logs** — capture per Search Skill call:
   - `query` (the agent-generated query string)
   - `source` tag (`agent` vs `human`)
   - `retrieved_doc_ids` (ordered list)
   - `task_context` (store now for Level 2 upgrade, even if Level 1 doesn't use it)

2. **Measure agent result consumption** — how many results does the agent actually read
   per call? This sets k for Precision@k AND informs PM's discount function revision.

3. **Adapt UMBRELLA judge prompt** for Level 1 on agent queries:
   - Score: 0-3 relevance given query + document only
   - Run on 50-100 sampled agent sessions
   - Measure judge variance and inter-annotator agreement before trusting scores
   - **Acceptance threshold: IAA >= 65%.** Below this, rework the judge prompt.

4. **Tag all eval queries by source** (human vs agent) from day one — this is the free
   distribution diagnostic AND the primary baseline (see Section 2.6).

5. **Build extractability judge** — second-pass judge on relevant docs (UMBRELLA >= 2):
   - Score 0-2 on format parseability (see Section 2.2 for rubric)
   - Log `doc_format` per retrieved document for decomposition by content type
   - Compute Extraction Success Rate (ESR) per query

6. **Connect to PM's discount function work** — present k measurement as shared
   instrumentation that serves both the eval and QSR revision.

---

## Appendix: Brainstorm Provenance

**Personas used:** Methodology Critic, Stakeholder Advocate, Pragmatist, Domain Expert
(`--domain search-relevance`)

**Unanimous assessment:** MAJOR_ISSUES on the broad question ("how to evaluate Search
Skills in agentic search"). Narrowing to retrieval quality resolved the scope concern.

**Domain Expert validation:** All 7 challenge patterns from `search-relevance.md` §9
fired. Key domain-specific insights not raised by other personas:
- BEIR/MTEB benchmarking as starting point
- Retrieval quality vs answer extractability distinction
- Information need model (user-defined vs plan-defined relevance)
- BM25 lexical/semantic balance for agent queries
- NDCG positional discount as invalid assumption transfer
