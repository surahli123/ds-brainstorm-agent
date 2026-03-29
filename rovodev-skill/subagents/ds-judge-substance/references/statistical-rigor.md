# Statistical Rigor (Binary)

Score this dimension using binary checkpoints. Answer true/false for each based on evidence in the text. If the information is not present, answer false.

## Checkpoints

- **has_confidence_intervals:** Are confidence intervals, error bars, or uncertainty ranges reported for key quantitative claims?
- **has_significance_tests:** Are statistical tests (p-values, chi-squared, t-tests, etc.) used where comparisons are made?
- **has_sample_sizes:** Are sample sizes or data volumes reported for each analysis segment?
- **has_effect_sizes:** Are effect sizes or practical significance discussed alongside statistical significance?

## Calibration

A dimension where all checkpoints are true represents genuinely rigorous quantitative work. All false indicates the analysis makes numerical claims without statistical backing.

When a checkpoint is not applicable (e.g., significance tests in a purely qualitative analysis), answer true and note the exception in your critique.

## Conversion

The orchestrator converts binary scores to 0-10:
```
score = (count_true / total_checkpoints) * 10
```
4 checkpoints: each true = 2.5 points.
