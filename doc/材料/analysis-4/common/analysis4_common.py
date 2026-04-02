from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import combinations, product
import json
import math
from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.patches import Circle

COLOR_COUNT = 3
COLOR_LABELS = ('R', 'G', 'B')
COLOR_HEX = {'R': '#d73027', 'G': '#1a9850', 'B': '#4575b4'}
EVIDENCE_LEVELS = {
    'high': (0.9, 0.05, 0.05),
    'medium': (0.6, 0.2, 0.2),
    'low': (0.4, 0.3, 0.3),
}
DEFAULT_BETA = 4.0
FAMILY_ORDER = ('M_exact', 'M_0', 'M_rho', 'M_rho,beta', 'M_star', 'M_cluster')
CANONICAL_FAMILIES = {
    'M_exact': {'family': 'M_exact', 'beta': DEFAULT_BETA},
    'M_0': {'family': 'M_0', 'beta': DEFAULT_BETA},
    'M_rho': {'family': 'M_rho', 'rho': 0.35, 'beta': DEFAULT_BETA},
    'M_rho,beta': {'family': 'M_rho,beta', 'rho': 0.35, 'beta': 2.5},
    'M_star': {'family': 'M_star', 'beta': DEFAULT_BETA},
    'M_cluster': {'family': 'M_cluster', 'beta': DEFAULT_BETA},
}
ANALYSIS4_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ANALYSIS4_ROOT.parent
ANALYSIS3_DATA_DIR = PROJECT_ROOT / 'analysis-3' / 'code' / 'data'


@dataclass(frozen=True)
class GraphRecord:
    graph_id: str
    n_nodes: int
    adjacency: tuple[tuple[int, ...], ...]
    edges: tuple[tuple[int, int], ...]
    descriptor: dict[str, object]
    preferred_color_template: tuple[int, ...]
    preferred_colors: dict[str, str]
    distances_from_root: dict[int, int]
    rooted_key: tuple[tuple[int, int], ...]
    high_kl_A0_to_A4: float


_ASSIGNMENT_CACHE: dict[int, tuple[tuple[int, ...], ...]] = {}


def assignments_for_n(n_nodes: int) -> tuple[tuple[int, ...], ...]:
    assignments = _ASSIGNMENT_CACHE.get(n_nodes)
    if assignments is None:
        assignments = tuple(product(range(COLOR_COUNT), repeat=n_nodes))
        _ASSIGNMENT_CACHE[n_nodes] = assignments
    return assignments


def normalize(values: Iterable[float]) -> tuple[float, ...]:
    values = tuple(values)
    total = sum(values)
    if total <= 0.0:
        return tuple(1.0 / len(values) for _ in values)
    return tuple(value / total for value in values)


def entropy(probabilities: Iterable[float]) -> float:
    return -sum(probability * math.log(probability) for probability in probabilities if probability > 0.0)


def kl_divergence(p: Iterable[float], q: Iterable[float], epsilon: float = 1e-12) -> float:
    p = tuple(p)
    q = tuple(max(value, epsilon) for value in q)
    return sum(left * math.log(left / right) for left, right in zip(p, q) if left > 0.0)


def js_divergence(p: Iterable[float], q: Iterable[float]) -> float:
    p = tuple(p)
    q = tuple(q)
    midpoint = tuple((left + right) / 2.0 for left, right in zip(p, q))
    return 0.5 * kl_divergence(p, midpoint) + 0.5 * kl_divergence(q, midpoint)


def total_variation(p: Iterable[float], q: Iterable[float]) -> float:
    return 0.5 * sum(abs(left - right) for left, right in zip(p, q))


def edges_from_adjacency(adjacency: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (node, neighbor)
        for node in range(len(adjacency))
        for neighbor in adjacency[node]
        if node < neighbor
    )


def adjacency_from_edges(n_nodes: int, edges: Iterable[tuple[int, int]]) -> tuple[tuple[int, ...], ...]:
    adjacency_sets = [set() for _ in range(n_nodes)]
    for left, right in edges:
        adjacency_sets[left].add(right)
        adjacency_sets[right].add(left)
    return tuple(tuple(sorted(neighbors)) for neighbors in adjacency_sets)


def bfs_distances(adjacency: tuple[tuple[int, ...], ...], source: int) -> dict[int, int]:
    distances = {source: 0}
    queue = [source]
    for node in queue:
        for neighbor in adjacency[node]:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[node] + 1
            queue.append(neighbor)
    return distances


def evidence_distribution(level: tuple[float, float, float], preferred_color: int) -> tuple[float, float, float]:
    strong, weak_left, weak_right = level
    probabilities = [weak_left, weak_right, weak_right]
    probabilities[preferred_color] = strong
    return tuple(probabilities)


