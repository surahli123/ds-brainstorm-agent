# Domain Knowledge: Search Relevance (Enterprise Search)

*Consolidated from: Rovo Search architecture blog, Search Metric Analyzer knowledge base*
*Last updated: 2026-03-23*
*Scope: Atlassian Rovo enterprise search — metrics, evaluation, architecture, failure modes*

---

## 1. Metric Definitions

### North Star: Query Success Rate (QSR)
- **Formula:** `max(click_quality, ai_trigger * ai_success)`
- **What it measures:** Whether the user's need was fulfilled — either by clicking a good result OR getting a satisfying AI answer
- **Baseline:** mean 0.378, weekly std 0.012
- **Alert thresholds:** P0 >4%, P1 1.5-4%, P2 0.5-1.5%
- **Key insight:** QSR is a composite. It can improve from better AI answers while click quality worsens. Decompose before celebrating or panicking.

### Click Quality: Discounted Long Click-Through Rate (DLCTR)
- **Formula:** `sum(long_clicks * log2_discount(rank)) / impressions`
- **What it measures:** Whether users find and engage with results, weighted by position
- **"Long click":** User clicks a link and finds the landing page useful (sufficient dwell time or post-click actions)
- **Baseline:** mean 0.280, weekly std 0.015
- **Baselines by segment:**
  - AI-on tenants: 0.220 (lower is EXPECTED — users get AI answers without clicking)
  - AI-off tenants: 0.310
  - Enterprise tier: 0.295 (more connectors = richer index = better results)
  - Standard tier: 0.245 (fewer connectors, sparser index)
- **Alert thresholds:** P0 >5%, P1 2-5%, P2 0.5-2%

### AI Answer Metrics
- **AI Trigger Rate:** `queries_with_ai_answer / total_queries` — baseline 0.220
  - A drop = system showing fewer AI answers (detection problem)
- **AI Success Rate:** `ai_answers_satisfying / ai_answers_triggered` — baseline 0.620
  - A drop = AI answers getting worse (quality problem), not fewer shown

### Decomposition Dimensions (slice these first)
- `tenant_tier` (standard / premium / enterprise)
- `ai_enablement` (ai_on / ai_off) — ALWAYS segment by this
- `connector_type` (confluence / slack / gdrive / jira / sharepoint)
- `product_source` (which Atlassian product the result came from)
- `query_type` (navigational / informational / action)
- `position_bucket` (1 / 2 / 3-5 / 6-10 / 10+)

---

## 2. Co-Movement Diagnostic Patterns

These patterns narrow the hypothesis space BEFORE any deep investigation:

| Click Quality | QSR | AI Trigger | AI Success | Likely Cause |
|--------------|-----|------------|------------|-------------|
| down | down | stable | stable | **Ranking regression** — check model, experiments |
| down | stable/up | up | up | **AI answers working** — cannibalization is POSITIVE |
| down | down | down | down | **Broad degradation** — model, experiment, or infra |
| down | down | stable | down | **AI answer quality regression** — AI model issue |
| down | stable | stable | stable | **Click behavior change** — UX changes, mix-shift |
| stable | down | down | stable | **AI trigger regression** — detection threshold issue |
| stable | down | stable | down | **AI answer quality issue** — answers surfacing but wrong |
| down | down | down | stable/down | **Query understanding regression** — L0 misclassifying |
| stable | stable | stable | stable | **Normal fluctuation** — no action needed |

**Critical anti-pattern:** Click Quality down + AI Trigger up = SUCCESS, not failure. Users get answers without clicking. Always segment by `ai_enablement` before diagnosing.

---

## 3. Search Architecture (8-Stage Pipeline)

```
User Query → Query Understanding (L0) → Retrieval (L1) → Reranking (L2)
  → Interleaving (L3) → Permission Filtering → AI Search (SAIN) → Presentation
```

### L0: Query Intelligence
- Intent classification, spell correction, acronym resolution, query reformulation
- Uses pre-trained language models + self-hosted LLMs
- **Failure mode:** Misclassification cascades — affects ALL downstream metrics because queries are misunderstood before reaching retrieval

