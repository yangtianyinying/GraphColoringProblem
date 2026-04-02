#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

ANALYSIS4_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ANALYSIS4_ROOT))

from common.analysis4_common import (
    CANONICAL_FAMILIES,
    COLOR_LABELS,
    FAMILY_ORDER,
    family_posterior,
    full_soft_evidence,
    graph_node_positions,
    js_divergence,
    load_rooted_library,
    load_selected_panel_ids,
    plot_graph,
    dump_json,
    write_csv_rows,
    edge_strengths_rho,
    edge_strengths_star,
    edge_strengths_cluster,
)


def family_specifications() -> list[dict[str, object]]:
    return [
        {
            'family': 'M_exact',
            'class': 'normative benchmark',
            'internal_graph_representation': 'true graph G preserved exactly',
            'factor_representation': 'all original pairwise anti-coordination factors retained with strength beta_edge',
            'free_parameters': 'beta_edge',
            'output_belief_object': 'exact target posterior on the true graph',
            'preserved_structure': 'all nodes, edges, and relay paths',
            'discarded_structure': 'none',
            'psychological_interpretation': 'full graph-aware inference benchmark',
            'canonical_downstream_setting': 'beta=4.0',
            'expected_D1_sensitivity': 'high',
            'expected_D2_sensitivity': 'high',
            'expected_D3_sensitivity': 'high',
            'computational_simplicity': 'low',
        },
        {
            'family': 'M_0',
            'class': 'fixed-graph local baseline',
            'internal_graph_representation': 'true graph retained but only shell-0 edges remain active via rho=0 energy decay',
            'factor_representation': 'only edges incident to the target contribute to the target posterior',
            'free_parameters': 'beta_edge',
            'output_belief_object': 'nearest-neighbour-only target posterior',
            'preserved_structure': 'target and direct-neighbour constraints',
            'discarded_structure': 'all multi-step relay paths and distal closure',
            'psychological_interpretation': 'strictly local bounded inference',
            'canonical_downstream_setting': 'beta=4.0',
            'expected_D1_sensitivity': 'high',
            'expected_D2_sensitivity': 'moderate',
            'expected_D3_sensitivity': 'low',
            'computational_simplicity': 'very high',
        },
        {
            'family': 'M_rho',
            'class': 'fixed-graph attenuation family',
            'internal_graph_representation': 'true graph G preserved',
            'factor_representation': 'edge energy beta_edge is scaled by rho^s_i(u,v) where s_i is shell distance from the target',
            'free_parameters': 'rho, beta_edge',
            'output_belief_object': 'attenuated target posterior on the true graph',
            'preserved_structure': 'full graph topology and shell ordering',
            'discarded_structure': 'none; remote factors are only down-weighted',
            'psychological_interpretation': 'continuous bounded propagation on the correct graph',
            'canonical_downstream_setting': 'rho=0.35, beta=4.0',
            'expected_D1_sensitivity': 'high',
            'expected_D2_sensitivity': 'high',
            'expected_D3_sensitivity': 'high but graded',
            'computational_simplicity': 'moderate',
        },
        {
            'family': 'M_rho,beta',
            'class': 'fixed-graph attenuation with factor-strength uncertainty',
            'internal_graph_representation': 'true graph G preserved',
            'factor_representation': 'same energy-decay rule as M_rho, but beta_edge is explicitly free',
            'free_parameters': 'rho, beta_edge',
            'output_belief_object': 'attenuated target posterior with coupling-strength flexibility',
            'preserved_structure': 'full graph topology and shell ordering',
            'discarded_structure': 'none structurally; flexibility lives in beta',
            'psychological_interpretation': 'bounded propagation plus uncertainty about local constraint strength',
            'canonical_downstream_setting': 'rho=0.35, beta=2.5',
            'expected_D1_sensitivity': 'high',
            'expected_D2_sensitivity': 'high',
            'expected_D3_sensitivity': 'high but potentially confounded with beta',
            'computational_simplicity': 'moderate',
        },
        {
            'family': 'M_star',
            'class': 'structure-rewrite family',
            'internal_graph_representation': 'graph is internally collapsed to a target-centred star',
            'factor_representation': 'each non-target node connects directly to the target with effective strength beta_edge / d_G(i,j)',
            'free_parameters': 'beta_edge',
            'output_belief_object': 'exact posterior on the rewritten star graph',
            'preserved_structure': 'distance-to-target ordering only',
            'discarded_structure': 'non-target/non-target connectivity and relay structure',
            'psychological_interpretation': 'all distal influence is rewritten into direct target-centred pushes',
            'canonical_downstream_setting': 'beta=4.0',
            'expected_D1_sensitivity': 'high',
            'expected_D2_sensitivity': 'low',
            'expected_D3_sensitivity': 'moderate',
            'computational_simplicity': 'high',
        },
        {
            'family': 'M_cluster',
            'class': 'local cluster / junction-lite family',
            'internal_graph_representation': 'retain target, shell-1, shell-2 nodes and add shell-1 fill-in edges induced by shared shell-2 neighbours',
            'factor_representation': 'original local edges keep strength beta_edge; added shell-1 fill-in edges use beta_edge',
            'free_parameters': 'beta_edge',
            'output_belief_object': 'exact posterior on a local cluster graph',
            'preserved_structure': 'local cliques, neighbour-neighbour coupling, shell-2 mediated closure',
            'discarded_structure': 'farther-than-shell-2 structure',
            'psychological_interpretation': 'participants chunk local motifs into a compact cluster representation',
            'canonical_downstream_setting': 'beta=4.0',
            'expected_D1_sensitivity': 'high',
            'expected_D2_sensitivity': 'very high',
            'expected_D3_sensitivity': 'moderate',
            'computational_simplicity': 'moderate to high',
        },
    ]


