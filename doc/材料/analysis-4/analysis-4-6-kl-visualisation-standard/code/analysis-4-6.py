#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

ANALYSIS4_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ANALYSIS4_ROOT))

from common.analysis4_common import (
    CANONICAL_FAMILIES,
    FAMILY_ORDER,
    belief_profile_bars,
    dump_json,
    family_posterior,
    full_soft_evidence,
    heatmap,
    js_divergence,
    load_rooted_library,
    plot_graph,
    write_csv_rows,
)


FIGURE_TYPES = [
    {
        'figure_type': 'A',
        'name': 'condition_specific_family_divergence_heatmap',
        'mandatory': True,
        'primary_question': 'Which family pairs are separated by this graph/evidence condition?',
        'required_inputs': 'graph/evidence condition, family posterior vectors, pairwise JS or KL',
        'required_annotations': 'family order, target marker, metric label, evidence level',
        'default_metric': 'JS divergence',
        'default_filename': 'analysis-N_figX_condition_family_heatmap.pdf',
    },
    {
        'figure_type': 'B',
        'name': 'target_belief_profile_panel',
        'mandatory': True,
        'primary_question': 'What behavioural predictions produce the divergence values?',
        'required_inputs': 'same condition as type A, target posterior per family',
        'required_annotations': 'graph, observed evidence, target node, family labels',
        'default_metric': 'posterior probabilities',
        'default_filename': 'analysis-N_figX_condition_belief_profiles.pdf',
    },
    {
        'figure_type': 'C',
        'name': 'global_family_confusion_summary',
        'mandatory': True,
        'primary_question': 'Which families are globally confusable across the current panel?',
        'required_inputs': 'panel-level divergences or synthetic recovery matrix',
        'required_annotations': 'same family order, panel description, metric summary',
        'default_metric': 'mean JS plus recovery matrix',
        'default_filename': 'analysis-N_figX_global_family_confusion.pdf',
    },
    {
        'figure_type': 'D',
        'name': 'parameter_grid_separability_map',
        'mandatory': False,
        'primary_question': 'Where are free parameters identifiable or degenerate?',
        'required_inputs': 'parameter grid, panel-level divergences or recovery',
        'required_annotations': 'parameter axes, anchor setting, color scale',
        'default_metric': 'mean JS to anchor / local identifiability',
        'default_filename': 'analysis-N_figX_parameter_grid.pdf',
    },
    {
        'figure_type': 'E',
        'name': 'rooted_descriptor_linkage_summary',
        'mandatory': True,
        'primary_question': 'Which rooted dimensions drive separability or identifiability?',
        'required_inputs': 'descriptor values and condition-level diagnostic scores',
        'required_annotations': 'D1/D2/D3 labels from analysis-3',
        'default_metric': 'mean JS or diagnostic score by descriptor bin',
        'default_filename': 'analysis-N_figX_descriptor_linkage.pdf',
    },
    {
        'figure_type': 'F',
        'name': 'ranked_diagnostic_condition_summary',
        'mandatory': False,
        'primary_question': 'Which conditions are most useful to carry forward?',
        'required_inputs': 'condition rankings and thumbnails',
        'required_annotations': 'pair-specific target, graph id, evidence level, score',
        'default_metric': 'ranking score',
        'default_filename': 'analysis-N_figX_ranked_conditions.pdf',
    },
]


CONVENTIONS = [
    {'key': 'family_order', 'value': ', '.join(FAMILY_ORDER)},
    {'key': 'overview_metric', 'value': 'JS divergence by default; use directional KL only when asymmetry is itself the scientific point.'},
    {'key': 'parameter_metric', 'value': 'Use local-neighbour identifiability or mean JS to a named anchor.'},
    {'key': 'colour_scale_rule', 'value': 'Keep identical colour scales across comparable heatmaps inside one analysis.'},
    {'key': 'naming_rule', 'value': 'analysis-N_figX_description.pdf with figure number fixed by report order.'},
    {'key': 'annotation_rule', 'value': 'Every condition-specific panel must show graph, evidence, target and family order.'},
]



