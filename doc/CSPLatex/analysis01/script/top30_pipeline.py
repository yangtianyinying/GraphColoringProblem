from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations, product
import csv
import json
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

if __package__ is None or __package__ == "":
    project_dir = Path(__file__).resolve().parents[1]
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))

from agent.models import CANONICAL_FAMILIES, FAMILY_ORDER, family_posterior


# TODO(2026-04-08) updated priors: high / medium / low only.
EVIDENCE_LEVELS = {
    "high": (0.9, 0.05, 0.05),
    "medium": (0.7, 0.15, 0.15),
    "low": (0.5, 0.25, 0.25),
}
N_RANGE = (5, 6)
DIVERSITY_WEIGHTS = {"template": 0.35, "occupancy": 0.20, "graph": 0.15}
TOP_K = 30


@dataclass(frozen=True)
class RootedGraph:
    graph_id: str
    n_nodes: int
    adjacency: tuple[tuple[int, ...], ...]
    rooted_key: tuple[tuple[int, int], ...]
    preferred_colors: tuple[int, ...]


def kl_divergence(p: tuple[float, ...], q: tuple[float, ...], epsilon: float = 1e-12) -> float:
    q = tuple(max(value, epsilon) for value in q)
    return sum(left * math.log(left / right) for left, right in zip(p, q) if left > 0.0)


def js_divergence(p: tuple[float, ...], q: tuple[float, ...]) -> float:
    midpoint = tuple((left + right) / 2.0 for left, right in zip(p, q))
    return 0.5 * kl_divergence(p, midpoint) + 0.5 * kl_divergence(q, midpoint)


def z_scores(values: list[float]) -> list[float]:
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    std = math.sqrt(variance)
    if std == 0.0:
        return [0.0 for _ in values]
    return [(value - mean_value) / std for value in values]


def edges_from_adjacency(adjacency: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (node, neighbor)
        for node in range(len(adjacency))
        for neighbor in adjacency[node]
        if node < neighbor
    )


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


def three_coloring(adjacency: tuple[tuple[int, ...], ...]) -> tuple[int, ...] | None:
    order = sorted(range(len(adjacency)), key=lambda node: (-len(adjacency[node]), node))
    colors = [-1] * len(adjacency)

    def backtrack(index: int) -> bool:
        if index == len(order):
            return True
        node = order[index]
        forbidden = {colors[neighbor] for neighbor in adjacency[node] if colors[neighbor] != -1}
        for color in (0, 1, 2):
            if color in forbidden:
                continue
            colors[node] = color
            if backtrack(index + 1):
                return True
            colors[node] = -1
        return False

    if backtrack(0):
        return tuple(colors)
    return None


def edge_key_after_permutation(
    adjacency: tuple[tuple[int, ...], ...], permutation: tuple[int, ...]
) -> tuple[tuple[int, int], ...]:
    inverse = {old_index: new_index for new_index, old_index in enumerate(permutation)}
    edges = []
    for left, right in edges_from_adjacency(adjacency):
        new_left = inverse[left]
        new_right = inverse[right]
        edges.append((min(new_left, new_right), max(new_left, new_right)))
    return tuple(sorted(edges))


def adjacency_from_edge_key(n_nodes: int, edge_key: tuple[tuple[int, int], ...]) -> tuple[tuple[int, ...], ...]:
    adjacency_sets = [set() for _ in range(n_nodes)]
    for left, right in edge_key:
        adjacency_sets[left].add(right)
        adjacency_sets[right].add(left)
    return tuple(tuple(sorted(neighbors)) for neighbors in adjacency_sets)


def canonical_unrooted_key(
    adjacency: tuple[tuple[int, ...], ...], all_permutations: tuple[tuple[int, ...], ...]
) -> tuple[tuple[int, int], ...]:
    best: tuple[tuple[int, int], ...] | None = None
    for permutation in all_permutations:
        key = edge_key_after_permutation(adjacency, permutation)
        if best is None or key < best:
            best = key
    return best


