# Data Interpretation Accuracy (Binary)

Score this dimension using binary checkpoints. Answer true/false for each based on evidence in the text.

## Checkpoints

- **numbers_described_correctly:** Are percentages, trends, and comparisons described accurately relative to the data shown (no "increased" when data shows a decrease, etc.)?
- **comparisons_have_baselines:** Are comparisons (YoY, vs benchmark, across segments) made against clearly stated baselines or reference points?
- **acknowledges_outliers:** Are outliers, anomalies, or edge cases noted rather than silently ignored?
- **avoids_overgeneralization:** Are findings scoped appropriately (e.g., "in this segment" rather than "overall") without overgeneralizing from subsets?

## Calibration

If the information is not present, answer false. This dimension rewards precision in describing what the data actually shows. Common failure: saying "sales increased significantly" when the increase is +1.3% with a CI spanning zero.

## Conversion

score = (count_true / 4) * 10. Each true = 2.5 points.
