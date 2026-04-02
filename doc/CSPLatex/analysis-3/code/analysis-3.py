#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations, permutations, product
import csv
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt


COLOR_COUNT = 3
COLOR_LABELS = ("R", "G", "B")
COLOR_HEX = {"R": "#d73027", "G": "#1a9850", "B": "#4575b4"}
RHO_AGENTS = (("A0", 0.0), ("A1", 0.25), ("A2", 0.50), ("A3", 0.75), ("A4", 1.0))
EVIDENCE_LEVELS = {
    "high": (0.9, 0.05, 0.05),
    "medium": (0.6, 0.2, 0.2),
    "low": (0.4, 0.3, 0.3),
}
BETA_EDGE = 4.0
MONOTONICITY_TOLERANCE = 5e-4
N_RANGE = (5, 6)
SELECTED_STIMULUS_TARGET_COUNT = 8
VISIBLE_D2_KL_DIFFERENCE = 0.5
FIGURE_FILENAMES = {
    "fig1": "analysis-3_fig1_design_schematic.pdf",
    "fig2": "analysis-3_fig2_rooted_stimulus_gallery.pdf",
    "fig3": "analysis-3_fig3_matched_comparisons.pdf",
    "fig4": "analysis-3_fig4_selected_stimuli_with_evidence.pdf",
    "fig5": "analysis-3_fig5_descriptor_effects.pdf",
}


@dataclass(frozen=True)
class GraphCache:
    n_nodes: int
    adjacency: tuple[tuple[int, ...], ...]
    edges: tuple[tuple[int, int], ...]
    edges_set: frozenset[tuple[int, int]]
    assignments: tuple[tuple[int, ...], ...]
    edge_weights_by_rho: dict[float, tuple[float, ...]]
    distances_from_target: dict[int, int]
    rooted_key: tuple[tuple[int, int], ...]
    centers_in_original_graph: tuple[int, ...]


@dataclass(frozen=True)
class TemplateCache:
    templates: tuple[tuple[int, ...], ...]
    unary_weights_by_template: dict[tuple[int, ...], dict[str, tuple[float, ...]]]


def normalize(values: list[float] | tuple[float, ...]) -> tuple[float, ...]:
    total = sum(values)
    return tuple(value / total for value in values)


def entropy(probabilities: tuple[float, ...] | list[float]) -> float:
    return -sum(probability * math.log(probability) for probability in probabilities if probability > 0.0)


def kl_divergence(p: tuple[float, ...] | list[float], q: tuple[float, ...] | list[float]) -> float:
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


def connected(adjacency: tuple[tuple[int, ...], ...]) -> bool:
    if not adjacency:
        return False
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


def enumerate_rooted_graphs(n_nodes: int) -> list[GraphCache]:
    all_edges = list(combinations(range(n_nodes), 2))
    all_permutations = tuple(permutations(range(n_nodes)))
    seen_rooted_keys: set[tuple[int, tuple[tuple[int, int], ...]]] = set()
    rooted_graphs = []
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
        _ = canonical_unrooted_key(adjacency, all_permutations)
        for rooted_key, rooted_adjacency, centers in rooted_central_forms(adjacency):
            dedupe_key = (n_nodes, rooted_key)
            if dedupe_key in seen_rooted_keys:
                continue
            seen_rooted_keys.add(dedupe_key)
            rooted_graphs.append(precompute_graph_cache(rooted_adjacency, centers, rooted_key))
    rooted_graphs.sort(key=lambda cache: (cache.n_nodes, cache.rooted_key))
    return rooted_graphs


def precompute_graph_cache(
    adjacency: tuple[tuple[int, ...], ...],
    centers_in_original_graph: tuple[int, ...],
    rooted_key: tuple[tuple[int, int], ...],
) -> GraphCache:
    edges = edges_from_adjacency(adjacency)
    assignments = tuple(product(range(COLOR_COUNT), repeat=len(adjacency)))
    distances_from_target = bfs_distances(adjacency, 0)
    edge_weights_by_rho: dict[float, tuple[float, ...]] = {}
    for _, rho in RHO_AGENTS:
        weights = []
        for assignment in assignments:
            energy = 0.0
            for left, right in edges:
                shell = min(distances_from_target[left], distances_from_target[right])
                if assignment[left] == assignment[right]:
                    energy += BETA_EDGE * (rho ** shell)
            weights.append(math.exp(-energy))
        edge_weights_by_rho[rho] = tuple(weights)
    return GraphCache(
        n_nodes=len(adjacency),
        adjacency=adjacency,
        edges=edges,
        edges_set=frozenset(edges),
        assignments=assignments,
        edge_weights_by_rho=edge_weights_by_rho,
        distances_from_target=distances_from_target,
        rooted_key=rooted_key,
        centers_in_original_graph=centers_in_original_graph,
    )


def evidence_distribution(level: tuple[float, ...], preferred_color: int) -> tuple[float, ...]:
    strong, weak_left, weak_right = level
    probabilities = [weak_left, weak_right, weak_right]
    probabilities[preferred_color] = strong
    return tuple(probabilities)


def build_template_cache(n_nodes: int) -> TemplateCache:
    templates = tuple(
        template
        for template in product(range(COLOR_COUNT), repeat=n_nodes - 1)
        if template[0] == 0
    )
    assignments = tuple(product(range(COLOR_COUNT), repeat=n_nodes))
    unary_weights_by_template: dict[tuple[int, ...], dict[str, tuple[float, ...]]] = {}
    for template in templates:
        level_weights: dict[str, tuple[float, ...]] = {}
        for level_name, level_values in EVIDENCE_LEVELS.items():
            evidence_by_node = {
                node: evidence_distribution(level_values, template[node - 1])
                for node in range(1, n_nodes)
            }
            weights = []
            for assignment in assignments:
                weight = 1.0
                for node in range(1, n_nodes):
                    weight *= evidence_by_node[node][assignment[node]]
                weights.append(weight)
            level_weights[level_name] = tuple(weights)
        unary_weights_by_template[template] = level_weights
    return TemplateCache(templates=templates, unary_weights_by_template=unary_weights_by_template)


