#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import json
import math
import random
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
    FAMILY_ORDER,
    dump_json,
    entropy,
    evidence_distribution,
    family_posterior,
    js_divergence,
    load_rooted_library,
    plot_graph,
    write_csv_rows,
)

CHOICE_TEMPERATURE = 6.0
RECOVERY_CONCENTRATION = 40.0
RECOVERY_REPEATS = 20


def softmax(values):
    maximum = max(values)
    weights = [math.exp(value - maximum) for value in values]
    total = sum(weights)
    return [value / total for value in weights]



def sample_dirichlet(probabilities, concentration: float, rng: random.Random):
    gammas = [rng.gammavariate(max(probability * concentration, 1e-3), 1.0) for probability in probabilities]
    total = sum(gammas)
    return tuple(value / total for value in gammas)



def load_design_panel():
    summary_path = ANALYSIS4_ROOT / 'analysis-4-2-family-separability' / 'code' / 'data' / 'analysis-4-2_summary.json'
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding='utf-8'))
        return [(row['graph_id'], row['evidence_level']) for row in summary['reduced_panel']]
    return [('RG036', 'high'), ('RG100', 'high'), ('RG112', 'high')]



def choose_observed_nodes(record) -> list[int]:
    node_info = []
    for node in range(1, record.n_nodes):
        preferred_color = record.preferred_color_template[node - 1]
        node_info.append((node, len(record.adjacency[node]), preferred_color))
    node_info.sort(key=lambda item: (-item[1], item[0]))
    observed = [node_info[0][0]]
    first_color = node_info[0][2]
    alternative = next((node for node, _, color in node_info[1:] if color != first_color), None)
    if alternative is None:
        alternative = node_info[1][0]
    observed.append(alternative)
    return sorted(observed)



def build_partial_evidence(record, observed_nodes: list[int], level_name: str):
    level = EVIDENCE_LEVELS[level_name]
    return {
        node: evidence_distribution(level, record.preferred_color_template[node - 1])
        for node in observed_nodes
    }



def family_target_posteriors(record, evidence_by_node, candidate_targets):
    payload = {}
    for family in FAMILY_ORDER:
        target_posteriors = {}
        certainty_scores = []
        for target in candidate_targets:
            posterior = family_posterior(record.adjacency, target, evidence_by_node, CANONICAL_FAMILIES[family])
            target_posteriors[target] = posterior
            certainty_scores.append(math.log(3.0) - entropy(posterior))
        choice_distribution = softmax([CHOICE_TEMPERATURE * value for value in certainty_scores])
        payload[family] = {
            'target_posteriors': target_posteriors,
            'choice_distribution': {target: round(probability, 6) for target, probability in zip(candidate_targets, choice_distribution)},
        }
    return payload



def choice_vector(candidate_targets, choice_distribution, n_nodes):
    vector = [0.0] * n_nodes
    for target in candidate_targets:
        vector[target] = choice_distribution[target]
    return vector



def combined_divergence(candidate_targets, info_left, info_right):
    selection_left = [info_left['choice_distribution'][target] for target in candidate_targets]
    selection_right = [info_right['choice_distribution'][target] for target in candidate_targets]
    selection_js = js_divergence(selection_left, selection_right)
    expected_belief_js = 0.0
    for target in candidate_targets:
        weight = 0.5 * (info_left['choice_distribution'][target] + info_right['choice_distribution'][target])
        expected_belief_js += weight * js_divergence(info_left['target_posteriors'][target], info_right['target_posteriors'][target])
    return selection_js + expected_belief_js, selection_js, expected_belief_js



