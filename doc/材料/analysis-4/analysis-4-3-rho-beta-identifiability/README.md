# Analysis 4-3: parameter identifiability of structural attenuation and factor strength

## What scientific question did this analysis address?
This analysis asked whether changes in **structural attenuation (`rho`)** can be distinguished from changes in **factor strength (`beta`)**, and whether family-level conclusions survive once `beta` is allowed to vary.

## How do the TODO criteria map to what was actually done?
- **Parameter atlas**: `code/data/analysis-4-3_parameter_atlas.csv`
- **Condition-level identifiability scores**: `code/data/analysis-4-3_condition_identifiability.csv`
- **Noiseless recovery**: `code/data/analysis-4-3_recovery_noiseless.csv`
- **Noisy recovery**: `code/data/analysis-4-3_recovery_noisy.csv`
- **Summary / recommendation**: `code/data/analysis-4-3_summary.json`
- **Figures**: the four PDFs in `figures/`

## Main findings
- The diagnostic recovery panel is: RG031 (high), RG100 (high), RG088 (high), RG087 (high), RG091 (high), RG111 (high), RG112 (high), RG114 (high).
- On that panel, the **noiseless exact-match rate is 1.0**, showing that the panel is informative in principle.
- Under noisy synthetic data, the exact-match rate falls to **0.3**, with mean absolute errors **0.136587 for `rho`** and **0.584921 for `beta`**.
- After beta optimisation, attenuation can still approach exact inference perfectly at the exact endpoint, but the best attenuation-vs-star match still leaves mean JS **0.027041**, so star rewrites remain meaningfully distinct.

## How do I run the code?
```bash
python3 code/analysis-4-3.py
```

## What do the outputs mean?
- `analysis-4-3_parameter_atlas.csv`: one row per `(rho, beta)` grid point. The key columns are `mean_js_to_exact_beta4`, `mean_js_to_local_beta4`, and `local_neighbor_identifiability`.
- `analysis-4-3_condition_identifiability.csv`: one row per graph/evidence condition. Use `diagnostic_score`, `rho_sensitivity`, and `beta_sensitivity` to rank stimuli.
- `analysis-4-3_summary.json`: read `recovery_panel`, `ridge_info`, `family_robustness_under_beta_optimisation`, and `recommendation` first.

## What should a student read first, and in what order?
1. This README
2. `analysis-4-3.tex`
3. `figures/analysis-4-3_fig1_parameter_atlas.pdf`
4. `figures/analysis-4-3_fig2_recovery.pdf`
5. `code/data/analysis-4-3_summary.json`
6. The condition-level identifiability CSV
