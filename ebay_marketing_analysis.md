# eBay Marketing Channel Analysis: Identifying Test Channels and Measuring Campaign Incrementality

## Executive Summary

**Finding:** Marketing Channel 1 is likely the test channel, with approximately 134 Designated Market Areas (DMAs) in the test group. However, the campaign's measured sales lift of +1.3% is unreliable — the 95% credible interval spans zero [-10.2%, +12.7%], meaning the true effect could range from a 10% decline to a 13% gain.

**Root cause of unreliability:** Two design issues undermine the readout: (1) the test/control DMA split fails placebo validation, suggesting selection bias in how DMAs were assigned, and (2) a strong correlation (r = 0.7) between Channel 1 and Channel 2 attributed sales suggests the last-touch attribution model may be double-counting conversions.

**Recommendation:** Do not use this readout for budget decisions. Before resetting the campaign, fix DMA matching (add pre-test covariates for better balance) and validate cross-channel attribution overlap. Only then can a re-run produce a trustworthy causal estimate.

---

## Problem Statement

Starting in early 2025, the marketing team adjusted budget allocation across channels. This analysis addresses two questions:

1. **Which channel is being tested, and which DMAs are in the test group?**
2. **What is the causal impact of the campaign on attributed sales?**

Our approach: compare pre-test vs. during-test attributed sales across all channels. The channel whose DMAs show the largest and most consistent shift in sales is likely the test channel.

### Why Month-over-Month (MoM) rather than Year-over-Year (YoY)?

- **Recency** — MoM captures the most current performance trends, critical for measuring incremental impact of recent budget changes
- **Market dynamics** — Digital marketing changes rapidly (platform algorithm updates, shifting consumer behavior), making last year's data a poor baseline
- **Budget cycles** — Marketing budgets are adjusted monthly or quarterly, so MoM aligns with the decision cadence

## Step 1: Identifying the Test Channel and Test DMAs

### Approach

We compared attributed sales in the pre-test window (January 1 – February 10, 2025) against the test window (February 11 – March 18, 2025) across all marketing channels. For each channel, we examined:

- **Breadth:** What fraction of DMAs showed a statistically significant change in attributed sales?
- **Magnitude:** How large were the changes?
- **Consistency:** Were the changes directionally aligned (i.e., mostly increases or mostly decreases, not a random mix)?

DMA-level significance was assessed using t-tests comparing each DMA's pre-test vs. post-test daily attributed sales. We then ranked channels by the share of DMAs showing significant, directionally consistent shifts.

### Observations

Across all channels examined, Marketing Channel 1 stood out:
- A higher proportion of its DMAs showed statistically significant sales changes compared to other channels
- The magnitude of changes was larger and more consistent in direction
- Other channels showed noisier, less systematic patterns

### Conclusion

Based on these signals, Channel 1 is most likely the test channel. Approximately 134 DMAs were identified as the test group — those showing significant directional shifts in Channel 1 attributed sales during the test window.

**Caveat:** This identification is heuristic. We assumed the test channel would show the largest systematic shift, which could be confounded by concurrent seasonality, organic trends, or spillover effects between channels. A definitive channel identification would require the experiment design documentation, which was not available for this analysis.

## Step 2: Causal Readout — Measuring Campaign Lift

### Method: Bayesian Structural Time Series (BSTS) with Synthetic Control

To estimate the causal effect, we constructed a counterfactual: what would Channel 1's attributed sales have looked like in the test DMAs *if the campaign had not run*? The difference between observed and counterfactual sales is the estimated lift.

**How Synthetic Control (SC) works:** SC builds a weighted combination of control DMAs that closely matches the test DMAs' pre-test sales trajectory. If the match is good, divergence during the test period can be attributed to the campaign.

**How BSTS extends this:** Bayesian Structural Time Series decomposes the time series into trend, seasonality, and regression components, then quantifies uncertainty around the counterfactual. Unlike frequentist methods, BSTS produces a posterior distribution, yielding a credible interval (not a confidence interval) that directly expresses the probability that the true lift falls within a range.

**Covariates used:**

| Component | Covariates |
|-----------|-----------|
| Synthetic Control matching | Channel 1, Channel 2, and Free marketing pre-test spend |
| BSTS model | Test and Control groups' pre-period time series, time trend, seasonality |

