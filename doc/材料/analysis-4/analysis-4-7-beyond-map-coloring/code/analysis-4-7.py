#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

ANALYSIS4_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ANALYSIS4_ROOT))

from common.analysis4_common import dump_json, write_csv_rows


DOMAIN_ROWS = [
    {
        'domain': 'map_colouring',
        'local_coupling': 'repulsive / anti-coordination',
        'example_framing': 'adjacent regions prefer different colours',
        'theoretical_value': 3,
        'experimental_simplicity': 5,
        'continuity_with_current_paradigm': 5,
        'expected_family_discriminability': 4,
        'shell_parity_heuristics_relevance': 'high',
        'notes': 'Excellent first testbed, but strongly tied to exclusion dynamics.',
    },
    {
        'domain': 'attractive_graph_labelling',
        'local_coupling': 'attractive / smoothing',
        'example_framing': 'neighbouring locations tend to share the same hidden label',
        'theoretical_value': 5,
        'experimental_simplicity': 4,
        'continuity_with_current_paradigm': 5,
        'expected_family_discriminability': 5,
        'shell_parity_heuristics_relevance': 'low',
        'notes': 'Best first extension: flips local semantics while keeping graph-based inference structure intact.',
    },
    {
        'domain': 'social_consensus',
        'local_coupling': 'attractive / alignment',
        'example_framing': 'linked agents tend to share opinions or affiliations',
        'theoretical_value': 4,
        'experimental_simplicity': 4,
        'continuity_with_current_paradigm': 4,
        'expected_family_discriminability': 4,
        'shell_parity_heuristics_relevance': 'low',
        'notes': 'Intuitive and psychologically rich; especially useful for cluster-style approximations.',
    },
    {
        'domain': 'diffusion_contagion',
        'local_coupling': 'attractive / transmission',
        'example_framing': 'infection or information spreads through edges',
        'theoretical_value': 4,
        'experimental_simplicity': 3,
        'continuity_with_current_paradigm': 3,
        'expected_family_discriminability': 4,
        'shell_parity_heuristics_relevance': 'very low',
        'notes': 'Preserves propagation logic, but task semantics and interface demands are more complex.',
    },
    {
        'domain': 'mixed_sign_coupling',
        'local_coupling': 'heterogeneous attractive and repulsive edges',
        'example_framing': 'some relations are cooperative, others competitive',
        'theoretical_value': 5,
        'experimental_simplicity': 2,
        'continuity_with_current_paradigm': 2,
        'expected_family_discriminability': 5,
        'shell_parity_heuristics_relevance': 'very low',
        'notes': 'Theoretically rich, but too complex as the immediate next step.',
    },
]


TRANSFER_ROWS = [
    {'family': 'M_exact', 'transfer_to_attractive_tasks': 'direct', 'transfer_to_social_consensus': 'direct', 'transfer_to_diffusion': 'direct', 'notes': 'Exact inference remains well-defined across all domains.'},
    {'family': 'M_0', 'transfer_to_attractive_tasks': 'direct', 'transfer_to_social_consensus': 'direct', 'transfer_to_diffusion': 'direct', 'notes': 'Nearest-neighbour-only truncation generalises cleanly.'},
    {'family': 'M_rho', 'transfer_to_attractive_tasks': 'direct', 'transfer_to_social_consensus': 'direct', 'transfer_to_diffusion': 'direct', 'notes': 'rho remains the main task-general structural attenuation parameter.'},
    {'family': 'M_rho,beta', 'transfer_to_attractive_tasks': 'direct', 'transfer_to_social_consensus': 'direct', 'transfer_to_diffusion': 'direct', 'notes': 'beta may become even more psychologically important when couplings vary in strength.'},
    {'family': 'M_star', 'transfer_to_attractive_tasks': 'direct', 'transfer_to_social_consensus': 'direct', 'transfer_to_diffusion': 'direct', 'notes': 'Target-centred rewrite remains meaningful across repulsive and attractive tasks.'},
    {'family': 'M_cluster', 'transfer_to_attractive_tasks': 'strong', 'transfer_to_social_consensus': 'strong', 'transfer_to_diffusion': 'moderate', 'notes': 'Chunking local clusters may become more plausible under attractive couplings.'},
]


PROSPECT_TEXT = (
    'Map-colouring remains an excellent first testbed for bounded graph inference, but it cannot on its own support domain-general claims '
    'about human structural approximation. The next task domain should preserve the graph-based inference interface while reversing the local '
    'coupling semantics from repulsive to attractive. A simple attractive graph-labelling task is therefore the cleanest first extension: '
    'it tests whether the same family taxonomy survives when shell-parity and local conflict counting cease to be the dominant cues.'
)



def weighted_score(row):
    return 0.35 * row['theoretical_value'] + 0.25 * row['experimental_simplicity'] + 0.20 * row['continuity_with_current_paradigm'] + 0.20 * row['expected_family_discriminability']



def plot_domain_comparison(output_path: Path) -> None:
    domains = [row['domain'] for row in DOMAIN_ROWS]
    criteria = ['theoretical_value', 'experimental_simplicity', 'continuity_with_current_paradigm', 'expected_family_discriminability']
    labels = ['theory', 'simplicity', 'continuity', 'discriminability']
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    width = 0.15
    offsets = [(index - (len(criteria) - 1) / 2.0) * width for index in range(len(criteria))]
    for offset, criterion, label in zip(offsets, criteria, labels):
        ax.bar(
            [index + offset for index in range(len(domains))],
            [row[criterion] for row in DOMAIN_ROWS],
            width=width,
            label=label,
        )
    ax.set_xticks(range(len(domains)), [domain.replace('_', '\n') for domain in domains])
    ax.set_ylabel('Score (1–5)')
    ax.set_title('Beyond map-colouring: candidate task-domain comparison')
    ax.legend(fontsize=7, ncol=4)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)



def main() -> None:
    analysis_dir = Path(__file__).resolve().parents[1]
    data_dir = analysis_dir / 'code' / 'data'
    figures_dir = analysis_dir / 'figures'
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    ranked_domains = sorted(
        [
            {
                **row,
                'weighted_priority_score': round(weighted_score(row), 3),
            }
            for row in DOMAIN_ROWS
        ],
        key=lambda item: item['weighted_priority_score'],
        reverse=True,
    )

    plot_domain_comparison(figures_dir / 'analysis-4-7_fig1_domain_comparison.pdf')

    write_csv_rows(data_dir / 'analysis-4-7_domain_comparison.csv', ranked_domains)
    write_csv_rows(data_dir / 'analysis-4-7_taxonomy_transfer.csv', TRANSFER_ROWS)
    dump_json(
        data_dir / 'analysis-4-7_summary.json',
        {
            'analysis': '4-7',
            'limitation_statement': 'Current findings are strongest for graph-based inference under repulsive local couplings. They should not yet be generalized to all graph-structured inference domains.',
            'ranked_domains': ranked_domains,
            'taxonomy_transfer': TRANSFER_ROWS,
            'future_task_recommendation': {
                'recommended_domain': ranked_domains[0]['domain'],
                'reason': ranked_domains[0]['notes'],
            },
            'prospect_section_draft': PROSPECT_TEXT,
        },
    )

    print(f'Wrote {data_dir / "analysis-4-7_domain_comparison.csv"}')
    print(f'Wrote {data_dir / "analysis-4-7_taxonomy_transfer.csv"}')
    print(f'Wrote {data_dir / "analysis-4-7_summary.json"}')
    print(f'Wrote {figures_dir / "analysis-4-7_fig1_domain_comparison.pdf"}')


if __name__ == '__main__':
    main()
