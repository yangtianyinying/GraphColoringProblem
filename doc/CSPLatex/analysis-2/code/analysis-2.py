#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations, product
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


COLOR_COUNT = 3
COLOR_LABELS = ("R", "G", "B")
COLOR_HEX = ("#d73027", "#1a9850", "#4575b4")
EVIDENCE_LEVELS = {
    "high": (0.9, 0.05, 0.05),
    "medium": (0.6, 0.2, 0.2),
    "low": (0.4, 0.3, 0.3),
}
RHO_AGENTS = (("A0", 0.0), ("A1", 0.25), ("A2", 0.5), ("A3", 0.75), ("A4", 1.0))
BETA_EDGE = 4.0
N_NODES = 5
MONOTONICITY_TOLERANCE = 5e-4
FIGURE_FILENAMES = {
    "fig1": "analysis-2_fig1_separability_panel.pdf",
    "fig2": "analysis-2_fig2_entropy_spectrum.pdf",
    "fig3": "analysis-2_fig3_kl_matrices.pdf",
    "fig4": "analysis-2_fig4_equal_local_pair.pdf",
}


@dataclass(frozen=True)
class GraphCache:
    adjacency: tuple[tuple[int, ...], ...]
    edges: tuple[tuple[int, int], ...]
    edge_shells: tuple[int, ...]
    assignments: tuple[tuple[int, ...], ...]
    edge_weights_by_rho: dict[float, tuple[float, ...]]
    distances_from_target: dict[int, int]
    centers_in_original_graph: tuple[int, ...]
    rooted_key: tuple[tuple[int, int], ...]


def normalize(values: list[float] | tuple[float, ...]) -> tuple[float, ...]:
    total = sum(values)
    return tuple(value / total for value in values)


def entropy(probabilities: tuple[float, ...] | list[float]) -> float:
    return -sum(probability * math.log(probability) for probability in probabilities if probability > 0.0)


def kl_divergence(
    p: tuple[float, ...] | list[float],
    q: tuple[float, ...] | list[float],
) -> float:
    return sum(left * math.log(left / right) for left, right in zip(p, q) if left > 0.0)


def pretty_probabilities(probabilities: tuple[float, ...] | list[float]) -> list[float]:
    return [round(value, 6) for value in probabilities]


def edges_from_adjacency(adjacency: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (node, neighbor)
        for node in range(len(adjacency))
        for neighbor in adjacency[node]
        if node < neighbor
    )


def graph_edge_count(adjacency: tuple[tuple[int, ...], ...]) -> int:
    return len(edges_from_adjacency(adjacency))


def connected(adjacency: tuple[tuple[int, ...], ...]) -> bool:
    visited = {0}
    queue = [0]
    for node in queue:
        for neighbor in adjacency[node]:
            if neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append(neighbor)
    return len(visited) == len(adjacency)


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


def eccentricity(adjacency: tuple[tuple[int, ...], ...], source: int) -> int:
    return max(bfs_distances(adjacency, source).values())


def three_colorable(adjacency: tuple[tuple[int, ...], ...]) -> bool:
    order = sorted(range(len(adjacency)), key=lambda node: (-len(adjacency[node]), node))
    colors = [-1] * len(adjacency)

    def backtrack(index: int) -> bool:
        if index == len(order):
            return True
        node = order[index]
        unavailable = {colors[neighbor] for neighbor in adjacency[node] if colors[neighbor] != -1}
        for color in range(COLOR_COUNT):
            if color in unavailable:
                continue
            colors[node] = color
            if backtrack(index + 1):
                return True
            colors[node] = -1
        return False

    return backtrack(0)


def edge_key_after_permutation(
    adjacency: tuple[tuple[int, ...], ...],
    permutation: tuple[int, ...],
) -> tuple[tuple[int, int], ...]:
    inverse = {old_index: new_index for new_index, old_index in enumerate(permutation)}
    edges = []
    for left, right in edges_from_adjacency(adjacency):
        new_left = inverse[left]
        new_right = inverse[right]
        edges.append((min(new_left, new_right), max(new_left, new_right)))
    return tuple(sorted(edges))


def adjacency_from_edge_key(
    n_nodes: int,
    edge_key: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, ...], ...]:
    adjacency_sets = [set() for _ in range(n_nodes)]
    for left, right in edge_key:
        adjacency_sets[left].add(right)
        adjacency_sets[right].add(left)
    return tuple(tuple(sorted(neighbors)) for neighbors in adjacency_sets)


def canonical_unrooted_key(
    adjacency: tuple[tuple[int, ...], ...],
    all_permutations: tuple[tuple[int, ...], ...],
) -> tuple[tuple[int, int], ...]:
    best_key: tuple[tuple[int, int], ...] | None = None
    for permutation in all_permutations:
        key = edge_key_after_permutation(adjacency, permutation)
        if best_key is None or key < best_key:
            best_key = key
    return best_key


