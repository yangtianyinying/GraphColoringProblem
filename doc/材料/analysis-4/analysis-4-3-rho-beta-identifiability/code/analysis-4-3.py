#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import json
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

ANALYSIS4_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ANALYSIS4_ROOT))

from common.analysis4_common import (
    EVIDENCE_LEVELS,
    dump_json,
    family_posterior,
    full_soft_evidence,
    js_divergence,
    load_rooted_library,
    write_csv_rows,
)

RHO_GRID = [0.0, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 1.0]
BETA_GRID = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
CANONICAL_SETTING = (0.35, 4.0)
RHO_NEIGHBORS = [(0.25, 4.0), (0.45, 4.0)]
BETA_NEIGHBORS = [(0.35, 2.5), (0.35, 5.0)]
RECOVERY_CONCENTRATION = 45.0
RECOVERY_REPEATS = 10
STAR_BETA_GRID = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]


def sample_dirichlet(probabilities, concentration: float, rng: random.Random):
    gammas = [rng.gammavariate(max(probability * concentration, 1e-3), 1.0) for probability in probabilities]
    total = sum(gammas)
    return tuple(value / total for value in gammas)


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def format_setting(setting: tuple[float, float]) -> str:
    return f'rho={setting[0]:.2f}|beta={setting[1]:.2f}'


def pairwise_mean_js(panel_a, panel_b, conditions):
    return mean(js_divergence(panel_a[condition], panel_b[condition]) for condition in conditions)


def build_predictions(records):
    condition_meta = []
    predictions = {}
    for rho in RHO_GRID:
        for beta in BETA_GRID:
            predictions[(rho, beta)] = {}
    star_predictions = {beta: {} for beta in STAR_BETA_GRID}
    exact_predictions = {beta: {} for beta in STAR_BETA_GRID}

    for record in records:
        for level_name in EVIDENCE_LEVELS:
            condition = (record.graph_id, level_name)
            evidence = full_soft_evidence(record, level_name)
            condition_meta.append(
                {
                    'condition_key': f'{record.graph_id}_{level_name}',
                    'graph_id': record.graph_id,
                    'evidence_level': level_name,
                    'D1_target_degree': record.descriptor['D1_target_degree'],
                    'D2_neighbor_coupling': record.descriptor['D2_neighbor_coupling'],
                    'D3_remote_class': record.descriptor['D3_remote_class'],
                    'S2_count': record.descriptor['S2_count'],
                    'e12': record.descriptor['e12'],
                    'e22': record.descriptor['e22'],
                    'radius': record.descriptor['radius'],
                }
            )
            for rho in RHO_GRID:
                for beta in BETA_GRID:
                    predictions[(rho, beta)][condition] = family_posterior(
                        record.adjacency,
                        0,
                        evidence,
                        {'family': 'M_rho,beta', 'rho': rho, 'beta': beta},
                    )
            for beta in STAR_BETA_GRID:
                star_predictions[beta][condition] = family_posterior(
                    record.adjacency,
                    0,
                    evidence,
                    {'family': 'M_star', 'beta': beta},
                )
                exact_predictions[beta][condition] = family_posterior(
                    record.adjacency,
                    0,
                    evidence,
                    {'family': 'M_exact', 'beta': beta},
                )
    return condition_meta, predictions, star_predictions, exact_predictions


def atlas_rows(condition_keys, predictions):
    exact_anchor = predictions[(1.0, 4.0)]
    local_anchor = predictions[(0.0, 4.0)]
    rows = []
    for rho in RHO_GRID:
        for beta in BETA_GRID:
            panel = predictions[(rho, beta)]
            neighbor_js = []
            rho_index = RHO_GRID.index(rho)
            beta_index = BETA_GRID.index(beta)
            for rho_neighbor_index in [rho_index - 1, rho_index + 1]:
                if 0 <= rho_neighbor_index < len(RHO_GRID):
                    neighbor_js.append(pairwise_mean_js(panel, predictions[(RHO_GRID[rho_neighbor_index], beta)], condition_keys))
            for beta_neighbor_index in [beta_index - 1, beta_index + 1]:
                if 0 <= beta_neighbor_index < len(BETA_GRID):
                    neighbor_js.append(pairwise_mean_js(panel, predictions[(rho, BETA_GRID[beta_neighbor_index])], condition_keys))
            rows.append(
                {
                    'rho': rho,
                    'beta': beta,
                    'mean_js_to_exact_beta4': round(pairwise_mean_js(panel, exact_anchor, condition_keys), 6),
                    'mean_js_to_local_beta4': round(pairwise_mean_js(panel, local_anchor, condition_keys), 6),
                    'local_neighbor_identifiability': round(mean(neighbor_js), 6),
                }
            )
    return rows


