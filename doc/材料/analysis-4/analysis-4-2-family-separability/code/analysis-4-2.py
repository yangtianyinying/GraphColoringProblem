#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
import math
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec

ANALYSIS4_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ANALYSIS4_ROOT))

from common.analysis4_common import (
    CANONICAL_FAMILIES,
    EVIDENCE_LEVELS,
    FAMILY_ORDER,
    belief_profile_bars,
    condition_slug,
    dump_json,
    family_posterior,
    full_soft_evidence,
    heatmap,
    js_divergence,
    load_rooted_library,
    load_selected_panel_ids,
    plot_graph,
    total_variation,
    write_csv_rows,
)

RECOVERY_CONCENTRATION = 30.0
RECOVERY_REPEATS = 8
KEY_PAIR_COLUMNS = {
    'exact_vs_rho_js': ('M_exact', 'M_rho'),
    'rho_vs_star_js': ('M_rho', 'M_star'),
    'star_vs_cluster_js': ('M_star', 'M_cluster'),
    'exact_vs_star_js': ('M_exact', 'M_star'),
    'cluster_vs_exact_js': ('M_cluster', 'M_exact'),
}


def sample_dirichlet(probabilities: tuple[float, float, float], concentration: float, rng: random.Random) -> tuple[float, float, float]:
    gammas = [rng.gammavariate(max(probability * concentration, 1e-3), 1.0) for probability in probabilities]
    total = sum(gammas)
    return tuple(value / total for value in gammas)