def build_condition_payload(records_by_id):
    condition_payload = {}
    choice_rows = []
    design_rows = []
    panel = load_design_panel()
    for graph_id, level_name in panel:
        record = records_by_id[graph_id]
        observed_nodes = choose_observed_nodes(record)
        evidence_by_node = build_partial_evidence(record, observed_nodes, level_name)
        candidate_targets = [node for node in range(record.n_nodes) if node not in observed_nodes]
        family_payload = family_target_posteriors(record, evidence_by_node, candidate_targets)
        condition_payload[(graph_id, level_name)] = {
            'record': record,
            'observed_nodes': observed_nodes,
            'candidate_targets': candidate_targets,
            'family_payload': family_payload,
        }
        for family in FAMILY_ORDER:
            choice_vector_payload = family_payload[family]['choice_distribution']
            for target in candidate_targets:
                choice_rows.append(
                    {
                        'graph_id': graph_id,
                        'evidence_level': level_name,
                        'family': family,
                        'target': target,
                        'choice_probability': choice_vector_payload[target],
                        'belief_p_R': round(family_payload[family]['target_posteriors'][target][0], 6),
                        'belief_p_G': round(family_payload[family]['target_posteriors'][target][1], 6),
                        'belief_p_B': round(family_payload[family]['target_posteriors'][target][2], 6),
                    }
                )
        for left_index, left_family in enumerate(FAMILY_ORDER):
            for right_family in FAMILY_ORDER[left_index + 1 :]:
                combined, selection_js, weighted_belief_js = combined_divergence(
                    candidate_targets,
                    family_payload[left_family],
                    family_payload[right_family],
                )
                belief_only_js = js_divergence(
                    family_payload[left_family]['target_posteriors'][0],
                    family_payload[right_family]['target_posteriors'][0],
                )
                design_rows.append(
                    {
                        'graph_id': graph_id,
                        'evidence_level': level_name,
                        'left_family': left_family,
                        'right_family': right_family,
                        'belief_only_js': round(belief_only_js, 6),
                        'selection_only_js': round(selection_js, 6),
                        'combined_js': round(combined, 6),
                        'weighted_belief_js': round(weighted_belief_js, 6),
                    }
                )
    return condition_payload, choice_rows, design_rows



def sample_target(targets, choice_distribution, rng: random.Random):
    threshold = rng.random()
    cumulative = 0.0
    for target in targets:
        cumulative += choice_distribution[target]
        if threshold <= cumulative:
            return target
    return targets[-1]



def recovery_simulation(condition_payload):
    rng = random.Random(44)
    confusion = {
        'belief_only': [[0 for _ in FAMILY_ORDER] for _ in FAMILY_ORDER],
        'selection_only': [[0 for _ in FAMILY_ORDER] for _ in FAMILY_ORDER],
        'combined': [[0 for _ in FAMILY_ORDER] for _ in FAMILY_ORDER],
    }
    for generating_index, generating_family in enumerate(FAMILY_ORDER):
        for _ in range(RECOVERY_REPEATS):
            scores = {design: [0.0 for _ in FAMILY_ORDER] for design in confusion}
            for (graph_id, level_name), payload in condition_payload.items():
                targets = payload['candidate_targets']
                family_info = payload['family_payload'][generating_family]
                chosen_target = sample_target(targets, family_info['choice_distribution'], rng)
                belief_sample = sample_dirichlet(family_info['target_posteriors'][chosen_target], RECOVERY_CONCENTRATION, rng)
                root_belief_sample = sample_dirichlet(family_info['target_posteriors'][0], RECOVERY_CONCENTRATION, rng)
                for candidate_index, candidate_family in enumerate(FAMILY_ORDER):
                    candidate_info = payload['family_payload'][candidate_family]
                    scores['belief_only'][candidate_index] += js_divergence(root_belief_sample, candidate_info['target_posteriors'][0])
                    scores['selection_only'][candidate_index] += -math.log(candidate_info['choice_distribution'][chosen_target] + 1e-12)
                    scores['combined'][candidate_index] += -math.log(candidate_info['choice_distribution'][chosen_target] + 1e-12)
                    scores['combined'][candidate_index] += js_divergence(belief_sample, candidate_info['target_posteriors'][chosen_target])
            for design in confusion:
                best_index = min(range(len(FAMILY_ORDER)), key=lambda index: scores[design][index])
                confusion[design][generating_index][best_index] += 1
    return {
        design: [
            [round(value / RECOVERY_REPEATS, 6) for value in row]
            for row in matrix
        ]
        for design, matrix in confusion.items()
    }



