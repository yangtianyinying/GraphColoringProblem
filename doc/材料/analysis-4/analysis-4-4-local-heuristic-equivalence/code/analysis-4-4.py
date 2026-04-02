#!/usr/bin/env python3
from __future__ import annotations

import json
import math
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
    EVIDENCE_LEVELS,
    belief_profile_bars,
    dump_json,
    family_posterior,
    full_soft_evidence,
    js_divergence,
    load_rooted_library,
    normalize,
    plot_graph,
    write_csv_rows,
)


def pure_local_log_evidence(adjacency, evidence_by_node, beta: float) -> tuple[float, float, float]:
    neighbors = adjacency[0]
    scores = []
    for target_color in range(3):
        score = 0.0
        for neighbor in neighbors:
            probabilities = evidence_by_node[neighbor]
            local_message = sum(
                probabilities[state] * math.exp(-beta * (1 if target_color == state else 0))
                for state in range(3)
            )
            score += math.log(local_message)
        scores.append(score)
    max_score = max(scores)
    unnormalized = [math.exp(score - max_score) for score in scores]
    return normalize(unnormalized)


def weighted_local_log_evidence(adjacency, evidence_by_node, beta: float) -> tuple[float, float, float]:
    neighbors = adjacency[0]
    mean_degree = sum(len(adjacency[node]) for node in neighbors) / max(1, len(neighbors))
    scores = []
    for target_color in range(3):
        score = 0.0
        for neighbor in neighbors:
            probabilities = evidence_by_node[neighbor]
            local_message = sum(
                probabilities[state] * math.exp(-beta * (1 if target_color == state else 0))
                for state in range(3)
            )
            weight = 0.7 + len(adjacency[neighbor]) / max(1.0, mean_degree)
            score += weight * math.log(local_message)
        scores.append(score)
    max_score = max(scores)
    unnormalized = [math.exp(score - max_score) for score in scores]
    return normalize(unnormalized)


def clipped_local_log_evidence(adjacency, evidence_by_node, beta: float) -> tuple[float, float, float]:
    neighbors = adjacency[0]
    scores = []
    for target_color in range(3):
        score = 0.0
        for neighbor in neighbors:
            probabilities = evidence_by_node[neighbor]
            local_message = sum(
                probabilities[state] * math.exp(-beta * (1 if target_color == state else 0))
                for state in range(3)
            )
            score += math.log(local_message)
        scores.append(math.tanh(score))
    max_score = max(scores)
    unnormalized = [math.exp(score - max_score) for score in scores]
    return normalize(unnormalized)


def load_example_condition() -> tuple[str, str]:
    summary_path = ANALYSIS4_ROOT / 'analysis-4-2-family-separability' / 'code' / 'data' / 'analysis-4-2_summary.json'
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding='utf-8'))
        row = max(summary['reduced_panel'], key=lambda item: float(item['panel_score']))
        return row['graph_id'], row['evidence_level']
    return 'RG112', 'high'


