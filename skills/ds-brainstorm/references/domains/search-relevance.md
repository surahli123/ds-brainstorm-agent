# Unraveling Rovo Search Relevance

*Source: Atlassian Engineering Blog*
*URL: https://www.atlassian.com/blog/atlassian-engineering/unraveling-rovo-search*
*Retrieved: 2026-02-21*
*Purpose: Domain expert reviewer calibration fixture*

---

## Overview

Rovo is Atlassian's unified search solution enabling organizations to discover content across Atlassian products and 50+ third-party SaaS applications including Google Drive, Slack, SharePoint, and others.

## Key Terminologies

- **Connector**: Integrations linking external SaaS applications to Rovo
- **OpenSearch**: AWS-hosted platform indexing content as searchable documents
- **BM25**: Ranking function estimating document relevance to queries
- **KNN**: K Nearest Neighbors algorithm for semantic similarity matching
- **LLM**: Large Language Models powering query understanding and answer generation

## Search Experiences

### Quick Find
Search box in Atlassian products for rapidly refinding recently accessed content.

### Full Search
Advanced search with filtering by product, type, contributor, and time, prioritizing relevant, authoritative, and popular results while considering user affinity.

### Smart Answers with Citations
"AI-generated answers grounded in authoritative content from across connected knowledge bases" with passage-level citations referencing source documents.

### Rovo Chat
AI Assistant leveraging the same underlying search infrastructure as Smart Answers.

## Multi-Connector Search Strategy

- **Full Ingestion**: Google Drive, Slack content fully indexed
- **Linked Content**: Figma content ingested when referenced in Confluence/Jira
- **Federated Approach**: Gmail and Outlook Mail integrate via third-party search APIs
- **Multiple Stacks**: Separate document, messaging, and default search stacks optimize for different content types

## Search Architecture

### Foundational Search Flow

1. **Query Intelligence**: Intent classification, query rewriting, typo correction, acronym handling via pre-trained language models and self-hosted LLMs

2. **OpenSearch Retriever L1**: BM25 and KNN matching with permission verification; fine-tuned Gradient Boosted Decision Tree rescoring based on popularity and contributor signals

3. **Semantic & Behavioral Ranker L2**: AWS SageMaker-hosted reranking using fine-tuned cross-encoder models for semantic relevance and Deep & Cross Network (DCN) for behavioral signals; outputs multiple scores (semantic relevance, predicted click-through rate) combined via shallow optimization layer

4. **Interleaver L3**: Results from multiple products interleaved based on product affinity and semantic relevance to query

### System Flow

Requests flow through a GraphQL endpoint in the "aggregator" service (query intelligence and product fanout) to the "searcher" service (OpenSearch communication). Post-reranking, an additional permission check ensures security before final L3 interleaving.

## Smart Answers Workflow

Query classification routes to:
- **Person/Team**: Entity resolution with smart cards
- **Bookmarks**: Direct links
- **Natural Language**: Full Smart Answer workflow
- **None**: Standard search results

For natural language queries:
1. Query rewriting using context enrichment (organization, location, time)
2. Document retrieval via foundational search
3. Transformation into unified data model
4. Passage-level chunking and cross-encoder ranking
5. Answer generation with passage-level citations

## Relevance Methodology

### Index Strategy

Content, contributors, metadata, popularity signals (views, likes, comments), authority indicators (contributor count, container type), and user relationships stored for ranking influence.

### Personalization Techniques

- User-created content ranked higher in personal searches
- Content from collaborators elevated
- For messaging apps, prioritizes user's active channels
- Authority determined via container type, content length, contributor count, freshness, activity
- Freshness boosted (penalizing older results) with product-specific time scales

### Evaluation Metrics

**Online Evaluation:**
- **Query Success Rate (QSR)**: North-star metric combining clicks, dwell time, and explicit feedback

**Offline Evaluation:**
- **Recall@k**: Percentage of queries returning expected document in top k results
- **NDCG**: Normalized Discounted Cumulative Gain measuring ranking effectiveness
- **MRR**: Mean Reciprocal Rank assessing target document position
- **LLM-as-a-Judge**: "LLM evaluates whether the ranking was good, simulating human assessment"

## Conclusion

Rovo combines multiple ranking layers, semantic understanding, behavioral signals, and personalization to deliver relevant results across diverse data sources. The multi-layered evaluation approach—combining user behavior, explicit feedback, and AI judgment—ensures search quality and user trust before and after production release.
