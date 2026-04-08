from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
import math
from typing import Iterable

COLOR_COUNT = 3
DEFAULT_BETA = 4.0
FAMILY_ORDER = ("M_exact", "M_0", "M_rho", "M_rho,beta", "M_star", "M_cluster")
CANONICAL_FAMILIES = {
    "M_exact": {"family": "M_exact", "beta": DEFAULT_BETA},
    "M_0": {"family": "M_0", "beta": DEFAULT_BETA},
    "M_rho": {"family": "M_rho", "rho": 0.35, "beta": DEFAULT_BETA},
    "M_rho,beta": {"family": "M_rho,beta", "rho": 0.35, "beta": 2.5},
    "M_star": {"family": "M_star", "beta": DEFAULT_BETA},
    "M_cluster": {"family": "M_cluster", "beta": DEFAULT_BETA},
}

_ASSIGNMENT_CACHE: dict[int, tuple[tuple[int, ...], ...]] = {}


@dataclass(frozen=True)
class FamilyResult:
    family: str
    posterior: tuple[float, float, float]


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


def edges_from_adjacency(adjacency: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (node, neighbor)
        for node in range(len(adjacency))
        for neighbor in adjacency[node]
        if node < neighbor
    )


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


def exact_posterior_from_edge_strengths(
    n_nodes: int,
    edge_strengths: dict[tuple[int, int], float],
    evidence_by_node: dict[int, tuple[float, float, float]],
    target: int,
) -> tuple[float, float, float]:
    assignments = assignments_for_n(n_nodes)
    active_edges = [
        (min(left, right), max(left, right), math.exp(-strength))
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
        for left, right, penalty in active_edges:
            if assignment[left] == assignment[right]:
                weight *= penalty
        partition += weight
        posterior[assignment[target]] += weight
    if partition == 0.0:
        return (1 / 3, 1 / 3, 1 / 3)
    return normalize(posterior)


def edge_strengths_rho(
    adjacency: tuple[tuple[int, ...], ...],
    target: int,
    rho: float,
    beta: float,
) -> dict[tuple[int, int], float]:
    distances = bfs_distances(adjacency, target)
    strengths = {}
    for left, right in edges_from_adjacency(adjacency):
        shell = min(distances[left], distances[right])
        strengths[(left, right)] = beta * (rho**shell)
    return strengths


def edge_strengths_star(
    adjacency: tuple[tuple[int, ...], ...],
    target: int,
    beta: float,
) -> dict[tuple[int, int], float]:
    distances = bfs_distances(adjacency, target)
    strengths = {}
    for node in range(len(adjacency)):
        if node == target:
            continue
        strengths[(min(target, node), max(target, node))] = beta / max(1, distances[node])
    return strengths


def edge_strengths_cluster(
    adjacency: tuple[tuple[int, ...], ...],
    target: int,
    beta: float,
) -> dict[tuple[int, int], float]:
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
    family = str(family_config["family"])
    beta = float(family_config.get("beta", DEFAULT_BETA))
    if family == "M_exact":
        edge_strengths = edge_strengths_rho(adjacency, target, rho=1.0, beta=beta)
    elif family == "M_0":
        edge_strengths = edge_strengths_rho(adjacency, target, rho=0.0, beta=beta)
    elif family in {"M_rho", "M_rho,beta"}:
        edge_strengths = edge_strengths_rho(adjacency, target, rho=float(family_config["rho"]), beta=beta)
    elif family == "M_star":
        edge_strengths = edge_strengths_star(adjacency, target, beta=beta)
    elif family == "M_cluster":
        edge_strengths = edge_strengths_cluster(adjacency, target, beta=beta)
    else:
        raise ValueError(f"Unknown family: {family}")
    return exact_posterior_from_edge_strengths(len(adjacency), edge_strengths, evidence_by_node, target)


def all_family_posteriors(
    adjacency: tuple[tuple[int, ...], ...],
    target: int,
    evidence_by_node: dict[int, tuple[float, float, float]],
    families: dict[str, dict[str, object]] | None = None,
) -> list[FamilyResult]:
    configs = CANONICAL_FAMILIES if families is None else families
    return [
        FamilyResult(
            family=family,
            posterior=family_posterior(adjacency, target, evidence_by_node, configs[family]),
        )
        for family in FAMILY_ORDER
    ]