### L1: OpenSearch Retriever
- BM25 (lexical) + KNN (semantic) matching with permission verification
- Fine-tuned Gradient Boosted Decision Tree rescoring (popularity + contributor signals)
- **Multi-stack:** Separate document, messaging, and default search stacks for different content types

### L2: Semantic & Behavioral Ranker
- AWS SageMaker-hosted reranking with fine-tuned cross-encoder (semantic relevance)
- Deep & Cross Network (DCN) for behavioral signals
- Outputs MULTIPLE scores (semantic relevance, predicted CTR) combined via optimization layer
- **Key implication:** Changing primary offline metric means potentially retuning this optimization layer

### L3: Interleaver
- Merges results from multiple products using product affinity + semantic relevance
- **Failure mode:** Interleaving policy shifts can move click depth without any single-stage fault

### AI Search (SAIN)
- Answer-generation layer on top of retrieval/ranking outputs
- Synthesizes evidence into direct answer experiences
- **Key implication:** SAIN can shift user behavior independently of ranking quality — metric movement may come from SAIN, not from ranking changes

### Multi-Connector Strategy
- **Full Ingestion:** Google Drive, Slack content fully indexed
- **Linked Content:** Figma content ingested when referenced in Confluence/Jira
- **Federated:** Gmail, Outlook via third-party APIs
- **50+ connectors** — each with different schema, freshness, and failure modes

### Personalization
- User-created content ranked higher in personal searches
- Content from collaborators elevated
- Freshness boosted (penalizing older results) with product-specific time scales
- Authority via container type, content length, contributor count

---

## 4. Evaluation Methodology

### Offline Metrics (all currently computed)
- **Recall@k:** Percentage of queries returning expected document in top k
- **NDCG:** Normalized Discounted Cumulative Gain — graded relevance, full ranking quality
- **MRR:** Mean Reciprocal Rank — first relevant result position only
- **LLM-as-a-Judge:** LLM evaluates whether ranking was good, simulating human assessment

### LLM-as-Judge: UMBRELLA Framework
- **Pointwise approach:** Each query-document pair gets independent relevance grade (0-3)
- **Accuracy:** 73.3% agreement with human labelers (GPT-4.1, WANDS dataset)
- **Weakness:** ~27% disagreement; noisy grading; conservative bias (underrates borderline results)
- **Strength:** Produces reusable numeric grades directly usable for NDCG/MRR computation

### LLM-as-Judge: Pairwise Preference
- **Approach:** Compare two results, choose more relevant. Simpler binary decision.
- **Double-check:** Swap LHS/RHS and only trust when both orderings agree
- **Combined precision:** 90.8% via decision tree over individual attribute judges
- **Strength:** Cheaper model suffices (gpt-4.1-mini), built-in position bias detection
- **Weakness:** O(n^2) comparisons needed; cannot directly compute NDCG without Elo conversion

### Measurement Pitfalls (things that fool you)

**Unlabeled ≠ Irrelevant:** New (unlabeled) results have no labels, not bad labels. NDCG computed with unlabeled=0 will show a DROP when a ranking improvement surfaces previously-unseen relevant content. Check unlabeled rate before diagnosing a metric drop.

**Judge Calibration Drift:** LLM judges drift across model versions and prompt changes. A/B test metrics with LLM-judge labels may reflect judge drift, not real quality change. Maintain a golden set and re-judge after any judge change.

**Conservative Judge Bias:** LLM judges are stricter than human labelers on borderline cases. NDCG from judge labels will be systematically lower than from human labels — a persistent negative offset.

**Position Bias:** In pairwise evaluation, LLMs may prefer whichever option is first/second. Coverage rates of 0.75-0.89 mean 11-25% of judgments are position-sensitive. Always use swap-based double-check.

---

## 5. Failure Taxonomy

