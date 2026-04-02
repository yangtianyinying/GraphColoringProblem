#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations, permutations, product
import csv
import json
import math
from pathlib import Path
import random


COLOR_COUNT = 3
COLOR_LABELS = ("R", "G", "B")
EVIDENCE_LEVELS = {
    "high": (0.9, 0.05, 0.05),
    "medium": (0.6, 0.2, 0.2),
    "low": (0.4, 0.3, 0.3),
}
DEFAULT_BETA_EDGE = 4.0
DEFAULT_KAPPA = 80.0
RHO_GRID = tuple(index / 20 for index in range(21))
REPRESENTATIVE_RHO = 0.5
PHASE1_SAMPLE_COUNTS = {6: 300, 7: 400, 8: 400}
PHASE2_SAMPLE_COUNTS = {7: 3000, 8: 3000}
PHASE1_PAIRS_PER_N = 3
PHASE2_GRAPHS_PER_N = 4
MODEL_RECOVERY_DATASETS_PER_CLASS = 60
MODEL_RECOVERY_PHASE1_QUOTA = 12
MODEL_RECOVERY_PHASE2_QUOTA = 12
BALANCED_LIST_COUNT = 6


@dataclass(frozen=True)
class NamedGraph:
    name: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    observed: str
    target: str

    def adjacency(self) -> dict[str, set[str]]:
        adjacency = {node: set() for node in self.nodes}
        for left, right in self.edges:
            adjacency[left].add(right)
            adjacency[right].add(left)
        return adjacency

    def neighbors(self, node: str) -> tuple[str, ...]:
        adjacency = self.adjacency()
        return tuple(sorted(adjacency[node]))

    def distances(self, source: str) -> dict[str, int]:
        adjacency = self.adjacency()
        distances = {source: 0}
        queue = [source]
        for node in queue:
            for neighbor in sorted(adjacency[node]):
                if neighbor in distances:
                    continue
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)
        return distances


def normalize(values: list[float] | tuple[float, ...]) -> tuple[float, ...]:
    total = sum(values)
    return tuple(value / total for value in values)


def entropy(probabilities: tuple[float, ...] | list[float]) -> float:
    return -sum(probability * math.log(probability) for probability in probabilities if probability > 0.0)


def kl_divergence(
    p: tuple[float, ...] | list[float],
    q: tuple[float, ...] | list[float],
) -> float:
    return sum(left * math.log(left / right) for left, right in zip(p, q))


def symmetric_kl_divergence(
    p: tuple[float, ...] | list[float],
    q: tuple[float, ...] | list[float],
) -> float:
    return 0.5 * (kl_divergence(p, q) + kl_divergence(q, p))


def pretty_probabilities(probabilities: tuple[float, ...] | list[float]) -> list[float]:
    return [round(value, 6) for value in probabilities]


def labels_for_n(n_nodes: int) -> tuple[str, ...]:
    return tuple(chr(ord("A") + index) for index in range(n_nodes))


def adjacency_from_edges(n_nodes: int, edges: tuple[tuple[int, int], ...] | list[tuple[int, int]]) -> list[set[int]]:
    adjacency = [set() for _ in range(n_nodes)]
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    return adjacency


