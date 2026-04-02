# Analysis 4-4: is the local log-evidence heuristic genuinely a new family?

## What scientific question did this analysis address?
This analysis tested whether the proposed **local log-evidence heuristic** is a genuinely new inference family or simply a re-expression of `M_0`.

## How do the TODO criteria map to what was actually done?
- **Formal definition and equivalence statement**: `code/data/analysis-4-4_equivalence.json`
- **Simulation comparison**: `code/data/analysis-4-4_simulation_comparison.csv`
- **Equivalence figure**: `figures/analysis-4-4_fig1_equivalence_check.pdf`
- **Example graph**: `figures/analysis-4-4_fig2_example_graph.pdf`

## Main findings
- The maximum absolute difference between the pure heuristic and `M_0` was **0.0** over the full library.
- Mean JS to `M_0` was **0.0** for the pure heuristic, **0.0114248243** for a weighted variant, and **0.014439751** for a clipped variant.
- Conclusion: the pure heuristic is exactly `M_0`; only distorted variants deserve separate heuristic status.

## How do I run the code?
```bash
python3 code/analysis-4-4.py
```

## What do the outputs mean?
- `analysis-4-4_equivalence.json`: read `formal_heuristic_definition`, `equivalence_statement`, `library_summary`, and `taxonomy_recommendation`.
- `analysis-4-4_simulation_comparison.csv`: one row per graph/evidence condition and variant. The important columns are `variant` and `js_to_M0`.

## What should a student read first, and in what order?
1. This README
2. `analysis-4-4.tex`
3. `figures/analysis-4-4_fig1_equivalence_check.pdf`
4. `code/data/analysis-4-4_equivalence.json`
5. The simulation CSV if you need the full numeric check
