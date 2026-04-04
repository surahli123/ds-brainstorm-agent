# Evaluation Framework: Search Skills in Agentic Search

**Date:** 2026-04-03
**Status:** Brainstorm output — ready for engineering review
**Author:** DS (brainstorm with 3-persona Socratic challenge)
**Context:** Baidu "Agentic Search" (CCIR 2026), SMA knowledge files, web research

---

## 1. Problem Statement

Search Skills are the search functions a Master Agent calls as tools within Agentic Search. Unlike traditional search (user types query → scans SERP → clicks), in agentic search:

- The **agent** generates queries, not the human
- A single user task triggers **multiple skill calls** with reformulated queries
- The agent **self-corrects** on failures (retry with different query)
- The agent **trusts retrieved results** and synthesizes answers — no human quality filter

Traditional search metrics (NDCG, DLCTR, click-through) don't transfer directly. We need a purpose-built evaluation framework.

---

## 2. Evaluation Architecture: Two Layers

### Layer 1: Task-Level (headline metric)

**"Did the user's task get completed?"**

| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| **Task Success Rate** | Binary: did the final answer satisfy the user's intent? | Headline metric for VP/stakeholder. Maps to Baidu's Outcome Reward (ORM). |
| **Answer Adoption Rate** | Did the user act on the output? | Behavioral signal replacing click quality. Maps to Baidu's "material adoption rate." |
| **Skill Call Efficiency** | How many skill calls per completed task? | Proxy for planning quality + skill reliability. >5 calls for a simple task = noisy skills. |
| **Task Latency** | Wall-clock time from user request to final answer | Skill latency compounds across multi-call trajectories (3s × 5 calls = 15s). |

### Layer 2: Skill-Level (diagnostic metric)

**"Why did the task succeed or fail, and which skill call is responsible?"**

Requires **skill-level trace logs** with: query input, results returned, agent accept/reject/retry signal, trace ID linking calls within a task.

| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| **Recall@k** | Does the skill retrieve the target documents? | Core retrieval quality — did we find it? |
| **Zero-Result Rate** | % of skill calls returning no results | Triggers agent retry; high rate = retrieval coverage gap |
| **Signal-to-Noise Ratio** | % of returned results the agent actually uses | Low ratio = context budget waste, per Baidu's token compression concern |
| **Trust Failure Rate** | % of calls returning plausible-but-wrong/stale results the agent accepts | The silent killer unique to agentic search (see Section 4) |
| **Retry Rate** | % of skill calls that required reformulation | High retry rate = skill doesn't understand agent-style queries |
| **Per-Connector Success** | Retrieval quality segmented by connector type | 50+ connectors with different schemas; failures concentrate in specific connectors |

---

## 3. Three Failure Classes

| Failure Class | What Goes Wrong | Metric | Detection Method | Severity |
|---|---|---|---|---|
| **Recall failure** | Skill doesn't find the document at all | Recall@k, Zero-Result Rate | Gold set of "must-find" docs per test query | HIGH — task fails visibly |
| **Precision failure** | Skill returns noise that wastes agent context | Signal-to-Noise Ratio | Compare returned results vs agent-used results in traces | MEDIUM — task may still succeed but slower |
| **Trust failure** | Skill returns plausible-but-wrong/stale results that agent accepts | Trust Failure Rate | Adversarial test set with wrong/stale docs alongside correct ones | CRITICAL — task "succeeds" with wrong answer, no signal |

### Why trust failures are the most dangerous

In traditional search, bad results are visible — the user sees them and reformulates. In agentic search, the agent trusts retrieved results and proceeds. A stale document, a wrong version, or an outdated policy retrieved confidently produces a polished, wrong answer.

Analogy from SMA knowledge: `corrections.yaml` documents a CQ drop blamed on ranking regression that was actually mix-shift. The system confidently returned a wrong diagnosis. Same pattern applies here.

---

## 4. v1 Scope (Start Here)

**Goal:** Baseline retrieval quality for Search Skills with early trust-failure signal.

**Timeline:** 4 weeks