def design_summary_rows(design_rows):
    grouped = defaultdict(list)
    for row in design_rows:
        grouped[(row['left_family'], row['right_family'])].append(row)
    rows = []
    for (left_family, right_family), items in grouped.items():
        rows.append(
            {
                'left_family': left_family,
                'right_family': right_family,
                'mean_belief_only_js': round(sum(float(item['belief_only_js']) for item in items) / len(items), 6),
                'mean_selection_only_js': round(sum(float(item['selection_only_js']) for item in items) / len(items), 6),
                'mean_combined_js': round(sum(float(item['combined_js']) for item in items) / len(items), 6),
            }
        )
    return rows



def plot_choice_distributions(condition_payload, output_path: Path) -> None:
    representative = []
    seen_d3 = set()
    for payload in condition_payload.values():
        d3 = payload['record'].descriptor['D3_remote_class']
        if d3 in seen_d3:
            continue
        representative.append(payload)
        seen_d3.add(d3)
    fig, axes = plt.subplots(len(representative), 1, figsize=(10.5, 3.2 * len(representative)))
    if len(representative) == 1:
        axes = [axes]
    for ax, payload in zip(axes, representative):
        targets = payload['candidate_targets']
        width = 0.12
        offsets = [(index - (len(FAMILY_ORDER) - 1) / 2.0) * width for index in range(len(FAMILY_ORDER))]
        for offset, family in zip(offsets, FAMILY_ORDER):
            probabilities = [payload['family_payload'][family]['choice_distribution'][target] for target in targets]
            ax.bar([target + offset for target in targets], probabilities, width=width, label=family)
        descriptor = payload['record'].descriptor
        ax.set_title(f"{payload['record'].graph_id} | D3={descriptor['D3_remote_class']} | observed={payload['observed_nodes']}")
        ax.set_xticks(targets, [str(target) for target in targets])
        ax.set_xlabel('Candidate target node')
        ax.set_ylabel('Choice probability')
    axes[0].legend(fontsize=7, ncol=3)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)



def plot_design_comparison(summary_rows, confusion, output_path: Path) -> None:
    mean_belief = sum(row['mean_belief_only_js'] for row in summary_rows) / len(summary_rows)
    mean_selection = sum(row['mean_selection_only_js'] for row in summary_rows) / len(summary_rows)
    mean_combined = sum(row['mean_combined_js'] for row in summary_rows) / len(summary_rows)

    def mean_diagonal(matrix):
        return sum(matrix[index][index] for index in range(len(matrix))) / len(matrix)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0))
    axes[0].bar(['belief-only', 'selection-only', 'combined'], [mean_belief, mean_selection, mean_combined], color=['#4c72b0', '#55a868', '#c44e52'])
    axes[0].set_ylabel('Mean pairwise separation')
    axes[0].set_title('Average family separation by design')

    axes[1].bar(
        ['belief-only', 'selection-only', 'combined'],
        [mean_diagonal(confusion['belief_only']), mean_diagonal(confusion['selection_only']), mean_diagonal(confusion['combined'])],
        color=['#4c72b0', '#55a868', '#c44e52'],
    )
    axes[1].set_ylabel('Mean recovery diagonal')
    axes[1].set_ylim(0.0, 1.0)
    axes[1].set_title('Synthetic recovery by design')
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)



