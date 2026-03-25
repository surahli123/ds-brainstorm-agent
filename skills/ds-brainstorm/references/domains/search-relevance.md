# Domain Knowledge: Search Relevance (Enterprise Search)

*Consolidated from: Rovo Search architecture blog, Search Metric Analyzer knowledge base*
*Last updated: 2026-03-24*
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
- **AI Success Rate:** `ai_answers_satisfying / ai_answers_triggered` — baseline 0.620

### Decomposition Dimensions (slice these first)
- `tenant_tier` (standard / premium / enterprise)
- `ai_enablement` (ai_on / ai_off) — ALWAYS segment by this
- `connector_type` (confluence / slack / gdrive / jira / sharepoint)
- `product_source` (which Atlassian product the result came from)
- `query_type` (navigational / informational / action)
- `position_bucket` (1 / 2 / 3-5 / 6-10 / 10+)

---

## 2. Co-Movement Diagnostic Patterns

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

**Critical anti-pattern:** Click Quality down + AI Trigger up = SUCCESS. Always segment by `ai_enablement` before diagnosing.

---

## 3. Search Architecture (8-Stage Pipeline)

```
User Query → Query Understanding (L0) → Retrieval (L1) → Reranking (L2)
  → Interleaving (L3) → Permission Filtering → AI Search (SAIN) → Presentation
```

### L0: Query Intelligence
- Intent classification, spell correction, acronym resolution, query reformulation
- Uses pre-trained language models + self-hosted LLMs
- **Failure mode:** Misclassification cascades — affects ALL downstream metrics

### L1: OpenSearch Retriever
- BM25 (lexical) + KNN (semantic) matching with permission verification
- Fine-tuned GBDT rescoring (popularity + contributor signals)
- **Multi-stack:** Separate document, messaging, and default search stacks

### L2: Semantic & Behavioral Ranker
- Cross-encoder (semantic relevance) + DCN (behavioral signals)
- Outputs MULTIPLE scores combined via optimization layer
- **Key implication:** Changing primary offline metric means potentially retuning this layer

### L3: Interleaver
- Merges results from multiple products using product affinity + semantic relevance

### AI Search (SAIN)
- Answer-generation layer on top of retrieval/ranking
- **Key implication:** SAIN can shift user behavior independently of ranking quality

### Multi-Connector Strategy
- **Full Ingestion:** Google Drive, Slack
- **Linked Content:** Figma (when referenced in Confluence/Jira)
- **Federated:** Gmail, Outlook via third-party APIs
- **50+ connectors** with different schema, freshness, and failure modes

### Personalization
- User-created content ranked higher, collaborator content elevated
- Freshness boosted with product-specific time scales
- Authority via container type, content length, contributor count

---

## 4. Evaluation Methodology

### Offline Metrics (all currently computed)
- **Recall@k**, **NDCG**, **MRR**, **LLM-as-a-Judge**

### LLM-as-Judge: UMBRELLA Framework
- Pointwise relevance grading (0-3 scale)
- 73.3% agreement with human labelers (GPT-4.1, WANDS dataset)
- Conservative bias: underrates borderline results

### LLM-as-Judge: Pairwise Preference
- Binary choice with swap-based double-check for position bias
- Combined precision: 90.8% via decision tree over attribute judges
- Cheaper model suffices (gpt-4.1-mini)

### Measurement Pitfalls
- **Unlabeled ≠ Irrelevant:** NDCG drops when new relevant results lack labels
- **Judge Calibration Drift:** Model version changes shift grades, not quality
- **Conservative Judge Bias:** Systematic negative offset vs human labels
- **Position Bias:** 11-25% of pairwise judgments are position-sensitive

---

## 5. Failure Taxonomy

| Failure Class | Pipeline Stage | Metric Signature | Fast Check |
|--------------|----------------|-----------------|------------|
| Query rewrite drift | L0 | QSR down on long-tail | Rewrite output diffs on fixed query set |
| Retrieval coverage loss | L1 | QSR + DLCTR down; zero-result up | Candidate-set size delta by connector |
| Reranker miscalibration | L2 | DLCTR down with stable recall | Offline re-score with previous model |
| Interleaving policy shift | L3 | DLCTR down, source mix shifts | Source contribution before/after |
| Permission filtering regression | Auth | QSR down for specific tenant | Pre/post-filter candidate counts |
| AI answer cannibalization | SAIN | DLCTR down + answer engagement up | Split by answer-shown cohort |
| SAIN generation regression | SAIN | QSR down in answer-shown cohorts | SAIN-on vs SAIN-off comparison |
| Telemetry issue | Logging | Abrupt jumps, no behavioral correlate | Schema change audit |
| Connector outage | Ingestion | DLCTR -2 to -8%, zero-result up | Connector health dashboard |

---

## 6. Known Recurring Patterns

- **Enterprise Onboarding Wave:** DLCTR -2 to -4% from mix-shift (new sparse-index tenants). Duration: 14-28 days.
- **AI Feature Batch Rollout:** DLCTR -2 to -4%, AI trigger +10 to +20%. THIS IS SUCCESS. Segment by ai_enablement.
- **Connector Outage:** DLCTR -2 to -8%, zero-result up. Duration: 0.5-3 days. Check connector health first.
- **End-of-Quarter Surge:** Volume +15 to +30%, DLCTR -0.5 to -1.5%. Mix-shift from exploratory searches.

---

## 7. Investigation Priority Order

1. Instrumentation/Logging — cheap to verify, expensive to miss
2. Connector/Data pipeline — most common root cause
3. Query understanding (L0) — cascading downstream effect
4. Algorithm/Model change
5. Experiment ramp/de-ramp
6. AI feature effect
7. Seasonal/External
8. User behavior shift — check LAST

---

## 8. Vocabulary Quick Reference

| Term | Definition |
|------|-----------|
| QSR | Query Success Rate — north-star online metric |
| DLCTR | Discounted Long Click-Through Rate — click quality metric |
| SAIN | Smart AI Answers — answer-generation layer |
| L0/L1/L2/L3 | Pipeline layers: Query Intelligence / Retrieval / Reranking / Interleaving |
| Long click | User clicks and finds the page useful (dwell time threshold) |
| Connector | Integration linking external SaaS app to Rovo |
| UMBRELLA | Pointwise LLM-as-Judge relevance labeling framework |
| Mix-shift | Metric movement from composition change, not quality change |
