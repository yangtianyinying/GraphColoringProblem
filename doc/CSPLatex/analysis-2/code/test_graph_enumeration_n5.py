#!/usr/bin/env python3
"""
Re-verify the count used in `analysis-2.tex` for n=5:
connected + 3-colorable + non-isomorphic unrooted graphs.

This script is intentionally self-contained so it can be run as a sanity check.
"""

from __future__ import annotations

from itertools import combinations, permutations
from typing import Dict, Iterable, List, Set, Tuple

COLOR_COUNT = 3


def connected(adjacency: Tuple[Tuple[int, ...], ...]) -> bool:
    visited: Set[int] = {0}
    queue: List[int] = [0]
    for node in queue:
        for neighbor in adjacency[node]:
            if neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append(neighbor)
    return len(visited) == len(adjacency)


def three_colorable(adjacency: Tuple[Tuple[int, ...], ...]) -> bool:
    """
    Backtracking exact check for chromatic number <= 3.
    """

    n = len(adjacency)
    order = sorted(range(n), key=lambda node: (-len(adjacency[node]), node))
    colors = [-1] * n

    def backtrack(index: int) -> bool:
        if index == n:
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


def edges_from_adjacency(adjacency: Tuple[Tuple[int, ...], ...]) -> Tuple[Tuple[int, int], ...]:
    n = len(adjacency)
    edges: List[Tuple[int, int]] = []
    for node in range(n):
        for neighbor in adjacency[node]:
            if node < neighbor:
                edges.append((node, neighbor))
    return tuple(sorted(edges))


def edge_key_after_permutation(
    adjacency: Tuple[Tuple[int, ...], ...],
    permutation: Tuple[int, ...],
) -> Tuple[Tuple[int, int], ...]:
    """
    Convert adjacency to a canonical representation under a vertex permutation.

    Returns an edge-set key: sorted (min(u,v), max(u,v)) for all edges.
    """
    inverse = {old_index: new_index for new_index, old_index in enumerate(permutation)}
    edges = []
    for left, right in edges_from_adjacency(adjacency):
        new_left = inverse[left]
        new_right = inverse[right]
        edges.append((min(new_left, new_right), max(new_left, new_right)))
    return tuple(sorted(edges))


def canonical_unrooted_key(
    adjacency: Tuple[Tuple[int, ...], ...],
    all_permutations: Tuple[Tuple[int, ...], ...],
) -> Tuple[Tuple[int, int], ...]:
    """
    Canonical key by taking the lexicographically smallest edge-set over all permutations.
    """
    best_key: Tuple[Tuple[int, int], ...] | None = None
    for permutation in all_permutations:
        key = edge_key_after_permutation(adjacency, permutation)
        if best_key is None or key < best_key:
            best_key = key
    assert best_key is not None
    return best_key


def adjacency_from_edge_key(
    n_nodes: int,
    edge_key: Tuple[Tuple[int, int], ...],
) -> Tuple[Tuple[int, ...], ...]:
    adjacency_sets = [set() for _ in range(n_nodes)]
    for left, right in edge_key:
        adjacency_sets[left].add(right)
        adjacency_sets[right].add(left)
    return tuple(tuple(sorted(neighbors)) for neighbors in adjacency_sets)


def graph_degree_signature(adjacency: Tuple[Tuple[int, ...], ...]) -> Tuple[int, ...]:
    return tuple(sorted(len(neighbors) for neighbors in adjacency))


def enumerate_graph_classes(n_nodes: int) -> Dict[Tuple[Tuple[int, int], ...], Dict[str, object]]:
    all_edges = list(combinations(range(n_nodes), 2))
    all_permutations = tuple(permutations(range(n_nodes)))

    graph_classes: Dict[Tuple[Tuple[int, int], ...], Dict[str, object]] = {}
    for mask in range(1, 1 << len(all_edges)):  # mask=0 is empty graph (disconnected anyway)
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
        graph_classes[key] = {"adjacency": adjacency}
    return graph_classes


def enumerate_connected_non_three_colorable(n_nodes: int) -> Dict[Tuple[Tuple[int, int], ...], Tuple[Tuple[int, ...], ...]]:
    all_edges = list(combinations(range(n_nodes), 2))
    all_permutations = tuple(permutations(range(n_nodes)))

    classes: Dict[Tuple[Tuple[int, int], ...], Tuple[Tuple[int, ...], ...]] = {}
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
        if three_colorable(adjacency):
            continue

        key = canonical_unrooted_key(adjacency, all_permutations)
        if key in classes:
            continue
        classes[key] = adjacency
    return classes


def main() -> None:
    n = 5
    classes_3 = enumerate_graph_classes(n)
    classes_non3 = enumerate_connected_non_three_colorable(n)

    print(f"n={n}")
    print(f"connected + 3-colorable + non-isomorphic (unrooted) count = {len(classes_3)}")
    print(f"connected + NOT 3-colorable + non-isomorphic count = {len(classes_non3)}")
    print()

    # Print a stable summary for diagnosis.
    def pretty_key(key: Tuple[Tuple[int, int], ...]) -> str:
        edges = [f"{u}-{v}" for u, v in key]
        return ", ".join(edges)

    print("3-colorable classes:")
    for idx, key in enumerate(sorted(classes_3.keys()), start=1):
        adjacency = adjacency_from_edge_key(n, key)
        degsig = graph_degree_signature(adjacency)
        print(f"  {idx:02d}. edges=[{pretty_key(key)}], degree_sig={degsig}")

    print()
    print("Non-3-colorable connected classes:")
    for idx, key in enumerate(sorted(classes_non3.keys()), start=1):
        adjacency = adjacency_from_edge_key(n, key)
        degsig = graph_degree_signature(adjacency)
        print(f"  {idx:02d}. edges=[{pretty_key(key)}], degree_sig={degsig}")


if __name__ == "__main__":
    main()