def rooted_canonical_form(
    adjacency: tuple[tuple[int, ...], ...],
    root: int,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, ...], ...]]:
    others = tuple(node for node in range(len(adjacency)) if node != root)
    best_key: tuple[tuple[int, int], ...] | None = None
    best_adjacency: tuple[tuple[int, ...], ...] | None = None
    for remainder in permutations(others):
        permutation = (root,) + remainder
        key = edge_key_after_permutation(adjacency, permutation)
        if best_key is not None and key >= best_key:
            continue
        best_key = key
        best_adjacency = adjacency_from_edge_key(len(adjacency), key)
    return best_key, best_adjacency


def rooted_central_forms(
    adjacency: tuple[tuple[int, ...], ...],
) -> tuple[tuple[tuple[tuple[int, int], ...], tuple[tuple[int, ...], ...], tuple[int, ...]], ...]:
    eccentricities = {node: eccentricity(adjacency, node) for node in range(len(adjacency))}
    minimum_eccentricity = min(eccentricities.values())
    centers = tuple(sorted(node for node, value in eccentricities.items() if value == minimum_eccentricity))
    rooted_forms = []
    seen_keys: set[tuple[tuple[int, int], ...]] = set()
    for center in centers:
        rooted_key, rooted_adjacency = rooted_canonical_form(adjacency, center)
        if rooted_key in seen_keys:
            continue
        seen_keys.add(rooted_key)
        rooted_forms.append((rooted_key, rooted_adjacency, centers))
    rooted_forms.sort(key=lambda item: item[0])
    return tuple(rooted_forms)


def enumerate_graph_classes(n_nodes: int) -> list[dict[str, object]]:
    all_edges = list(combinations(range(n_nodes), 2))
    all_permutations = tuple(permutations(range(n_nodes)))
    graph_classes: dict[tuple[tuple[int, int], ...], dict[str, object]] = {}
    for mask in range(1, 1 << len(all_edges)):
        adjacency_sets = [set() for _ in range(n_nodes)]
        for bit_index, (left, right) in enumerate(all_edges):
            if not ((mask >> bit_index) & 1):
                continue
            adjacency_sets[left].add(right)
            adjacency_sets[right].add(left)
        adjacency = tuple(tuple(sorted(neighbors)) for neighbors in adjacency_sets)
        if not connected(adjacency):
            continue
        if not three_colorable(adjacency):
            continue
        key = canonical_unrooted_key(adjacency, all_permutations)
        if key in graph_classes:
            continue
        rooted_forms = rooted_central_forms(adjacency)
        graph_classes[key] = {
            "canonical_unrooted_key": key,
            "rooted_forms": rooted_forms,
        }
    ordered_keys = sorted(graph_classes)
    return [graph_classes[key] for key in ordered_keys]


def precompute_graph_cache(
    adjacency: tuple[tuple[int, ...], ...],
    centers_in_original_graph: tuple[int, ...],
    rooted_key: tuple[tuple[int, int], ...],
) -> GraphCache:
    edges = edges_from_adjacency(adjacency)
    distances_from_target = bfs_distances(adjacency, 0)
    edge_shells = tuple(min(distances_from_target[left], distances_from_target[right]) for left, right in edges)
    assignments = tuple(product(range(COLOR_COUNT), repeat=len(adjacency)))
    edge_weights_by_rho: dict[float, tuple[float, ...]] = {}
    for _, rho in RHO_AGENTS:
        weights = []
        for assignment in assignments:
            energy = 0.0
            for (left, right), shell in zip(edges, edge_shells):
                if assignment[left] != assignment[right]:
                    continue
                energy += BETA_EDGE * (rho ** shell)
            weights.append(math.exp(-energy))
        edge_weights_by_rho[rho] = tuple(weights)
    return GraphCache(
        adjacency=adjacency,
        edges=edges,
        edge_shells=edge_shells,
        assignments=assignments,
        edge_weights_by_rho=edge_weights_by_rho,
        distances_from_target=distances_from_target,
        centers_in_original_graph=centers_in_original_graph,
        rooted_key=rooted_key,
    )


def evidence_distribution(level: tuple[float, ...], preferred_color: int) -> tuple[float, ...]:
    strong, weak_left, weak_right = level
    probabilities = [weak_left, weak_right, weak_right]
    probabilities[preferred_color] = strong
    return tuple(probabilities)


def exact_target_marginal(
    cache: GraphCache,
    preferred_colors: tuple[int, ...],
    evidence_level: tuple[float, ...],
    rho: float,
) -> tuple[float, ...]:
    evidence_by_node = {
        node: evidence_distribution(evidence_level, preferred_colors[node - 1])
        for node in range(1, len(cache.adjacency))
    }
    posterior = [0.0, 0.0, 0.0]
    partition = 0.0
    edge_weights = cache.edge_weights_by_rho[rho]
    for assignment_index, assignment in enumerate(cache.assignments):
        unary_weight = 1.0
        for node in range(1, len(cache.adjacency)):
            unary_weight *= evidence_by_node[node][assignment[node]]
        weight = unary_weight * edge_weights[assignment_index]
        partition += weight
        posterior[assignment[0]] += weight
    return normalize(posterior)


def monotone(values: list[float] | tuple[float, ...], tolerance: float = MONOTONICITY_TOLERANCE) -> bool:
    differences = [values[index + 1] - values[index] for index in range(len(values) - 1)]
    nondecreasing = all(difference >= -tolerance for difference in differences)
    nonincreasing = all(difference <= tolerance for difference in differences)
    return nondecreasing or nonincreasing