def exact_target_marginal_from_precomputed(
    cache: GraphCache,
    unary_weights: tuple[float, ...],
    rho: float,
) -> tuple[float, ...]:
    posterior = [0.0, 0.0, 0.0]
    partition = 0.0
    edge_weights = cache.edge_weights_by_rho[rho]
    for assignment_index, assignment in enumerate(cache.assignments):
        weight = unary_weights[assignment_index] * edge_weights[assignment_index]
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


def evaluate_template(cache: GraphCache, template_cache: TemplateCache, template: tuple[int, ...]) -> dict[str, object]:
    level_records: dict[str, dict[str, object]] = {}
    all_pairwise_total = 0.0
    adjacent_total = 0.0
    monotone_all_levels = True
    separable_high = False
    max_p_r_violation = 0.0
    max_entropy_violation = 0.0
    for level_name in EVIDENCE_LEVELS:
        unary_weights = template_cache.unary_weights_by_template[template][level_name]
        agent_records = []
        for agent_label, rho in RHO_AGENTS:
            posterior = exact_target_marginal_from_precomputed(cache, unary_weights, rho)
            agent_records.append(
                {
                    "agent": agent_label,
                    "rho": rho,
                    "posterior": posterior,
                    "p_R": posterior[0],
                    "entropy": entropy(posterior),
                }
            )
        pairwise_kl = []
        for left_record in agent_records:
            row = []
            for right_record in agent_records:
                row.append(kl_divergence(left_record["posterior"], right_record["posterior"]))
            pairwise_kl.append(row)
        p_r_sequence = [record["p_R"] for record in agent_records]
        entropy_sequence = [record["entropy"] for record in agent_records]
        all_pairwise_total += sum(
            pairwise_kl[left_index][right_index]
            for left_index in range(len(pairwise_kl))
            for right_index in range(left_index + 1, len(pairwise_kl))
        )
        adjacent_total += sum(pairwise_kl[index][index + 1] for index in range(len(pairwise_kl) - 1))
        level_monotone = monotone(p_r_sequence) and monotone(entropy_sequence)
        monotone_all_levels = monotone_all_levels and level_monotone
        max_p_r_violation = max(max_p_r_violation, maximum_monotonicity_violation(p_r_sequence))
        max_entropy_violation = max(max_entropy_violation, maximum_monotonicity_violation(entropy_sequence))
        if level_name == "high" and pairwise_kl[0][-1] > 0.01:
            separable_high = True
        level_records[level_name] = {
            "agent_distributions": [
                {
                    "agent": record["agent"],
                    "rho": record["rho"],
                    "posterior": pretty_probabilities(record["posterior"]),
                    "p_R": round(record["p_R"], 6),
                    "entropy": round(record["entropy"], 6),
                }
                for record in agent_records
            ],
            "pairwise_kl": [[round(value, 6) for value in row] for row in pairwise_kl],
            "p_R_sequence": [round(value, 6) for value in p_r_sequence],
            "entropy_sequence": [round(value, 6) for value in entropy_sequence],
            "monotone_p_R": monotone(p_r_sequence),
            "monotone_entropy": monotone(entropy_sequence),
            "kl_A0_to_A4": round(pairwise_kl[0][-1], 6),
            "adjacent_kl_sum": round(sum(pairwise_kl[index][index + 1] for index in range(len(pairwise_kl) - 1)), 6),
        }
    return {
        "preferred_colors": list(template),
        "all_pairwise_total": all_pairwise_total,
        "adjacent_total": adjacent_total,
        "monotone_all_levels": monotone_all_levels,
        "separable_high": separable_high,
        "max_p_R_violation": max_p_r_violation,
        "max_entropy_violation": max_entropy_violation,
        "level_records": level_records,
    }


def choose_best_adaptive_conflicting_template(cache: GraphCache, template_cache: TemplateCache) -> dict[str, object]:
    best_choice: dict[str, object] | None = None
    for template in template_cache.templates:
        if len(set(template)) == 1:
            continue
        evaluation = evaluate_template(cache, template_cache, template)
        candidate = {
            "template": template,
            "evaluation": evaluation,
        }
        ranking = (
            evaluation["monotone_all_levels"],
            evaluation["all_pairwise_total"],
            evaluation["adjacent_total"],
            evaluation["separable_high"],
            -evaluation["max_p_R_violation"],
            -evaluation["max_entropy_violation"],
        )
        if best_choice is None or ranking > best_choice["ranking"]:
            best_choice = candidate
            best_choice["ranking"] = ranking
    return best_choice


def count_edges_within(nodes: tuple[int, ...], edges_set: frozenset[tuple[int, int]]) -> int:
    count = 0
    for left_index, left in enumerate(nodes):
        for right in nodes[left_index + 1 :]:
            if (left, right) in edges_set or (right, left) in edges_set:
                count += 1
    return count


def count_edges_between(left_nodes: tuple[int, ...], right_nodes: tuple[int, ...], edges_set: frozenset[tuple[int, int]]) -> int:
    count = 0
    for left in left_nodes:
        for right in right_nodes:
            if left == right:
                continue
            if (min(left, right), max(left, right)) in edges_set:
                count += 1
    return count