def condition_identifiability_rows(condition_meta, predictions):
    rows = []
    for meta in condition_meta:
        condition = (meta['graph_id'], meta['evidence_level'])
        anchor = predictions[CANONICAL_SETTING][condition]
        rho_sensitivity = mean(js_divergence(anchor, predictions[setting][condition]) for setting in RHO_NEIGHBORS)
        beta_sensitivity = mean(js_divergence(anchor, predictions[setting][condition]) for setting in BETA_NEIGHBORS)
        cross_axis = mean(
            js_divergence(predictions[rho_setting][condition], predictions[beta_setting][condition])
            for rho_setting in RHO_NEIGHBORS
            for beta_setting in BETA_NEIGHBORS
        )
        rows.append(
            {
                **meta,
                'rho_sensitivity': round(rho_sensitivity, 6),
                'beta_sensitivity': round(beta_sensitivity, 6),
                'cross_axis_js': round(cross_axis, 6),
                'diagnostic_score': round(min(rho_sensitivity, beta_sensitivity) + cross_axis, 6),
            }
        )
    return rows


def choose_recovery_panel(condition_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    chosen = []
    seen = set()
    grouped = defaultdict(list)
    for row in condition_rows:
        grouped[row['D3_remote_class']].append(row)
    for d3_value in sorted(grouped):
        row = max(grouped[d3_value], key=lambda item: float(item['diagnostic_score']))
        chosen.append(row)
        seen.add((row['graph_id'], row['evidence_level']))
    for row in sorted(condition_rows, key=lambda item: float(item['diagnostic_score']), reverse=True):
        key = (row['graph_id'], row['evidence_level'])
        if key in seen:
            continue
        chosen.append(row)
        seen.add(key)
        if len(chosen) >= 8:
            break
    return chosen[:8]


def recovery_analysis(panel_conditions, predictions):
    rng = random.Random(43)
    noiseless_rows = []
    noisy_rows = []
    recovery_panel_keys = [(row['graph_id'], row['evidence_level']) for row in panel_conditions]
    setting_list = [(rho, beta) for rho in RHO_GRID for beta in BETA_GRID]
    for true_setting in setting_list:
        true_panel = predictions[true_setting]
        noiseless_best = min(
            setting_list,
            key=lambda candidate: pairwise_mean_js(true_panel, predictions[candidate], recovery_panel_keys),
        )
        noiseless_rows.append(
            {
                'true_rho': true_setting[0],
                'true_beta': true_setting[1],
                'recovered_rho': noiseless_best[0],
                'recovered_beta': noiseless_best[1],
                'regime': 'noiseless',
            }
        )
        for repeat in range(RECOVERY_REPEATS):
            synthetic_panel = {}
            for condition in recovery_panel_keys:
                synthetic_panel[condition] = sample_dirichlet(true_panel[condition], RECOVERY_CONCENTRATION, rng)
            noisy_best = min(
                setting_list,
                key=lambda candidate: mean(
                    js_divergence(synthetic_panel[condition], predictions[candidate][condition])
                    for condition in recovery_panel_keys
                ),
            )
            noisy_rows.append(
                {
                    'true_rho': true_setting[0],
                    'true_beta': true_setting[1],
                    'recovered_rho': noisy_best[0],
                    'recovered_beta': noisy_best[1],
                    'repeat': repeat,
                    'regime': 'noisy',
                }
            )
    return noiseless_rows, noisy_rows


def ridge_summary(condition_keys, predictions):
    anchors = [(0.35, 4.0), (0.55, 2.5)]
    summary = {}
    for anchor in anchors:
        distances = []
        for rho in RHO_GRID:
            for beta in BETA_GRID:
                setting = (rho, beta)
                distances.append(
                    {
                        'rho': rho,
                        'beta': beta,
                        'mean_js_to_anchor': round(pairwise_mean_js(predictions[anchor], predictions[setting], condition_keys), 6),
                    }
                )
        ranked = sorted(
            [row for row in distances if not (row['rho'] == anchor[0] and row['beta'] == anchor[1])],
            key=lambda item: item['mean_js_to_anchor'],
        )
        summary[format_setting(anchor)] = {
            'anchor': {'rho': anchor[0], 'beta': anchor[1]},
            'grid_distances': distances,
            'nearest_alternatives': ranked[:10],
        }
    return summary


def family_robustness(condition_keys, predictions, star_predictions, exact_predictions):
    attenuation_settings = [(rho, beta) for rho in RHO_GRID for beta in BETA_GRID]
    star_settings = list(STAR_BETA_GRID)
    exact_settings = list(STAR_BETA_GRID)

    best_star = None
    for attenuation_setting in attenuation_settings:
        for beta in star_settings:
            value = pairwise_mean_js(predictions[attenuation_setting], star_predictions[beta], condition_keys)
            candidate = {
                'attenuation_setting': {'rho': attenuation_setting[0], 'beta': attenuation_setting[1]},
                'star_beta': beta,
                'mean_js': round(value, 6),
            }
            if best_star is None or candidate['mean_js'] < best_star['mean_js']:
                best_star = candidate

    best_exact = None
    for attenuation_setting in attenuation_settings:
        for beta in exact_settings:
            value = pairwise_mean_js(predictions[attenuation_setting], exact_predictions[beta], condition_keys)
            candidate = {
                'attenuation_setting': {'rho': attenuation_setting[0], 'beta': attenuation_setting[1]},
                'exact_beta': beta,
                'mean_js': round(value, 6),
            }
            if best_exact is None or candidate['mean_js'] < best_exact['mean_js']:
                best_exact = candidate

    best_exact_vs_star = None
    for exact_beta in exact_settings:
        for star_beta in star_settings:
            value = pairwise_mean_js(exact_predictions[exact_beta], star_predictions[star_beta], condition_keys)
            candidate = {
                'exact_beta': exact_beta,
                'star_beta': star_beta,
                'mean_js': round(value, 6),
            }
            if best_exact_vs_star is None or candidate['mean_js'] < best_exact_vs_star['mean_js']:
                best_exact_vs_star = candidate

    return {
        'best_attenuation_vs_star_after_beta_optimisation': best_star,
        'best_attenuation_vs_exact_after_beta_optimisation': best_exact,
        'best_exact_vs_star_after_beta_optimisation': best_exact_vs_star,
    }


def summarize_descriptor(rows: list[dict[str, object]], dimension: str) -> list[dict[str, object]]:
    grouped = defaultdict(list)
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
                'mean_diagnostic_score': round(mean(float(row['diagnostic_score']) for row in group_rows), 6),
                'mean_rho_sensitivity': round(mean(float(row['rho_sensitivity']) for row in group_rows), 6),
                'mean_beta_sensitivity': round(mean(float(row['beta_sensitivity']) for row in group_rows), 6),
            }
        )
    return summary