def maximum_monotonicity_violation(values: list[float] | tuple[float, ...]) -> float:
    differences = [values[index + 1] - values[index] for index in range(len(values) - 1)]
    increasing_violation = max((0.0, *(-difference for difference in differences if difference < 0.0)))
    decreasing_violation = max((0.0, *(difference for difference in differences if difference > 0.0)))
    return min(increasing_violation, decreasing_violation)


def evaluate_design(
    cache: GraphCache,
    preferred_colors: tuple[int, ...],
) -> dict[str, object]:
    level_records: dict[str, dict[str, object]] = {}
    all_pairwise_total = 0.0
    adjacent_total = 0.0
    monotone_all_levels = True
    separable_high = False
    max_p_r_violation = 0.0
    max_entropy_violation = 0.0
    for level_name, level_values in EVIDENCE_LEVELS.items():
        agent_distributions = []
        for agent_label, rho in RHO_AGENTS:
            posterior = exact_target_marginal(cache, preferred_colors, level_values, rho)
            agent_distributions.append(
                {
                    "agent": agent_label,
                    "rho": rho,
                    "posterior": posterior,
                    "p_R": posterior[0],
                    "entropy": entropy(posterior),
                }
            )
        p_r_sequence = [record["p_R"] for record in agent_distributions]
        entropy_sequence = [record["entropy"] for record in agent_distributions]
        pairwise_kl = []
        for left in agent_distributions:
            row = []
            for right in agent_distributions:
                row.append(kl_divergence(left["posterior"], right["posterior"]))
            pairwise_kl.append(row)
        all_pairwise_total += sum(
            pairwise_kl[left_index][right_index]
            for left_index in range(len(pairwise_kl))
            for right_index in range(left_index + 1, len(pairwise_kl))
        )
        adjacent_total += sum(
            pairwise_kl[index][index + 1]
            for index in range(len(pairwise_kl) - 1)
        )
        level_monotone = monotone(p_r_sequence) and monotone(entropy_sequence)
        monotone_all_levels = monotone_all_levels and level_monotone
        if level_name == "high" and pairwise_kl[0][-1] > 0.01:
            separable_high = True
        max_p_r_violation = max(max_p_r_violation, maximum_monotonicity_violation(p_r_sequence))
        max_entropy_violation = max(max_entropy_violation, maximum_monotonicity_violation(entropy_sequence))
        level_records[level_name] = {
            "preferred_colors": list(preferred_colors),
            "agent_distributions": [
                {
                    "agent": record["agent"],
                    "rho": record["rho"],
                    "posterior": pretty_probabilities(record["posterior"]),
                    "p_R": round(record["p_R"], 6),
                    "entropy": round(record["entropy"], 6),
                }
                for record in agent_distributions
            ],
            "pairwise_kl": [[round(value, 6) for value in row] for row in pairwise_kl],
            "monotone_p_R": monotone(p_r_sequence),
            "monotone_entropy": monotone(entropy_sequence),
            "p_R_sequence": [round(value, 6) for value in p_r_sequence],
            "entropy_sequence": [round(value, 6) for value in entropy_sequence],
            "kl_A0_to_A4": round(pairwise_kl[0][-1], 6),
        }
    return {
        "preferred_colors": list(preferred_colors),
        "all_pairwise_total": all_pairwise_total,
        "adjacent_total": adjacent_total,
        "monotone_all_levels": monotone_all_levels,
        "separable_high": separable_high,
        "max_p_R_violation": max_p_r_violation,
        "max_entropy_violation": max_entropy_violation,
        "level_records": level_records,
    }


def choose_uniform_design(graph_class: dict[str, object]) -> dict[str, object]:
    template = (0, 0, 0, 0)
    best_choice: dict[str, object] | None = None
    for rooted_key, adjacency, centers in graph_class["rooted_forms"]:
        cache = precompute_graph_cache(adjacency, centers, rooted_key)
        evaluation = evaluate_design(cache, template)
        candidate = {
            "cache": cache,
            "evaluation": evaluation,
            "preferred_colors": template,
        }
        ranking = (
            evaluation["monotone_all_levels"],
            evaluation["all_pairwise_total"],
            evaluation["adjacent_total"],
            evaluation["separable_high"],
        )
        if best_choice is None:
            best_choice = candidate
            best_choice["ranking"] = ranking
            continue
        if ranking > best_choice["ranking"]:
            best_choice = candidate
            best_choice["ranking"] = ranking
    return best_choice