**Test set:**
- 50 test tasks across top 5 connectors (by task volume)
- 10-15 adversarial "trust cases" with stale/wrong docs alongside correct ones
- Stratify by: connector type, query complexity (single-hop vs multi-hop), intent type

**Metrics (v1 only):**
1. **Recall@k** per skill call — can the skill find the right documents?
2. **Zero-Result Rate** per skill call — how often does the skill fail completely?
3. **Trust Failure Rate** on adversarial set — does the skill surface the right version?
4. **Task Success Rate** — end-to-end binary (LLM-as-judge on final answer)

**Judging method:**
- Task Success: LLM-as-judge (repurpose existing UMBRELLA infrastructure with task-level prompts)
- Recall: gold set comparison (human-curated "must-find" docs)
- Trust cases: binary correct/incorrect on adversarial pairs

**Infrastructure prerequisite:**
- [ ] Confirm skill-level trace logs exist (query, results, accept/reject, trace ID)
- [ ] If not: instrument traces BEFORE designing metrics

**What v1 does NOT include:**
- Per-skill attribution in multi-call chains (Phase 2)
- PRM/trajectory scoring (Phase 3)
- Ranking quality within skill results (engineers confirmed: irrelevant at this stage)

---

## 5. Future Phases (Documented Options)

### Phase 2: Skill-Level Attribution (Quarter 2)

**Trigger:** v1 reveals systemic failures worth diagnosing at the per-call level.

| Component | Description | Complexity |
|-----------|-------------|------------|
| **Query quality scoring** | Rate agent-generated queries independently from results. Separates "skill returned bad results" from "agent asked a bad query." | Medium — needs query quality rubric |
| **Per-call UMBRELLA** | Run UMBRELLA pointwise on each skill call's results. Requires re-validating 73.3% agreement rate on agent-generated queries (may not transfer from WANDS). | Medium — revalidation study needed |
| **Retry analysis** | When agent reformulates, compare quality of call N vs call N+1. Measures self-correction effectiveness. | Low — trace log analysis only |
| **Signal-to-noise tracking** | Log which returned results the agent actually uses vs ignores. Build efficiency metric. | Low — trace enrichment |
| **Connector-level decomposition** | Segment all metrics by connector type. Expect failure concentration in specific connectors. | Low — slicing existing metrics |

### Phase 3: Trajectory-Level Evaluation (Quarter 3+)

**Trigger:** Need to optimize multi-call planning, not just individual call quality.