def remote_structure_class(s2_count: int, e12: int, e22: int) -> str:
    if s2_count == 0:
        return "D3-0:no-remote"
    if e12 == s2_count and e22 == 0:
        return "D3-1:tree-like-remote"
    return "D3-2:strong-remote"


def descriptor_family_key(descriptor: dict[str, object]) -> tuple[int, int, str]:
    return (descriptor["D1_target_degree"], descriptor["D2_neighbor_coupling"], descriptor["D3_remote_class"])


def raw_descriptor_key(descriptor: dict[str, object]) -> tuple[int, int, int, int, int, int]:
    return (
        descriptor["D1_target_degree"],
        descriptor["D2_neighbor_coupling"],
        descriptor["S2_count"],
        descriptor["e12"],
        descriptor["e22"],
        descriptor["radius"],
    )


def describe_graph(cache: GraphCache) -> dict[str, object]:
    shell1 = tuple(node for node, distance in cache.distances_from_target.items() if distance == 1)
    shell2 = tuple(node for node, distance in cache.distances_from_target.items() if distance == 2)
    shell3 = tuple(node for node, distance in cache.distances_from_target.items() if distance == 3)
    e11 = count_edges_within(shell1, cache.edges_set)
    e22 = count_edges_within(shell2, cache.edges_set) if shell2 else 0
    e12 = count_edges_between(shell1, shell2, cache.edges_set) if shell2 else 0
    max_local_edges = len(shell1) * (len(shell1) - 1) // 2
    closure_density = e11 / max_local_edges if max_local_edges else 0.0
    remote_class = remote_structure_class(len(shell2), e12, e22)
    return {
        "shell1_nodes": list(shell1),
        "shell2_nodes": list(shell2),
        "shell3_nodes": list(shell3),
        "D1_target_degree": len(shell1),
        "D2_neighbor_coupling": e11,
        "S2_count": len(shell2),
        "e12": e12,
        "e22": e22,
        "radius": max(cache.distances_from_target.values()),
        "tree_like": len(cache.edges) == cache.n_nodes - 1,
        "closure_density": round(closure_density, 6),
        "D3_remote_class": remote_class,
    }


def build_rooted_graph_records() -> tuple[list[dict[str, object]], dict[int, TemplateCache]]:
    template_caches = {n_nodes: build_template_cache(n_nodes) for n_nodes in N_RANGE}
    records = []
    graph_index = 1
    for n_nodes in N_RANGE:
        rooted_graphs = enumerate_rooted_graphs(n_nodes)
        for cache in rooted_graphs:
            descriptor = describe_graph(cache)
            best_choice = choose_best_adaptive_conflicting_template(cache, template_caches[n_nodes])
            graph_id = f"RG{graph_index:03d}"
            graph_index += 1
            records.append(
                {
                    "graph_id": graph_id,
                    "cache": cache,
                    "descriptor": descriptor,
                    "best_template": best_choice["template"],
                    "evaluation": best_choice["evaluation"],
                }
            )
    return records, template_caches


def serialize_graph_record(record: dict[str, object]) -> dict[str, object]:
    cache = record["cache"]
    descriptor = record["descriptor"]
    evaluation = record["evaluation"]
    template = record["best_template"]
    preferred_colors = {f"E{node}": COLOR_LABELS[template[node - 1]] for node in range(1, cache.n_nodes)}
    return {
        "graph_id": record["graph_id"],
        "n_nodes": cache.n_nodes,
        "edges": [[left, right] for left, right in cache.edges],
        "distances_from_target": {f"E{node}": distance for node, distance in cache.distances_from_target.items() if node != 0},
        "rooted_key": [[left, right] for left, right in cache.rooted_key],
        "graph_centers_in_original_graph": list(cache.centers_in_original_graph),
        "descriptor": descriptor,
        "preferred_color_template": list(template),
        "preferred_colors": preferred_colors,
        "monotone_all_levels": evaluation["monotone_all_levels"],
        "separable_high": evaluation["separable_high"],
        "all_pairwise_total": round(evaluation["all_pairwise_total"], 6),
        "adjacent_total": round(evaluation["adjacent_total"], 6),
        "max_p_R_violation": round(evaluation["max_p_R_violation"], 6),
        "max_entropy_violation": round(evaluation["max_entropy_violation"], 6),
        "high_kl_A0_to_A4": evaluation["level_records"]["high"]["kl_A0_to_A4"],
        "high_adjacent_kl_sum": evaluation["level_records"]["high"]["adjacent_kl_sum"],
        "A4_exact_by_level": {
            level_name: evaluation["level_records"][level_name]["agent_distributions"][-1]["posterior"]
            for level_name in EVIDENCE_LEVELS
        },
    }


def build_long_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for record in records:
        evaluation = record["evaluation"]
        descriptor = record["descriptor"]
        for level_name in EVIDENCE_LEVELS:
            level_record = evaluation["level_records"][level_name]
            pairwise_kl = level_record["pairwise_kl"]
            for agent_index, agent_record in enumerate(level_record["agent_distributions"]):
                rows.append(
                    {
                        "graph_id": record["graph_id"],
                        "n_nodes": record["cache"].n_nodes,
                        "evidence_level": level_name,
                        "agent": agent_record["agent"],
                        "agent_rho": agent_record["rho"],
                        "p_R": agent_record["posterior"][0],
                        "p_G": agent_record["posterior"][1],
                        "p_B": agent_record["posterior"][2],
                        "entropy": agent_record["entropy"],
                        "kl_to_A0": pairwise_kl[agent_index][0],
                        "kl_to_A4": pairwise_kl[agent_index][-1],
                        "D1_target_degree": descriptor["D1_target_degree"],
                        "D2_neighbor_coupling": descriptor["D2_neighbor_coupling"],
                        "D3_remote_class": descriptor["D3_remote_class"],
                        "S2_count": descriptor["S2_count"],
                        "e12": descriptor["e12"],
                        "e22": descriptor["e22"],
                        "radius": descriptor["radius"],
                        "preferred_color_template": "-".join(str(value) for value in record["best_template"]),
                    }
                )
    return rows