def load_rooted_library() -> list[GraphRecord]:
    catalog_path = ANALYSIS3_DATA_DIR / 'analysis-3_rooted_motif_catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    records = []
    for item in catalog['rooted_graphs']:
        edges = tuple(tuple(edge) for edge in item['edges'])
        adjacency = adjacency_from_edges(item['n_nodes'], edges)
        records.append(
            GraphRecord(
                graph_id=item['graph_id'],
                n_nodes=item['n_nodes'],
                adjacency=adjacency,
                edges=edges,
                descriptor=item['descriptor'],
                preferred_color_template=tuple(item['preferred_color_template']),
                preferred_colors=item['preferred_colors'],
                distances_from_root=bfs_distances(adjacency, 0),
                rooted_key=tuple(tuple(edge) for edge in item['rooted_key']),
                high_kl_A0_to_A4=float(item['high_kl_A0_to_A4']),
            )
        )
    return records


def load_selected_panel_ids() -> set[str]:
    selected_path = ANALYSIS3_DATA_DIR / 'analysis-3_selected_stimuli.json'
    selected = json.loads(selected_path.read_text(encoding='utf-8'))
    return {item['graph_id'] for item in selected['selected_stimuli']}


def full_soft_evidence(record: GraphRecord, level_name: str) -> dict[int, tuple[float, float, float]]:
    level = EVIDENCE_LEVELS[level_name]
    return {
        node_index + 1: evidence_distribution(level, preferred_color)
        for node_index, preferred_color in enumerate(record.preferred_color_template)
    }


def exact_posterior_from_edge_strengths(
    n_nodes: int,
    edge_strengths: dict[tuple[int, int], float],
    evidence_by_node: dict[int, tuple[float, float, float]],
    target: int,
) -> tuple[float, float, float]:
    assignments = assignments_for_n(n_nodes)
    active_edges = [
        (min(left, right), max(left, right), strength, math.exp(-strength))
        for (left, right), strength in edge_strengths.items()
        if strength > 0.0
    ]
    posterior = [0.0, 0.0, 0.0]
    partition = 0.0
    for assignment in assignments:
        weight = 1.0
        for node, probabilities in evidence_by_node.items():
            weight *= probabilities[assignment[node]]
            if weight == 0.0:
                break
        if weight == 0.0:
            continue
        for left, right, _, penalty in active_edges:
            if assignment[left] == assignment[right]:
                weight *= penalty
        partition += weight
        posterior[assignment[target]] += weight
    if partition == 0.0:
        return (1 / 3, 1 / 3, 1 / 3)
    return normalize(posterior)


def edge_strengths_rho(adjacency: tuple[tuple[int, ...], ...], target: int, rho: float, beta: float) -> dict[tuple[int, int], float]:
    distances = bfs_distances(adjacency, target)
    strengths = {}
    for left, right in edges_from_adjacency(adjacency):
        shell = min(distances[left], distances[right])
        strengths[(left, right)] = beta * (rho ** shell)
    return strengths


def edge_strengths_star(adjacency: tuple[tuple[int, ...], ...], target: int, beta: float) -> dict[tuple[int, int], float]:
    distances = bfs_distances(adjacency, target)
    strengths = {}
    for node in range(len(adjacency)):
        if node == target:
            continue
        strengths[(min(target, node), max(target, node))] = beta / max(1, distances[node])
    return strengths


def edge_strengths_cluster(adjacency: tuple[tuple[int, ...], ...], target: int, beta: float) -> dict[tuple[int, int], float]:
    distances = bfs_distances(adjacency, target)
    shell1 = tuple(node for node, distance in distances.items() if distance == 1)
    shell2 = tuple(node for node, distance in distances.items() if distance == 2)
    keep_nodes = {target, *shell1, *shell2}
    strengths: dict[tuple[int, int], float] = {}
    for left, right in edges_from_adjacency(adjacency):
        if left in keep_nodes and right in keep_nodes:
            strengths[(left, right)] = beta
    for left, right in combinations(shell1, 2):
        edge = (min(left, right), max(left, right))
        if edge in strengths:
            continue
        if any(shell in adjacency[left] and shell in adjacency[right] for shell in shell2):
            strengths[edge] = beta
    return strengths