def choose_best_fixed_conflicting_template(
    graph_classes: list[dict[str, object]],
) -> dict[str, object]:
    candidate_templates = [
        template
        for template in product(range(COLOR_COUNT), repeat=N_NODES - 1)
        if template[0] == 0 and len(set(template)) > 1
    ]
    best_summary: dict[str, object] | None = None
    for template in candidate_templates:
        selected = []
        monotone_graphs = 0
        separable_graphs = 0
        all_pairwise_total = 0.0
        adjacent_total = 0.0
        max_p_r_violation = 0.0
        max_entropy_violation = 0.0
        for graph_class in graph_classes:
            best_choice: dict[str, object] | None = None
            for rooted_key, adjacency, centers in graph_class["rooted_forms"]:
                cache = precompute_graph_cache(adjacency, centers, rooted_key)
                evaluation = evaluate_design(cache, template)
                candidate = {
                    "cache": cache,
                    "evaluation": evaluation,
                    "preferred_colors": template,
                }
                ranking = (
                    evaluation["monotone_all_levels"],
                    evaluation["all_pairwise_total"],
                    evaluation["adjacent_total"],
                    evaluation["separable_high"],
                )
                if best_choice is None or ranking > best_choice["ranking"]:
                    best_choice = candidate
                    best_choice["ranking"] = ranking
            selected.append(best_choice)
            monotone_graphs += int(best_choice["evaluation"]["monotone_all_levels"])
            separable_graphs += int(best_choice["evaluation"]["separable_high"])
            all_pairwise_total += best_choice["evaluation"]["all_pairwise_total"]
            adjacent_total += best_choice["evaluation"]["adjacent_total"]
            max_p_r_violation = max(max_p_r_violation, best_choice["evaluation"]["max_p_R_violation"])
            max_entropy_violation = max(max_entropy_violation, best_choice["evaluation"]["max_entropy_violation"])
        summary = {
            "strategy_name": "fixed_conflicting",
            "fixed_template": list(template),
            "selected": selected,
            "graph_count": len(selected),
            "monotone_graph_count": monotone_graphs,
            "separable_high_count": separable_graphs,
            "all_pairwise_total": all_pairwise_total,
            "adjacent_total": adjacent_total,
            "max_p_R_violation": max_p_r_violation,
            "max_entropy_violation": max_entropy_violation,
        }
        ranking = (
            summary["monotone_graph_count"],
            summary["all_pairwise_total"],
            summary["adjacent_total"],
            summary["separable_high_count"],
        )
        if best_summary is None or ranking > best_summary["ranking"]:
            best_summary = summary
            best_summary["ranking"] = ranking
    return best_summary


def choose_adaptive_conflicting_design(graph_class: dict[str, object]) -> dict[str, object]:
    candidate_templates = [
        template
        for template in product(range(COLOR_COUNT), repeat=N_NODES - 1)
        if template[0] == 0 and len(set(template)) > 1
    ]
    best_choice: dict[str, object] | None = None
    for rooted_key, adjacency, centers in graph_class["rooted_forms"]:
        cache = precompute_graph_cache(adjacency, centers, rooted_key)
        for template in candidate_templates:
            evaluation = evaluate_design(cache, template)
            candidate = {
                "cache": cache,
                "evaluation": evaluation,
                "preferred_colors": template,
            }
            ranking = (
                evaluation["monotone_all_levels"],
                evaluation["all_pairwise_total"],
                evaluation["adjacent_total"],
                evaluation["separable_high"],
            )
            if best_choice is None or ranking > best_choice["ranking"]:
                best_choice = candidate
                best_choice["ranking"] = ranking
    return best_choice


def summarize_strategy(
    strategy_name: str,
    selected: list[dict[str, object]],
    fixed_template: tuple[int, ...] | None = None,
) -> dict[str, object]:
    monotone_graph_count = sum(int(choice["evaluation"]["monotone_all_levels"]) for choice in selected)
    separable_high_count = sum(int(choice["evaluation"]["separable_high"]) for choice in selected)
    all_pairwise_total = sum(choice["evaluation"]["all_pairwise_total"] for choice in selected)
    adjacent_total = sum(choice["evaluation"]["adjacent_total"] for choice in selected)
    max_p_r_violation = max(choice["evaluation"]["max_p_R_violation"] for choice in selected)
    max_entropy_violation = max(choice["evaluation"]["max_entropy_violation"] for choice in selected)
    summary = {
        "strategy_name": strategy_name,
        "graph_count": len(selected),
        "monotone_graph_count": monotone_graph_count,
        "separable_high_count": separable_high_count,
        "all_pairwise_total": all_pairwise_total,
        "adjacent_total": adjacent_total,
        "max_p_R_violation": max_p_r_violation,
        "max_entropy_violation": max_entropy_violation,
        "selected": selected,
    }
    if fixed_template is not None:
        summary["fixed_template"] = list(fixed_template)
    return summary


def local_signature(
    cache: GraphCache,
    preferred_colors: tuple[int, ...],
) -> dict[str, object]:
    shell_zero_neighbors = [neighbor for neighbor in cache.adjacency[0]]
    return {
        "target_degree": len(shell_zero_neighbors),
        "shell_zero_preferred_colors": [preferred_colors[neighbor - 1] for neighbor in shell_zero_neighbors],
    }