def plot_results(scatter_points, example_payload, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0))

    x_values = [point['m0_p_R'] for point in scatter_points]
    y_values = [point['pure_p_R'] for point in scatter_points]
    axes[0].scatter(x_values, y_values, alpha=0.55, s=16)
    axes[0].plot([0, 1], [0, 1], color='black', linewidth=1.0, linestyle='--')
    axes[0].set_xlabel('M_0 P(R)')
    axes[0].set_ylabel('Pure heuristic P(R)')
    axes[0].set_title('Pure local log-evidence equals M_0')

    variant_labels = ['pure', 'weighted', 'clipped']
    variant_means = [
        example_payload['library_summary']['mean_js_to_M0'][label]
        for label in variant_labels
    ]
    axes[1].bar(range(len(variant_labels)), variant_means, color=['#55a868', '#c44e52', '#8172b2'])
    axes[1].set_xticks(range(len(variant_labels)), variant_labels)
    axes[1].set_ylabel('Mean JS to M_0 across library')
    axes[1].set_title('Only distorted variants depart from M_0')

    belief_profile_bars(
        axes[2],
        [
            ('M_0', tuple(example_payload['example_posteriors']['M_0'])),
            ('pure', tuple(example_payload['example_posteriors']['pure'])),
            ('weighted', tuple(example_payload['example_posteriors']['weighted'])),
            ('clipped', tuple(example_payload['example_posteriors']['clipped'])),
        ],
        f"Example condition {example_payload['example_condition']['graph_id']} | {example_payload['example_condition']['evidence_level']}",
    )
    axes[2].legend(fontsize=7)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def main() -> None:
    analysis_dir = Path(__file__).resolve().parents[1]
    data_dir = analysis_dir / 'code' / 'data'
    figures_dir = analysis_dir / 'figures'
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    records = load_rooted_library()
    example_graph_id, example_level = load_example_condition()

    simulation_rows = []
    scatter_points = []
    max_abs_difference = 0.0
    js_by_variant = {'pure': [], 'weighted': [], 'clipped': []}
    example_posteriors = {}
    example_graph_payload = None

    for record in records:
        for level_name in EVIDENCE_LEVELS:
            evidence = full_soft_evidence(record, level_name)
            m0_posterior = family_posterior(record.adjacency, 0, evidence, CANONICAL_FAMILIES['M_0'])
            pure_posterior = pure_local_log_evidence(record.adjacency, evidence, beta=CANONICAL_FAMILIES['M_0']['beta'])
            weighted_posterior = weighted_local_log_evidence(record.adjacency, evidence, beta=CANONICAL_FAMILIES['M_0']['beta'])
            clipped_posterior = clipped_local_log_evidence(record.adjacency, evidence, beta=CANONICAL_FAMILIES['M_0']['beta'])

            diff = max(abs(left - right) for left, right in zip(m0_posterior, pure_posterior))
            max_abs_difference = max(max_abs_difference, diff)
            scatter_points.append(
                {
                    'graph_id': record.graph_id,
                    'evidence_level': level_name,
                    'm0_p_R': round(m0_posterior[0], 6),
                    'pure_p_R': round(pure_posterior[0], 6),
                }
            )

            for variant_name, posterior in [('pure', pure_posterior), ('weighted', weighted_posterior), ('clipped', clipped_posterior)]:
                js_value = js_divergence(m0_posterior, posterior)
                js_by_variant[variant_name].append(js_value)
                simulation_rows.append(
                    {
                        'graph_id': record.graph_id,
                        'evidence_level': level_name,
                        'variant': variant_name,
                        'js_to_M0': round(js_value, 10),
                        'p_R': round(posterior[0], 6),
                        'p_G': round(posterior[1], 6),
                        'p_B': round(posterior[2], 6),
                    }
                )

            if record.graph_id == example_graph_id and level_name == example_level:
                example_posteriors = {
                    'M_0': [round(value, 6) for value in m0_posterior],
                    'pure': [round(value, 6) for value in pure_posterior],
                    'weighted': [round(value, 6) for value in weighted_posterior],
                    'clipped': [round(value, 6) for value in clipped_posterior],
                }
                example_graph_payload = {
                    'graph_id': record.graph_id,
                    'evidence_level': level_name,
                    'adjacency': record.adjacency,
                    'observed_labels': {node: color for node, color in enumerate(record.preferred_colors.values(), start=1)},
                }

    summary = {
        'analysis': '4-4',
        'formal_heuristic_definition': {
            'inputs': 'soft evidence on direct neighbours of the target only',
            'score': 'score(x_i=c) = sum_{j in N(i)} log sum_{x_j} lambda_j(x_j) exp[-beta_edge 1(c = x_j)]',
            'readout': 'posterior(x_i=c) = softmax(score(c))',
        },
        'equivalence_statement': 'Under standard pairwise factor semantics with direct neighbours only and exponentiate-normalise readout, the heuristic is exactly M_0 written in log space.',
        'max_abs_difference_between_M0_and_pure_heuristic': round(max_abs_difference, 12),
        'library_summary': {
            'mean_js_to_M0': {name: round(sum(values) / len(values), 10) for name, values in js_by_variant.items()},
            'max_js_to_M0': {name: round(max(values), 10) for name, values in js_by_variant.items()},
        },
        'distortion_taxonomy': [
            {'distortion': 'neighbour-specific arbitrary weights', 'example_variant': 'weighted', 'status': 'distinct from M_0'},
            {'distortion': 'score clipping / saturation before normalisation', 'example_variant': 'clipped', 'status': 'distinct from M_0'},
            {'distortion': 'post-hoc response transform', 'example_variant': 'not simulated here', 'status': 'would be inference-plus-response model, not a new inference family'},
        ],
        'taxonomy_recommendation': 'Do not retain the pure local log-evidence rule as a separate family. Retain only response-distorted or otherwise non-factorisable local summary variants as optional heuristic baselines.',
        'example_condition': {'graph_id': example_graph_id, 'evidence_level': example_level},
        'example_posteriors': example_posteriors,
    }

    plot_results(scatter_points, summary, figures_dir / 'analysis-4-4_fig1_equivalence_check.pdf')

    if example_graph_payload is not None:
        fig, ax = plt.subplots(figsize=(3.4, 3.2))
        plot_graph(
            ax,
            example_graph_payload['adjacency'],
            target=0,
            observed_state_labels=example_graph_payload['observed_labels'],
            title=f"Example graph {example_graph_id}",
        )
        fig.tight_layout()
        fig.savefig(figures_dir / 'analysis-4-4_fig2_example_graph.pdf')
        plt.close(fig)

    write_csv_rows(data_dir / 'analysis-4-4_simulation_comparison.csv', simulation_rows)
    dump_json(data_dir / 'analysis-4-4_equivalence.json', summary)

    print(f'Wrote {data_dir / "analysis-4-4_simulation_comparison.csv"}')
    print(f'Wrote {data_dir / "analysis-4-4_equivalence.json"}')
    print(f'Wrote {figures_dir / "analysis-4-4_fig1_equivalence_check.pdf"}')
    if example_graph_payload is not None:
        print(f'Wrote {figures_dir / "analysis-4-4_fig2_example_graph.pdf"}')


if __name__ == '__main__':
    main()