def family_posterior(
    adjacency: tuple[tuple[int, ...], ...],
    target: int,
    evidence_by_node: dict[int, tuple[float, float, float]],
    family_config: dict[str, object],
) -> tuple[float, float, float]:
    family = family_config['family']
    beta = float(family_config.get('beta', DEFAULT_BETA))
    if family == 'M_exact':
        edge_strengths = edge_strengths_rho(adjacency, target, rho=1.0, beta=beta)
    elif family == 'M_0':
        edge_strengths = edge_strengths_rho(adjacency, target, rho=0.0, beta=beta)
    elif family in {'M_rho', 'M_rho,beta'}:
        edge_strengths = edge_strengths_rho(adjacency, target, rho=float(family_config['rho']), beta=beta)
    elif family == 'M_star':
        edge_strengths = edge_strengths_star(adjacency, target, beta=beta)
    elif family == 'M_cluster':
        edge_strengths = edge_strengths_cluster(adjacency, target, beta=beta)
    else:
        raise ValueError(f'Unknown family: {family}')
    return exact_posterior_from_edge_strengths(len(adjacency), edge_strengths, evidence_by_node, target)


def graph_node_positions(adjacency: tuple[tuple[int, ...], ...], target: int = 0) -> dict[int, tuple[float, float]]:
    distances = bfs_distances(adjacency, target)
    shells: dict[int, list[int]] = {}
    for node, distance in distances.items():
        shells.setdefault(distance, []).append(node)
    positions = {target: (0.0, 0.0)}
    for shell, nodes in sorted(shells.items()):
        if shell == 0:
            continue
        nodes = sorted(nodes)
        if len(nodes) == 1:
            positions[nodes[0]] = (0.0, float(shell))
            continue
        for index, node in enumerate(nodes):
            angle = math.pi / 2 + 2 * math.pi * index / len(nodes)
            radius = float(shell)
            positions[node] = (radius * math.cos(angle), radius * math.sin(angle))
    return positions


def plot_graph(
    ax,
    adjacency: tuple[tuple[int, ...], ...],
    target: int = 0,
    observed_state_labels: dict[int, str] | None = None,
    title: str | None = None,
) -> None:
    observed_state_labels = observed_state_labels or {}
    positions = graph_node_positions(adjacency, target)
    for left, right in edges_from_adjacency(adjacency):
        x_values = [positions[left][0], positions[right][0]]
        y_values = [positions[left][1], positions[right][1]]
        ax.plot(x_values, y_values, color='#444444', linewidth=1.4, zorder=1)
    for node, (x_pos, y_pos) in positions.items():
        fill = '#ffffff'
        label = f'{node}'
        if node in observed_state_labels:
            color = observed_state_labels[node]
            fill = COLOR_HEX[color]
            label = f'{node}\n{color}'
        circle = Circle((x_pos, y_pos), radius=0.16, facecolor=fill, edgecolor='black', linewidth=1.4 if node == target else 1.0, zorder=3)
        ax.add_patch(circle)
        ax.text(x_pos, y_pos, label, ha='center', va='center', fontsize=8, color='white' if fill != '#ffffff' else 'black', zorder=4)
    ax.set_aspect('equal')
    ax.axis('off')
    if title:
        ax.set_title(title, fontsize=10)


def belief_profile_bars(ax, family_posteriors: list[tuple[str, tuple[float, float, float]]], title: str | None = None) -> None:
    x_base = list(range(len(COLOR_LABELS)))
    width = 0.12 if len(family_posteriors) >= 5 else 0.18
    offsets = [
        (index - (len(family_posteriors) - 1) / 2.0) * width
        for index in range(len(family_posteriors))
    ]
    for offset, (family, posterior) in zip(offsets, family_posteriors):
        ax.bar(
            [value + offset for value in x_base],
            posterior,
            width=width,
            label=family,
            alpha=0.85,
        )
    ax.set_xticks(x_base, COLOR_LABELS)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel('P(target state)')
    if title:
        ax.set_title(title, fontsize=10)


def heatmap(ax, matrix: list[list[float]], labels: list[str], title: str, cmap: str = 'viridis') -> None:
    image = ax.imshow(matrix, cmap=cmap)
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha='right')
    ax.set_yticks(range(len(labels)), labels)
    ax.set_title(title, fontsize=10)
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            ax.text(column_index, row_index, f'{value:.2f}', ha='center', va='center', fontsize=7, color='white' if value > max(0.25, max(max(r) for r in matrix) * 0.55) else 'black')
    plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04)


def write_csv_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    fieldnames = list(rows[0].keys())
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def dump_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding='utf-8')


def condition_slug(graph_id: str, level_name: str) -> str:
    return f'{graph_id}_{level_name}'


def family_label(config: dict[str, object]) -> str:
    family = config['family']
    if family == 'M_rho':
        return f"M_rho(rho={float(config['rho']):.2f})"
    if family == 'M_rho,beta':
        return f"M_rho,beta(rho={float(config['rho']):.2f}, beta={float(config['beta']):.2f})"
    if 'beta' in config:
        return f"{family}(beta={float(config['beta']):.2f})"
    return family