def redundancy_assessment() -> dict[str, object]:
    statement = (
        'If the proposed local heuristic sums direct-neighbour log evidence and then exponentiates/normalises, '
        'it is exactly the shell-0 factor-graph posterior and therefore equivalent to M_0. '
        'It only becomes distinct once an extra response distortion, arbitrary neighbour weighting, clipping, '
        'or another non-factorisable transform is added.'
    )
    return {
        'status': 'exactly_equivalent_under_standard_assumptions',
        'equivalent_to': 'M_0',
        'statement': statement,
        'distinct_only_if': [
            'neighbour-specific weights not representable as local log-potentials',
            'state-wise clipping or saturation',
            'non-normalised score readout',
            'post-hoc response transform applied after local posterior computation',
        ],
        'recommendation': 'Carry the pure heuristic forward only as a verbal restatement of M_0; reserve separate family status for response-distorted variants only.',
    }


def simulation_ready_check(records) -> dict[str, object]:
    selected_ids = load_selected_panel_ids()
    selected_records = [record for record in records if record.graph_id in selected_ids]
    pair_rows = []
    summary = defaultdict(list)
    for record in selected_records:
        evidence = full_soft_evidence(record, 'high')
        posteriors = {
            family: family_posterior(record.adjacency, 0, evidence, CANONICAL_FAMILIES[family])
            for family in FAMILY_ORDER
        }
        for left, right in combinations(FAMILY_ORDER, 2):
            js_value = js_divergence(posteriors[left], posteriors[right])
            pair_rows.append({
                'graph_id': record.graph_id,
                'left_family': left,
                'right_family': right,
                'js_divergence': round(js_value, 6),
            })
            summary[(left, right)].append(js_value)
    pair_summary = [
        {
            'left_family': left,
            'right_family': right,
            'mean_js_on_selected_panel': round(sum(values) / len(values), 6),
            'min_js_on_selected_panel': round(min(values), 6),
            'max_js_on_selected_panel': round(max(values), 6),
        }
        for (left, right), values in sorted(summary.items())
    ]
    return {
        'selected_panel_size': len(selected_records),
        'canonical_family_settings': CANONICAL_FAMILIES,
        'pair_rows': pair_rows,
        'pair_summary': pair_summary,
    }


def choose_exemplar_graph(records):
    candidates = [record for record in records if record.descriptor['S2_count'] > 0]
    if not candidates:
        return max(records, key=lambda item: item.high_kl_A0_to_A4)
    return max(candidates, key=lambda item: (item.descriptor['D2_neighbor_coupling'], item.high_kl_A0_to_A4))


def draw_weighted_graph(ax, record, edge_strengths, title):
    positions = graph_node_positions(record.adjacency, 0)
    observed_labels = {node: COLOR_LABELS[color] for node, color in enumerate(record.preferred_color_template, start=1)}
    max_strength = max(edge_strengths.values()) if edge_strengths else 1.0
    for left, right in record.edges:
        edge = (left, right)
        if edge not in edge_strengths:
            edge = (right, left)
        strength = edge_strengths.get(edge, 0.0)
        if strength <= 0.0:
            continue
        linewidth = 0.8 + 3.0 * strength / max_strength
        alpha = min(0.95, 0.25 + 0.7 * strength / max_strength)
        ax.plot(
            [positions[left][0], positions[right][0]],
            [positions[left][1], positions[right][1]],
            color='#4d4d4d',
            linewidth=linewidth,
            alpha=alpha,
            zorder=1,
        )
    plot_graph(ax, record.adjacency, target=0, observed_state_labels=observed_labels, title=title)


