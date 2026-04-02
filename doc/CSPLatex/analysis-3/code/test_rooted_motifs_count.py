#!/usr/bin/env python3
"""
Re-verify the rooted motif counts claimed in `analysis-3.tex`:

We enumerate all connected, 3-colorable unrooted graphs with n in {5,6},
then do rooted deduplication:
 - compute all graph centers (min eccentricity)
 - for each center, compute rooted-canonical key by permuting all other vertices
 - if the same unrooted graph has multiple centers, keep rooted-canonical forms for
   all (mutually non-equivalent) centers
 - global deduplication is by (n_nodes, rooted_key)

This script computes the counts from scratch (no reuse of existing json outputs),
and cross-checks against `analysis-3_rooted_motif_catalog.json` length.
"""

from __future__ import annotations

from itertools import combinations, permutations
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

COLOR_COUNT = 3


def connected(adjacency: Tuple[Tuple[int, ...], ...]) -> bool:
    if not adjacency:
        return False
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


def edges_from_adjacency(adjacency: Tuple[Tuple[int, ...], ...]) -> Tuple[Tuple[int, int], ...]:
    n = len(adjacency)
    edges: List[Tuple[int, int]] = []
    for node in range(n):
        for neighbor in adjacency[node]:
            if node < neighbor:
                edges.append((node, neighbor))
    return tuple(sorted(edges))


def bfs_distances(adjacency: Tuple[Tuple[int, ...], ...], source: int) -> Dict[int, int]:
    distances: Dict[int, int] = {source: 0}
    queue: List[int] = [source]
    for node in queue:
        for neighbor in adjacency[node]:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[node] + 1
            queue.append(neighbor)
    return distances


def eccentricity(adjacency: Tuple[Tuple[int, ...], ...], source: int) -> int:
    return max(bfs_distances(adjacency, source).values())


def edge_key_after_permutation(
    adjacency: Tuple[Tuple[int, ...], ...],
    permutation: Tuple[int, ...],
) -> Tuple[Tuple[int, int], ...]:
    """
    Canonicalize an adjacency under a vertex permutation by turning the edge list into
    a sorted key of (min(new_u,new_v), max(...)).
    """
    inverse = {old_index: new_index for new_index, old_index in enumerate(permutation)}
    edges: List[Tuple[int, int]] = []
    for left, right in edges_from_adjacency(adjacency):
        new_left = inverse[left]
        new_right = inverse[right]
        edges.append((min(new_left, new_right), max(new_left, new_right)))
    return tuple(sorted(edges))


def rooted_canonical_form(
    adjacency: Tuple[Tuple[int, ...], ...],
    root: int,
) -> Tuple[Tuple[Tuple[int, int], ...], Tuple[Tuple[int, ...], ...]]:
    """
    Rooted canonical key: keep root fixed as canonical label 0, permute the rest,
    and pick lexicographically smallest edge-set key.
    """
    n = len(adjacency)
    others = tuple(node for node in range(n) if node != root)
    best_key: Tuple[Tuple[int, int], ...] | None = None
    best_adjacency: Tuple[Tuple[int, ...], ...] | None = None

    for remainder in permutations(others):
        permutation = (root,) + remainder
        key = edge_key_after_permutation(adjacency, permutation)
        if best_key is not None and key >= best_key:
            continue
        best_key = key

        # Build adjacency from edge-set key for completeness (not strictly needed for counting).
        adjacency_sets = [set() for _ in range(n)]
        for left, right in key:
            adjacency_sets[left].add(right)
            adjacency_sets[right].add(left)
        best_adjacency = tuple(tuple(sorted(neighbors)) for neighbors in adjacency_sets)

    assert best_key is not None and best_adjacency is not None
    return best_key, best_adjacency


def rooted_central_keys(adjacency: Tuple[Tuple[int, ...], ...]) -> Tuple[Tuple[Tuple[Tuple[int, int], ...], ...], ...]:
    """
    Return all (mutually non-equivalent) rooted-canonical keys across graph centers.

    This mirrors the logic in `analysis-3.py`'s rooted_central_forms:
    - compute all centers (min eccentricity)
    - for each center compute rooted_canonical_form
    - dedupe by rooted_key only
    """
    n = len(adjacency)
    eccentricities = {node: eccentricity(adjacency, node) for node in range(n)}
    minimum_ecc = min(eccentricities.values())
    centers = tuple(sorted(node for node, value in eccentricities.items() if value == minimum_ecc))

    seen_keys: Set[Tuple[Tuple[int, int], ...]] = set()
    rooted_keys: List[Tuple[Tuple[int, int], ...]] = []
    for center in centers:
        rooted_key, _ = rooted_canonical_form(adjacency, center)
        if rooted_key in seen_keys:
            continue
        seen_keys.add(rooted_key)
        rooted_keys.append(rooted_key)

    rooted_keys.sort()
    return tuple(rooted_keys)


def enumerate_rooted_motif_keys(n_nodes: int) -> Set[Tuple[Tuple[int, int], ...]]:
    all_edges = list(combinations(range(n_nodes), 2))
    edge_count = len(all_edges)
    all_perms = permutations(range(n_nodes))  # for canonical_unrooted_key parity; unused in dedupe

    # Global deduplication (analysis-3.py): seen_rooted_keys is by (n_nodes, rooted_key).
    # For our purposes, root_n is fixed, so just collect rooted_key.
    rooted_key_set: Set[Tuple[Tuple[int, int], ...]] = set()

    for mask in range(1, 1 << edge_count):  # mask=0 is empty graph
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

        # analysis-3.py computes canonical_unrooted_key but does not use it for dedup;
        # we omit it for speed.
        for rooted_key in rooted_central_keys(adjacency):
            rooted_key_set.add(rooted_key)

    return rooted_key_set


def main() -> None:
    # Current file: doc/CSPLatex/analysis-3/code/test_rooted_motifs_count.py
    # parents[4] is the repository root.
    repo_root = Path(__file__).resolve().parents[4]
    catalog_path = (
        repo_root
        / "doc"
        / "CSPLatex"
        / "analysis-3"
        / "code"
        / "data"
        / "analysis-3_rooted_motif_catalog.json"
    )

    computed: Dict[int, int] = {}
    rooted_keys_union = 0
    for n in (5, 6):
        keys = enumerate_rooted_motif_keys(n)
        computed[n] = len(keys)
        rooted_keys_union += len(keys)

    computed_total = rooted_keys_union
    print("Recomputed rooted motif counts (from scratch):")
    print(f"  n=5  -> {computed[5]} rooted motifs (claimed 27)")
    print(f"  n=6  -> {computed[6]} rooted motifs (claimed 173)")
    print(f"  total -> {computed_total} rooted motifs (claimed 200)")

    if computed[5] == 27 and computed[6] == 173 and computed_total == 200:
        print("PASS: counts match the claims.")
    else:
        print("FAIL: counts differ from the claims.")

    # Cross-check with existing catalog output length.
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog_len = len(catalog.get("rooted_graphs", [])) if isinstance(catalog, dict) else len(catalog)
        print()
        print(f"Catalog file cross-check: {catalog_path.name} contains {catalog_len} rooted graphs.")
    except FileNotFoundError:
        print()
        print(f"(Skip catalog cross-check: file not found: {catalog_path})")


if __name__ == "__main__":
    main()