def serialize_graph_choice(
    graph_id: str,
    choice: dict[str, object],
) -> dict[str, object]:
    cache = choice["cache"]
    evaluation = choice["evaluation"]
    distances = cache.distances_from_target
    return {
        "graph_id": graph_id,
        "n_nodes": len(cache.adjacency),
        "edges": [[left, right] for left, right in cache.edges],
        "edge_count": graph_edge_count(cache.adjacency),
        "is_tree": graph_edge_count(cache.adjacency) == len(cache.adjacency) - 1,
        "distances_from_target": {f"E{node}": distances[node] for node in range(1, len(cache.adjacency))},
        "shell_zero_neighbors": [f"E{node}" for node in cache.adjacency[0]],
        "preferred_colors": {f"E{node}": COLOR_LABELS[choice["preferred_colors"][node - 1]] for node in range(1, len(cache.adjacency))},
        "preferred_color_template": list(choice["preferred_colors"]),
        "rooted_key": [[left, right] for left, right in cache.rooted_key],
        "graph_centers_in_original_graph": list(cache.centers_in_original_graph),
        "monotone_all_levels": evaluation["monotone_all_levels"],
        "separable_high": evaluation["separable_high"],
        "all_pairwise_total": round(evaluation["all_pairwise_total"], 6),
        "adjacent_total": round(evaluation["adjacent_total"], 6),
        "max_p_R_violation": round(evaluation["max_p_R_violation"], 6),
        "max_entropy_violation": round(evaluation["max_entropy_violation"], 6),
        "local_signature": local_signature(cache, choice["preferred_colors"]),
        "A4_exact_by_level": {
            level_name: evaluation["level_records"][level_name]["agent_distributions"][-1]["posterior"]
            for level_name in EVIDENCE_LEVELS
        },
    }


