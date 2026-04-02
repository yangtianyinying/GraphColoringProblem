# Analysis 4-6: standardising KL-based visual diagnostics

## What scientific question did this analysis address?
This analysis asked how future graph/evidence analyses should be visualised so that family separation and parameter identifiability can be compared **consistently across reports**.

## How do the TODO criteria map to what was actually done?
- **Visual standard document**: `code/data/analysis-4-6_visual_standard.json`
- **Template checklist**: `code/data/analysis-4-6_template_checklist.csv`
- **Conventions guide**: `code/data/analysis-4-6_conventions.csv`
- **Worked example**: `figures/analysis-4-6_fig1_worked_example_panel.pdf`

## Main findings
- The mandatory default suite contains four figure types: condition_specific_family_divergence_heatmap, target_belief_profile_panel, global_family_confusion_summary, rooted_descriptor_linkage_summary.
- The worked example is built on **RG112 (high)**, with descriptor `D3-2:strong-remote`.
- The standard explicitly fixes family order, overview metric (JS), naming conventions, and the requirement that every condition-specific panel include graph, evidence, target, and family heatmap.

## How do I run the code?
```bash
python3 code/analysis-4-6.py
```

## What do the outputs mean?
- `analysis-4-6_visual_standard.json`: the master specification; read `figure_types`, `conventions`, and `minimal_mandatory_suite` first.
- `analysis-4-6_template_checklist.csv`: one row per figure type with purpose, inputs, and filename rule.
- `analysis-4-6_conventions.csv`: short key-value guide for family order, metrics, colours, and annotation rules.

## What should a student read first, and in what order?
1. This README
2. `analysis-4-6.tex`
3. `figures/analysis-4-6_fig1_worked_example_panel.pdf`
4. `code/data/analysis-4-6_visual_standard.json`