def plot_example_task(condition_payload, output_path: Path) -> None:
    payload = next(iter(condition_payload.values()))
    observed_labels = {
        node: COLOR_LABELS[payload['record'].preferred_color_template[node - 1]]
        for node in payload['observed_nodes']
    }
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    plot_graph(
        ax,
        payload['record'].adjacency,
        target=0,
        observed_state_labels=observed_labels,
        title=f"Example fixed-evidence selection task: {payload['record'].graph_id}",
    )
    for target in payload['candidate_targets']:
        x_pos, y_pos = ax.texts[target].get_position()
        ax.text(x_pos, y_pos - 0.32, 'candidate', ha='center', va='center', fontsize=7, color='#333333')
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
    records_by_id = {record.graph_id: record for record in records}
    condition_payload, choice_rows, design_rows = build_condition_payload(records_by_id)
    summary_rows = design_summary_rows(design_rows)
    confusion = recovery_simulation(condition_payload)

    plot_choice_distributions(condition_payload, figures_dir / 'analysis-4-5_fig1_choice_distributions.pdf')
    plot_design_comparison(summary_rows, confusion, figures_dir / 'analysis-4-5_fig2_design_comparison.pdf')
    plot_example_task(condition_payload, figures_dir / 'analysis-4-5_fig3_example_task.pdf')

    write_csv_rows(data_dir / 'analysis-4-5_choice_distributions.csv', choice_rows)
    write_csv_rows(data_dir / 'analysis-4-5_design_metrics.csv', design_rows)
    write_csv_rows(data_dir / 'analysis-4-5_design_summary.csv', summary_rows)
    dump_json(
        data_dir / 'analysis-4-5_summary.json',
        {
            'analysis': '4-5',
            'design_variants': [
                {'variant': 'forced-target belief only', 'behavioural_output': 'belief on a fixed target node', 'role': 'baseline'},
                {'variant': 'selection only', 'behavioural_output': 'first chosen node under fixed evidence', 'role': 'proxy for free-query order'},
                {'variant': 'choose-node then report-belief', 'behavioural_output': 'node choice plus belief on the chosen node', 'role': 'primary candidate design'},
            ],
            'selection_policy_summary': [
                {'family': 'M_exact', 'policy': 'choose the node with the highest certainty under exact inference on the true graph'},
                {'family': 'M_0', 'policy': 'choose the node with the highest certainty under strictly local inference'},
                {'family': 'M_rho', 'policy': 'choose the node with the highest certainty under attenuated graph inference'},
                {'family': 'M_rho,beta', 'policy': 'choose the node with the highest certainty under attenuated inference with flexible beta'},
                {'family': 'M_star', 'policy': 'choose the node that is easiest under the star-rewrite posterior'},
                {'family': 'M_cluster', 'policy': 'choose the node that is easiest under the local-cluster posterior'},
            ],
            'condition_keys': [f'{graph_id}_{level_name}' for graph_id, level_name in condition_payload],
            'mean_pairwise_separation': {
                'belief_only': round(sum(row['mean_belief_only_js'] for row in summary_rows) / len(summary_rows), 6),
                'selection_only': round(sum(row['mean_selection_only_js'] for row in summary_rows) / len(summary_rows), 6),
                'combined': round(sum(row['mean_combined_js'] for row in summary_rows) / len(summary_rows), 6),
            },
            'recovery_confusion': confusion,
            'design_recommendation': 'The fixed-evidence choose-node-then-report-belief design is the cleanest richer extension. In this simulation it substantially increases average pairwise family separation relative to belief-only, although under the present simple noise model its recovery advantage is more modest. It is best treated as a targeted extension rather than a full replacement for forced-target trials.',
        },
    )

    print(f'Wrote {data_dir / "analysis-4-5_choice_distributions.csv"}')
    print(f'Wrote {data_dir / "analysis-4-5_design_metrics.csv"}')
    print(f'Wrote {data_dir / "analysis-4-5_design_summary.csv"}')
    print(f'Wrote {data_dir / "analysis-4-5_summary.json"}')
    print(f'Wrote {figures_dir / "analysis-4-5_fig1_choice_distributions.pdf"}')
    print(f'Wrote {figures_dir / "analysis-4-5_fig2_design_comparison.pdf"}')
    print(f'Wrote {figures_dir / "analysis-4-5_fig3_example_task.pdf"}')


if __name__ == '__main__':
    main()