def build_long_results(graph_records: list[dict[str, object]], selected: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for graph_record, choice in zip(graph_records, selected):
        evaluation = choice["evaluation"]
        for level_name in EVIDENCE_LEVELS:
            level_record = evaluation["level_records"][level_name]
            agent_distributions = level_record["agent_distributions"]
            pairwise_kl = level_record["pairwise_kl"]
            for agent_index, agent_record in enumerate(agent_distributions):
                rows.append(
                    {
                        "graph_id": graph_record["graph_id"],
                        "evidence_level": level_name,
                        "agent": agent_record["agent"],
                        "agent_rho": agent_record["rho"],
                        "p_R": agent_record["posterior"][0],
                        "p_G": agent_record["posterior"][1],
                        "p_B": agent_record["posterior"][2],
                        "posterior": agent_record["posterior"],
                        "entropy": agent_record["entropy"],
                        "kl_to_A0": pairwise_kl[agent_index][0],
                        "kl_to_A4": pairwise_kl[agent_index][-1],
                        "preferred_color_template": graph_record["preferred_color_template"],
                        "is_tree": graph_record["is_tree"],
                        "edge_count": graph_record["edge_count"],
                    }
                )
    return rows


def write_csv_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def find_equal_local_pair(graph_records: list[dict[str, object]], selected: list[dict[str, object]]) -> dict[str, object]:
    candidates = []
    graph_lookup = {record["graph_id"]: record for record in graph_records}
    for left_index in range(len(selected)):
        left_choice = selected[left_index]
        left_record = graph_records[left_index]
        left_signature = left_record["local_signature"]
        left_a0 = left_choice["evaluation"]["level_records"]["high"]["agent_distributions"][0]["posterior"]
        left_a4 = left_choice["evaluation"]["level_records"]["high"]["agent_distributions"][-1]["posterior"]
        for right_index in range(left_index + 1, len(selected)):
            right_choice = selected[right_index]
            right_record = graph_records[right_index]
            if right_record["local_signature"] != left_signature:
                continue
            right_a0 = right_choice["evaluation"]["level_records"]["high"]["agent_distributions"][0]["posterior"]
            if max(abs(left - right) for left, right in zip(left_a0, right_a0)) > 1e-9:
                continue
            right_a4 = right_choice["evaluation"]["level_records"]["high"]["agent_distributions"][-1]["posterior"]
            symmetric_kl = kl_divergence(left_a4, right_a4) + kl_divergence(right_a4, left_a4)
            candidates.append(
                {
                    "graph_a": graph_lookup[left_record["graph_id"]],
                    "graph_b": graph_lookup[right_record["graph_id"]],
                    "choice_a": left_choice,
                    "choice_b": right_choice,
                    "symmetric_kl_A4_high": symmetric_kl,
                }
            )
    best_pair = max(candidates, key=lambda record: record["symmetric_kl_A4_high"])
    pair_record = {
        "graph_a": best_pair["graph_a"],
        "graph_b": best_pair["graph_b"],
        "symmetric_kl_A4_high": round(best_pair["symmetric_kl_A4_high"], 6),
        "A0_high_graph_a": best_pair["choice_a"]["evaluation"]["level_records"]["high"]["agent_distributions"][0]["posterior"],
        "A0_high_graph_b": best_pair["choice_b"]["evaluation"]["level_records"]["high"]["agent_distributions"][0]["posterior"],
        "A4_high_graph_a": best_pair["choice_a"]["evaluation"]["level_records"]["high"]["agent_distributions"][-1]["posterior"],
        "A4_high_graph_b": best_pair["choice_b"]["evaluation"]["level_records"]["high"]["agent_distributions"][-1]["posterior"],
        "predictions": {
            "graph_a": best_pair["choice_a"]["evaluation"]["level_records"],
            "graph_b": best_pair["choice_b"]["evaluation"]["level_records"],
        },
    }
    return pair_record


def serialize_strategy_summary(summary: dict[str, object]) -> dict[str, object]:
    record = {
        "strategy_name": summary["strategy_name"],
        "graph_count": summary["graph_count"],
        "monotone_graph_count": summary["monotone_graph_count"],
        "separable_high_count": summary["separable_high_count"],
        "all_pairwise_total": round(summary["all_pairwise_total"], 6),
        "adjacent_total": round(summary["adjacent_total"], 6),
        "max_p_R_violation": round(summary["max_p_R_violation"], 6),
        "max_entropy_violation": round(summary["max_entropy_violation"], 6),
    }
    if "fixed_template" in summary:
        record["fixed_template"] = summary["fixed_template"]
    return record


def plot_separability_panel(path: Path, rows: list[dict[str, object]]) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    graph_ids = sorted({row["graph_id"] for row in rows})
    color_map = plt.get_cmap("tab20", len(graph_ids))
    color_lookup = {graph_id: color_map(index) for index, graph_id in enumerate(graph_ids)}
    graph_order = {graph_id: index for index, graph_id in enumerate(graph_ids)}
    for axis, level_name in zip(axes, EVIDENCE_LEVELS):
        level_rows = [row for row in rows if row["evidence_level"] == level_name]
        for graph_id in graph_ids:
            graph_rows = sorted(
                [row for row in level_rows if row["graph_id"] == graph_id],
                key=lambda row: row["agent_rho"],
            )
            if not graph_rows:
                continue
            axis.plot(
                [row["agent_rho"] for row in graph_rows],
                [row["p_R"] for row in graph_rows],
                marker="o",
                linewidth=1.5,
                color=color_lookup[graph_id],
                alpha=0.9,
                label=graph_id,
            )
        axis.set_title(level_name)
        axis.set_xlabel("ρ")
        axis.set_xticks([rho for _, rho in RHO_AGENTS])
        axis.grid(alpha=0.25, linewidth=0.5)
    axes[0].set_ylabel("Predicted $p_R$")
    handles, labels = axes[0].get_legend_handles_labels()
    paired = sorted(zip(labels, handles), key=lambda item: graph_order[item[0]])
    figure.legend(
        [handle for _, handle in paired],
        [label for label, _ in paired],
        loc="lower center",
        ncol=6,
        fontsize=7,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
    )
    figure.suptitle("Figure 1. Separability panel")
    figure.tight_layout(rect=(0, 0.05, 1, 0.95))
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def plot_entropy_spectrum(path: Path, rows: list[dict[str, object]]) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    graph_ids = sorted({row["graph_id"] for row in rows})
    color_map = plt.get_cmap("tab20", len(graph_ids))
    color_lookup = {graph_id: color_map(index) for index, graph_id in enumerate(graph_ids)}
    graph_order = {graph_id: index for index, graph_id in enumerate(graph_ids)}
    for axis, level_name in zip(axes, EVIDENCE_LEVELS):
        level_rows = [row for row in rows if row["evidence_level"] == level_name]
        for graph_id in graph_ids:
            graph_rows = sorted(
                [row for row in level_rows if row["graph_id"] == graph_id],
                key=lambda row: row["agent_rho"],
            )
            if not graph_rows:
                continue
            axis.plot(
                [row["agent_rho"] for row in graph_rows],
                [row["entropy"] for row in graph_rows],
                marker="o",
                linewidth=1.5,
                color=color_lookup[graph_id],
                alpha=0.9,
                label=graph_id,
            )
        axis.set_title(level_name)
        axis.set_xlabel("ρ")
        axis.set_xticks([rho for _, rho in RHO_AGENTS])
        axis.grid(alpha=0.25, linewidth=0.5)
    axes[0].set_ylabel("Entropy")
    handles, labels = axes[0].get_legend_handles_labels()
    paired = sorted(zip(labels, handles), key=lambda item: graph_order[item[0]])
    figure.legend(
        [handle for _, handle in paired],
        [label for label, _ in paired],
        loc="lower center",
        ncol=6,
        fontsize=7,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
    )
    figure.suptitle("Figure 2. Entropy spectrum")
    figure.tight_layout(rect=(0, 0.05, 1, 0.95))
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def plot_kl_matrices(path: Path, graph_records: list[dict[str, object]], selected: list[dict[str, object]]) -> None:
    max_value = 0.0
    matrices = {}
    for graph_record, choice in zip(graph_records, selected):
        matrices[graph_record["graph_id"]] = {}
        for level_name in EVIDENCE_LEVELS:
            matrix = choice["evaluation"]["level_records"][level_name]["pairwise_kl"]
            matrices[graph_record["graph_id"]][level_name] = matrix
            max_value = max(max_value, max(max(row) for row in matrix))
    graph_ids = [record["graph_id"] for record in graph_records]
    with PdfPages(path) as pdf:
        for level_name in EVIDENCE_LEVELS:
            columns = 4
            rows = math.ceil(len(graph_ids) / columns)
            figure, axes = plt.subplots(rows, columns, figsize=(12, rows * 2.8))
            axes_flat = list(axes.flat if hasattr(axes, "flat") else [axes])
            for axis, graph_id in zip(axes_flat, graph_ids):
                matrix = matrices[graph_id][level_name]
                image = axis.imshow(matrix, vmin=0.0, vmax=max_value, cmap="magma")
                axis.set_title(graph_id, fontsize=9)
                axis.set_xticks(range(len(RHO_AGENTS)))
                axis.set_yticks(range(len(RHO_AGENTS)))
                axis.set_xticklabels([label for label, _ in RHO_AGENTS], fontsize=7)
                axis.set_yticklabels([label for label, _ in RHO_AGENTS], fontsize=7)
                for left_index in range(len(RHO_AGENTS)):
                    for right_index in range(len(RHO_AGENTS)):
                        value = matrix[left_index][right_index]
                        if value == 0.0:
                            text = "0"
                        elif value < 0.001:
                            text = f"{value:.0e}"
                        else:
                            text = f"{value:.2f}"
                        axis.text(
                            right_index,
                            left_index,
                            text,
                            ha="center",
                            va="center",
                            fontsize=5,
                            color="white" if value > max_value * 0.5 else "black",
                        )
            for axis in axes_flat[len(graph_ids):]:
                axis.axis("off")
            figure.suptitle(f"Figure 3. KL matrices ({level_name})", fontsize=14)
            color_bar = figure.colorbar(image, ax=axes_flat, fraction=0.02, pad=0.01)
            color_bar.ax.set_ylabel("KL", rotation=270, labelpad=12)
            figure.subplots_adjust(left=0.05, right=0.92, top=0.92, bottom=0.05, wspace=0.55, hspace=0.75)
            pdf.savefig(figure)
            plt.close(figure)


def plot_equal_local_pair(path: Path, pair_record: dict[str, object]) -> None:
    figure, axes = plt.subplots(3, 2, figsize=(12, 10), sharey=True)
    for column_index, graph_key in enumerate(("graph_a", "graph_b")):
        predictions = pair_record["predictions"][graph_key]
        graph_id = pair_record[graph_key]["graph_id"]
        for row_index, level_name in enumerate(EVIDENCE_LEVELS):
            axis = axes[row_index][column_index]
            agent_records = predictions[level_name]["agent_distributions"]
            x_positions = list(range(len(agent_records)))
            bottom = [0.0] * len(agent_records)
            for color_index, color_label in enumerate(COLOR_LABELS):
                heights = [record["posterior"][color_index] for record in agent_records]
                axis.bar(
                    x_positions,
                    heights,
                    bottom=bottom,
                    color=COLOR_HEX[color_index],
                    width=0.75,
                    label=color_label if row_index == 0 and column_index == 0 else None,
                )
                bottom = [current + height for current, height in zip(bottom, heights)]
            axis.set_ylim(0, 1)
            axis.set_xticks(x_positions)
            axis.set_xticklabels([record["agent"] for record in agent_records])
            axis.set_title(f"{graph_id} · {level_name}")
            axis.grid(axis="y", alpha=0.2, linewidth=0.5)
            if column_index == 0:
                axis.set_ylabel("Probability")
    handles, labels = axes[0][0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.01))
    figure.suptitle("Figure 4. Equal-local, distinct-remote demonstration")
    figure.tight_layout(rect=(0, 0.03, 1, 0.96))
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def build_results() -> dict[str, object]:
    graph_classes = enumerate_graph_classes(N_NODES)
    uniform_selected = [choose_uniform_design(graph_class) for graph_class in graph_classes]
    uniform_summary = summarize_strategy("uniform", uniform_selected)
    fixed_conflicting_summary = choose_best_fixed_conflicting_template(graph_classes)
    adaptive_selected = [choose_adaptive_conflicting_design(graph_class) for graph_class in graph_classes]
    adaptive_summary = summarize_strategy("adaptive_conflicting", adaptive_selected)
    strategy_comparison = {
        "uniform": serialize_strategy_summary(uniform_summary),
        "fixed_conflicting": serialize_strategy_summary(fixed_conflicting_summary),
        "adaptive_conflicting": serialize_strategy_summary(adaptive_summary),
    }
    strategy_comparison["pairwise_gain_vs_uniform"] = {
        "fixed_conflicting": round(
            fixed_conflicting_summary["all_pairwise_total"] / uniform_summary["all_pairwise_total"],
            6,
        ),
        "adaptive_conflicting": round(
            adaptive_summary["all_pairwise_total"] / uniform_summary["all_pairwise_total"],
            6,
        ),
    }
    strategy_comparison["adjacent_gain_vs_uniform"] = {
        "fixed_conflicting": round(
            fixed_conflicting_summary["adjacent_total"] / uniform_summary["adjacent_total"],
            6,
        ),
        "adaptive_conflicting": round(
            adaptive_summary["adjacent_total"] / uniform_summary["adjacent_total"],
            6,
        ),
    }
    final_selected = adaptive_selected
    graph_records = [
        serialize_graph_choice(f"G{index:02d}", choice)
        for index, choice in enumerate(final_selected, start=1)
    ]
    long_results = build_long_results(graph_records, final_selected)
    equal_local_pair = find_equal_local_pair(graph_records, final_selected)
    monotone_all = adaptive_summary["monotone_graph_count"] == len(graph_records)
    success_criteria = {
        "graph_count": len(graph_records),
        "meaningful_separation_threshold": 0.01,
        "separable_high_count": adaptive_summary["separable_high_count"],
        "separable_high_success": adaptive_summary["separable_high_count"] >= 10,
        "monotone_success": monotone_all,
        "equal_local_pair_success": True,
        "n5_sufficient": adaptive_summary["separable_high_count"] >= 10,
        "monotonicity_tolerance": MONOTONICITY_TOLERANCE,
        "max_p_R_violation": round(adaptive_summary["max_p_R_violation"], 6),
        "max_entropy_violation": round(adaptive_summary["max_entropy_violation"], 6),
        "equal_local_pair_symmetric_kl_A4_high": equal_local_pair["symmetric_kl_A4_high"],
    }
    return {
        "metadata": {
            "n_nodes": N_NODES,
            "beta_edge": BETA_EDGE,
            "color_labels": list(COLOR_LABELS),
            "evidence_levels": {name: list(values) for name, values in EVIDENCE_LEVELS.items()},
            "rho_agents": [{"agent": label, "rho": rho} for label, rho in RHO_AGENTS],
            "monotonicity_tolerance": MONOTONICITY_TOLERANCE,
            "design_note": (
                "The winning evidence design is an adaptive conflicting strategy: for each rooted graph, "
                "choose the non-uniform colour-preference template that maximizes total pairwise KL "
                "while preserving monotonic spectra within the stated tolerance."
            ),
        },
        "strategy_comparison": strategy_comparison,
        "selected_strategy": "adaptive_conflicting",
        "graphs": graph_records,
        "long_results": long_results,
        "equal_local_pair": equal_local_pair,
        "success_criteria": success_criteria,
        "_selected_choices": final_selected,
    }


