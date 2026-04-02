# Analysis 4-1: agent taxonomy and formal model space

## What scientific question did this analysis address?
This analysis asked what the **smallest simulation-ready family set** should be once the project moves beyond a single attenuation parameter. The key question was whether we need only fixed-graph attenuation models, or also structure-rewrite families such as a target-centred star and a local cluster rewrite.

## How do the TODO criteria map to what was actually done?
- **D1 taxonomy document**: `code/data/analysis-4-1_taxonomy.json`
- **D2 unified notation table**: `code/data/analysis-4-1_unified_notation.csv`
- **D3 family comparison table**: `code/data/analysis-4-1_family_comparison.csv`
- **D4 redundancy assessment**: the same JSON file states that the pure local log-evidence heuristic is redundant with `M_0`
- **D5 visual schematic**: `figures/analysis-4-1_fig1_family_schematic.pdf`

## Main findings
- The minimal family set carried forward is: **M_exact, M_0, M_rho, M_rho,beta, M_star, M_cluster**.
- The pure local log-evidence heuristic is **exactly equivalent** to `M_0` under standard exponentiate-and-normalise readout.
- The selected canonical prototypes are simulation-ready and already show non-trivial separation on the analysis-3 selected panel. For example, `M_0` vs `M_cluster` had mean JS `0.162905`, and `M_0` vs `M_rho` had mean JS `0.10859`.

## How do I run the code?
```bash
python3 code/analysis-4-1.py
```

## What do the outputs mean?
- `analysis-4-1_unified_notation.csv`: one row per family; key columns are `internal_graph_representation`, `factor_representation`, `free_parameters`, and `canonical_downstream_setting`.
- `analysis-4-1_family_comparison.csv`: compact side-by-side comparison; the most useful columns are `graph_preserved_or_rewritten`, `local_vs_nonlocal_sensitivity`, and `computational_simplicity`.
- `analysis-4-1_taxonomy.json`: the master record. Read `family_specifications`, `redundancy_assessment`, and `simulation_ready_check` first.

## What should a student read first, and in what order?
1. This README
2. `analysis-4-1.tex`
3. `figures/analysis-4-1_fig1_family_schematic.pdf`
4. `code/data/analysis-4-1_taxonomy.json`
5. The two CSV summary tables
