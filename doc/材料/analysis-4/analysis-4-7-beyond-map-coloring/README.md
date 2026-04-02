# Analysis 4-7: beyond map-colouring

## What scientific question did this analysis address?
This analysis asked whether the long-term scientific question---human structural approximation on graphs---can really be answered inside a single **repulsive map-colouring** domain.

## How do the TODO criteria map to what was actually done?
- **Alternative-domain comparison table**: `code/data/analysis-4-7_domain_comparison.csv`
- **Taxonomy transfer summary**: `code/data/analysis-4-7_taxonomy_transfer.csv`
- **Master summary and prospect text**: `code/data/analysis-4-7_summary.json`
- **Comparison figure**: `figures/analysis-4-7_fig1_domain_comparison.pdf`

## Main findings
- The recommended next task domain is **attractive_graph_labelling**.
- The top three weighted-priority domains were: attractive_graph_labelling (4.75), map_colouring (4.1), social_consensus (4.0).
- The reason for prioritising attractive graph labelling is simple: it flips local semantics from repulsive to attractive while preserving most of the graph-inference interface, so it is the cleanest test of whether the Analysis 4 family taxonomy is task-general.

## How do I run the code?
```bash
python3 code/analysis-4-7.py
```

## What do the outputs mean?
- `analysis-4-7_domain_comparison.csv`: one row per domain. The key columns are `theoretical_value`, `experimental_simplicity`, `continuity_with_current_paradigm`, and `weighted_priority_score`.
- `analysis-4-7_taxonomy_transfer.csv`: one row per family; use this to see which analysis-4 families transfer cleanly beyond map-colouring.
- `analysis-4-7_summary.json`: read `limitation_statement`, `future_task_recommendation`, and `prospect_section_draft` first.

## What should a student read first, and in what order?
1. This README
2. `analysis-4-7.tex`
3. `figures/analysis-4-7_fig1_domain_comparison.pdf`
4. `code/data/analysis-4-7_summary.json`