### Results

| Metric | Value |
|--------|-------|
| Point estimate (posterior mean) | +1.3% attributed sales lift |
| 95% credible interval | [-10.2%, +12.7%] |
| Upper-bound daily impact | ~$2k/day (~$73k over the 36-day test period) |
| Interval includes zero? | Yes — campaign may have had no effect |

### Interpretation

The +1.3% point estimate is small and the credible interval is wide, spanning zero. This means:

- We **cannot reject the null hypothesis** that the campaign had no incremental effect on sales
- The estimate is consistent with outcomes ranging from a 10% sales decline to a 13% gain
- Even the optimistic upper bound (~$73k) represents modest business impact over 36 days

**Bottom line:** This test does not provide evidence of positive incrementality. The result is inconclusive, not negative — the campaign may work, but this experiment cannot tell us.

## Step 3: Diagnosing Why the Readout Is Inconclusive

The wide credible interval suggests the experimental design has issues, not just that the effect is small. Two likely contributing factors were identified through model diagnostics:

### Issue 1: DMA Selection Imbalance (Failed Placebo Test)

A placebo test checks whether the Synthetic Control produces a "zero effect" when applied to a period where no treatment occurred. Our placebo test **failed**, indicating that the synthetic control does not adequately replicate the test DMAs' sales trajectory even in the pre-test period.

**What this means:** The test and control DMA groups are not well-balanced on the covariates used for matching. The counterfactual is unreliable, which inflates the credible interval and can introduce bias in either direction.

**Likely cause:** DMA assignment may have been based on criteria (e.g., market size, historical performance) correlated with the outcome, or the available covariates (channel spend, time trend) are insufficient to capture the true differences between test and control markets.

**Recommended fix:** Enrich the matching with additional pre-test covariates — market demographics, customer behavior patterns (e.g., conversion rates, basket size), and non-marketing sales drivers — to achieve better pre-period fit.

### Issue 2: Cross-Channel Attribution Overlap

We found a correlation of r = 0.7 between Channel 1 and Channel 2 attributed sales across DMAs. This is a notably strong correlation that raises concern about attribution accuracy.

**What this means:** Under a last-touch attribution model, the same conversion may be credited to whichever channel the user touched last. If Channel 1 and Channel 2 frequently appear in the same customer journeys, increasing Channel 1 spend could shift attribution *from* Channel 2 without generating truly incremental conversions. The measured +1.3% lift may partly reflect attribution reshuffling rather than real sales growth.

**Recommended fix:** Validate the interaction between Channel 1, Channel 2, and Free (organic) channels by:
- Analyzing customer journey paths to quantify how often users touch multiple channels before converting
- Comparing attributed sales trends across channels at the DMA level to detect substitution patterns
- Considering a multi-touch attribution model as a sensitivity check

## Recommendations

Before relaunching the campaign or making budget decisions based on this readout:

1. **Fix DMA matching** — Add pre-test covariates (demographics, behavioral metrics) to the Synthetic Control to achieve placebo-test validity
2. **Audit attribution overlap** — Validate cross-channel customer journeys to determine whether the r = 0.7 correlation reflects true interaction or attribution artifact
3. **Investigate Heterogeneous Treatment Effects (HTE)** — Once the design issues above are resolved, examine whether the campaign effect varies across DMAs (e.g., by market size, competitive intensity, or baseline Channel 1 penetration). Understanding HTE can guide more efficient DMA targeting in the next test

## Key Assumptions and Limitations

| Assumption | Implication |
|-----------|-------------|
| Last-touch attribution; channels treated as independent after deduplication | May overstate or misattribute lift if customer journeys span channels |
| Test period: Feb 11 – Mar 18, 2025 (36 days) | Short window limits statistical power for small effects |
| Channel identification via MoM trend comparison | Heuristic — could misidentify if multiple channels changed simultaneously |
| DMA assignment via t-test significance | No multiple-comparison correction applied; some DMAs may be false positives |
| Effect size target >±5% for business relevance | Actual lift of +1.3% is below this threshold even at the point estimate |
| DMAs may exhibit HTE | Aggregate analysis may mask meaningful variation across markets |
