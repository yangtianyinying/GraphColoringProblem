# Analysis 4-5: does a two-stage query-plus-belief task provide stronger behavioural constraints?

## What scientific question did this analysis address?
This analysis asked whether a **fixed-evidence, choose-node-then-report-belief** paradigm yields better family discrimination than a standard forced-target belief report.

## How do the TODO criteria map to what was actually done?
- **Choice distributions and belief outputs**: `code/data/analysis-4-5_choice_distributions.csv`
- **Condition-level design metrics**: `code/data/analysis-4-5_design_metrics.csv`
- **Pairwise design summary**: `code/data/analysis-4-5_design_summary.csv`
- **Overall recommendation and recovery matrices**: `code/data/analysis-4-5_summary.json`
- **Figures**: the three PDFs in `figures/`

## Main findings
- Mean pairwise family separation was **0.003211** for belief-only, **0.030576** for selection-only, and **0.054955** for the combined design.
- In other words, adding node selection increased average pairwise discriminability substantially relative to forced-target belief alone.
- Under the simple synthetic recovery model used here, mean recovery diagonals were approximately **0.592** for belief-only, **0.392** for selection-only, and **0.450** for the combined design. So the gain is real, but it is more naturally interpreted as a **targeted extension** than a full replacement.

## How do I run the code?
```bash
python3 code/analysis-4-5.py
```

## What do the outputs mean?
- `analysis-4-5_choice_distributions.csv`: one row per condition, family, and candidate target. Use `choice_probability` and the `belief_p_*` columns together.
- `analysis-4-5_design_metrics.csv`: one row per condition and family pair. The main columns are `belief_only_js`, `selection_only_js`, and `combined_js`.
- `analysis-4-5_summary.json`: read `mean_pairwise_separation`, `recovery_confusion`, and `design_recommendation` first.

## What should a student read first, and in what order?
1. This README
2. `analysis-4-5.tex`
3. `figures/analysis-4-5_fig2_design_comparison.pdf`
4. `figures/analysis-4-5_fig1_choice_distributions.pdf`
5. `code/data/analysis-4-5_summary.json`