def summarize_descriptor(rows: list[dict[str, object]], dimension: str) -> list[dict[str, object]]:
    grouped: dict[object, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[row[dimension]].append(row)
    summary = []
    for value in sorted(grouped, key=lambda item: str(item)):
        group_rows = grouped[value]
        summary.append(
            {
                'dimension': dimension,
                'value': value,
                'count': len(group_rows),
                'mean_exact_vs_rho_js': round(sum(float(row['exact_vs_rho_js']) for row in group_rows) / len(group_rows), 6),
                'mean_rho_vs_star_js': round(sum(float(row['rho_vs_star_js']) for row in group_rows) / len(group_rows), 6),
                'mean_star_vs_cluster_js': round(sum(float(row['star_vs_cluster_js']) for row in group_rows) / len(group_rows), 6),
                'mean_mean_js_all_pairs': round(sum(float(row['mean_js_all_pairs']) for row in group_rows) / len(group_rows), 6),
            }
        )
    return summary


def select_reduced_panel(condition_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    chosen: list[dict[str, object]] = []
    seen = set()

    def add_best(sorted_rows: list[dict[str, object]]) -> None:
        for row in sorted_rows:
            key = (row['graph_id'], row['evidence_level'])
            if key in seen:
                continue
            chosen.append(row)
            seen.add(key)
            return

    for column in ['exact_vs_rho_js', 'rho_vs_star_js', 'star_vs_cluster_js', 'M0_vs_nonlocal_mean_js']:
        add_best(sorted(condition_rows, key=lambda item: float(item[column]), reverse=True))

    d3_values = {row['D3_remote_class'] for row in chosen}
    for d3_value in sorted({row['D3_remote_class'] for row in condition_rows} - d3_values):
        add_best(
            sorted(
                [row for row in condition_rows if row['D3_remote_class'] == d3_value],
                key=lambda item: float(item['mean_js_all_pairs']),
                reverse=True,
            )
        )

    for row in sorted(condition_rows, key=lambda item: float(item['mean_js_all_pairs']), reverse=True):
        key = (row['graph_id'], row['evidence_level'])
        if key in seen:
            continue
        chosen.append(row)
        seen.add(key)
        if len(chosen) >= 6:
            break
    return chosen[:6]


def find_matched_pair(condition_rows: list[dict[str, object]], score_column: str) -> dict[str, object] | None:
    grouped: dict[tuple[int, int], list[dict[str, object]]] = defaultdict(list)
    for row in condition_rows:
        if row['evidence_level'] != 'high':
            continue
        grouped[(row['D1_target_degree'], row['D2_neighbor_coupling'])].append(row)
    best: dict[str, object] | None = None
    for key, rows in grouped.items():
        if len(rows) < 2:
            continue
        rows = sorted(rows, key=lambda item: str(item['D3_remote_class']))
        for left_index, left in enumerate(rows):
            for right in rows[left_index + 1 :]:
                if left['D3_remote_class'] == right['D3_remote_class']:
                    continue
                delta = abs(float(left[score_column]) - float(right[score_column]))
                candidate = {
                    'score_column': score_column,
                    'match_key': {'D1_target_degree': key[0], 'D2_neighbor_coupling': key[1]},
                    'left_condition': left,
                    'right_condition': right,
                    'delta': round(delta, 6),
                }
                if best is None or candidate['delta'] > best['delta']:
                    best = candidate
    return best


def plot_condition_panels(selected_rows: list[dict[str, object]], posteriors_by_condition, records_by_id, output_path: Path) -> None:
    figure = plt.figure(figsize=(14, 10))
    outer = GridSpec(2, 2, figure=figure, wspace=0.25, hspace=0.35)
    for panel_index, row in enumerate(selected_rows[:4]):
        subgrid = outer[panel_index].subgridspec(3, 1, height_ratios=[1.0, 1.2, 0.9], hspace=0.25)
        ax_graph = figure.add_subplot(subgrid[0])
        ax_heat = figure.add_subplot(subgrid[1])
        ax_bars = figure.add_subplot(subgrid[2])
        record = records_by_id[row['graph_id']]
        observed_labels = {node: color for node, color in enumerate(record.preferred_colors.values(), start=1)}
        plot_graph(
            ax_graph,
            record.adjacency,
            target=0,
            observed_state_labels=observed_labels,
            title=f"{row['graph_id']} | {row['evidence_level']} | D1={row['D1_target_degree']} D2={row['D2_neighbor_coupling']} {row['D3_remote_class']}",
        )
        condition_key = condition_slug(row['graph_id'], row['evidence_level'])
        posteriors = posteriors_by_condition[condition_key]
        matrix = [
            [js_divergence(posteriors[left], posteriors[right]) for right in FAMILY_ORDER]
            for left in FAMILY_ORDER
        ]
        heatmap(ax_heat, matrix, list(FAMILY_ORDER), 'Family JS heatmap')
        belief_profile_bars(ax_bars, [(family, posteriors[family]) for family in FAMILY_ORDER], 'Target belief profiles')
        ax_bars.legend(fontsize=7, ncol=3, loc='upper right')
    figure.suptitle('Analysis 4-2 condition-specific family diagnostics', fontsize=13)
    figure.tight_layout(rect=[0, 0, 1, 0.97])
    figure.savefig(output_path)
    plt.close(figure)


def plot_global_confusion(avg_js_matrix, recovery_matrix, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    heatmap(axes[0], avg_js_matrix, list(FAMILY_ORDER), 'Average JS across full library')
    heatmap(axes[1], recovery_matrix, list(FAMILY_ORDER), 'Noisy synthetic family recovery')
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_descriptor_linkage(descriptor_summaries: dict[str, list[dict[str, object]]], output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    pair_columns = [
        ('mean_exact_vs_rho_js', 'M_exact vs M_rho'),
        ('mean_rho_vs_star_js', 'M_rho vs M_star'),
        ('mean_star_vs_cluster_js', 'M_star vs M_cluster'),
    ]
    for axis, dimension in zip(axes, ['D1_target_degree', 'D2_neighbor_coupling', 'D3_remote_class']):
        rows = descriptor_summaries[dimension]
        x_labels = [str(row['value']) for row in rows]
        for column, label in pair_columns:
            axis.plot(x_labels, [row[column] for row in rows], marker='o', label=label)
        axis.set_title(dimension)
        axis.set_ylabel('Mean JS')
        axis.tick_params(axis='x', rotation=25)
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_reduced_panel_summary(reduced_panel: list[dict[str, object]], output_path: Path) -> None:
    labels = [f"{row['graph_id']}\n{row['evidence_level']}" for row in reduced_panel]
    scores = [float(row['panel_score']) for row in reduced_panel]
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    bars = ax.bar(range(len(reduced_panel)), scores, color='#4c72b0')
    ax.set_xticks(range(len(reduced_panel)), labels)
    ax.set_ylabel('Panel score')
    ax.set_title('Recommended reduced stimulus panel')
    for bar, row in zip(bars, reduced_panel):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"D1={row['D1_target_degree']}\nD2={row['D2_neighbor_coupling']}", ha='center', va='bottom', fontsize=7)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def pick_main_figure_conditions(reduced_panel: list[dict[str, object]]) -> list[dict[str, object]]:
    chosen: list[dict[str, object]] = []
    seen = set()
    by_d3: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in reduced_panel:
        by_d3[row['D3_remote_class']].append(row)
    for d3_value in sorted(by_d3):
        row = max(by_d3[d3_value], key=lambda item: float(item['panel_score']))
        chosen.append(row)
        seen.add((row['graph_id'], row['evidence_level']))
    for row in sorted(reduced_panel, key=lambda item: float(item['panel_score']), reverse=True):
        key = (row['graph_id'], row['evidence_level'])
        if key in seen:
            continue
        chosen.append(row)
        if len(chosen) >= 4:
            break
    return chosen[:4]


def main() -> None:
    analysis_dir = Path(__file__).resolve().parents[1]
    data_dir = analysis_dir / 'code' / 'data'
    figures_dir = analysis_dir / 'figures'
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(42)
    records = load_rooted_library()
    selected_ids = load_selected_panel_ids()
    records_by_id = {record.graph_id: record for record in records}

    condition_rows: list[dict[str, object]] = []
    pair_rows: list[dict[str, object]] = []
    posterior_rows: list[dict[str, object]] = []
    posteriors_by_condition: dict[str, dict[str, tuple[float, float, float]]] = {}

    js_matrix_totals = [[0.0 for _ in FAMILY_ORDER] for _ in FAMILY_ORDER]
    confusion_counts = [[0 for _ in FAMILY_ORDER] for _ in FAMILY_ORDER]
    condition_count = 0

    for record in records:
        for level_name in EVIDENCE_LEVELS:
            evidence = full_soft_evidence(record, level_name)
            family_posteriors = {
                family: family_posterior(record.adjacency, 0, evidence, CANONICAL_FAMILIES[family])
                for family in FAMILY_ORDER
            }
            key = condition_slug(record.graph_id, level_name)
            posteriors_by_condition[key] = family_posteriors

            for family in FAMILY_ORDER:
                posterior_rows.append(
                    {
                        'graph_id': record.graph_id,
                        'evidence_level': level_name,
                        'family': family,
                        'p_R': round(family_posteriors[family][0], 6),
                        'p_G': round(family_posteriors[family][1], 6),
                        'p_B': round(family_posteriors[family][2], 6),
                    }
                )

            pair_metrics = {}
            all_js = []
            all_tv = []
            for left_index, left_family in enumerate(FAMILY_ORDER):
                for right_index, right_family in enumerate(FAMILY_ORDER):
                    js_value = js_divergence(family_posteriors[left_family], family_posteriors[right_family])
                    tv_value = total_variation(family_posteriors[left_family], family_posteriors[right_family])
                    js_matrix_totals[left_index][right_index] += js_value
                    if left_index < right_index:
                        pair_rows.append(
                            {
                                'graph_id': record.graph_id,
                                'evidence_level': level_name,
                                'left_family': left_family,
                                'right_family': right_family,
                                'js_divergence': round(js_value, 6),
                                'total_variation': round(tv_value, 6),
                                'D1_target_degree': record.descriptor['D1_target_degree'],
                                'D2_neighbor_coupling': record.descriptor['D2_neighbor_coupling'],
                                'D3_remote_class': record.descriptor['D3_remote_class'],
                            }
                        )
                        all_js.append(js_value)
                        all_tv.append(tv_value)
                        pair_metrics[(left_family, right_family)] = js_value
                        pair_metrics[(right_family, left_family)] = js_value
            condition_count += 1

            for generating_index, generating_family in enumerate(FAMILY_ORDER):
                generating_posterior = family_posteriors[generating_family]
                for _ in range(RECOVERY_REPEATS):
                    sampled_response = sample_dirichlet(generating_posterior, RECOVERY_CONCENTRATION, rng)
                    best_index = min(
                        range(len(FAMILY_ORDER)),
                        key=lambda candidate_index: js_divergence(sampled_response, family_posteriors[FAMILY_ORDER[candidate_index]]),
                    )
                    confusion_counts[generating_index][best_index] += 1

            m0_vs_nonlocal = [
                pair_metrics[('M_0', candidate)]
                for candidate in ['M_exact', 'M_rho', 'M_rho,beta', 'M_star', 'M_cluster']
            ]
            condition_rows.append(
                {
                    'graph_id': record.graph_id,
                    'evidence_level': level_name,
                    'selected_in_analysis_3': record.graph_id in selected_ids,
                    'n_nodes': record.n_nodes,
                    'D1_target_degree': record.descriptor['D1_target_degree'],
                    'D2_neighbor_coupling': record.descriptor['D2_neighbor_coupling'],
                    'D3_remote_class': record.descriptor['D3_remote_class'],
                    'S2_count': record.descriptor['S2_count'],
                    'e12': record.descriptor['e12'],
                    'e22': record.descriptor['e22'],
                    'radius': record.descriptor['radius'],
                    'mean_js_all_pairs': round(sum(all_js) / len(all_js), 6),
                    'min_js_all_pairs': round(min(all_js), 6),
                    'mean_tv_all_pairs': round(sum(all_tv) / len(all_tv), 6),
                    'exact_vs_rho_js': round(pair_metrics[('M_exact', 'M_rho')], 6),
                    'rho_vs_star_js': round(pair_metrics[('M_rho', 'M_star')], 6),
                    'star_vs_cluster_js': round(pair_metrics[('M_star', 'M_cluster')], 6),
                    'exact_vs_star_js': round(pair_metrics[('M_exact', 'M_star')], 6),
                    'cluster_vs_exact_js': round(pair_metrics[('M_cluster', 'M_exact')], 6),
                    'M0_vs_nonlocal_mean_js': round(sum(m0_vs_nonlocal) / len(m0_vs_nonlocal), 6),
                }
            )

    avg_js_matrix = [
        [round(value / condition_count, 6) for value in row]
        for row in js_matrix_totals
    ]
    recovery_matrix = []
    for row in confusion_counts:
        total = sum(row)
        recovery_matrix.append([round(value / total, 6) if total else 0.0 for value in row])

    descriptor_summaries = {
        dimension: summarize_descriptor(condition_rows, dimension)
        for dimension in ['D1_target_degree', 'D2_neighbor_coupling', 'D3_remote_class']
    }

    ranked_conditions = {
        'mean_js_all_pairs': sorted(condition_rows, key=lambda item: float(item['mean_js_all_pairs']), reverse=True)[:20],
        'exact_vs_rho_js': sorted(condition_rows, key=lambda item: float(item['exact_vs_rho_js']), reverse=True)[:20],
        'rho_vs_star_js': sorted(condition_rows, key=lambda item: float(item['rho_vs_star_js']), reverse=True)[:20],
        'star_vs_cluster_js': sorted(condition_rows, key=lambda item: float(item['star_vs_cluster_js']), reverse=True)[:20],
        'M0_vs_nonlocal_mean_js': sorted(condition_rows, key=lambda item: float(item['M0_vs_nonlocal_mean_js']), reverse=True)[:20],
    }

    reduced_panel = [dict(row) for row in select_reduced_panel(condition_rows)]
    for row in reduced_panel:
        row['panel_score'] = round(
            float(row['exact_vs_rho_js'])
            + float(row['rho_vs_star_js'])
            + float(row['star_vs_cluster_js'])
            + float(row['M0_vs_nonlocal_mean_js']),
            6,
        )

    matched_pairs = {
        'rho_vs_star_d3_match': find_matched_pair(condition_rows, 'rho_vs_star_js'),
        'exact_vs_star_d3_match': find_matched_pair(condition_rows, 'exact_vs_star_js'),
    }

    main_figure_conditions = pick_main_figure_conditions(reduced_panel)

    plot_condition_panels(main_figure_conditions, posteriors_by_condition, records_by_id, figures_dir / 'analysis-4-2_fig1_condition_panels.pdf')
    plot_global_confusion(avg_js_matrix, recovery_matrix, figures_dir / 'analysis-4-2_fig2_global_confusion.pdf')
    plot_descriptor_linkage(descriptor_summaries, figures_dir / 'analysis-4-2_fig3_descriptor_linkage.pdf')
    plot_reduced_panel_summary(reduced_panel, figures_dir / 'analysis-4-2_fig4_reduced_panel_summary.pdf')

    write_csv_rows(data_dir / 'analysis-4-2_condition_metrics.csv', condition_rows)
    write_csv_rows(data_dir / 'analysis-4-2_pair_metrics.csv', pair_rows)
    write_csv_rows(data_dir / 'analysis-4-2_posteriors.csv', posterior_rows)
    write_csv_rows(
        data_dir / 'analysis-4-2_ranked_conditions.csv',
        [
            {'ranking': ranking, 'rank': index + 1, **row}
            for ranking, rows in ranked_conditions.items()
            for index, row in enumerate(rows)
        ],
    )
    dump_json(
        data_dir / 'analysis-4-2_summary.json',
        {
            'analysis': '4-2',
            'family_order': list(FAMILY_ORDER),
            'canonical_families': CANONICAL_FAMILIES,
            'condition_count': condition_count,
            'average_js_matrix': avg_js_matrix,
            'recovery_matrix': recovery_matrix,
            'descriptor_summaries': descriptor_summaries,
            'ranked_conditions': ranked_conditions,
            'reduced_panel': reduced_panel,
            'main_figure_conditions': main_figure_conditions,
            'matched_pairs': matched_pairs,
            'key_pair_columns': {key: list(value) for key, value in KEY_PAIR_COLUMNS.items()},
            'recovery_note': f'Dirichlet noisy family recovery with concentration={RECOVERY_CONCENTRATION} and repeats={RECOVERY_REPEATS} per condition.',
        },
    )

    print(f'Wrote {data_dir / "analysis-4-2_condition_metrics.csv"}')
    print(f'Wrote {data_dir / "analysis-4-2_pair_metrics.csv"}')
    print(f'Wrote {data_dir / "analysis-4-2_posteriors.csv"}')
    print(f'Wrote {data_dir / "analysis-4-2_ranked_conditions.csv"}')
    print(f'Wrote {data_dir / "analysis-4-2_summary.json"}')
    print(f'Wrote {figures_dir / "analysis-4-2_fig1_condition_panels.pdf"}')
    print(f'Wrote {figures_dir / "analysis-4-2_fig2_global_confusion.pdf"}')
    print(f'Wrote {figures_dir / "analysis-4-2_fig3_descriptor_linkage.pdf"}')
    print(f'Wrote {figures_dir / "analysis-4-2_fig4_reduced_panel_summary.pdf"}')


if __name__ == '__main__':
    main()