def plot_parameter_atlas(atlas, output_path: Path) -> None:
    def matrix_for(column: str):
        return [
            [next(row[column] for row in atlas if row['rho'] == rho and row['beta'] == beta) for beta in BETA_GRID]
            for rho in RHO_GRID
        ]

    matrices = [
        ('mean_js_to_exact_beta4', 'Mean JS to exact (beta=4)'),
        ('mean_js_to_local_beta4', 'Mean JS to local (beta=4)'),
        ('local_neighbor_identifiability', 'Local neighbour identifiability'),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.0))
    for ax, (column, title) in zip(axes, matrices):
        image = ax.imshow(matrix_for(column), cmap='viridis')
        ax.set_xticks(range(len(BETA_GRID)), [str(beta) for beta in BETA_GRID], rotation=45, ha='right')
        ax.set_yticks(range(len(RHO_GRID)), [str(rho) for rho in RHO_GRID])
        ax.set_xlabel('beta')
        ax.set_ylabel('rho')
        ax.set_title(title)
        plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_recovery(noiseless_rows, noisy_rows, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0))
    axes[0].scatter([row['true_rho'] for row in noiseless_rows], [row['recovered_rho'] for row in noiseless_rows], alpha=0.7, s=18)
    axes[0].scatter([row['true_rho'] for row in noisy_rows], [row['recovered_rho'] for row in noisy_rows], alpha=0.18, s=10)
    axes[0].plot([min(RHO_GRID), max(RHO_GRID)], [min(RHO_GRID), max(RHO_GRID)], color='black', linestyle='--', linewidth=1.0)
    axes[0].set_xlabel('True rho')
    axes[0].set_ylabel('Recovered rho')
    axes[0].set_title('rho recovery')

    axes[1].scatter([row['true_beta'] for row in noiseless_rows], [row['recovered_beta'] for row in noiseless_rows], alpha=0.7, s=18)
    axes[1].scatter([row['true_beta'] for row in noisy_rows], [row['recovered_beta'] for row in noisy_rows], alpha=0.18, s=10)
    axes[1].plot([min(BETA_GRID), max(BETA_GRID)], [min(BETA_GRID), max(BETA_GRID)], color='black', linestyle='--', linewidth=1.0)
    axes[1].set_xlabel('True beta')
    axes[1].set_ylabel('Recovered beta')
    axes[1].set_title('beta recovery')

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_ridges(ridge_info, output_path: Path) -> None:
    anchors = list(ridge_info.keys())
    fig, axes = plt.subplots(1, len(anchors), figsize=(10.5, 4.0))
    if len(anchors) == 1:
        axes = [axes]
    for ax, anchor_key in zip(axes, anchors):
        distance_lookup = {
            (row['rho'], row['beta']): row['mean_js_to_anchor']
            for row in ridge_info[anchor_key]['grid_distances']
        }
        matrix = []
        for rho in RHO_GRID:
            row = []
            for beta in BETA_GRID:
                row.append(distance_lookup[(rho, beta)])
            matrix.append(row)
        image = ax.imshow(matrix, cmap='magma_r')
        ax.set_xticks(range(len(BETA_GRID)), [str(beta) for beta in BETA_GRID], rotation=45, ha='right')
        ax.set_yticks(range(len(RHO_GRID)), [str(rho) for rho in RHO_GRID])
        ax.set_title(f"Anchor {anchor_key}")
        ax.set_xlabel('beta')
        ax.set_ylabel('rho')
        plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_descriptor_summary(descriptor_summary, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    for ax, dimension in zip(axes, ['D1_target_degree', 'D2_neighbor_coupling', 'D3_remote_class']):
        rows = descriptor_summary[dimension]
        x_labels = [str(row['value']) for row in rows]
        ax.plot(x_labels, [row['mean_diagnostic_score'] for row in rows], marker='o', label='diagnostic score')
        ax.plot(x_labels, [row['mean_rho_sensitivity'] for row in rows], marker='s', label='rho sensitivity')
        ax.plot(x_labels, [row['mean_beta_sensitivity'] for row in rows], marker='^', label='beta sensitivity')
        ax.set_title(dimension)
        ax.set_ylabel('Mean value')
        ax.tick_params(axis='x', rotation=25)
    axes[0].legend(fontsize=7)
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
    condition_meta, predictions, star_predictions, exact_predictions = build_predictions(records)
    condition_keys = [(meta['graph_id'], meta['evidence_level']) for meta in condition_meta]

    atlas = atlas_rows(condition_keys, predictions)
    condition_rows = condition_identifiability_rows(condition_meta, predictions)
    recovery_panel = choose_recovery_panel(condition_rows)
    recovery_panel_keys = [(row['graph_id'], row['evidence_level']) for row in recovery_panel]
    noiseless_rows, noisy_rows = recovery_analysis(recovery_panel, predictions)
    ridge_info = ridge_summary(recovery_panel_keys, predictions)
    robustness = family_robustness(recovery_panel_keys, predictions, star_predictions, exact_predictions)
    descriptor_summary = {
        dimension: summarize_descriptor(condition_rows, dimension)
        for dimension in ['D1_target_degree', 'D2_neighbor_coupling', 'D3_remote_class']
    }

    noisy_abs_rho = [abs(row['true_rho'] - row['recovered_rho']) for row in noisy_rows]
    noisy_abs_beta = [abs(row['true_beta'] - row['recovered_beta']) for row in noisy_rows]
    noiseless_exact_match = mean(
        1.0 if row['true_rho'] == row['recovered_rho'] and row['true_beta'] == row['recovered_beta'] else 0.0
        for row in noiseless_rows
    )
    noisy_exact_match = mean(
        1.0 if row['true_rho'] == row['recovered_rho'] and row['true_beta'] == row['recovered_beta'] else 0.0
        for row in noisy_rows
    )

    plot_parameter_atlas(atlas, figures_dir / 'analysis-4-3_fig1_parameter_atlas.pdf')
    plot_recovery(noiseless_rows, noisy_rows, figures_dir / 'analysis-4-3_fig2_recovery.pdf')
    plot_ridges(ridge_info, figures_dir / 'analysis-4-3_fig3_tradeoff_ridges.pdf')
    plot_descriptor_summary(descriptor_summary, figures_dir / 'analysis-4-3_fig4_descriptor_identifiability.pdf')

    write_csv_rows(data_dir / 'analysis-4-3_parameter_atlas.csv', atlas)
    write_csv_rows(data_dir / 'analysis-4-3_condition_identifiability.csv', condition_rows)
    write_csv_rows(data_dir / 'analysis-4-3_recovery_noiseless.csv', noiseless_rows)
    write_csv_rows(data_dir / 'analysis-4-3_recovery_noisy.csv', noisy_rows)
    dump_json(
        data_dir / 'analysis-4-3_summary.json',
        {
            'analysis': '4-3',
            'rho_grid': RHO_GRID,
            'beta_grid': BETA_GRID,
            'canonical_setting': {'rho': CANONICAL_SETTING[0], 'beta': CANONICAL_SETTING[1]},
            'recovery_panel': recovery_panel,
            'ridge_info': ridge_info,
            'family_robustness_under_beta_optimisation': robustness,
            'descriptor_summary': descriptor_summary,
            'recommendation': {
                'noiseless_exact_match_rate': round(noiseless_exact_match, 6),
                'noisy_exact_match_rate': round(noisy_exact_match, 6),
                'mean_abs_rho_error_noisy': round(mean(noisy_abs_rho), 6),
                'mean_abs_beta_error_noisy': round(mean(noisy_abs_beta), 6),
                'beta_treatment_recommendation': 'beta should not be ignored: it is partly recoverable, but it meaningfully trades off with rho on a nontrivial subset of conditions. Future comparisons should either jointly fit rho and beta or restrict to the diagnostic panel recovered here.',
            },
            'top_conditions_by_identifiability': sorted(condition_rows, key=lambda item: float(item['diagnostic_score']), reverse=True)[:20],
        },
    )

    print(f'Wrote {data_dir / "analysis-4-3_parameter_atlas.csv"}')
    print(f'Wrote {data_dir / "analysis-4-3_condition_identifiability.csv"}')
    print(f'Wrote {data_dir / "analysis-4-3_recovery_noiseless.csv"}')
    print(f'Wrote {data_dir / "analysis-4-3_recovery_noisy.csv"}')
    print(f'Wrote {data_dir / "analysis-4-3_summary.json"}')
    print(f'Wrote {figures_dir / "analysis-4-3_fig1_parameter_atlas.pdf"}')
    print(f'Wrote {figures_dir / "analysis-4-3_fig2_recovery.pdf"}')
    print(f'Wrote {figures_dir / "analysis-4-3_fig3_tradeoff_ridges.pdf"}')
    print(f'Wrote {figures_dir / "analysis-4-3_fig4_descriptor_identifiability.pdf"}')


if __name__ == '__main__':
    main()