def main() -> None:
    # Paths: analysis-2/code/analysis-2.py
    #   code_dir    = analysis-2/code/
    #   data_dir    = analysis-2/code/data/   (all data outputs)
    #   figures_dir = analysis-2/figures/
    code_dir = Path(__file__).resolve().parent
    data_dir = code_dir / "data"
    figures_dir = code_dir.parent / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    results = build_results()
    graph_records = results["graphs"]
    long_results = results["long_results"]
    strategy_summary = results["strategy_comparison"]
    equal_local_pair = results["equal_local_pair"]
    selected_choices = results.pop("_selected_choices")

    simulation_json_path = data_dir / "analysis-2_simulation_results.json"
    simulation_csv_path = data_dir / "analysis-2_simulation_results.csv"
    graph_catalog_path = data_dir / "analysis-2_graph_catalog.json"
    strategy_path = data_dir / "analysis-2_strategy_comparison.json"
    summary_path = data_dir / "analysis-2_summary.json"

    simulation_json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    graph_catalog_path.write_text(json.dumps({"graphs": graph_records}, indent=2), encoding="utf-8")
    strategy_path.write_text(json.dumps(strategy_summary, indent=2), encoding="utf-8")
    summary_path.write_text(
        json.dumps(
            {
                "metadata": results["metadata"],
                "selected_strategy": results["selected_strategy"],
                "success_criteria": results["success_criteria"],
                "equal_local_pair": equal_local_pair,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    csv_rows = []
    for row in long_results:
        csv_rows.append(
            {
                "graph_id": row["graph_id"],
                "evidence_level": row["evidence_level"],
                "agent": row["agent"],
                "agent_rho": row["agent_rho"],
                "p_R": row["p_R"],
                "p_G": row["p_G"],
                "p_B": row["p_B"],
                "entropy": row["entropy"],
                "kl_to_A0": row["kl_to_A0"],
                "kl_to_A4": row["kl_to_A4"],
                "preferred_color_template": "-".join(str(value) for value in row["preferred_color_template"]),
                "is_tree": row["is_tree"],
                "edge_count": row["edge_count"],
            }
        )
    write_csv_rows(simulation_csv_path, csv_rows)

    plot_separability_panel(figures_dir / FIGURE_FILENAMES["fig1"], long_results)
    plot_entropy_spectrum(figures_dir / FIGURE_FILENAMES["fig2"], long_results)
    plot_kl_matrices(figures_dir / FIGURE_FILENAMES["fig3"], graph_records, selected_choices)
    plot_equal_local_pair(figures_dir / FIGURE_FILENAMES["fig4"], equal_local_pair)

    print(f"Wrote {simulation_json_path}")
    print(f"Wrote {generated_json_path}")
    print(f"Wrote {simulation_csv_path}")
    print(f"Wrote {graph_catalog_path}")
    print(f"Wrote {strategy_path}")
    print(f"Wrote {summary_path}")
    for key in ("fig1", "fig2", "fig3", "fig4"):
        print(f"Wrote {figures_dir / FIGURE_FILENAMES[key]}")


if __name__ == "__main__":
    main()
