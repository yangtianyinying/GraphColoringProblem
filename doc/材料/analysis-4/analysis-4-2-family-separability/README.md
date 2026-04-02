# Analysis 4-2: family separability on the existing stimulus library

## What scientific question did this analysis address?
This analysis asked whether the **existing rooted-shell stimulus library** is already rich enough to separate the candidate families from Analysis 4-1 at the level of target-node belief outputs.

## How do the TODO criteria map to what was actually done?
- **Condition-level family diagnostics**: `code/data/analysis-4-2_condition_metrics.csv`
- **All pairwise family divergences**: `code/data/analysis-4-2_pair_metrics.csv`
- **Posterior library**: `code/data/analysis-4-2_posteriors.csv`
- **Ranked diagnostic conditions**: `code/data/analysis-4-2_ranked_conditions.csv`
- **Global summary + reduced panel**: `code/data/analysis-4-2_summary.json`
- **Figures**: the four PDFs in `figures/`

## Main findings
- The analysis covered **600 graph/evidence conditions**.
- The strongest average family contrast was `M_exact` vs `M_star` with mean JS **0.113605** across the full library.
- `M_star` vs `M_cluster` was also strong (mean JS **0.10413**), while `M_exact` vs canonical `M_rho` was weak (mean JS **0.009751**), which directly motivates Analysis 4-3.
- The reduced diagnostic panel retained the following six high-value conditions: RG119 (high), RG112 (high), RG121 (high), RG114 (high), RG036 (high), RG100 (high).
- The main figure conditions used for the report are: RG036 (high), RG100 (high), RG112 (high), RG114 (high).

## How do I run the code?
```bash
python3 code/analysis-4-2.py
```

## What do the outputs mean?
- `analysis-4-2_condition_metrics.csv`: one row per graph/evidence condition. The key columns are `mean_js_all_pairs`, `exact_vs_rho_js`, `rho_vs_star_js`, `star_vs_cluster_js`, and `M0_vs_nonlocal_mean_js`.
- `analysis-4-2_pair_metrics.csv`: long-format pairwise library. Use this when you need family-pair-specific summaries.
- `analysis-4-2_summary.json`: read `average_js_matrix`, `recovery_matrix`, `reduced_panel`, `main_figure_conditions`, and `matched_pairs` first.

## What should a student read first, and in what order?
1. This README
2. `analysis-4-2.tex`
3. `figures/analysis-4-2_fig1_condition_panels.pdf`
4. `figures/analysis-4-2_fig2_global_confusion.pdf`
5. `code/data/analysis-4-2_summary.json`
6. The condition-level CSVs