def draw_transformed_graph(ax, record, edge_strengths, title):
    positions = graph_node_positions(record.adjacency, 0)
    observed_labels = {node: COLOR_LABELS[color] for node, color in enumerate(record.preferred_color_template, start=1)}
    max_strength = max(edge_strengths.values()) if edge_strengths else 1.0
    for (left, right), strength in edge_strengths.items():
        linewidth = 0.8 + 3.0 * strength / max_strength
        alpha = min(0.95, 0.25 + 0.7 * strength / max_strength)
        ax.plot(
            [positions[left][0], positions[right][0]],
            [positions[left][1], positions[right][1]],
            [ ],
        )
        ax.plot(
            [positions[left][0], positions[right][0]],
            [positions[left][1], positions[right][1]],
            color='#4d4d4d',
            linewidth=linewidth,
            alpha=alpha,
            zorder=1,
        )
    for node, (x_pos, y_pos) in positions.items():
        fill = '#ffffff'
        label = f'{node}'
        if node in observed_labels:
            fill = {'R': '#d73027', 'G': '#1a9850', 'B': '#4575b4'}[observed_labels[node]]
            label = f'{node}\n{observed_labels[node]}'
        circle_kwargs = {'linewidth': 1.5 if node == 0 else 1.0, 'edgecolor': 'black', 'facecolor': fill, 'zorder': 3}
        patch = plt.Circle((x_pos, y_pos), radius=0.16, **circle_kwargs)
        ax.add_patch(patch)
        ax.text(x_pos, y_pos, label, ha='center', va='center', fontsize=8, color='white' if fill != '#ffffff' else 'black', zorder=4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=10)


def plot_schematic(records, output_path: Path) -> dict[str, object]:
    exemplar = choose_exemplar_graph(records)
    exact_strengths = edge_strengths_rho(exemplar.adjacency, 0, rho=1.0, beta=4.0)
    attenuated_strengths = edge_strengths_rho(exemplar.adjacency, 0, rho=0.55, beta=4.0)
    star_strengths = edge_strengths_star(exemplar.adjacency, 0, beta=4.0)
    cluster_strengths = edge_strengths_cluster(exemplar.adjacency, 0, beta=4.0)

    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6))
    draw_weighted_graph(axes[0], exemplar, exact_strengths, 'Exact graph')
    draw_weighted_graph(axes[1], exemplar, attenuated_strengths, 'Attenuated true graph')
    draw_transformed_graph(axes[2], exemplar, star_strengths, 'Target-centred star')
    draw_transformed_graph(axes[3], exemplar, cluster_strengths, 'Local cluster / junction-lite')
    fig.suptitle(f'Analysis 4-1 family schematic on exemplar graph {exemplar.graph_id}', fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(output_path)
    plt.close(fig)
    return {
        'exemplar_graph_id': exemplar.graph_id,
        'descriptor': exemplar.descriptor,
    }


def main() -> None:
    analysis_dir = Path(__file__).resolve().parents[1]
    data_dir = analysis_dir / 'code' / 'data'
    figures_dir = analysis_dir / 'figures'
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    records = load_rooted_library()
    specs = family_specifications()
    comparison_rows = [
        {
            'family': row['family'],
            'class': row['class'],
            'graph_preserved_or_rewritten': row['internal_graph_representation'],
            'local_vs_nonlocal_sensitivity': f"D1={row['expected_D1_sensitivity']}; D2={row['expected_D2_sensitivity']}; D3={row['expected_D3_sensitivity']}",
            'computational_simplicity': row['computational_simplicity'],
            'psychological_interpretation': row['psychological_interpretation'],
        }
        for row in specs
    ]
    redundancy = redundancy_assessment()
    readiness = simulation_ready_check(records)
    schematic_meta = plot_schematic(records, figures_dir / 'analysis-4-1_fig1_family_schematic.pdf')

    dump_json(
        data_dir / 'analysis-4-1_taxonomy.json',
        {
            'analysis': '4-1',
            'minimal_family_set': [row['family'] for row in specs],
            'family_specifications': specs,
            'redundancy_assessment': redundancy,
            'simulation_ready_check': readiness,
            'recommendation_for_analysis_4_2': [row['family'] for row in specs],
            'schematic_meta': schematic_meta,
        },
    )
    write_csv_rows(data_dir / 'analysis-4-1_unified_notation.csv', specs)
    write_csv_rows(data_dir / 'analysis-4-1_family_comparison.csv', comparison_rows)

    print(f'Wrote {data_dir / "analysis-4-1_taxonomy.json"}')
    print(f'Wrote {data_dir / "analysis-4-1_unified_notation.csv"}')
    print(f'Wrote {data_dir / "analysis-4-1_family_comparison.csv"}')
    print(f'Wrote {figures_dir / "analysis-4-1_fig1_family_schematic.pdf"}')


if __name__ == '__main__':
    main()
