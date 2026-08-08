---
name: eda
description: Exploratory data analysis for a dataset in a SageMaker Notebook/Studio environment. Use when the user wants to profile a new dataset, understand distributions/missingness/correlations before feature engineering, or asks to "explore the data".
---

# EDA

Generates and runs exploratory-data-analysis code directly in the notebook. This skill is local-only and has no AWS side effects — it never submits a Processing/Training job, so it never needs a confirmation step.

Read `CONTEXT.md` at the repo root first, if it exists, so column/entity names in your commentary match the project's domain vocabulary rather than raw dataframe column names.

## Steps

1. **Locate the data.** Ask where the dataset lives if not stated — most likely S3 (`s3://...`) read via `pandas`/`awswrangler`, or already local in the notebook's `/data` or `/tmp` directory. Load a sample first if the dataset is large; don't pull a multi-GB dataset into memory without checking size.
2. **Structural profile.** Shape, dtypes, memory footprint, missingness per column, cardinality of categorical columns, duplicate rows.
3. **Distributions.** Histograms/KDE for numeric columns, value counts for categoricals, class balance for the target column if one is named.
4. **Relationships.** Correlation matrix for numeric features, target-vs-feature plots for the top candidate predictors. Call out multicollinearity and any feature that looks like target leakage (near-perfect correlation with the target, or a column that couldn't be known at prediction time).
5. **Data quality flags.** Anything that will bite later: mixed types in a column, timestamps out of expected range, IDs that aren't unique, obvious sentinel values (`-1`, `9999`) standing in for missing data.
6. **Summarize.** End with a short written summary: what the target is, what the strongest candidate features look like, and what needs cleaning before `/feature-engineering`.

## Notes

- Prefer generating cells the user runs in their own notebook over running heavy computation yourself — keep output readable, don't dump full dataframes.
- If the dataset is already registered in Feature Store, check there first rather than re-deriving features that already exist.