def choose_worked_example(records):
    summary_path = ANALYSIS4_ROOT / 'analysis-4-2-family-separability' / 'code' / 'data' / 'analysis-4-2_summary.json'
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding='utf-8'))
        row = max(summary['main_figure_conditions'], key=lambda item: float(item['panel_score']))
        record = next(item for item in records if item.graph_id == row['graph_id'])
        return record, row['evidence_level']
    return records[0], 'high'



def worked_example(records, output_path: Path):
    record, level_name = choose_worked_example(records)
    evidence = full_soft_evidence(record, level_name)
    observed_labels = {node: color for node, color in enumerate(record.preferred_colors.values(), start=1)}
    posteriors = {
        family: family_posterior(record.adjacency, 0, evidence, CANONICAL_FAMILIES[family])
        for family in FAMILY_ORDER
    }
    matrix = [
        [js_divergence(posteriors[left], posteriors[right]) for right in FAMILY_ORDER]
        for left in FAMILY_ORDER
    ]

    fig = plt.figure(figsize=(11.8, 4.6))
    grid = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.55], width_ratios=[1.0, 1.1, 1.35], hspace=0.35, wspace=0.28)
    ax_graph = fig.add_subplot(grid[0, 0])
    ax_heat = fig.add_subplot(grid[0, 1])
    ax_bars = fig.add_subplot(grid[0, 2])
    ax_text = fig.add_subplot(grid[1, :])

    plot_graph(ax_graph, record.adjacency, target=0, observed_state_labels=observed_labels, title=f'Graph + evidence ({record.graph_id}, {level_name})')
    heatmap(ax_heat, matrix, list(FAMILY_ORDER), 'Family JS heatmap')
    belief_profile_bars(ax_bars, [(family, posteriors[family]) for family in FAMILY_ORDER], 'Target belief profiles')
    ax_bars.legend(fontsize=7, ncol=2)

    ax_text.axis('off')
    ax_text.text(
        0.01,
        0.92,
        'Worked example annotations:\n'
        f'- D1={record.descriptor["D1_target_degree"]}, D2={record.descriptor["D2_neighbor_coupling"]}, D3={record.descriptor["D3_remote_class"]}\n'
        '- This single condition shows the recommended standard stack: graph/evidence, family heatmap, and belief profiles.\n'
        '- Companion figures elsewhere in the report should add the global confusion summary and rooted-descriptor linkage summary.',
        va='top',
        fontsize=9,
    )

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return {
        'graph_id': record.graph_id,
        'evidence_level': level_name,
        'descriptor': record.descriptor,
    }



def main() -> None:
    analysis_dir = Path(__file__).resolve().parents[1]
    data_dir = analysis_dir / 'code' / 'data'
    figures_dir = analysis_dir / 'figures'
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    records = load_rooted_library()
    example_meta = worked_example(records, figures_dir / 'analysis-4-6_fig1_worked_example_panel.pdf')

    write_csv_rows(data_dir / 'analysis-4-6_template_checklist.csv', FIGURE_TYPES)
    write_csv_rows(data_dir / 'analysis-4-6_conventions.csv', CONVENTIONS)
    dump_json(
        data_dir / 'analysis-4-6_visual_standard.json',
        {
            'analysis': '4-6',
            'default_family_order': list(FAMILY_ORDER),
            'figure_types': FIGURE_TYPES,
            'conventions': CONVENTIONS,
            'minimal_mandatory_suite': [item['name'] for item in FIGURE_TYPES if item['mandatory']],
            'worked_example': example_meta,
            'continuity_note': 'D1/D2/D3 labels must remain aligned with analysis-3 rooted descriptor terminology.',
        },
    )

    print(f'Wrote {data_dir / "analysis-4-6_template_checklist.csv"}')
    print(f'Wrote {data_dir / "analysis-4-6_conventions.csv"}')
    print(f'Wrote {data_dir / "analysis-4-6_visual_standard.json"}')
    print(f'Wrote {figures_dir / "analysis-4-6_fig1_worked_example_panel.pdf"}')


if __name__ == '__main__':
    main()