def rooted_canonical_form(
    adjacency: tuple[tuple[int, ...], ...], root: int
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


def enumerate_rooted_graphs() -> list[RootedGraph]:
    rooted_records: list[RootedGraph] = []
    for n_nodes in N_RANGE:
        print(f"[scan] start enumerating n={n_nodes}")
        all_edges = list(combinations(range(n_nodes), 2))
        all_permutations = tuple(permutations(range(n_nodes)))
        graph_classes: dict[tuple[tuple[int, int], ...], tuple[tuple[int, ...], ...]] = {}
        total_masks = (1 << len(all_edges)) - 1
        progress_step = max(1, total_masks // 20)
        for mask in range(1, 1 << len(all_edges)):
            if mask == 1 or mask == total_masks or mask % progress_step == 0:
                print(f"[scan] n={n_nodes} mask={mask}/{total_masks}")
            adjacency_sets = [set() for _ in range(n_nodes)]
            for bit_index, (left, right) in enumerate(all_edges):
                if (mask >> bit_index) & 1:
                    adjacency_sets[left].add(right)
                    adjacency_sets[right].add(left)
            adjacency = tuple(tuple(sorted(neighbors)) for neighbors in adjacency_sets)
            if not connected(adjacency):
                continue
            if three_coloring(adjacency) is None:
                continue
            key = canonical_unrooted_key(adjacency, all_permutations)
            graph_classes.setdefault(key, adjacency)

        graph_index = 0
        for _, adjacency in sorted(graph_classes.items(), key=lambda item: item[0]):
            graph_index += 1
            graph_id = f"n{n_nodes}_g{graph_index:03d}"
            rooted_seen: set[tuple[tuple[int, int], ...]] = set()
            for target in range(n_nodes):
                rooted_key, rooted_adjacency = rooted_canonical_form(adjacency, target)
                if rooted_key in rooted_seen:
                    continue
                rooted_seen.add(rooted_key)
                colors = three_coloring(rooted_adjacency)
                assert colors is not None
                rooted_records.append(
                    RootedGraph(
                        graph_id=graph_id,
                        n_nodes=n_nodes,
                        adjacency=rooted_adjacency,
                        rooted_key=rooted_key,
                        preferred_colors=colors,
                    )
                )
        print(
            f"[scan] done n={n_nodes}: unique_unrooted={len(graph_classes)} "
            f"accumulated_rooted={len(rooted_records)}"
        )
    return rooted_records


def evidence_distribution(level: str, preferred_color: int) -> tuple[float, float, float]:
    strong, weak_left, weak_right = EVIDENCE_LEVELS[level]
    probabilities = [weak_left, weak_right, weak_right]
    probabilities[preferred_color] = strong
    return tuple(probabilities)


def valid_local_conflict_rule(
    adjacency: tuple[tuple[int, ...], ...], preferred_colors: tuple[int, ...]
) -> bool:
    # Updated TODO: only high/medium/low levels remain, so all nodes are constrained.
    for left, right in edges_from_adjacency(adjacency):
        if left == 0 or right == 0:
            continue
        if preferred_colors[left] == preferred_colors[right]:
            return False
    return True


def compute_condition_rows(rooted_graphs: list[RootedGraph]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    total_graphs = len(rooted_graphs)
    graph_step = max(1, total_graphs // 20)
    for graph_index, record in enumerate(rooted_graphs, start=1):
        if graph_index == 1 or graph_index == total_graphs or graph_index % graph_step == 0:
            print(f"[scan] condition progress graph={graph_index}/{total_graphs} current_rows={len(rows)}")
        non_target_nodes = [node for node in range(record.n_nodes) if node != 0]
        for level_template in product(EVIDENCE_LEVELS.keys(), repeat=len(non_target_nodes)):
            if not valid_local_conflict_rule(record.adjacency, record.preferred_colors):
                continue
            levels_by_node = {node: level for node, level in zip(non_target_nodes, level_template)}
            evidence = {
                node: evidence_distribution(levels_by_node[node], record.preferred_colors[node])
                for node in non_target_nodes
            }
            posteriors = {
                family: family_posterior(record.adjacency, 0, evidence, CANONICAL_FAMILIES[family])
                for family in FAMILY_ORDER
            }

            s_sep = 0.0
            for left_index, left_family in enumerate(FAMILY_ORDER):
                for right_family in FAMILY_ORDER[left_index + 1 :]:
                    s_sep += js_divergence(posteriors[left_family], posteriors[right_family])
            argmax_set = {max(range(3), key=lambda idx: posteriors[family][idx]) for family in FAMILY_ORDER}
            s_arg = float(len(argmax_set))

            uniform = (1 / 3, 1 / 3, 1 / 3)
            deltas = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
            b1 = sum(js_divergence(posteriors[family], uniform) for family in FAMILY_ORDER) / len(FAMILY_ORDER)
            b2 = (
                sum(min(js_divergence(posteriors[family], delta) for delta in deltas) for family in FAMILY_ORDER)
                / len(FAMILY_ORDER)
            )
            s_bal = math.sqrt(max(b1 * b2, 0.0))
            occupancy = tuple(level_template.count(level) for level in ("high", "medium", "low"))
            rows.append(
                {
                    "graph_id": record.graph_id,
                    "n_nodes": record.n_nodes,
                    "rooted_key": str(record.rooted_key),
                    "template_key": "|".join(level_template),
                    "occupancy_key": str(occupancy),
                    "s_sep": s_sep,
                    "s_arg": s_arg,
                    "s_bal": s_bal,
                    "family_posteriors": posteriors,
                    "adjacency": record.adjacency,
                }
            )

    s_sep_z = z_scores([float(row["s_sep"]) for row in rows])
    s_arg_z = z_scores([float(row["s_arg"]) for row in rows])
    s_bal_z = z_scores([float(row["s_bal"]) for row in rows])
    for index, row in enumerate(rows):
        row["s_sep_z"] = s_sep_z[index]
        row["s_arg_z"] = s_arg_z[index]
        row["s_bal_z"] = s_bal_z[index]
        row["w"] = s_sep_z[index] + 0.6 * s_arg_z[index] + 0.8 * s_bal_z[index]
    return rows


def select_top_k(rows: list[dict[str, object]], k: int) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    template_counts: dict[str, int] = {}
    occupancy_counts: dict[str, int] = {}
    graph_counts: dict[str, int] = {}
    remaining = set(range(len(rows)))
    while remaining and len(selected) < k:
        best_index = None
        best_score = None
        for index in remaining:
            row = rows[index]
            n_template = template_counts.get(str(row["template_key"]), 0)
            n_occupancy = occupancy_counts.get(str(row["occupancy_key"]), 0)
            n_graph = graph_counts.get(str(row["graph_id"]), 0)
            denominator = (
                (1 + DIVERSITY_WEIGHTS["template"] * n_template)
                * (1 + DIVERSITY_WEIGHTS["occupancy"] * n_occupancy)
                * (1 + DIVERSITY_WEIGHTS["graph"] * n_graph)
            )
            adjusted = float(row["w"]) / denominator
            if best_score is None or adjusted > best_score:
                best_score = adjusted
                best_index = index
        assert best_index is not None
        chosen = dict(rows[best_index])
        chosen["w_adj"] = best_score
        selected.append(chosen)
        template_counts[str(chosen["template_key"])] = template_counts.get(str(chosen["template_key"]), 0) + 1
        occupancy_counts[str(chosen["occupancy_key"])] = occupancy_counts.get(str(chosen["occupancy_key"]), 0) + 1
        graph_counts[str(chosen["graph_id"])] = graph_counts.get(str(chosen["graph_id"]), 0) + 1
        remaining.remove(best_index)
    return selected


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = [key for key in rows[0].keys() if key not in {"family_posteriors", "adjacency"}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})


def plot_top30_overview(path: Path, top_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots(figsize=(12, 4))
    x = list(range(1, len(top_rows) + 1))
    ax.plot(x, [row["w"] for row in top_rows], marker="o", label="W")
    ax.plot(x, [row["w_adj"] for row in top_rows], marker="s", label="W_adj")
    ax.set_xlabel("Selected rank")
    ax.set_ylabel("Score")
    ax.set_title("Top-30 weighted score and diversity-adjusted score")
    ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def plot_score_components(path: Path, rows: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    axes[0].hist([row["s_sep"] for row in rows], bins=30, color="#4575b4", alpha=0.85)
    axes[0].set_title("S_sep")
    axes[1].hist([row["s_arg"] for row in rows], bins=[0.5, 1.5, 2.5, 3.5], color="#1a9850", alpha=0.85)
    axes[1].set_title("S_arg")
    axes[2].hist([row["s_bal"] for row in rows], bins=30, color="#d73027", alpha=0.85)
    axes[2].set_title("S_bal")
    for ax in axes:
        ax.set_ylabel("Count")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def plot_family_heatmap(path: Path, top_rows: list[dict[str, object]]) -> None:
    matrix = [[0.0 for _ in FAMILY_ORDER] for _ in FAMILY_ORDER]
    for left_index, left_family in enumerate(FAMILY_ORDER):
        for right_index, right_family in enumerate(FAMILY_ORDER):
            values = [
                js_divergence(row["family_posteriors"][left_family], row["family_posteriors"][right_family])
                for row in top_rows
            ]
            matrix[left_index][right_index] = sum(values) / len(values)
    fig, ax = plt.subplots(figsize=(6.8, 5.6))
    image = ax.imshow(matrix, cmap="viridis")
    ax.set_xticks(range(len(FAMILY_ORDER)), FAMILY_ORDER, rotation=45, ha="right")
    ax.set_yticks(range(len(FAMILY_ORDER)), FAMILY_ORDER)
    ax.set_title("Mean JS divergence on top-30")
    for row_index, row in enumerate(matrix):
        for col_index, value in enumerate(row):
            ax.text(col_index, row_index, f"{value:.3f}", ha="center", va="center", fontsize=8, color="white")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def plot_top30_graphs(path: Path, top_rows: list[dict[str, object]]) -> None:
    cols = 6
    rows_count = 5
    fig, axes = plt.subplots(rows_count, cols, figsize=(14, 10))
    for idx, row in enumerate(top_rows[: cols * rows_count]):
        ax = axes[idx // cols][idx % cols]
        adjacency = row["adjacency"]
        n_nodes = len(adjacency)
        positions = {
            node: (math.cos(2 * math.pi * node / n_nodes), math.sin(2 * math.pi * node / n_nodes))
            for node in range(n_nodes)
        }
        for left, right in edges_from_adjacency(adjacency):
            ax.plot(
                [positions[left][0], positions[right][0]],
                [positions[left][1], positions[right][1]],
                color="#666666",
                linewidth=1.0,
            )
        for node in range(n_nodes):
            color = "#d73027" if node == 0 else "#f0f0f0"
            ax.scatter([positions[node][0]], [positions[node][1]], s=70, c=color, edgecolors="black", zorder=3)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{idx + 1}", fontsize=9)
        ax.set_aspect("equal")
    for idx in range(len(top_rows), cols * rows_count):
        axes[idx // cols][idx % cols].axis("off")
    fig.suptitle("Top-30 selected graph conditions (target node in red)", fontsize=12)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def run_pipeline(base_dir: Path) -> dict[str, object]:
    output_dir = base_dir / "output"
    figures_dir = output_dir / "figures"
    rooted_graphs = enumerate_rooted_graphs()
    all_rows = compute_condition_rows(rooted_graphs)
    top_rows = select_top_k(all_rows, TOP_K)
    top_rows = sorted(top_rows, key=lambda row: float(row["w_adj"]), reverse=True)

    write_csv(output_dir / "analysis-5_all_scored.csv", all_rows)
    write_csv(output_dir / "analysis-5_top30.csv", top_rows)
    summary = {
        "n_values": list(N_RANGE),
        "family_order": list(FAMILY_ORDER),
        "total_rooted_graphs": len(rooted_graphs),
        "total_conditions_after_filters": len(all_rows),
        "top_k": TOP_K,
        "diversity_weights": DIVERSITY_WEIGHTS,
        "n5_structures_expected": 17,
        "n6_structures_expected": 81,
        "candidate_space_formula_todo": "17*5*(4^4)+81*6*(5^4)=325510",
    }
    (output_dir / "analysis-5_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    plot_top30_overview(figures_dir / "fig_top30_overview.pdf", top_rows)
    plot_score_components(figures_dir / "fig_score_components.pdf", all_rows)
    plot_family_heatmap(figures_dir / "fig_family_separation_heatmap.pdf", top_rows)
    plot_top30_graphs(figures_dir / "fig_top30_graphs.pdf", top_rows)
    return summary


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    summary = run_pipeline(base_dir)
    print(f"Wrote {base_dir / 'output' / 'analysis-5_top30.csv'}")
    print(f"Wrote {base_dir / 'output' / 'analysis-5_all_scored.csv'}")
    print(f"Wrote {base_dir / 'output' / 'analysis-5_summary.json'}")
    print(f"Total conditions: {summary['total_conditions_after_filters']}")


if __name__ == "__main__":
    main()