| Component | Description | Complexity |
|-----------|-------------|------------|
| **Process Reward Model (PRM)** | Score each step in the agent's trajectory independently. Per Baidu's CCIR 2026 design. Requires trajectory-level training data. | HIGH — research project |
| **Outcome Reward Model (ORM)** | Score final task outcome. Combined with PRM via GRPO training. | HIGH — requires PRM first |
| **Multi-agent listwise inspection** | Multiple LLM judges evaluate the full trajectory (Baidu's labeling approach). | Medium — prompt engineering + infrastructure |
| **Trajectory efficiency optimization** | Minimize skill calls while maintaining task success. Measures planning quality. | Medium — requires trajectory baseline |

### Phase 4: Production Monitoring (Ongoing)

| Component | Description | Complexity |
|-----------|-------------|------------|
| **Task Success Rate dashboard** | Real-time monitoring segmented by: intent type, connector, tenant tier, agent version | Medium — instrumentation + dashboard |
| **Anomaly detection on retry rate** | Spike in retry rate = skill degradation or query distribution shift | Low — statistical process control |
| **Trust failure sampling** | Periodic random sampling of agent-accepted results for human spot-check | Low — sampling pipeline |
| **Freshness/provenance metadata** | Skills return document timestamps + source authority. Agent filters stale results pre-synthesis. | Medium — skill API change |
| **Multi-skill verification** | For high-stakes queries, agent calls skill 2x with different formulations and cross-checks. Contradictions → human review. | HIGH — doubles cost for flagged queries |
| **A/B testing framework** | Interleaving or user-level randomization for skill versions. Standard but needs agentic-specific design (randomize at task level, not query level). | Medium — experiment platform extension |

### Phase 5: Closed-Loop Improvement (Future)

| Component | Description | Complexity |
|-----------|-------------|------------|
| **Adversarial test set expansion** | Continuously add trust-failure cases from production incidents | Low — ongoing curation |
| **Skill SOP evolution** | Per Baidu: successful task paths crystallize into system SOPs. Skills self-improve via user feedback. | HIGH — requires feedback loop infrastructure |
| **Agent-generated query characterization** | Measure KL-divergence between agent query distribution and traditional query distribution. Track drift over time. | Medium — distributional analysis |
| **Cross-model judge calibration** | If switching judge models, re-validate agreement rates. Judge drift ≠ quality change. | Medium — calibration study |

---

## 6. Key Design Decisions & Rationale

| Decision | Choice | Rationale | Alternative Considered |
|----------|--------|-----------|----------------------|
| Start with retrieval, not ranking | Recall@k over NDCG | Engineers confirmed ranking is irrelevant — agent handles result selection. Retrieval coverage is the bottleneck. | NDCG per skill call (deferred: no positional discount needed when agent scans all results) |
| Task-level success as headline metric | Task Success Rate (binary) | VP needs one number. "Did the job get done?" is the agentic equivalent of QSR. | Composite score (rejected: too opaque for stakeholders) |
| Include trust failures in v1 | 10-15 adversarial test cases | Small investment, catches the most dangerous failure class unique to agentic search. Silent failures compound. | Defer to Phase 2 (rejected: too risky to launch without any trust signal) |
| LLM-as-judge for task success | Repurpose UMBRELLA infra | Existing infrastructure. Binary task success is easier to judge than graded relevance — expect higher agreement rate. | Human labeling (too slow for v1 iteration speed) |
| Don't port NDCG directly | — | NDCG assumes positional discounting on a single ranked list. Agentic skills may return unranked sets or be called 3x with different queries. Positional discount is meaningless. | Adapted NDCG (rejected: adds complexity without signal) |
| Don't build PRM in v1 | — | PRM+ORM (Baidu) is a research project requiring trajectory-level training data. Ship task-success-rate first. | Full trajectory scoring (deferred to Phase 3) |
| Segment by connector from day one | Top 5 connectors in v1 | Failures concentrate in specific connectors (different schemas, freshness, failure modes). Aggregate metrics hide this. | All 50+ connectors (rejected: scope creep) |

---

## 7. Open Questions (Needs Engineering Input)

1. **Trace log format:** What fields are available per skill call? Minimum: query, results, accept/reject, trace_id, timestamp, connector_type.
2. **Gold set construction:** Who curates the "must-find" documents for recall evaluation? DS + domain experts? Automated from click logs?
3. **Adversarial test set:** How to construct plausible-but-wrong documents? Options: historical versions of updated docs, cross-connector duplicates with conflicting info.
4. **Judge model selection:** Which LLM judges task success? Must be different from the Master Agent model (cross-model independence — per CLAUDE.md anti-pattern).
5. **Refresh cadence:** How often do we re-run the eval? After every skill code change? Weekly? On-demand?

---

## 8. References

- Baidu Search Science, "Agentic Search in Baidu" (CCIR 2026) — 3-stage evolution, PRM+ORM reward, skill SOPs, multi-agent labeling
- SMA Knowledge Files: metric_definitions.yaml, evaluation_methods.yaml, search_pipeline_knowledge.yaml, corrections.yaml
- [Agentic Search Benchmark 2026](https://aimultiple.com/agentic-search) — 8 APIs, Agent Score metric
- [Evaluating LLM Agents Survey](https://arxiv.org/html/2507.21504v1) — two-dimensional taxonomy of agent evaluation
- [ABC: Agentic Benchmark Checklist](https://arxiv.org/pdf/2507.02825) — task setup issues cause 100% over/underestimation
- [MCPVerse](https://arxiv.org/html/2508.16260v1) — 550+ real tools, outcome-based evaluation
- [Gartner 2026](https://www.gartner.com/en/newsroom/press-releases/2025-08-26-gartner-predicts-40-percent-of-enterprise-apps-will-feature-task-specific-ai-agents-by-2026-up-from-less-than-5-percent-in-2025) — 40% enterprise apps will feature AI agents by 2026