def summarize_dimension(records: list[dict[str, object]], key: str) -> list[dict[str, object]]:
    groups: dict[object, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        groups[record["descriptor"][key]].append(record)
    summary = []
    for value in sorted(groups):
        group = groups[value]
        high_kls = [record["evaluation"]["level_records"]["high"]["kl_A0_to_A4"] for record in group]
        summary.append(
            {
                "value": value,
                "count": len(group),
                "mean_high_kl_A0_to_A4": round(sum(high_kls) / len(high_kls), 6),
                "min_high_kl_A0_to_A4": round(min(high_kls), 6),
                "max_high_kl_A0_to_A4": round(max(high_kls), 6),
                "graph_ids": [record["graph_id"] for record in group],
            }
        )
    return summary


def build_descriptor_results(records: list[dict[str, object]]) -> dict[str, object]:
    family_groups: dict[tuple[int, int, str], list[dict[str, object]]] = defaultdict(list)
    raw_groups: dict[tuple[int, int, int, int, int, int], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        family_groups[descriptor_family_key(record["descriptor"])].append(record)
        raw_groups[raw_descriptor_key(record["descriptor"])].append(record)

    family_summary = []
    representative_by_family: dict[tuple[int, int, str], str] = {}
    for key in sorted(family_groups):
        group = family_groups[key]
        representative = min(
            group,
            key=lambda record: (
                record["cache"].n_nodes,
                -record["evaluation"]["level_records"]["high"]["kl_A0_to_A4"],
                record["graph_id"],
            ),
        )
        representative_by_family[key] = representative["graph_id"]
        high_kls = [record["evaluation"]["level_records"]["high"]["kl_A0_to_A4"] for record in group]
        family_summary.append(
            {
                "family_key": {
                    "D1_target_degree": key[0],
                    "D2_neighbor_coupling": key[1],
                    "D3_remote_class": key[2],
                },
                "count": len(group),
                "representative_graph_id": representative["graph_id"],
                "representative_n_nodes": representative["cache"].n_nodes,
                "mean_high_kl_A0_to_A4": round(sum(high_kls) / len(high_kls), 6),
                "min_high_kl_A0_to_A4": round(min(high_kls), 6),
                "max_high_kl_A0_to_A4": round(max(high_kls), 6),
                "graph_ids": [record["graph_id"] for record in group],
            }
        )

    raw_summary = []
    for key in sorted(raw_groups):
        group = raw_groups[key]
        high_kls = [record["evaluation"]["level_records"]["high"]["kl_A0_to_A4"] for record in group]
        raw_summary.append(
            {
                "raw_key": {
                    "D1_target_degree": key[0],
                    "D2_neighbor_coupling": key[1],
                    "S2_count": key[2],
                    "e12": key[3],
                    "e22": key[4],
                    "radius": key[5],
                },
                "count": len(group),
                "mean_high_kl_A0_to_A4": round(sum(high_kls) / len(high_kls), 6),
                "graph_ids": [record["graph_id"] for record in group],
            }
        )

    return {
        "family_summary": family_summary,
        "raw_descriptor_summary": raw_summary,
        "dimension_summary": {
            "D1_target_degree": summarize_dimension(records, "D1_target_degree"),
            "D2_neighbor_coupling": summarize_dimension(records, "D2_neighbor_coupling"),
            "D3_remote_class": summarize_dimension(records, "D3_remote_class"),
        },
        "representative_by_family": {str(key): value for key, value in representative_by_family.items()},
    }


def find_best_pair(records: list[dict[str, object]], dimension: str) -> dict[str, object]:
    monotone_records = [record for record in records if record["evaluation"]["monotone_all_levels"]]
    candidates = []
    for left_index, left in enumerate(monotone_records):
        for right in monotone_records[left_index + 1 :]:
            left_descriptor = left["descriptor"]
            right_descriptor = right["descriptor"]
            left_kl = left["evaluation"]["level_records"]["high"]["kl_A0_to_A4"]
            right_kl = right["evaluation"]["level_records"]["high"]["kl_A0_to_A4"]
            if dimension == "D1":
                if left_descriptor["D1_target_degree"] == right_descriptor["D1_target_degree"]:
                    continue
                if left_descriptor["D3_remote_class"] != right_descriptor["D3_remote_class"]:
                    continue
                score = (
                    left_descriptor["D2_neighbor_coupling"] == right_descriptor["D2_neighbor_coupling"],
                    -abs(left_descriptor["D2_neighbor_coupling"] - right_descriptor["D2_neighbor_coupling"]),
                    -abs(left_descriptor["S2_count"] - right_descriptor["S2_count"]),
                    -abs(left_descriptor["e12"] - right_descriptor["e12"]),
                    abs(left_kl - right_kl),
                    left_kl + right_kl,
                    -(left["cache"].n_nodes + right["cache"].n_nodes),
                )
            elif dimension == "D2":
                if left_descriptor["D1_target_degree"] != right_descriptor["D1_target_degree"]:
                    continue
                if left_descriptor["D3_remote_class"] != right_descriptor["D3_remote_class"]:
                    continue
                if left_descriptor["D2_neighbor_coupling"] == right_descriptor["D2_neighbor_coupling"]:
                    continue
                # For D2 we want a clean local-coupling manipulation that is visibly useful
                # in the report, not just two already-separable graphs with nearly identical KL.
                score = (
                    left_descriptor["S2_count"] == right_descriptor["S2_count"]
                    and left_descriptor["e12"] == right_descriptor["e12"]
                    and left_descriptor["e22"] == right_descriptor["e22"],
                    left["best_template"] == right["best_template"],
                    abs(left_kl - right_kl) >= VISIBLE_D2_KL_DIFFERENCE,
                    min(left_kl, right_kl),
                    abs(left_descriptor["D2_neighbor_coupling"] - right_descriptor["D2_neighbor_coupling"]),
                    abs(left_kl - right_kl),
                    left_kl + right_kl,
                    -(left["cache"].n_nodes + right["cache"].n_nodes),
                )
            else:
                if left_descriptor["D1_target_degree"] != right_descriptor["D1_target_degree"]:
                    continue
                if left_descriptor["D2_neighbor_coupling"] != right_descriptor["D2_neighbor_coupling"]:
                    continue
                if left_descriptor["D3_remote_class"] == right_descriptor["D3_remote_class"]:
                    continue
                left_remote_code = left_descriptor["D3_remote_class"].split(":")[0]
                right_remote_code = right_descriptor["D3_remote_class"].split(":")[0]
                score = (
                    abs(int(left_remote_code[-1]) - int(right_remote_code[-1])),
                    abs(left_kl - right_kl),
                    left_kl + right_kl,
                    -(left["cache"].n_nodes + right["cache"].n_nodes),
                )
            candidates.append((score, left, right))
    best = max(candidates, key=lambda item: item[0])
    _, left, right = best
    return {
        "dimension": dimension,
        "graph_ids": [left["graph_id"], right["graph_id"]],
        "graphs": [left, right],
        "high_kl_difference": round(
            abs(
                left["evaluation"]["level_records"]["high"]["kl_A0_to_A4"]
                - right["evaluation"]["level_records"]["high"]["kl_A0_to_A4"]
            ),
            6,
        ),
    }


def select_stimuli(records: list[dict[str, object]], matched_pairs: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    selected_ids: dict[str, set[str]] = defaultdict(set)
    for dimension, pair in matched_pairs.items():
        for graph in pair["graphs"]:
            selected_ids[graph["graph_id"]].add(f"matched_{dimension}")

    by_remote_class: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        if not record["evaluation"]["monotone_all_levels"]:
            continue
        by_remote_class[record["descriptor"]["D3_remote_class"]].append(record)
    for remote_class, group in by_remote_class.items():
        if any(record["graph_id"] in selected_ids for record in group):
            continue
        best = max(group, key=lambda record: record["evaluation"]["level_records"]["high"]["kl_A0_to_A4"])
        selected_ids[best["graph_id"]].add("coverage_remote_class")

    ranked_remaining = sorted(
        records,
        key=lambda record: (
            record["evaluation"]["monotone_all_levels"],
            record["evaluation"]["level_records"]["high"]["kl_A0_to_A4"],
            -record["cache"].n_nodes,
        ),
        reverse=True,
    )
    for record in ranked_remaining:
        if len(selected_ids) >= SELECTED_STIMULUS_TARGET_COUNT:
            break
        if record["graph_id"] in selected_ids:
            continue
        selected_ids[record["graph_id"]].add("high_separability")

    selected = []
    lookup = {record["graph_id"]: record for record in records}
    for graph_id in sorted(selected_ids):
        selected.append(
            {
                "record": lookup[graph_id],
                "selection_reasons": sorted(selected_ids[graph_id]),
            }
        )
    return selected


def graph_node_positions(cache: GraphCache) -> dict[int, tuple[float, float]]:
    shell_map: dict[int, list[int]] = defaultdict(list)
    for node, distance in cache.distances_from_target.items():
        shell_map[distance].append(node)
    positions = {0: (0.0, 0.0)}
    shell1 = sorted(shell_map.get(1, []))
    shell2 = sorted(shell_map.get(2, []))
    shell3 = sorted(shell_map.get(3, []))

    def place_nodes(nodes: list[int], radius: float, start_angle: float, end_angle: float) -> None:
        if not nodes:
            return
        if len(nodes) == 1:
            angle_values = [(start_angle + end_angle) / 2.0]
        else:
            step = (end_angle - start_angle) / (len(nodes) - 1)
            angle_values = [start_angle + step * index for index in range(len(nodes))]
        for node, angle in zip(nodes, angle_values):
            radians = math.radians(angle)
            positions[node] = (round(radius * math.cos(radians), 3), round(radius * math.sin(radians), 3))

    place_nodes(shell1, 1.7, 150.0, -150.0)
    place_nodes(shell2, 3.1, 150.0, -150.0)
    place_nodes(shell3, 4.4, 150.0, -150.0)
    return positions


def tikz_escape(text: str) -> str:
    return text.replace("_", "\\_")


def tikz_graph_block(
    record: dict[str, object],
    shift_x: float,
    shift_y: float,
    title: str,
    subtitle_lines: list[str],
    show_evidence_labels: bool,
) -> str:
    cache = record["cache"]
    positions = graph_node_positions(cache)
    descriptor = record["descriptor"]
    template = record["best_template"]
    lines = [f"\\begin{{scope}}[shift={{({shift_x:.2f},{shift_y:.2f})}}]"]
    lines.append(f"\\node[font=\\bfseries] at (0,2.9) {{{tikz_escape(title)}}};")
    for line_index, subtitle in enumerate(subtitle_lines):
        lines.append(f"\\node[font=\\scriptsize] at (0,{2.45 - 0.28 * line_index:.2f}) {{{tikz_escape(subtitle)}}};")
    for left, right in cache.edges:
        x1, y1 = positions[left]
        x2, y2 = positions[right]
        lines.append(f"\\draw[black, thick] ({x1},{y1}) -- ({x2},{y2});")
    for node in range(cache.n_nodes):
        x, y = positions[node]
        if node == 0:
            style = "targetnode"
            label = "X"
        else:
            distance = cache.distances_from_target[node]
            style = "shellonenode" if distance == 1 else "shelltwonode"
            if show_evidence_labels:
                label = COLOR_LABELS[template[node - 1]]
            else:
                label = f"E{node}"
        lines.append(f"\\node[{style}] at ({x},{y}) {{{label}}};")
    lines.append("\\end{scope}")
    return "\n".join(lines)


def write_tikz_figure(path: Path, picture_body: str) -> None:
    tex_source = """\\documentclass{article}
\\usepackage[paperwidth=14in,paperheight=10in,margin=6mm]{geometry}
\\pagestyle{empty}
\\usepackage{tikz}
\\usepackage{xcolor}
\\usetikzlibrary{positioning,fit,calc,backgrounds}
\\tikzset{
    targetnode/.style={circle, draw=black, double, very thick, fill=white, minimum size=7.5mm, inner sep=0pt, font=\\small},
    shellonenode/.style={circle, draw=blue!70!black, very thick, fill=blue!10, minimum size=7.5mm, inner sep=0pt, font=\\scriptsize},
    shelltwonode/.style={circle, draw=teal!70!black, very thick, fill=teal!10, minimum size=7.5mm, inner sep=0pt, font=\\scriptsize},
    shellthreenode/.style={circle, draw=orange!80!black, very thick, fill=orange!10, minimum size=7.5mm, inner sep=0pt, font=\\scriptsize}
}
\\begin{document}
\\thispagestyle{empty}
\\begin{tikzpicture}
%s
\\end{tikzpicture}
\\end{document}
""" % picture_body
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        tex_path = temp_dir / "figure.tex"
        tex_path.write_text(tex_source, encoding="utf-8")
        subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "figure.tex"],
            cwd=temp_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        shutil.copyfile(temp_dir / "figure.pdf", path)


def plot_design_schematic(path: Path) -> None:
    picture = r"""
\node[font=\bfseries\large] at (0,4.8) {Figure 1. Three rooted design dimensions};
\begin{scope}[shift={(-7.0,0)}]
    \node[font=\bfseries] at (0,3.5) {D1: target degree};
    \draw[black, thick] (0,0) -- (-1.4,1.1);
    \draw[black, thick] (0,0) -- (1.4,1.1);
    \node[targetnode] at (0,0) {X};
    \node[shellonenode] at (-1.4,1.1) {E};
    \node[shellonenode] at (1.4,1.1) {E};
    \node[font=\scriptsize, align=center] at (0,-1.4) {$|S_1|$ changes\\the number of direct neighbours};
\end{scope}
\begin{scope}[shift={(0,0)}]
    \node[font=\bfseries] at (0,3.5) {D2: neighbour coupling};
    \draw[black, thick] (0,0) -- (-1.4,1.1);
    \draw[black, thick] (0,0) -- (1.4,1.1);
    \draw[black, thick] (-1.4,1.1) -- (1.4,1.1);
    \node[targetnode] at (0,0) {X};
    \node[shellonenode] at (-1.4,1.1) {E};
    \node[shellonenode] at (1.4,1.1) {E};
    \node[font=\scriptsize, align=center] at (0,-1.4) {$e_{11}$ changes\\direct constraints within $S_1$};
\end{scope}
\begin{scope}[shift={(7.0,0)}]
    \node[font=\bfseries] at (0,3.5) {D3: remote structure};
    \draw[black, thick] (0,0) -- (-1.1,1.0);
    \draw[black, thick] (0,0) -- (1.1,1.0);
    \draw[black, thick] (-1.1,1.0) -- (0,2.1);
    \draw[black, thick] (1.1,1.0) -- (0,2.1);
    \node[targetnode] at (0,0) {X};
    \node[shellonenode] at (-1.1,1.0) {E};
    \node[shellonenode] at (1.1,1.0) {E};
    \node[shelltwonode] at (0,2.1) {E};
    \node[font=\scriptsize, align=center] at (0,-1.4) {$|S_2|, e_{12}, e_{22}$ change\\remote structure beyond $S_1$};
\end{scope}
"""
    write_tikz_figure(path, picture)


def plot_gallery(path: Path, gallery_records: list[dict[str, object]]) -> None:
    blocks = ["\\node[font=\\bfseries\\large] at (0,8.8) {Figure 2. Rooted stimulus type gallery};"]
    columns = 3
    x_positions = (-8.0, 0.0, 8.0)
    y_positions = (5.4, 0.2, -5.0)
    for index, record in enumerate(gallery_records):
        row = index // columns
        column = index % columns
        descriptor = record["descriptor"]
        subtitle_lines = [
            f"D1={descriptor['D1_target_degree']}, D2={descriptor['D2_neighbor_coupling']}",
            f"D3={descriptor['D3_remote_class'].split(':',1)[1]}",
            f"n={record['cache'].n_nodes}, KL={record['evaluation']['level_records']['high']['kl_A0_to_A4']:.3f}",
        ]
        blocks.append(
            tikz_graph_block(
                record,
                x_positions[column],
                y_positions[row],
                record["graph_id"],
                subtitle_lines,
                show_evidence_labels=False,
            )
        )
    write_tikz_figure(path, "\n".join(blocks))


def plot_matched_comparisons(path: Path, matched_pairs: dict[str, dict[str, object]]) -> None:
    blocks = ["\\node[font=\\bfseries\\large] at (0,10.0) {Figure 3. Matched comparisons by rooted dimension};"]
    y_lookup = {"D1": 6.1, "D2": 0.8, "D3": -4.5}
    x_lookup = (-4.5, 4.5)
    for dimension, title in (("D1", "Match on D2 and D3; vary D1"), ("D2", "Match on D1 and D3; vary D2"), ("D3", "Match on D1 and D2; vary D3")):
        pair = matched_pairs[dimension]
        blocks.append(f"\\node[font=\\bfseries] at (0,{y_lookup[dimension] + 3.2:.2f}) {{{title}}};")
        for index, record in enumerate(pair["graphs"]):
            descriptor = record["descriptor"]
            subtitle_lines = [
                f"D1={descriptor['D1_target_degree']}, D2={descriptor['D2_neighbor_coupling']}",
                f"D3={descriptor['D3_remote_class'].split(':',1)[1]}",
                f"KL={record['evaluation']['level_records']['high']['kl_A0_to_A4']:.3f}",
            ]
            blocks.append(
                tikz_graph_block(
                    record,
                    x_lookup[index],
                    y_lookup[dimension],
                    record["graph_id"],
                    subtitle_lines,
                    show_evidence_labels=False,
                )
            )
    write_tikz_figure(path, "\n".join(blocks))


def plot_selected_stimuli(path: Path, selected_stimuli: list[dict[str, object]]) -> None:
    blocks = ["\\node[font=\\bfseries\\large] at (0,8.8) {Figure 4. Selected stimuli with winning evidence labels};"]
    columns = 4
    x_positions = (-12.0, -4.0, 4.0, 12.0)
    y_positions = (5.2, -0.5)
    for index, item in enumerate(selected_stimuli[:8]):
        row = index // columns
        column = index % columns
        record = item["record"]
        subtitle_lines = [
            ", ".join(item["selection_reasons"]),
            f"KL={record['evaluation']['level_records']['high']['kl_A0_to_A4']:.3f}",
        ]
        blocks.append(
            tikz_graph_block(
                record,
                x_positions[column],
                y_positions[row],
                record["graph_id"],
                subtitle_lines,
                show_evidence_labels=True,
            )
        )
    write_tikz_figure(path, "\n".join(blocks))


def plot_descriptor_effects(path: Path, records: list[dict[str, object]], matched_pairs: dict[str, dict[str, object]]) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    d3_order = ["D3-0:no-remote", "D3-1:tree-like-remote", "D3-2:strong-remote"]
    d3_labels = [label.split(":", 1)[1] for label in d3_order]
    d3_groups = [
        [record["evaluation"]["level_records"]["high"]["kl_A0_to_A4"] for record in records if record["descriptor"]["D3_remote_class"] == label]
        for label in d3_order
    ]
    axes[0].boxplot(d3_groups, tick_labels=d3_labels)
    axes[0].set_title("High-evidence KL by D3 class")
    axes[0].set_ylabel("KL(A0 || A4)")
    axes[0].grid(alpha=0.25, linewidth=0.5)

    family_records = defaultdict(list)
    for record in records:
        family_key = descriptor_family_key(record["descriptor"])
        family_records[family_key].append(record["evaluation"]["level_records"]["high"]["kl_A0_to_A4"])
    family_keys = sorted(family_records)
    family_labels = [f"({key[0]},{key[1]},{key[2].split(':')[0][-1]})" for key in family_keys]
    family_means = [sum(values) / len(values) for values in (family_records[key] for key in family_keys)]
    axes[1].plot(range(len(family_keys)), family_means, marker="o", linewidth=1.5)
    axes[1].set_xticks(range(len(family_keys)))
    axes[1].set_xticklabels(family_labels, rotation=60, ha="right", fontsize=7)
    axes[1].set_title("Mean KL by descriptor family")
    axes[1].grid(alpha=0.25, linewidth=0.5)

    x_positions = [0, 1, 2]
    for index, dimension in enumerate(("D1", "D2", "D3")):
        pair = matched_pairs[dimension]
        values = [graph["evaluation"]["level_records"]["high"]["kl_A0_to_A4"] for graph in pair["graphs"]]
        axes[2].plot([index, index], [values[0], values[1]], color="#444444", linewidth=1.2)
        axes[2].scatter([index - 0.05, index + 0.05], values, s=35)
        axes[2].text(index, max(values) + 0.02, dimension, ha="center", va="bottom", fontsize=9)
    axes[2].set_xlim(-0.5, 2.5)
    axes[2].set_xticks(x_positions)
    axes[2].set_xticklabels(["D1", "D2", "D3"])
    axes[2].set_title("Matched-comparison KL shifts")
    axes[2].grid(alpha=0.25, linewidth=0.5)

    figure.suptitle("Figure 5. Descriptor-level separability")
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def write_csv_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_results() -> dict[str, object]:
    rooted_records, _ = build_rooted_graph_records()
    serialized_graphs = [serialize_graph_record(record) for record in rooted_records]
    descriptor_results = build_descriptor_results(rooted_records)
    matched_pairs = {
        "D1": find_best_pair(rooted_records, "D1"),
        "D2": find_best_pair(rooted_records, "D2"),
        "D3": find_best_pair(rooted_records, "D3"),
    }
    selected_stimuli = select_stimuli(rooted_records, matched_pairs)
    return {
        "metadata": {
            "n_range": list(N_RANGE),
            "beta_edge": BETA_EDGE,
            "rho_agents": [{"agent": label, "rho": rho} for label, rho in RHO_AGENTS],
            "evidence_levels": {name: list(values) for name, values in EVIDENCE_LEVELS.items()},
            "monotonicity_tolerance": MONOTONICITY_TOLERANCE,
            "design_note": (
                "Rooted-shell structure is the scientific design axis. Node count is used only as the smallest "
                "container needed to instantiate a rooted motif. Adaptive conflicting evidence is fixed from analysis-2."
            ),
        },
        "rooted_records": rooted_records,
        "serialized_graphs": serialized_graphs,
        "descriptor_results": descriptor_results,
        "matched_pairs": matched_pairs,
        "selected_stimuli": selected_stimuli,
        "long_rows": build_long_rows(rooted_records),
    }


def serialize_matched_pair(pair: dict[str, object]) -> dict[str, object]:
    return {
        "dimension": pair["dimension"],
        "graph_ids": pair["graph_ids"],
        "high_kl_difference": pair["high_kl_difference"],
    }


def serialize_selected_item(item: dict[str, object]) -> dict[str, object]:
    record = item["record"]
    serialized = serialize_graph_record(record)
    serialized["selection_reasons"] = item["selection_reasons"]
    return serialized


def write_outputs(results: dict[str, object], project_root: Path) -> None:
    # Paths: analysis-3/code/analysis-3.py
    #   code_dir    = analysis-3/code/
    #   data_dir    = analysis-3/code/data/   (all data outputs)
    #   figures_dir = analysis-3/figures/
    code_dir = project_root
    data_dir = code_dir / "data"
    figures_dir = project_root.parent / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    motif_catalog_path = data_dir / "analysis-3_rooted_motif_catalog.json"
    descriptor_results_json_path = data_dir / "analysis-3_descriptor_results.json"
    descriptor_results_csv_path = data_dir / "analysis-3_descriptor_results.csv"
    selected_stimuli_json_path = data_dir / "analysis-3_selected_stimuli.json"
    selected_stimuli_csv_path = data_dir / "analysis-3_selected_stimuli.csv"

    motif_catalog = {
        "metadata": results["metadata"],
        "rooted_graph_count": len(results["serialized_graphs"]),
        "rooted_graphs": results["serialized_graphs"],
    }
    motif_catalog_path.write_text(json.dumps(motif_catalog, indent=2), encoding="utf-8")

    descriptor_json = {
        "metadata": results["metadata"],
        "descriptor_results": results["descriptor_results"],
        "matched_pairs": {key: serialize_matched_pair(value) for key, value in results["matched_pairs"].items()},
    }
    descriptor_results_json_path.write_text(json.dumps(descriptor_json, indent=2), encoding="utf-8")
    write_csv_rows(descriptor_results_csv_path, results["long_rows"])

    selected_items = [serialize_selected_item(item) for item in results["selected_stimuli"]]
    selected_stimuli_json_path.write_text(
        json.dumps({"metadata": results["metadata"], "selected_stimuli": selected_items}, indent=2),
        encoding="utf-8",
    )
    selected_csv_rows = []
    for item in selected_items:
        row = {
            "graph_id": item["graph_id"],
            "n_nodes": item["n_nodes"],
            "D1_target_degree": item["descriptor"]["D1_target_degree"],
            "D2_neighbor_coupling": item["descriptor"]["D2_neighbor_coupling"],
            "D3_remote_class": item["descriptor"]["D3_remote_class"],
            "S2_count": item["descriptor"]["S2_count"],
            "e12": item["descriptor"]["e12"],
            "e22": item["descriptor"]["e22"],
            "high_kl_A0_to_A4": item["high_kl_A0_to_A4"],
            "selection_reasons": ",".join(item["selection_reasons"]),
            "preferred_color_template": "-".join(str(value) for value in item["preferred_color_template"]),
        }
        selected_csv_rows.append(row)
    write_csv_rows(selected_stimuli_csv_path, selected_csv_rows)

    gallery_records = []
    seen_families = set()
    for record in sorted(
        results["rooted_records"],
        key=lambda item: (
            item["descriptor"]["D1_target_degree"],
            item["descriptor"]["D3_remote_class"],
            item["descriptor"]["D2_neighbor_coupling"],
            -item["evaluation"]["level_records"]["high"]["kl_A0_to_A4"],
        ),
    ):
        family_key = descriptor_family_key(record["descriptor"])
        if family_key in seen_families:
            continue
        seen_families.add(family_key)
        gallery_records.append(record)
        if len(gallery_records) >= 9:
            break

    plot_design_schematic(figures_dir / FIGURE_FILENAMES["fig1"])
    plot_gallery(figures_dir / FIGURE_FILENAMES["fig2"], gallery_records)
    plot_matched_comparisons(figures_dir / FIGURE_FILENAMES["fig3"], results["matched_pairs"])
    plot_selected_stimuli(figures_dir / FIGURE_FILENAMES["fig4"], results["selected_stimuli"])
    plot_descriptor_effects(figures_dir / FIGURE_FILENAMES["fig5"], results["rooted_records"], results["matched_pairs"])

    print(f"Wrote {motif_catalog_path}")
    print(f"Wrote {descriptor_results_json_path}")
    print(f"Wrote {descriptor_results_csv_path}")
    print(f"Wrote {selected_stimuli_json_path}")
    print(f"Wrote {selected_stimuli_csv_path}")
    for figure_name in FIGURE_FILENAMES.values():
        print(f"Wrote {figures_dir / figure_name}")


def main() -> None:
    # project_root passed to write_outputs is the code/ dir itself (data lives here)
    project_root = Path(__file__).resolve().parent
    results = build_results()
    write_outputs(results, project_root)


if __name__ == "__main__":
    main()