| Failure Class | Pipeline Stage | Metric Signature | Fast Check |
|--------------|----------------|-----------------|------------|
| Query rewrite drift | L0 Query Understanding | QSR down on long-tail queries | Compare rewrite output diffs on fixed query set |
| Retrieval coverage loss | L1 Retrieval | QSR + DLCTR down; zero-result rate up | Candidate-set size delta by connector |
| Reranker miscalibration | L2 Reranking | DLCTR down with stable recall; clicks shift deeper | Offline re-score with previous model |
| Interleaving policy shift | L3 Interleaver | DLCTR down from deeper click depth; source mix shifts | Source contribution before/after |
| Permission filtering regression | Auth/Policy | QSR down for specific tenant/cohort | Pre/post-filter candidate counts |
| AI answer cannibalization | SAIN | QSR mixed; DLCTR down + answer engagement up | Split by answer-shown cohort |
| SAIN generation regression | SAIN | QSR down in answer-shown cohorts | Compare SAIN-on vs SAIN-off |
| Telemetry/pipeline issue | Logging/Metrics | Abrupt jumps without behavioral correlate | Schema change audit, missing-event rates |
| Connector outage | Data Ingestion | DLCTR down -2 to -8%, zero-result rate up | Connector health dashboard |

---

## 6. Known Recurring Patterns

### Enterprise Onboarding Wave
- **Trigger:** Large tenant batch onboarding
- **Impact:** DLCTR -2 to -4%, QSR -1 to -2%
- **Mechanism:** New tenants have sparse indexes, dragging down aggregate metrics via mix-shift
- **Duration:** 14-28 days. Recovery as tenants configure connectors (30-90 days)
- **Key check:** Segment by tenant_age — if drop concentrated in <30-day tenants, this is expected

### AI Feature Batch Rollout
- **Trigger:** Batch AI enablement for tenant cohort
- **Impact:** DLCTR -2 to -4%, AI trigger rate +10 to +20%, QSR +0.5 to +1.5%
- **THIS IS SUCCESS, NOT FAILURE.** Users get AI answers instead of clicking
- **Key check:** Always segment by ai_enablement first

### Connector Outage
- **Trigger:** Third-party connector service degradation
- **Impact:** DLCTR -2 to -8%, zero-result rate up +2 to +10%
- **Duration:** 0.5-3 days
- **Diagnostic shortcut:** Check connector health dashboard first — if status shows failure, skip decomposition

### End-of-Quarter Surge
- **Trigger:** Finance/compliance/strategy searches at quarter-end
- **Impact:** Query volume +15 to +30%, DLCTR -0.5 to -1.5%
- **Mechanism:** Exploratory searches have lower click-through. Mix-shift, not regression.

---

## 7. Investigation Priority Order

When metrics move, check in this order:
1. **Instrumentation/Logging** — cheap to verify, expensive to miss
2. **Connector/Data pipeline** — most common root cause in enterprise search
3. **Query understanding (L0)** — cascading effect on all downstream
4. **Algorithm/Model change** — ranking model, embedding model, retraining
5. **Experiment ramp/de-ramp** — A/B test exposure changes
6. **AI feature effect** — SAIN adoption, threshold change, model migration
7. **Seasonal/External** — calendar effects, industry cycles
8. **User behavior shift** — null hypothesis, check LAST, accept only after ruling out engineering causes

---

## 8. Why Debugging Enterprise Search is Hard

- **Stage-level confounding:** Rewrite, retrieval, rerank, interleaving changes produce similar metric signatures
- **Position bias & depth sensitivity:** DLCTR moves when ranking depth changes, even with stable relevance
- **Composite metric masking:** QSR can improve from answer engagement while click behavior worsens
- **SAIN policy masking:** Direct answers reduce clicks (DLCTR down) while task completion improves
- **Topline masking:** Localized regressions cancel out in aggregate — always decompose
- **Release/experiment overlap:** Concurrent experiments across teams make temporal attribution ambiguous
- **Connector heterogeneity:** Source-specific schema and freshness variation cause segment-confounded movement

---

## 9. Vocabulary Quick Reference

| Term | Definition |
|------|-----------|
| QSR | Query Success Rate — north-star online metric |
| DLCTR | Discounted Long Click-Through Rate — click quality metric |
| SAIN | Smart AI Answers — the answer-generation layer |
| L0/L1/L2/L3 | Pipeline layers: Query Intelligence / Retrieval / Reranking / Interleaving |
| Long click | User clicks and finds the page useful (dwell time threshold) |
| Connector | Integration linking external SaaS app to Rovo |
| UMBRELLA | Pointwise LLM-as-Judge relevance labeling framework |
| Product affinity | User's tendency to prefer results from specific Atlassian products |
| Mix-shift | Metric movement caused by composition change (new tenants, new query types), not quality change |