def edges_from_adjacency(adjacency: list[set[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        sorted((node, neighbor) for node in range(len(adjacency)) for neighbor in adjacency[node] if node < neighbor)
    )


def labeled_edges_from_adjacency(adjacency: list[set[int]]) -> list[list[str]]:
    labels = labels_for_n(len(adjacency))
    return [[labels[left], labels[right]] for left, right in edges_from_adjacency(adjacency)]


def graph_edge_count(adjacency: list[set[int]]) -> int:
    return sum(len(neighbors) for neighbors in adjacency) // 2


def graph_density(adjacency: list[set[int]]) -> float:
    n_nodes = len(adjacency)
    if n_nodes <= 1:
        return 0.0
    return graph_edge_count(adjacency) / (n_nodes * (n_nodes - 1) / 2)


def degree_sequence(adjacency: list[set[int]]) -> list[int]:
    return sorted((len(neighbors) for neighbors in adjacency), reverse=True)


def connected(adjacency: list[set[int]]) -> bool:
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


def bfs_distances(adjacency: list[set[int]], source: int) -> dict[int, int]:
    distances = {source: 0}
    queue = [source]
    for node in queue:
        for neighbor in sorted(adjacency[node]):
            if neighbor in distances:
                continue
            distances[neighbor] = distances[node] + 1
            queue.append(neighbor)
    return distances


def anti_color_weight(color_left: int, color_right: int, beta_edge: float) -> float:
    return math.exp(-beta_edge) if color_left == color_right else 1.0


def exact_target_marginal_adj(
    adjacency: list[set[int]],
    observed: int,
    target: int,
    evidence: tuple[float, ...],
    beta_edge: float,
    rho: float | None = None,
) -> tuple[float, ...]:
    n_nodes = len(adjacency)
    edges = edges_from_adjacency(adjacency)
    shell_distance = bfs_distances(adjacency, target)
    posterior = [0.0, 0.0, 0.0]
    partition = 0.0
    for assignment in product(range(COLOR_COUNT), repeat=n_nodes):
        weight = evidence[assignment[observed]]
        for left, right in edges:
            effective_beta = beta_edge
            if rho is not None:
                shell = min(shell_distance[left], shell_distance[right])
                effective_beta = beta_edge * (rho ** shell)
            weight *= anti_color_weight(assignment[left], assignment[right], effective_beta)
        partition += weight
        posterior[assignment[target]] += weight
    return normalize(posterior)


def independent_target_marginal_adj(
    adjacency: list[set[int]],
    observed: int,
    target: int,
    evidence: tuple[float, ...],
    beta_edge: float,
) -> tuple[float, ...]:
    belief = [1.0, 1.0, 1.0]
    for neighbor in sorted(adjacency[target]):
        if neighbor != observed:
            continue
        message = []
        for target_color in range(COLOR_COUNT):
            total = 0.0
            for observed_color in range(COLOR_COUNT):
                total += evidence[observed_color] * anti_color_weight(
                    target_color,
                    observed_color,
                    beta_edge,
                )
            message.append(total)
        belief = [left * right for left, right in zip(belief, message)]
    return normalize(belief)


def pairwise_bp_target_marginal_adj(
    adjacency: list[set[int]],
    observed: int,
    target: int,
    evidence: tuple[float, ...],
    beta_edge: float,
    damping: float = 1.0,
    max_iterations: int = 500,
    tolerance: float = 1e-12,
) -> tuple[tuple[float, ...], int, float]:
    unary = {
        node: (list(evidence) if node == observed else [1.0, 1.0, 1.0])
        for node in range(len(adjacency))
    }
    pairwise = [
        [anti_color_weight(left_color, right_color, beta_edge) for right_color in range(COLOR_COUNT)]
        for left_color in range(COLOR_COUNT)
    ]
    messages = {
        (source, destination): [1.0 / COLOR_COUNT] * COLOR_COUNT
        for source in range(len(adjacency))
        for destination in sorted(adjacency[source])
    }
    max_change = 0.0
    iteration_count = 0
    for iteration in range(1, max_iterations + 1):
        next_messages: dict[tuple[int, int], list[float]] = {}
        max_change = 0.0
        for source in range(len(adjacency)):
            for destination in sorted(adjacency[source]):
                support = unary[source][:]
                for neighbor in sorted(adjacency[source]):
                    if neighbor == destination:
                        continue
                    support = [
                        current * incoming
                        for current, incoming in zip(support, messages[(neighbor, source)])
                    ]
                updated = []
                for destination_color in range(COLOR_COUNT):
                    total = 0.0
                    for source_color in range(COLOR_COUNT):
                        total += pairwise[source_color][destination_color] * support[source_color]
                    updated.append(total)
                normalized = list(normalize(updated))
                if damping < 1.0:
                    normalized = [
                        (1.0 - damping) * previous + damping * current
                        for previous, current in zip(messages[(source, destination)], normalized)
                    ]
                    normalized = list(normalize(normalized))
                max_change = max(
                    max_change,
                    max(
                        abs(current - previous)
                        for current, previous in zip(normalized, messages[(source, destination)])
                    ),
                )
                next_messages[(source, destination)] = normalized
        messages = next_messages
        iteration_count = iteration
        if max_change < tolerance:
            break
    belief = unary[target][:]
    for neighbor in sorted(adjacency[target]):
        belief = [current * incoming for current, incoming in zip(belief, messages[(neighbor, target)])]
    return normalize(belief), iteration_count, max_change


def named_graph_to_indexed(graph: NamedGraph) -> tuple[list[set[int]], dict[str, int]]:
    index = {node: offset for offset, node in enumerate(graph.nodes)}
    adjacency = [set() for _ in graph.nodes]
    for left, right in graph.edges:
        left_index = index[left]
        right_index = index[right]
        adjacency[left_index].add(right_index)
        adjacency[right_index].add(left_index)
    return adjacency, index


def exact_target_marginal(
    graph: NamedGraph,
    evidence: dict[str, tuple[float, ...]],
    beta_edge: float,
    rho: float | None = None,
) -> tuple[float, ...]:
    adjacency, index = named_graph_to_indexed(graph)
    observed_name, evidence_values = next(iter(evidence.items()))
    return exact_target_marginal_adj(
        adjacency,
        index[observed_name],
        index[graph.target],
        evidence_values,
        beta_edge,
        rho=rho,
    )


def independent_target_marginal(
    graph: NamedGraph,
    evidence: dict[str, tuple[float, ...]],
    beta_edge: float,
) -> tuple[float, ...]:
    adjacency, index = named_graph_to_indexed(graph)
    observed_name, evidence_values = next(iter(evidence.items()))
    return independent_target_marginal_adj(
        adjacency,
        index[observed_name],
        index[graph.target],
        evidence_values,
        beta_edge,
    )


def pairwise_bp_target_marginal(
    graph: NamedGraph,
    evidence: dict[str, tuple[float, ...]],
    beta_edge: float,
    damping: float = 1.0,
    max_iterations: int = 500,
    tolerance: float = 1e-12,
) -> tuple[tuple[float, ...], int, float]:
    adjacency, index = named_graph_to_indexed(graph)
    observed_name, evidence_values = next(iter(evidence.items()))
    return pairwise_bp_target_marginal_adj(
        adjacency,
        index[observed_name],
        index[graph.target],
        evidence_values,
        beta_edge,
        damping=damping,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )


def three_colorable(adjacency: list[set[int]]) -> bool:
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


def fill_count(adjacency: list[set[int]], node: int) -> int:
    neighbors = sorted(adjacency[node])
    count = 0
    for left_index, left in enumerate(neighbors):
        for right in neighbors[left_index + 1 :]:
            if right not in adjacency[left]:
                count += 1
    return count


def eliminate_node(adjacency: list[set[int]], node: int) -> tuple[list[tuple[int, int]], int]:
    neighbors = sorted(adjacency[node])
    fill_edges: list[tuple[int, int]] = []
    for left_index, left in enumerate(neighbors):
        for right in neighbors[left_index + 1 :]:
            if right in adjacency[left]:
                continue
            adjacency[left].add(right)
            adjacency[right].add(left)
            fill_edges.append((left, right))
    omega = len(neighbors) + 1
    for neighbor in neighbors:
        adjacency[neighbor].remove(node)
    adjacency[node].clear()
    return fill_edges, omega


def heuristic_trace(
    adjacency: list[set[int]],
    mode: str,
) -> tuple[list[int], list[int], list[int], list[list[tuple[int, int]]]]:
    active = set(range(len(adjacency)))
    work = [set(neighbors) for neighbors in adjacency]
    order: list[int] = []
    fill_counts: list[int] = []
    omegas: list[int] = []
    fill_edges_per_step: list[list[tuple[int, int]]] = []
    while active:
        if mode == "min_degree":
            score = lambda node: (len(work[node]), node)
        else:
            score = lambda node: (fill_count(work, node), len(work[node]), node)
        chosen = min(active, key=score)
        fill_edges, omega = eliminate_node(work, chosen)
        order.append(chosen)
        fill_counts.append(len(fill_edges))
        omegas.append(omega)
        fill_edges_per_step.append(fill_edges)
        active.remove(chosen)
    return order, fill_counts, omegas, fill_edges_per_step


def serialize_trace(
    order: list[int],
    fill_counts: list[int],
    omegas: list[int],
    fill_edges_per_step: list[list[tuple[int, int]]],
    labels: tuple[str, ...],
) -> dict[str, object]:
    return {
        "order": [labels[node] for node in order],
        "fill_counts": fill_counts,
        "omegas": omegas,
        "fill_edges": [
            [[labels[left], labels[right]] for left, right in fill_edges]
            for fill_edges in fill_edges_per_step
        ],
        "sum_fill": sum(fill_counts),
        "max_omega": max(omegas),
    }


def graph_record(
    graph_id: str,
    adjacency: list[set[int]],
    source: str,
) -> dict[str, object]:
    return {
        "graph_id": graph_id,
        "adjacency": [set(neighbors) for neighbors in adjacency],
        "n_nodes": len(adjacency),
        "source": source,
    }


def graph_summary(record: dict[str, object]) -> dict[str, object]:
    adjacency = record["adjacency"]
    return {
        "graph_id": record["graph_id"],
        "n_nodes": record["n_nodes"],
        "source": record["source"],
        "edges": labeled_edges_from_adjacency(adjacency),
        "edge_count": graph_edge_count(adjacency),
        "density": round(graph_density(adjacency), 6),
        "degree_sequence": degree_sequence(adjacency),
    }


def random_colorable_graph(n_nodes: int, rng: random.Random) -> list[set[int]]:
    while True:
        latent_colors = [rng.randrange(COLOR_COUNT) for _ in range(n_nodes)]
        if len(set(latent_colors)) < 2:
            continue
        edge_probability = rng.uniform(0.35, 0.8)
        adjacency = [set() for _ in range(n_nodes)]
        for left, right in combinations(range(n_nodes), 2):
            if latent_colors[left] == latent_colors[right]:
                continue
            if rng.random() >= edge_probability:
                continue
            adjacency[left].add(right)
            adjacency[right].add(left)
        if graph_edge_count(adjacency) < n_nodes - 1:
            continue
        if not connected(adjacency):
            continue
        return adjacency


def sample_unique_colorable_graph_records(
    sample_counts: dict[int, int],
    seed: int,
    prefix: str,
) -> dict[int, list[dict[str, object]]]:
    records_by_n: dict[int, list[dict[str, object]]] = {}
    for n_nodes, count in sample_counts.items():
        rng = random.Random(seed + n_nodes)
        seen_edges: set[tuple[tuple[int, int], ...]] = set()
        records: list[dict[str, object]] = []
        while len(records) < count:
            adjacency = random_colorable_graph(n_nodes, rng)
            key = edges_from_adjacency(adjacency)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            records.append(
                graph_record(
                    f"{prefix}_n{n_nodes}_{len(records) + 1:03d}",
                    adjacency,
                    f"random_colorable_sample_n{n_nodes}",
                )
            )
        records_by_n[n_nodes] = records
    return records_by_n


def iter_connected_three_colorable_graphs(n_nodes: int):
    all_edges = list(combinations(range(n_nodes), 2))
    for mask in range(1, 1 << len(all_edges)):
        adjacency = [set() for _ in range(n_nodes)]
        for bit_index, (left, right) in enumerate(all_edges):
            if not ((mask >> bit_index) & 1):
                continue
            adjacency[left].add(right)
            adjacency[right].add(left)
        if not connected(adjacency):
            continue
        if not three_colorable(adjacency):
            continue
        yield adjacency


def exhaustive_complexity_statistics(n_nodes: int) -> dict[str, object]:
    connected_three_colorable = 0
    order_difference = 0
    fill_gap_count = 0
    max_fill_gap = 0
    exemplar: dict[str, object] | None = None
    exemplar_key: tuple[int, tuple[tuple[int, int], ...]] | None = None
    labels = labels_for_n(n_nodes)
    for adjacency in iter_connected_three_colorable_graphs(n_nodes):
        connected_three_colorable += 1
        min_degree = heuristic_trace(adjacency, "min_degree")
        min_fill = heuristic_trace(adjacency, "min_fill")
        if min_degree[0] != min_fill[0]:
            order_difference += 1
        fill_gap = sum(min_degree[1]) - sum(min_fill[1])
        if fill_gap <= 0:
            continue
        fill_gap_count += 1
        max_fill_gap = max(max_fill_gap, fill_gap)
        edge_key = edges_from_adjacency(adjacency)
        candidate_key = (graph_edge_count(adjacency), edge_key)
        if exemplar_key is not None and candidate_key >= exemplar_key:
            continue
        exemplar_key = candidate_key
        exemplar = {
            "labels": list(labels),
            "edges": labeled_edges_from_adjacency(adjacency),
            "min_degree": serialize_trace(*min_degree, labels),
            "min_fill": serialize_trace(*min_fill, labels),
        }
    return {
        "n_nodes": n_nodes,
        "connected_three_colorable_graphs": connected_three_colorable,
        "order_difference_count": order_difference,
        "order_difference_rate": order_difference / connected_three_colorable,
        "fill_gap_count": fill_gap_count,
        "fill_gap_rate": fill_gap_count / connected_three_colorable,
        "max_fill_gap": max_fill_gap,
        "exemplar": exemplar,
    }


def phase1_local_signature(
    adjacency: list[set[int]],
    observed: int,
    target: int,
) -> tuple[int, int, int, tuple[int, ...]] | None:
    distances = bfs_distances(adjacency, observed)
    if target not in distances:
        return None
    if distances[target] not in (2, 3):
        return None
    if observed in adjacency[target]:
        return None
    neighbors = sorted(adjacency[target])
    if not (2 <= len(neighbors) <= 4):
        return None
    local_neighbor_degrees = tuple(
        sorted(
            sum((other in adjacency[node]) for other in neighbors if other != node)
            for node in neighbors
        )
    )
    return (len(adjacency), distances[target], len(neighbors), local_neighbor_degrees)


def serialize_phase1_signature(signature: tuple[int, int, int, tuple[int, ...]]) -> dict[str, object]:
    return {
        "n_nodes": signature[0],
        "observed_target_distance": signature[1],
        "target_degree": signature[2],
        "neighbor_internal_degrees": list(signature[3]),
    }


def phase1_instance(
    record: dict[str, object],
    observed: int,
    target: int,
    signature: tuple[int, int, int, tuple[int, ...]],
    beta_edge: float,
) -> dict[str, object]:
    adjacency = record["adjacency"]
    exact_high = exact_target_marginal_adj(adjacency, observed, target, EVIDENCE_LEVELS["high"], beta_edge)
    independent_high = independent_target_marginal_adj(
        adjacency,
        observed,
        target,
        EVIDENCE_LEVELS["high"],
        beta_edge,
    )
    return {
        "record": record,
        "observed": observed,
        "target": target,
        "signature": signature,
        "high_exact": exact_high,
        "high_independent": independent_high,
    }


def serialize_phase1_endpoint(instance: dict[str, object], beta_edge: float) -> dict[str, object]:
    record = instance["record"]
    adjacency = record["adjacency"]
    labels = labels_for_n(record["n_nodes"])
    observed = instance["observed"]
    target = instance["target"]
    exact_by_level = {
        level: pretty_probabilities(
            exact_target_marginal_adj(adjacency, observed, target, evidence, beta_edge)
        )
        for level, evidence in EVIDENCE_LEVELS.items()
    }
    independent_by_level = {
        level: pretty_probabilities(
            independent_target_marginal_adj(adjacency, observed, target, evidence, beta_edge)
        )
        for level, evidence in EVIDENCE_LEVELS.items()
    }
    rho_mid_high = exact_target_marginal_adj(
        adjacency,
        observed,
        target,
        EVIDENCE_LEVELS["high"],
        beta_edge,
        rho=REPRESENTATIVE_RHO,
    )
    bp_high, iterations, residual = pairwise_bp_target_marginal_adj(
        adjacency,
        observed,
        target,
        EVIDENCE_LEVELS["high"],
        beta_edge,
    )
    graph_info = graph_summary(record)
    graph_info.update(
        {
            "observed": labels[observed],
            "target": labels[target],
            "distance_observed_to_target": bfs_distances(adjacency, observed)[target],
            "exact_posteriors": exact_by_level,
            "independent_posteriors": independent_by_level,
            "high_evidence_model_posteriors": {
                "M0": pretty_probabilities(independent_target_marginal_adj(
                    adjacency,
                    observed,
                    target,
                    EVIDENCE_LEVELS["high"],
                    beta_edge,
                )),
                "rho_0.5": pretty_probabilities(rho_mid_high),
                "exact": pretty_probabilities(exact_target_marginal_adj(
                    adjacency,
                    observed,
                    target,
                    EVIDENCE_LEVELS["high"],
                    beta_edge,
                )),
                "BP": pretty_probabilities(bp_high),
            },
            "bp_iterations_high": iterations,
            "bp_final_change_high": residual,
        }
    )
    return graph_info


def screen_phase1_pairs(
    records_by_n: dict[int, list[dict[str, object]]],
    beta_edge: float,
) -> tuple[list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    grouped_instances: defaultdict[tuple[int, int, int, tuple[int, ...]], list[dict[str, object]]] = defaultdict(list)
    summary_by_n: dict[int, dict[str, int]] = {}
    per_graph_limits = {6: 12, 7: 10, 8: 10}
    for n_nodes, records in records_by_n.items():
        eligible_instances = 0
        for record in records:
            per_graph_count = 0
            for observed in range(n_nodes):
                for target in range(n_nodes):
                    if observed == target:
                        continue
                    signature = phase1_local_signature(record["adjacency"], observed, target)
                    if signature is None:
                        continue
                    grouped_instances[signature].append(
                        phase1_instance(record, observed, target, signature, beta_edge)
                    )
                    eligible_instances += 1
                    per_graph_count += 1
                    if per_graph_count >= per_graph_limits[n_nodes]:
                        break
                if per_graph_count >= per_graph_limits[n_nodes]:
                    break
        summary_by_n[n_nodes] = {
            "sampled_graphs": len(records),
            "eligible_instances": eligible_instances,
            "signature_groups": 0,
            "candidate_groups_above_threshold": 0,
            "selected_pairs": 0,
        }
    pair_candidates: list[dict[str, object]] = []
    for signature, instances in grouped_instances.items():
        n_nodes = signature[0]
        summary_by_n[n_nodes]["signature_groups"] += 1
        if len(instances) < 2:
            continue
        low_instance = min(instances, key=lambda item: item["high_exact"][0])
        high_instance = max(instances, key=lambda item: item["high_exact"][0])
        delta_p_high = high_instance["high_exact"][0] - low_instance["high_exact"][0]
        if delta_p_high < 0.08:
            continue
        summary_by_n[n_nodes]["candidate_groups_above_threshold"] += 1
        pair_candidates.append(
            {
                "n_nodes": n_nodes,
                "signature": signature,
                "low_instance": low_instance,
                "high_instance": high_instance,
                "delta_p_high": delta_p_high,
                "kl_high": kl_divergence(high_instance["high_exact"], low_instance["high_exact"]),
            }
        )
    pair_candidates.sort(
        key=lambda candidate: (candidate["delta_p_high"], candidate["kl_high"]),
        reverse=True,
    )
    selected_pairs: list[dict[str, object]] = []
    used_graphs: set[str] = set()
    per_n_counter: Counter[int] = Counter()
    for candidate in pair_candidates:
        n_nodes = candidate["n_nodes"]
        if per_n_counter[n_nodes] >= PHASE1_PAIRS_PER_N:
            continue
        graph_ids = {
            candidate["low_instance"]["record"]["graph_id"],
            candidate["high_instance"]["record"]["graph_id"],
        }
        if used_graphs & graph_ids:
            continue
        pair_id = f"phase1_n{n_nodes}_pair_{per_n_counter[n_nodes] + 1}"
        low_exact = {
            level: exact_target_marginal_adj(
                candidate["low_instance"]["record"]["adjacency"],
                candidate["low_instance"]["observed"],
                candidate["low_instance"]["target"],
                evidence,
                beta_edge,
            )
            for level, evidence in EVIDENCE_LEVELS.items()
        }
        high_exact = {
            level: exact_target_marginal_adj(
                candidate["high_instance"]["record"]["adjacency"],
                candidate["high_instance"]["observed"],
                candidate["high_instance"]["target"],
                evidence,
                beta_edge,
            )
            for level, evidence in EVIDENCE_LEVELS.items()
        }
        serialized_pair = {
            "pair_id": pair_id,
            "n_nodes": n_nodes,
            "local_signature": serialize_phase1_signature(candidate["signature"]),
            "selection_metrics": {
                "delta_p_target_R": {
                    level: round(high_exact[level][0] - low_exact[level][0], 6)
                    for level in EVIDENCE_LEVELS
                },
                "kl_high_vs_low": {
                    level: round(kl_divergence(high_exact[level], low_exact[level]), 6)
                    for level in EVIDENCE_LEVELS
                },
            },
            "graph_low": serialize_phase1_endpoint(candidate["low_instance"], beta_edge),
            "graph_high": serialize_phase1_endpoint(candidate["high_instance"], beta_edge),
        }
        selected_pairs.append(
            {
                "serialized": serialized_pair,
                "pair_id": pair_id,
                "n_nodes": n_nodes,
                "low_instance": candidate["low_instance"],
                "high_instance": candidate["high_instance"],
            }
        )
        used_graphs |= graph_ids
        per_n_counter[n_nodes] += 1
        summary_by_n[n_nodes]["selected_pairs"] += 1
    summary = {
        "sampling_strategy": {
            str(n_nodes): {
                "source": f"random 3-colorable sample ({PHASE1_SAMPLE_COUNTS[n_nodes]} unique graphs)",
                **summary_by_n[n_nodes],
            }
            for n_nodes in sorted(summary_by_n)
        },
        "selection_rule": {
            "max_pairs_per_n": PHASE1_PAIRS_PER_N,
            "minimum_delta_p_target_R_high": 0.08,
            "signature_fields": [
                "n_nodes",
                "observed_target_distance",
                "target_degree",
                "neighbor_internal_degrees",
            ],
        },
    }
    return [pair["serialized"] for pair in selected_pairs], summary, selected_pairs


def best_observed_target_pair_for_models(
    adjacency: list[set[int]],
    beta_edge: float,
) -> dict[str, object] | None:
    best: dict[str, object] | None = None
    for observed in range(len(adjacency)):
        distances = bfs_distances(adjacency, observed)
        for target in range(len(adjacency)):
            if observed == target:
                continue
            if target not in distances:
                continue
            if distances[target] not in (2, 3):
                continue
            predictions = {
                "M0": independent_target_marginal_adj(
                    adjacency,
                    observed,
                    target,
                    EVIDENCE_LEVELS["high"],
                    beta_edge,
                ),
                "rho_0.5": exact_target_marginal_adj(
                    adjacency,
                    observed,
                    target,
                    EVIDENCE_LEVELS["high"],
                    beta_edge,
                    rho=REPRESENTATIVE_RHO,
                ),
                "exact": exact_target_marginal_adj(
                    adjacency,
                    observed,
                    target,
                    EVIDENCE_LEVELS["high"],
                    beta_edge,
                ),
                "BP": pairwise_bp_target_marginal_adj(
                    adjacency,
                    observed,
                    target,
                    EVIDENCE_LEVELS["high"],
                    beta_edge,
                )[0],
            }
            score = 0.0
            model_names = list(predictions)
            for left_index, left_name in enumerate(model_names):
                for right_name in model_names[left_index + 1 :]:
                    score += symmetric_kl_divergence(predictions[left_name], predictions[right_name])
            candidate = {
                "observed": observed,
                "target": target,
                "distance": distances[target],
                "informativeness_high": score,
                "model_posteriors_high": {
                    name: pretty_probabilities(probabilities)
                    for name, probabilities in predictions.items()
                },
            }
            if best is None or candidate["informativeness_high"] > best["informativeness_high"]:
                best = candidate
    return best


def serialize_phase2_candidate(candidate: dict[str, object]) -> dict[str, object]:
    record = candidate["record"]
    labels = labels_for_n(record["n_nodes"])
    return {
        **graph_summary(record),
        "min_degree": serialize_trace(*candidate["min_degree_trace"], labels),
        "min_fill": serialize_trace(*candidate["min_fill_trace"], labels),
        "gaps": {
            "total_fill_gap": candidate["total_fill_gap"],
            "max_omega_gap": candidate["max_omega_gap"],
            "first_step_fill_gap": candidate["first_step_fill_gap"],
            "first_step_omega_gap": candidate["first_step_omega_gap"],
        },
        "recommended_observed_target": {
            "observed": labels[candidate["best_pair"]["observed"]],
            "target": labels[candidate["best_pair"]["target"]],
            "distance": candidate["best_pair"]["distance"],
            "informativeness_high": round(candidate["best_pair"]["informativeness_high"], 6),
            "model_posteriors_high": candidate["best_pair"]["model_posteriors_high"],
        },
    }


def screen_phase2_graphs(beta_edge: float) -> tuple[list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    candidate_pool: list[dict[str, object]] = []
    summary_by_n: dict[int, dict[str, int | str]] = {
        6: {
            "source": "exhaustive connected 3-colorable graph space",
            "screened_graphs": 0,
            "strong_candidates": 0,
            "selected_graphs": 0,
        },
        7: {
            "source": f"random 3-colorable sample ({PHASE2_SAMPLE_COUNTS[7]} unique graphs)",
            "screened_graphs": 0,
            "strong_candidates": 0,
            "selected_graphs": 0,
        },
        8: {
            "source": f"random 3-colorable sample ({PHASE2_SAMPLE_COUNTS[8]} unique graphs)",
            "screened_graphs": 0,
            "strong_candidates": 0,
            "selected_graphs": 0,
        },
    }
    n6_index = 0
    for adjacency in iter_connected_three_colorable_graphs(6):
        n6_index += 1
        summary_by_n[6]["screened_graphs"] += 1
        record = graph_record(f"phase2_n6_{n6_index:05d}", adjacency, "exhaustive_connected_3_colorable_n6")
        min_degree_trace = heuristic_trace(adjacency, "min_degree")
        min_fill_trace = heuristic_trace(adjacency, "min_fill")
        total_fill_gap = sum(min_degree_trace[1]) - sum(min_fill_trace[1])
        max_omega_gap = max(min_degree_trace[2]) - max(min_fill_trace[2])
        if total_fill_gap <= 0 and max_omega_gap <= 0:
            continue
        best_pair = best_observed_target_pair_for_models(adjacency, beta_edge)
        if best_pair is None:
            continue
        summary_by_n[6]["strong_candidates"] += 1
        candidate_pool.append(
            {
                "record": record,
                "min_degree_trace": min_degree_trace,
                "min_fill_trace": min_fill_trace,
                "total_fill_gap": total_fill_gap,
                "max_omega_gap": max_omega_gap,
                "first_step_fill_gap": min_degree_trace[1][0] - min_fill_trace[1][0],
                "first_step_omega_gap": min_degree_trace[2][0] - min_fill_trace[2][0],
                "best_pair": best_pair,
            }
        )
    sampled_phase2 = sample_unique_colorable_graph_records(PHASE2_SAMPLE_COUNTS, seed=20260325, prefix="phase2")
    for n_nodes in (7, 8):
        for record in sampled_phase2[n_nodes]:
            summary_by_n[n_nodes]["screened_graphs"] += 1
            adjacency = record["adjacency"]
            min_degree_trace = heuristic_trace(adjacency, "min_degree")
            min_fill_trace = heuristic_trace(adjacency, "min_fill")
            total_fill_gap = sum(min_degree_trace[1]) - sum(min_fill_trace[1])
            max_omega_gap = max(min_degree_trace[2]) - max(min_fill_trace[2])
            if total_fill_gap <= 0 and max_omega_gap <= 0:
                continue
            best_pair = best_observed_target_pair_for_models(adjacency, beta_edge)
            if best_pair is None:
                continue
            summary_by_n[n_nodes]["strong_candidates"] += 1
            candidate_pool.append(
                {
                    "record": record,
                    "min_degree_trace": min_degree_trace,
                    "min_fill_trace": min_fill_trace,
                    "total_fill_gap": total_fill_gap,
                    "max_omega_gap": max_omega_gap,
                    "first_step_fill_gap": min_degree_trace[1][0] - min_fill_trace[1][0],
                    "first_step_omega_gap": min_degree_trace[2][0] - min_fill_trace[2][0],
                    "best_pair": best_pair,
                }
            )
    candidate_pool.sort(
        key=lambda candidate: (
            candidate["total_fill_gap"],
            candidate["max_omega_gap"],
            candidate["first_step_fill_gap"],
            candidate["first_step_omega_gap"],
            candidate["best_pair"]["informativeness_high"],
            graph_edge_count(candidate["record"]["adjacency"]),
        ),
        reverse=True,
    )
    selected_candidates: list[dict[str, object]] = []
    per_n_counter: Counter[int] = Counter()
    for candidate in candidate_pool:
        n_nodes = candidate["record"]["n_nodes"]
        if per_n_counter[n_nodes] >= PHASE2_GRAPHS_PER_N:
            continue
        selected_candidates.append(candidate)
        per_n_counter[n_nodes] += 1
        summary_by_n[n_nodes]["selected_graphs"] += 1
    summary = {
        "selection_rule": {
            "max_graphs_per_n": PHASE2_GRAPHS_PER_N,
            "strong_candidate_definition": "total_fill_gap > 0 or max_omega_gap > 0",
        },
        "screening_summary": {str(n_nodes): summary_by_n[n_nodes] for n_nodes in sorted(summary_by_n)},
    }
    return [serialize_phase2_candidate(candidate) for candidate in selected_candidates], summary, selected_candidates


def trial_candidate(
    category: str,
    graph_id: str,
    adjacency: list[set[int]],
    observed: int,
    target: int,
    evidence_name: str,
    beta_edge: float,
    subgroup_id: str,
) -> dict[str, object]:
    evidence = EVIDENCE_LEVELS[evidence_name]
    representative_predictions = {
        "M0": independent_target_marginal_adj(adjacency, observed, target, evidence, beta_edge),
        "rho": exact_target_marginal_adj(adjacency, observed, target, evidence, beta_edge, rho=REPRESENTATIVE_RHO),
        "exact": exact_target_marginal_adj(adjacency, observed, target, evidence, beta_edge),
        "BP": pairwise_bp_target_marginal_adj(adjacency, observed, target, evidence, beta_edge)[0],
    }
    score = 0.0
    model_names = list(representative_predictions)
    for left_index, left_name in enumerate(model_names):
        for right_name in model_names[left_index + 1 :]:
            score += symmetric_kl_divergence(
                representative_predictions[left_name],
                representative_predictions[right_name],
            )
    labels = labels_for_n(len(adjacency))
    return {
        "trial_id": f"{category}_{graph_id}_{labels[observed]}_{labels[target]}_{evidence_name}",
        "category": category,
        "subgroup_id": subgroup_id,
        "graph_id": graph_id,
        "adjacency": [set(neighbors) for neighbors in adjacency],
        "n_nodes": len(adjacency),
        "observed": observed,
        "target": target,
        "evidence_name": evidence_name,
        "score": score,
        "representative_predictions": representative_predictions,
    }


def build_recovery_trial_library(
    selected_phase1_pairs: list[dict[str, object]],
    selected_phase2_graphs: list[dict[str, object]],
    beta_edge: float,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for pair in selected_phase1_pairs:
        for role_name, instance in (("low", pair["low_instance"]), ("high", pair["high_instance"])):
            for evidence_name in ("high", "medium"):
                candidates.append(
                    trial_candidate(
                        "phase1",
                        instance["record"]["graph_id"],
                        instance["record"]["adjacency"],
                        instance["observed"],
                        instance["target"],
                        evidence_name,
                        beta_edge,
                        f"{pair['pair_id']}::{role_name}",
                    )
                )
    for graph in selected_phase2_graphs:
        best_pair = graph["best_pair"]
        for evidence_name in ("high", "medium"):
            candidates.append(
                trial_candidate(
                    "phase2",
                    graph["record"]["graph_id"],
                    graph["record"]["adjacency"],
                    best_pair["observed"],
                    best_pair["target"],
                    evidence_name,
                    beta_edge,
                    graph["record"]["graph_id"],
                )
            )
    candidates.sort(key=lambda candidate: candidate["score"], reverse=True)
    selected_trials: list[dict[str, object]] = []
    per_category_counter: Counter[str] = Counter()
    per_graph_counter: Counter[str] = Counter()
    for candidate in candidates:
        if candidate["category"] == "phase1" and per_category_counter["phase1"] >= MODEL_RECOVERY_PHASE1_QUOTA:
            continue
        if candidate["category"] == "phase2" and per_category_counter["phase2"] >= MODEL_RECOVERY_PHASE2_QUOTA:
            continue
        if per_graph_counter[candidate["graph_id"]] >= 2:
            continue
        selected_trials.append(candidate)
        per_category_counter[candidate["category"]] += 1
        per_graph_counter[candidate["graph_id"]] += 1
        if (
            per_category_counter["phase1"] >= MODEL_RECOVERY_PHASE1_QUOTA
            and per_category_counter["phase2"] >= MODEL_RECOVERY_PHASE2_QUOTA
        ):
            break
    labels_cache = {trial["n_nodes"]: labels_for_n(trial["n_nodes"]) for trial in selected_trials}
    serialized_trials = []
    for trial in selected_trials:
        labels = labels_cache[trial["n_nodes"]]
        serialized_trials.append(
            {
                "trial_id": trial["trial_id"],
                "category": trial["category"],
                "subgroup_id": trial["subgroup_id"],
                "graph_id": trial["graph_id"],
                "n_nodes": trial["n_nodes"],
                "edges": labeled_edges_from_adjacency(trial["adjacency"]),
                "observed": labels[trial["observed"]],
                "target": labels[trial["target"]],
                "evidence_name": trial["evidence_name"],
                "informativeness_score": round(trial["score"], 6),
                "representative_model_posteriors": {
                    "M0": pretty_probabilities(trial["representative_predictions"]["M0"]),
                    "rho_0.5": pretty_probabilities(trial["representative_predictions"]["rho"]),
                    "exact": pretty_probabilities(trial["representative_predictions"]["exact"]),
                    "BP": pretty_probabilities(trial["representative_predictions"]["BP"]),
                },
            }
        )
    summary = {
        "candidate_trial_count": len(candidates),
        "selected_trial_count": len(selected_trials),
        "selected_by_category": dict(per_category_counter),
        "max_trials_per_graph": 2,
        "representative_rho_for_screening": REPRESENTATIVE_RHO,
    }
    return selected_trials, serialized_trials, summary


def build_model_prediction_bundle(
    adjacency: list[set[int]],
    observed: int,
    target: int,
    evidence_name: str,
    beta_edge: float,
) -> tuple[dict[str, tuple[float, ...]], float]:
    evidence = EVIDENCE_LEVELS[evidence_name]
    predictions = {
        "M0": independent_target_marginal_adj(adjacency, observed, target, evidence, beta_edge),
        "rho_0.5": exact_target_marginal_adj(
            adjacency,
            observed,
            target,
            evidence,
            beta_edge,
            rho=REPRESENTATIVE_RHO,
        ),
        "exact": exact_target_marginal_adj(adjacency, observed, target, evidence, beta_edge),
        "BP": pairwise_bp_target_marginal_adj(adjacency, observed, target, evidence, beta_edge)[0],
    }
    model_names = list(predictions)
    informativeness = 0.0
    for left_index, left_name in enumerate(model_names):
        for right_name in model_names[left_index + 1 :]:
            informativeness += symmetric_kl_divergence(predictions[left_name], predictions[right_name])
    return predictions, informativeness


def serialize_model_predictions(
    model_predictions: dict[str, tuple[float, ...] | list[float]],
) -> dict[str, list[float]]:
    return {
        model_name: pretty_probabilities(probabilities)
        for model_name, probabilities in model_predictions.items()
    }


def make_phase1_experiment_trial(
    pair: dict[str, object],
    pair_role: str,
    instance: dict[str, object],
    evidence_name: str,
    beta_edge: float,
) -> dict[str, object]:
    record = instance["record"]
    adjacency = record["adjacency"]
    labels = labels_for_n(record["n_nodes"])
    observed = instance["observed"]
    target = instance["target"]
    predictions, informativeness = build_model_prediction_bundle(
        adjacency,
        observed,
        target,
        evidence_name,
        beta_edge,
    )
    return {
        "trial_id": f"{pair['pair_id']}::{pair_role}::{evidence_name}",
        "phase": "phase1",
        "trial_mode": "forced_target_report",
        "graph_id": record["graph_id"],
        "pair_id": pair["pair_id"],
        "pair_role": pair_role,
        "source_item_id": pair["pair_id"],
        "n_nodes": record["n_nodes"],
        "nodes": list(labels),
        "adjacency": [set(neighbors) for neighbors in adjacency],
        "edges": labeled_edges_from_adjacency(adjacency),
        "edge_count": graph_edge_count(adjacency),
        "density": graph_density(adjacency),
        "degree_sequence": degree_sequence(adjacency),
        "observed": observed,
        "observed_node": labels[observed],
        "target": target,
        "target_node": labels[target],
        "target_in_task": True,
        "observed_target_distance": bfs_distances(adjacency, observed)[target],
        "evidence_name": evidence_name,
        "evidence_probs": list(EVIDENCE_LEVELS[evidence_name]),
        "model_predictions": predictions,
        "informativeness_score": informativeness,
        "phase1_metadata": {
            "local_signature": pair["serialized"]["local_signature"],
            "selection_metrics": pair["serialized"]["selection_metrics"],
            "graph_role": pair_role,
            "source": record["source"],
        },
        "phase2_metadata": None,
    }


def make_phase2_experiment_trial(
    graph: dict[str, object],
    evidence_name: str,
    beta_edge: float,
) -> dict[str, object]:
    record = graph["record"]
    adjacency = record["adjacency"]
    labels = labels_for_n(record["n_nodes"])
    observed = graph["best_pair"]["observed"]
    target = graph["best_pair"]["target"]
    predictions, informativeness = build_model_prediction_bundle(
        adjacency,
        observed,
        target,
        evidence_name,
        beta_edge,
    )
    return {
        "trial_id": f"{record['graph_id']}::{evidence_name}",
        "phase": "phase2",
        "trial_mode": "free_query",
        "graph_id": record["graph_id"],
        "pair_id": None,
        "pair_role": None,
        "source_item_id": record["graph_id"],
        "n_nodes": record["n_nodes"],
        "nodes": list(labels),
        "adjacency": [set(neighbors) for neighbors in adjacency],
        "edges": labeled_edges_from_adjacency(adjacency),
        "edge_count": graph_edge_count(adjacency),
        "density": graph_density(adjacency),
        "degree_sequence": degree_sequence(adjacency),
        "observed": observed,
        "observed_node": labels[observed],
        "target": target,
        "target_node": labels[target],
        "target_in_task": False,
        "observed_target_distance": bfs_distances(adjacency, observed)[target],
        "evidence_name": evidence_name,
        "evidence_probs": list(EVIDENCE_LEVELS[evidence_name]),
        "model_predictions": predictions,
        "informativeness_score": informativeness,
        "phase1_metadata": None,
        "phase2_metadata": {
            "source": record["source"],
            "gaps": {
                "total_fill_gap": graph["total_fill_gap"],
                "max_omega_gap": graph["max_omega_gap"],
                "first_step_fill_gap": graph["first_step_fill_gap"],
                "first_step_omega_gap": graph["first_step_omega_gap"],
            },
            "min_degree": serialize_trace(*graph["min_degree_trace"], labels),
            "min_fill": serialize_trace(*graph["min_fill_trace"], labels),
            "recommended_anchor_pair": {
                "observed": labels[observed],
                "target": labels[target],
                "distance": graph["best_pair"]["distance"],
                "informativeness_high": round(graph["best_pair"]["informativeness_high"], 6),
            },
        },
    }


def serialize_experiment_trial(trial: dict[str, object]) -> dict[str, object]:
    return {
        "trial_id": trial["trial_id"],
        "phase": trial["phase"],
        "trial_mode": trial["trial_mode"],
        "graph_id": trial["graph_id"],
        "pair_id": trial["pair_id"],
        "pair_role": trial["pair_role"],
        "graph": {
            "nodes": trial["nodes"],
            "edges": trial["edges"],
            "n_nodes": trial["n_nodes"],
            "edge_count": trial["edge_count"],
            "density": round(trial["density"], 6),
            "degree_sequence": trial["degree_sequence"],
        },
        "evidence": {
            "node": trial["observed_node"],
            "level": trial["evidence_name"],
            "probabilities": trial["evidence_probs"],
        },
        "query": {
            "target_node": trial["target_node"],
            "target_in_task": trial["target_in_task"],
            "observed_target_distance": trial["observed_target_distance"],
        },
        "model_predictions": serialize_model_predictions(trial["model_predictions"]),
        "informativeness_score": round(trial["informativeness_score"], 6),
        "phase1_metadata": trial["phase1_metadata"],
        "phase2_metadata": trial["phase2_metadata"],
    }


def build_experiment_trial_pool(
    selected_phase1_pairs: list[dict[str, object]],
    selected_phase2_graphs: list[dict[str, object]],
    beta_edge: float,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    trials: list[dict[str, object]] = []
    for pair in selected_phase1_pairs:
        for pair_role, instance in (("low", pair["low_instance"]), ("high", pair["high_instance"])):
            for evidence_name in EVIDENCE_LEVELS:
                trials.append(make_phase1_experiment_trial(pair, pair_role, instance, evidence_name, beta_edge))
    for graph in selected_phase2_graphs:
        for evidence_name in EVIDENCE_LEVELS:
            trials.append(make_phase2_experiment_trial(graph, evidence_name, beta_edge))
    serialized = [serialize_experiment_trial(trial) for trial in trials]
    summary = {
        "trial_count": len(trials),
        "phase_counts": dict(Counter(trial["phase"] for trial in trials)),
        "n_nodes_counts": dict(Counter(trial["n_nodes"] for trial in trials)),
        "evidence_counts": dict(Counter(trial["evidence_name"] for trial in trials)),
        "phase_by_n_nodes": {
            phase: dict(Counter(trial["n_nodes"] for trial in trials if trial["phase"] == phase))
            for phase in ("phase1", "phase2")
        },
        "phase_by_evidence": {
            phase: dict(Counter(trial["evidence_name"] for trial in trials if trial["phase"] == phase))
            for phase in ("phase1", "phase2")
        },
        "phase1_pair_count": len(selected_phase1_pairs),
        "phase2_graph_count": len(selected_phase2_graphs),
    }
    return trials, serialized, summary


def list_identifier(index: int) -> str:
    return f"L{index + 1:02d}"


def flatten_trial_row(
    trial: dict[str, object],
    list_id: str | None = None,
    order_index: int | None = None,
) -> dict[str, object]:
    return {
        "list_id": list_id or "",
        "order_index": order_index if order_index is not None else "",
        "trial_id": trial["trial_id"],
        "phase": trial["phase"],
        "trial_mode": trial["trial_mode"],
        "graph_id": trial["graph_id"],
        "pair_id": trial["pair_id"] or "",
        "pair_role": trial["pair_role"] or "",
        "n_nodes": trial["n_nodes"],
        "edge_count": trial["edge_count"],
        "density": round(trial["density"], 6),
        "nodes_json": json.dumps(trial["nodes"], ensure_ascii=False),
        "edges_json": json.dumps(trial["edges"], ensure_ascii=False),
        "degree_sequence_json": json.dumps(trial["degree_sequence"], ensure_ascii=False),
        "observed_node": trial["observed_node"],
        "target_node": trial["target_node"],
        "target_in_task": int(trial["target_in_task"]),
        "observed_target_distance": trial["observed_target_distance"],
        "evidence_name": trial["evidence_name"],
        "evidence_probs_json": json.dumps(trial["evidence_probs"], ensure_ascii=False),
        "informativeness_score": round(trial["informativeness_score"], 6),
        "model_M0_json": json.dumps(pretty_probabilities(trial["model_predictions"]["M0"]), ensure_ascii=False),
        "model_rho_0_5_json": json.dumps(
            pretty_probabilities(trial["model_predictions"]["rho_0.5"]),
            ensure_ascii=False,
        ),
        "model_exact_json": json.dumps(
            pretty_probabilities(trial["model_predictions"]["exact"]),
            ensure_ascii=False,
        ),
        "model_BP_json": json.dumps(pretty_probabilities(trial["model_predictions"]["BP"]), ensure_ascii=False),
        "phase1_local_signature_json": json.dumps(
            trial["phase1_metadata"]["local_signature"] if trial["phase1_metadata"] else None,
            ensure_ascii=False,
        ),
        "phase1_delta_p_target_R_json": json.dumps(
            trial["phase1_metadata"]["selection_metrics"]["delta_p_target_R"]
            if trial["phase1_metadata"]
            else None,
            ensure_ascii=False,
        ),
        "phase2_gaps_json": json.dumps(
            trial["phase2_metadata"]["gaps"] if trial["phase2_metadata"] else None,
            ensure_ascii=False,
        ),
        "phase2_min_degree_order_json": json.dumps(
            trial["phase2_metadata"]["min_degree"]["order"] if trial["phase2_metadata"] else None,
            ensure_ascii=False,
        ),
        "phase2_min_fill_order_json": json.dumps(
            trial["phase2_metadata"]["min_fill"]["order"] if trial["phase2_metadata"] else None,
            ensure_ascii=False,
        ),
    }


def write_csv_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def assign_phase1_trials_to_lists(
    phase1_trials: list[dict[str, object]],
    list_count: int,
    seed: int,
) -> list[list[dict[str, object]]]:
    pair_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for trial in phase1_trials:
        pair_groups[trial["pair_id"]].append(trial)
    target_evidence = {
        evidence_name: sum(trial["evidence_name"] == evidence_name for trial in phase1_trials) // list_count
        for evidence_name in EVIDENCE_LEVELS
    }
    low_role_target = sum(trial["pair_role"] == "low" for trial in phase1_trials) / list_count
    high_role_target = sum(trial["pair_role"] == "high" for trial in phase1_trials) / list_count
    rng = random.Random(seed)
    best_assignment = None
    best_role_score = None
    pair_ids = sorted(pair_groups)
    for _ in range(250):
        shuffled_pairs = pair_ids[:]
        rng.shuffle(shuffled_pairs)
        lists = [[] for _ in range(list_count)]
        evidence_counts = [Counter() for _ in range(list_count)]
        role_counts = [Counter() for _ in range(list_count)]
        success = True
        for pair_id in shuffled_pairs:
            trials = sorted(
                pair_groups[pair_id],
                key=lambda trial: (trial["pair_role"], trial["evidence_name"]),
            )
            best_option = None
            best_score = None
            for permutation in permutations(trials, list_count):
                feasible = True
                score = 0.0
                for list_index, trial in enumerate(permutation):
                    if evidence_counts[list_index][trial["evidence_name"]] >= target_evidence[trial["evidence_name"]]:
                        feasible = False
                        break
                    projected_evidence = evidence_counts[list_index][trial["evidence_name"]] + 1
                    projected_low = role_counts[list_index]["low"] + (trial["pair_role"] == "low")
                    projected_high = role_counts[list_index]["high"] + (trial["pair_role"] == "high")
                    score += 100.0 * (projected_evidence - target_evidence[trial["evidence_name"]]) ** 2
                    score += (projected_low - low_role_target) ** 2
                    score += (projected_high - high_role_target) ** 2
                if not feasible:
                    continue
                if best_score is None or score < best_score:
                    best_score = score
                    best_option = permutation
            if best_option is None:
                success = False
                break
            for list_index, trial in enumerate(best_option):
                lists[list_index].append(trial)
                evidence_counts[list_index][trial["evidence_name"]] += 1
                role_counts[list_index][trial["pair_role"]] += 1
        if not success:
            continue
        if any(
            evidence_counts[list_index][evidence_name] != target_evidence[evidence_name]
            for list_index in range(list_count)
            for evidence_name in EVIDENCE_LEVELS
        ):
            continue
        role_score = sum(
            abs(role_counts[list_index]["low"] - role_counts[list_index]["high"])
            for list_index in range(list_count)
        )
        if best_role_score is None or role_score < best_role_score:
            best_role_score = role_score
            best_assignment = [[trial for trial in trials] for trials in lists]
    if best_assignment is None:
        raise RuntimeError("Could not balance phase-1 trials across participant lists")
    return best_assignment


def assign_phase2_trials_to_lists(
    phase2_trials: list[dict[str, object]],
    list_count: int,
    seed: int,
) -> list[list[dict[str, object]]]:
    graph_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for trial in phase2_trials:
        graph_groups[trial["graph_id"]].append(trial)
    target_n = {
        n_nodes: sum(trial["n_nodes"] == n_nodes for trial in phase2_trials) // list_count
        for n_nodes in sorted({trial["n_nodes"] for trial in phase2_trials})
    }
    target_evidence = {
        evidence_name: sum(trial["evidence_name"] == evidence_name for trial in phase2_trials) // list_count
        for evidence_name in EVIDENCE_LEVELS
    }
    target_total = len(phase2_trials) // list_count
    graph_ids = sorted(
        graph_groups,
        key=lambda graph_id: (
            max(trial["observed_target_distance"] for trial in graph_groups[graph_id]),
            max(trial["informativeness_score"] for trial in graph_groups[graph_id]),
        ),
        reverse=True,
    )
    rng = random.Random(seed)
    best_assignment = None
    best_distance_penalty = None
    for _ in range(600):
        ordered_graphs = graph_ids[:]
        head = ordered_graphs[:1]
        tail = ordered_graphs[1:]
        rng.shuffle(tail)
        ordered_graphs = head + tail
        lists = [[] for _ in range(list_count)]
        total_counts = [0 for _ in range(list_count)]
        n_counts = [Counter() for _ in range(list_count)]
        evidence_counts = [Counter() for _ in range(list_count)]
        distance_counts = [Counter() for _ in range(list_count)]
        success = True
        for graph_id in ordered_graphs:
            trials = sorted(graph_groups[graph_id], key=lambda trial: trial["evidence_name"])
            best_option = None
            best_score = None
            for list_indices in permutations(range(list_count), len(trials)):
                feasible = True
                score = 0.0
                for trial, list_index in zip(trials, list_indices):
                    if total_counts[list_index] >= target_total:
                        feasible = False
                        break
                    if n_counts[list_index][trial["n_nodes"]] >= target_n[trial["n_nodes"]]:
                        feasible = False
                        break
                    if evidence_counts[list_index][trial["evidence_name"]] >= target_evidence[trial["evidence_name"]]:
                        feasible = False
                        break
                    projected_total = total_counts[list_index] + 1
                    projected_n = n_counts[list_index][trial["n_nodes"]] + 1
                    projected_evidence = evidence_counts[list_index][trial["evidence_name"]] + 1
                    score += 100.0 * (projected_total - target_total) ** 2
                    score += 120.0 * (projected_n - target_n[trial["n_nodes"]]) ** 2
                    score += 120.0 * (projected_evidence - target_evidence[trial["evidence_name"]]) ** 2
                    if trial["observed_target_distance"] == 3:
                        score += 5.0 * distance_counts[list_index][3]
                if not feasible:
                    continue
                if best_score is None or score < best_score:
                    best_score = score
                    best_option = list_indices
            if best_option is None:
                success = False
                break
            for trial, list_index in zip(trials, best_option):
                lists[list_index].append(trial)
                total_counts[list_index] += 1
                n_counts[list_index][trial["n_nodes"]] += 1
                evidence_counts[list_index][trial["evidence_name"]] += 1
                distance_counts[list_index][trial["observed_target_distance"]] += 1
        if not success:
            continue
        if any(total_counts[list_index] != target_total for list_index in range(list_count)):
            continue
        if any(
            n_counts[list_index][n_nodes] != target_n[n_nodes]
            for list_index in range(list_count)
            for n_nodes in target_n
        ):
            continue
        if any(
            evidence_counts[list_index][evidence_name] != target_evidence[evidence_name]
            for list_index in range(list_count)
            for evidence_name in EVIDENCE_LEVELS
        ):
            continue
        distance_penalty = sum(max(0, distance_counts[list_index][3] - 1) for list_index in range(list_count))
        if best_distance_penalty is None or distance_penalty < best_distance_penalty:
            best_distance_penalty = distance_penalty
            best_assignment = [[trial for trial in trials] for trials in lists]
    if best_assignment is None:
        raise RuntimeError("Could not balance phase-2 trials across participant lists")
    return best_assignment


def order_trials_within_list(trials: list[dict[str, object]], seed: int) -> list[dict[str, object]]:
    rng = random.Random(seed)
    remaining = [trial for trial in trials]
    ordered: list[dict[str, object]] = []
    while remaining:
        if not ordered:
            remaining.sort(
                key=lambda trial: (
                    trial["phase"] == "phase2",
                    trial["observed_target_distance"],
                    trial["informativeness_score"],
                ),
                reverse=True,
            )
            chosen = remaining[0]
        else:
            previous = ordered[-1]
            best_trial = None
            best_score = None
            for trial in remaining:
                score = 0.0
                if trial["phase"] == previous["phase"]:
                    score += 3.0
                if trial["n_nodes"] == previous["n_nodes"]:
                    score += 2.0
                if trial["evidence_name"] == previous["evidence_name"]:
                    score += 2.0
                if trial["graph_id"] == previous["graph_id"]:
                    score += 100.0
                if len(ordered) >= 2 and ordered[-2]["phase"] == previous["phase"] == trial["phase"]:
                    score += 4.0
                score -= 0.05 * trial["informativeness_score"]
                score += 0.001 * rng.random()
                if best_score is None or score < best_score:
                    best_score = score
                    best_trial = trial
            chosen = best_trial
        ordered.append(chosen)
        remaining.remove(chosen)
    return ordered


def participant_list_summary(trials: list[dict[str, object]]) -> dict[str, object]:
    phase_counts = Counter(trial["phase"] for trial in trials)
    n_counts = Counter(trial["n_nodes"] for trial in trials)
    evidence_counts = Counter(trial["evidence_name"] for trial in trials)
    phase_n_counts = {
        phase: dict(Counter(trial["n_nodes"] for trial in trials if trial["phase"] == phase))
        for phase in ("phase1", "phase2")
    }
    phase_evidence_counts = {
        phase: dict(Counter(trial["evidence_name"] for trial in trials if trial["phase"] == phase))
        for phase in ("phase1", "phase2")
    }
    phase1_role_counts = dict(
        Counter(trial["pair_role"] for trial in trials if trial["phase"] == "phase1")
    )
    phase2_distance_counts = dict(
        Counter(trial["observed_target_distance"] for trial in trials if trial["phase"] == "phase2")
    )
    return {
        "trial_count": len(trials),
        "phase_counts": dict(phase_counts),
        "n_nodes_counts": dict(n_counts),
        "evidence_counts": dict(evidence_counts),
        "phase_by_n_nodes": phase_n_counts,
        "phase_by_evidence": phase_evidence_counts,
        "phase1_role_counts": phase1_role_counts,
        "phase2_distance_counts": phase2_distance_counts,
    }


def build_balanced_participant_lists(
    experiment_trials: list[dict[str, object]],
    list_count: int,
    seed: int,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    phase1_trials = [trial for trial in experiment_trials if trial["phase"] == "phase1"]
    phase2_trials = [trial for trial in experiment_trials if trial["phase"] == "phase2"]
    phase1_lists = assign_phase1_trials_to_lists(phase1_trials, list_count, seed)
    phase2_lists = assign_phase2_trials_to_lists(phase2_trials, list_count, seed + 1)
    participant_lists = []
    flat_rows: list[dict[str, object]] = []
    for list_index in range(list_count):
        list_id = list_identifier(list_index)
        combined_trials = phase1_lists[list_index] + phase2_lists[list_index]
        ordered_trials = order_trials_within_list(combined_trials, seed + 100 + list_index)
        serialized_trials = []
        for order_index, trial in enumerate(ordered_trials, start=1):
            serialized = serialize_experiment_trial(trial)
            serialized["list_id"] = list_id
            serialized["order_index"] = order_index
            serialized_trials.append(serialized)
            flat_rows.append(flatten_trial_row(trial, list_id=list_id, order_index=order_index))
        participant_lists.append(
            {
                "list_id": list_id,
                "summary": participant_list_summary(ordered_trials),
                "trials": serialized_trials,
            }
        )
    target_summary = {
        "trial_count": len(experiment_trials) // list_count,
        "phase_counts": dict(Counter(trial["phase"] for trial in experiment_trials)),
        "n_nodes_counts": dict(Counter(trial["n_nodes"] for trial in experiment_trials)),
        "evidence_counts": dict(Counter(trial["evidence_name"] for trial in experiment_trials)),
        "per_list_targets": {
            "phase_counts": {
                phase: sum(trial["phase"] == phase for trial in experiment_trials) // list_count
                for phase in ("phase1", "phase2")
            },
            "n_nodes_counts": {
                n_nodes: sum(trial["n_nodes"] == n_nodes for trial in experiment_trials) // list_count
                for n_nodes in sorted({trial["n_nodes"] for trial in experiment_trials})
            },
            "evidence_counts": {
                evidence_name: sum(trial["evidence_name"] == evidence_name for trial in experiment_trials) // list_count
                for evidence_name in EVIDENCE_LEVELS
            },
            "phase_by_n_nodes": {
                phase: {
                    n_nodes: sum(
                        trial["phase"] == phase and trial["n_nodes"] == n_nodes
                        for trial in experiment_trials
                    )
                    // list_count
                    for n_nodes in sorted({trial["n_nodes"] for trial in experiment_trials})
                }
                for phase in ("phase1", "phase2")
            },
            "phase_by_evidence": {
                phase: {
                    evidence_name: sum(
                        trial["phase"] == phase and trial["evidence_name"] == evidence_name
                        for trial in experiment_trials
                    )
                    // list_count
                    for evidence_name in EVIDENCE_LEVELS
                }
                for phase in ("phase1", "phase2")
            },
        },
    }
    balanced_object = {
        "settings": {
            "list_count": list_count,
            "seed": seed,
            "balancing_dimensions": [
                "phase",
                "n_nodes",
                "evidence_name",
                "phase_by_n_nodes",
                "phase_by_evidence",
            ],
        },
        "target_summary": target_summary,
        "participant_lists": participant_lists,
    }
    return balanced_object, flat_rows


def dirichlet_sample(rng: random.Random, alpha: list[float]) -> tuple[float, ...]:
    draws = [rng.gammavariate(component, 1.0) for component in alpha]
    return normalize(draws)


def dirichlet_logpdf(y: tuple[float, ...], alpha: list[float]) -> float:
    return (
        math.lgamma(sum(alpha))
        - sum(math.lgamma(component) for component in alpha)
        + sum((component - 1.0) * math.log(max(value, 1e-300)) for component, value in zip(alpha, y))
    )


def fit_dataset_with_bic(
    dataset: list[tuple[dict[str, object], tuple[float, ...]]],
    kappa: float,
) -> dict[str, object]:
    n_trials = len(dataset)
    log_likelihoods = {
        "M0": sum(
            dirichlet_logpdf(
                response,
                [kappa * value for value in trial["prediction_grid"]["M0"]],
            )
            for trial, response in dataset
        ),
        "exact": sum(
            dirichlet_logpdf(
                response,
                [kappa * value for value in trial["prediction_grid"]["exact"]],
            )
            for trial, response in dataset
        ),
        "BP": sum(
            dirichlet_logpdf(
                response,
                [kappa * value for value in trial["prediction_grid"]["BP"]],
            )
            for trial, response in dataset
        ),
    }
    best_rho_key = None
    best_rho_log_likelihood = None
    for rho in RHO_GRID:
        rho_key = f"{rho:.2f}"
        rho_log_likelihood = sum(
            dirichlet_logpdf(
                response,
                [kappa * value for value in trial["prediction_grid"]["rho_family"][rho_key]],
            )
            for trial, response in dataset
        )
        if best_rho_log_likelihood is None or rho_log_likelihood > best_rho_log_likelihood:
            best_rho_log_likelihood = rho_log_likelihood
            best_rho_key = rho_key
    log_likelihoods["rho"] = best_rho_log_likelihood
    bic = {
        model_name: -2.0 * log_likelihood + (1 if model_name == "rho" else 0) * math.log(n_trials)
        for model_name, log_likelihood in log_likelihoods.items()
    }
    ranking = sorted(bic.items(), key=lambda item: item[1])
    return {
        "best_model": ranking[0][0],
        "runner_up_model": ranking[1][0],
        "bic": bic,
        "best_rho": float(best_rho_key),
        "bic_margin": ranking[1][1] - ranking[0][1],
    }


def run_model_recovery(
    selected_trials: list[dict[str, object]],
    kappa: float,
    datasets_per_class: int,
    seed: int,
    beta_edge: float,
) -> dict[str, object]:
    for trial in selected_trials:
        evidence = EVIDENCE_LEVELS[trial["evidence_name"]]
        trial["prediction_grid"] = {
            "M0": independent_target_marginal_adj(
                trial["adjacency"],
                trial["observed"],
                trial["target"],
                evidence,
                beta_edge,
            ),
            "exact": exact_target_marginal_adj(
                trial["adjacency"],
                trial["observed"],
                trial["target"],
                evidence,
                beta_edge,
            ),
            "BP": pairwise_bp_target_marginal_adj(
                trial["adjacency"],
                trial["observed"],
                trial["target"],
                evidence,
                beta_edge,
            )[0],
            "rho_family": {
                f"{rho:.2f}": exact_target_marginal_adj(
                    trial["adjacency"],
                    trial["observed"],
                    trial["target"],
                    evidence,
                    beta_edge,
                    rho=rho,
                )
                for rho in RHO_GRID
            },
        }
    rng = random.Random(seed)
    confusion_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    bic_margins: defaultdict[str, list[float]] = defaultdict(list)
    rho_absolute_errors: list[float] = []
    rho_estimate_histogram: Counter[str] = Counter()
    for generative_model in ("M0", "rho", "exact", "BP"):
        for _ in range(datasets_per_class):
            true_rho = rng.choice((0.25, 0.50, 0.75)) if generative_model == "rho" else None
            dataset: list[tuple[dict[str, object], tuple[float, ...]]] = []
            for trial in selected_trials:
                if generative_model == "rho":
                    prediction = trial["prediction_grid"]["rho_family"][f"{true_rho:.2f}"]
                else:
                    prediction = trial["prediction_grid"][generative_model]
                response = dirichlet_sample(rng, [kappa * value for value in prediction])
                dataset.append((trial, response))
            fit = fit_dataset_with_bic(dataset, kappa)
            confusion_counts[generative_model][fit["best_model"]] += 1
            bic_margins[generative_model].append(fit["bic_margin"])
            if generative_model == "rho":
                rho_absolute_errors.append(abs(fit["best_rho"] - true_rho))
                rho_estimate_histogram[f"{fit['best_rho']:.2f}"] += 1
    confusion_rates = {
        generative_model: {
            fitted_model: confusion_counts[generative_model][fitted_model] / datasets_per_class
            for fitted_model in ("M0", "rho", "exact", "BP")
        }
        for generative_model in ("M0", "rho", "exact", "BP")
    }
    return {
        "settings": {
            "kappa": kappa,
            "datasets_per_class": datasets_per_class,
            "seed": seed,
            "rho_grid": [round(rho, 2) for rho in RHO_GRID],
            "rho_generative_values": [0.25, 0.50, 0.75],
        },
        "confusion_counts": {
            generative_model: {
                fitted_model: confusion_counts[generative_model][fitted_model]
                for fitted_model in ("M0", "rho", "exact", "BP")
            }
            for generative_model in ("M0", "rho", "exact", "BP")
        },
        "confusion_rates": confusion_rates,
        "model_selection_accuracy": {
            generative_model: confusion_rates[generative_model][generative_model]
            for generative_model in ("M0", "rho", "exact", "BP")
        },
        "mean_bic_margin": {
            generative_model: round(sum(bic_margins[generative_model]) / len(bic_margins[generative_model]), 6)
            for generative_model in ("M0", "rho", "exact", "BP")
        },
        "rho_estimation": {
            "mean_abs_error": round(sum(rho_absolute_errors) / len(rho_absolute_errors), 6),
            "median_abs_error": round(sorted(rho_absolute_errors)[len(rho_absolute_errors) // 2], 6),
            "max_abs_error": round(max(rho_absolute_errors), 6),
            "estimated_rho_histogram": dict(rho_estimate_histogram),
        },
    }


def build_results() -> dict[str, object]:
    beta_edge = DEFAULT_BETA_EDGE
    strong_evidence = {"X1": EVIDENCE_LEVELS["high"]}

    local_equivalence_chain = NamedGraph(
        name="4-node chain local-equivalence graph",
        nodes=("X1", "X2", "X3", "X4"),
        edges=(("X1", "X2"), ("X2", "X3"), ("X3", "X4")),
        observed="X1",
        target="X3",
    )
    local_equivalence_cycle = NamedGraph(
        name="4-node cycle local-equivalence graph",
        nodes=("X1", "X2", "X3", "X4"),
        edges=(("X1", "X2"), ("X2", "X3"), ("X3", "X4"), ("X4", "X1")),
        observed="X1",
        target="X3",
    )
    minimal_panel = [
        NamedGraph(
            name="3-node chain",
            nodes=("X1", "X2", "X3"),
            edges=(("X1", "X2"), ("X2", "X3")),
            observed="X1",
            target="X3",
        ),
        NamedGraph(
            name="4-node chain",
            nodes=("X1", "X2", "X3", "X4"),
            edges=(("X1", "X2"), ("X2", "X3"), ("X3", "X4")),
            observed="X1",
            target="X4",
        ),
        NamedGraph(
            name="4-node tree",
            nodes=("X1", "X2", "X3", "X4"),
            edges=(("X1", "X2"), ("X2", "X3"), ("X2", "X4")),
            observed="X1",
            target="X4",
        ),
        local_equivalence_cycle,
    ]
    minimal_panel_results = []
    for graph in minimal_panel:
        posterior = exact_target_marginal(graph, strong_evidence, beta_edge)
        minimal_panel_results.append(
            {
                "graph": graph.name,
                "target": graph.target,
                "posterior": pretty_probabilities(posterior),
                "p_target_R": round(posterior[0], 6),
                "distance_from_evidence": graph.distances(graph.observed)[graph.target],
            }
        )

    pair_results = []
    for level_name, evidence_tuple in EVIDENCE_LEVELS.items():
        evidence = {"X1": evidence_tuple}
        chain_posterior = exact_target_marginal(local_equivalence_chain, evidence, beta_edge)
        cycle_posterior = exact_target_marginal(local_equivalence_cycle, evidence, beta_edge)
        independent_posterior = independent_target_marginal(local_equivalence_chain, evidence, beta_edge)
        pair_results.append(
            {
                "evidence_level": level_name,
                "evidence": list(evidence_tuple),
                "independent": pretty_probabilities(independent_posterior),
                "chain": pretty_probabilities(chain_posterior),
                "cycle": pretty_probabilities(cycle_posterior),
                "p_target_R": {
                    "independent": round(independent_posterior[0], 6),
                    "chain": round(chain_posterior[0], 6),
                    "cycle": round(cycle_posterior[0], 6),
                },
                "kl_cycle_vs_chain": round(kl_divergence(cycle_posterior, chain_posterior), 6),
                "kl_chain_vs_independent": round(
                    kl_divergence(chain_posterior, independent_posterior),
                    6,
                ),
                "kl_cycle_vs_independent": round(
                    kl_divergence(cycle_posterior, independent_posterior),
                    6,
                ),
            }
        )

    rho_results = []
    for rho in (0.0, 0.25, 0.5, 0.75, 1.0):
        posterior = exact_target_marginal(local_equivalence_cycle, strong_evidence, beta_edge, rho=rho)
        rho_results.append(
            {
                "rho": rho,
                "posterior": pretty_probabilities(posterior),
                "p_target_R": round(posterior[0], 6),
                "entropy": round(entropy(posterior), 6),
            }
        )

    bp_tree = NamedGraph(
        name="4-node chain",
        nodes=("X1", "X2", "X3", "X4"),
        edges=(("X1", "X2"), ("X2", "X3"), ("X3", "X4")),
        observed="X1",
        target="X3",
    )
    bp_loopy = NamedGraph(
        name="4-node chorded cycle",
        nodes=("X1", "X2", "X3", "X4"),
        edges=(("X1", "X2"), ("X2", "X3"), ("X3", "X4"), ("X4", "X1"), ("X2", "X4")),
        observed="X1",
        target="X3",
    )
    bp_results = []
    for graph in (bp_tree, bp_loopy):
        exact = exact_target_marginal(graph, strong_evidence, beta_edge)
        approximate, iterations, residual = pairwise_bp_target_marginal(
            graph,
            strong_evidence,
            beta_edge,
        )
        bp_results.append(
            {
                "graph": graph.name,
                "target": graph.target,
                "exact": pretty_probabilities(exact),
                "bp": pretty_probabilities(approximate),
                "kl_exact_vs_bp": round(kl_divergence(exact, approximate), 6),
                "iterations": iterations,
                "final_change": residual,
            }
        )

    complexity_five = exhaustive_complexity_statistics(5)
    complexity_six = exhaustive_complexity_statistics(6)

    phase1_records = sample_unique_colorable_graph_records(
        PHASE1_SAMPLE_COUNTS,
        seed=20260326,
        prefix="phase1",
    )
    phase1_pairs_serialized, phase1_screening_summary, phase1_pairs_internal = screen_phase1_pairs(
        phase1_records,
        beta_edge,
    )
    phase2_graphs_serialized, phase2_screening_summary, phase2_graphs_internal = screen_phase2_graphs(
        beta_edge,
    )
    recovery_trials_internal, recovery_trials_serialized, recovery_trial_summary = build_recovery_trial_library(
        phase1_pairs_internal,
        phase2_graphs_internal,
        beta_edge,
    )
    model_recovery = run_model_recovery(
        recovery_trials_internal,
        DEFAULT_KAPPA,
        MODEL_RECOVERY_DATASETS_PER_CLASS,
        seed=20260327,
        beta_edge=beta_edge,
    )
    model_recovery["selected_trials"] = recovery_trials_serialized
    model_recovery["trial_library_summary"] = recovery_trial_summary

    experiment_trials_internal, experiment_trials_serialized, experiment_trial_summary = build_experiment_trial_pool(
        phase1_pairs_internal,
        phase2_graphs_internal,
        beta_edge,
    )
    balanced_lists, balanced_list_rows = build_balanced_participant_lists(
        experiment_trials_internal,
        BALANCED_LIST_COUNT,
        seed=20260328,
    )

    stimulus_screening = {
        "settings": {
            "phase1_sample_counts": PHASE1_SAMPLE_COUNTS,
            "phase2_sample_counts": PHASE2_SAMPLE_COUNTS,
            "representative_rho": REPRESENTATIVE_RHO,
            "beta_edge": beta_edge,
        },
        "phase1_screening_summary": phase1_screening_summary,
        "phase1_pairs": phase1_pairs_serialized,
        "phase2_screening_summary": phase2_screening_summary,
        "phase2_graphs": phase2_graphs_serialized,
    }
    experiment_exports = {
        "trial_pool_summary": experiment_trial_summary,
        "balanced_lists_summary": {
            "list_count": balanced_lists["settings"]["list_count"],
            "per_list_targets": balanced_lists["target_summary"]["per_list_targets"],
            "list_summaries": [
                {
                    "list_id": participant_list["list_id"],
                    "summary": participant_list["summary"],
                }
                for participant_list in balanced_lists["participant_lists"]
            ],
        },
    }

    return {
        "note": (
            "The continuous rho family is implemented by attenuating edge energies. "
            "Multiplying an entire factor by rho^d would cancel after normalization "
            "and would therefore not define a meaningful continuum."
        ),
        "beta_edge": beta_edge,
        "color_labels": list(COLOR_LABELS),
        "minimal_panel": minimal_panel_results,
        "local_equivalence_pair": pair_results,
        "rho_continuum": rho_results,
        "bp_comparison": bp_results,
        "complexity_statistics": [complexity_five, complexity_six],
        "heuristic_exemplar": complexity_six["exemplar"],
        "stimulus_screening": stimulus_screening,
        "model_recovery": model_recovery,
        "experiment_exports": experiment_exports,
        "_experiment_trial_pool": experiment_trials_serialized,
        "_experiment_trial_rows": [flatten_trial_row(trial) for trial in experiment_trials_internal],
        "_balanced_lists": balanced_lists,
        "_balanced_list_rows": balanced_list_rows,
    }


def main() -> None:
    # Paths: analysis-1/code/analysis-1.py
    #   code_dir    = analysis-1/code/
    #   data_dir    = analysis-1/code/data/   (all data outputs)
    code_dir = Path(__file__).resolve().parent
    data_dir = code_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    results = build_results()
    base_path = data_dir / "analysis-1_execution_results.json"
    stimulus_path = data_dir / "analysis-1_stimulus_library.json"
    recovery_path = data_dir / "analysis-1_model_recovery.json"
    trial_pool_json_path = data_dir / "analysis-1_experiment_trials.json"
    trial_pool_csv_path = data_dir / "analysis-1_experiment_trials.csv"
    balanced_json_path = data_dir / "analysis-1_balanced_lists.json"
    balanced_csv_path = data_dir / "analysis-1_balanced_lists.csv"
    experiment_trial_pool = results.pop("_experiment_trial_pool")
    experiment_trial_rows = results.pop("_experiment_trial_rows")
    balanced_lists = results.pop("_balanced_lists")
    balanced_list_rows = results.pop("_balanced_list_rows")
    base_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    stimulus_path.write_text(json.dumps(results["stimulus_screening"], indent=2), encoding="utf-8")
    recovery_path.write_text(json.dumps(results["model_recovery"], indent=2), encoding="utf-8")
    trial_pool_json_path.write_text(json.dumps({"trials": experiment_trial_pool}, indent=2), encoding="utf-8")
    balanced_json_path.write_text(json.dumps(balanced_lists, indent=2), encoding="utf-8")
    write_csv_rows(trial_pool_csv_path, experiment_trial_rows)
    write_csv_rows(balanced_csv_path, balanced_list_rows)
    print(f"Wrote {base_path}")
    print(f"Wrote {stimulus_path}")
    print(f"Wrote {recovery_path}")
    print(f"Wrote {trial_pool_json_path}")
    print(f"Wrote {trial_pool_csv_path}")
    print(f"Wrote {balanced_json_path}")
    print(f"Wrote {balanced_csv_path}")
    high = results["local_equivalence_pair"][0]
    print(
        "High-evidence local-equivalence pair:",
        f"M0 p(R)={high['p_target_R']['independent']:.6f},",
        f"chain={high['p_target_R']['chain']:.6f},",
        f"cycle={high['p_target_R']['cycle']:.6f}",
    )
    phase1_pairs = results["stimulus_screening"]["phase1_pairs"]
    phase2_graphs = results["stimulus_screening"]["phase2_graphs"]
    print(
        "Stimulus library:",
        f"{len(phase1_pairs)} phase-1 pairs, {len(phase2_graphs)} phase-2 graphs",
    )
    recovery_accuracy = results["model_recovery"]["model_selection_accuracy"]
    print("Model recovery accuracy:", recovery_accuracy)
    print(
        "Experiment exports:",
        f"{results['experiment_exports']['trial_pool_summary']['trial_count']} master trials,",
        f"{len(results['experiment_exports']['balanced_lists_summary']['list_summaries'])} balanced lists",
    )


if __name__ == "__main__":
    main()
