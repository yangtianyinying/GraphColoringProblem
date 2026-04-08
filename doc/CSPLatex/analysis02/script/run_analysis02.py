from __future__ import annotations

import ast
import csv
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt


if __package__ is None or __package__ == "":
    base_dir = Path(__file__).resolve().parents[1]
    analysis01_dir = base_dir.parent / "analysis01"
    if str(analysis01_dir) not in sys.path:
        sys.path.insert(0, str(analysis01_dir))

from agent.models import CANONICAL_FAMILIES, FAMILY_ORDER, family_posterior

EVIDENCE_LEVELS = {
    "high": (0.9, 0.05, 0.05),
    "medium": (0.7, 0.15, 0.15),
    "low": (0.5, 0.25, 0.25),
}
EPSILON = 1e-12


@dataclass(frozen=True)
class TrialRecord:
    graph_id: str
    n_nodes: int
    adjacency: tuple[tuple[int, ...], ...]
    template_levels: tuple[str, ...]
    posteriors: dict[str, tuple[float, float, float]]


def edges_to_adjacency(n_nodes: int, edge_key: tuple[tuple[int, int], ...]) -> tuple[tuple[int, ...], ...]:
    adjacency_sets = [set() for _ in range(n_nodes)]
    for left, right in edge_key:
        adjacency_sets[left].add(right)
        adjacency_sets[right].add(left)
    return tuple(tuple(sorted(neighbors)) for neighbors in adjacency_sets)


def three_coloring(adjacency: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
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

    if not backtrack(0):
        raise ValueError("Graph is not 3-colorable, cannot build evidence template.")
    return tuple(colors)


def evidence_distribution(level: str, preferred_color: int) -> tuple[float, float, float]:
    strong, weak_left, weak_right = EVIDENCE_LEVELS[level]
    probs = [weak_left, weak_right, weak_right]
    probs[preferred_color] = strong
    return tuple(probs)


def load_top30_trials(csv_path: Path) -> list[TrialRecord]:
    trials: list[TrialRecord] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            n_nodes = int(row["n_nodes"])
            edge_key = ast.literal_eval(row["rooted_key"])
            adjacency = edges_to_adjacency(n_nodes, edge_key)
            preferred_colors = three_coloring(adjacency)
            levels = tuple(str(row["template_key"]).split("|"))
            non_target_nodes = [node for node in range(n_nodes) if node != 0]
            if len(non_target_nodes) != len(levels):
                raise ValueError("template_key length does not match non-target node count.")
            evidence = {
                node: evidence_distribution(level, preferred_colors[node])
                for node, level in zip(non_target_nodes, levels)
            }
            posteriors = {
                family: family_posterior(adjacency, 0, evidence, CANONICAL_FAMILIES[family])
                for family in FAMILY_ORDER
            }
            trials.append(
                TrialRecord(
                    graph_id=row["graph_id"],
                    n_nodes=n_nodes,
                    adjacency=adjacency,
                    template_levels=levels,
                    posteriors=posteriors,
                )
            )
    return trials


def sample_color(rng: random.Random, probs: tuple[float, float, float]) -> int:
    pivot = rng.random()
    cum = 0.0
    for idx, value in enumerate(probs):
        cum += value
        if pivot <= cum:
            return idx
    return 2


def compute_log_likelihood(trials: list[TrialRecord], responses: list[int], fit_family: str) -> float:
    total = 0.0
    for trial, response in zip(trials, responses):
        total += math.log(max(trial.posteriors[fit_family][response], EPSILON))
    return total


def run_categorical_confusion(
    trials: list[TrialRecord], repeats_per_family: int = 200, seed: int = 20260408
) -> dict[str, object]:
    rng = random.Random(seed)
    counts = [[0 for _ in FAMILY_ORDER] for _ in FAMILY_ORDER]
    all_gaps: list[float] = []

    for true_idx, true_family in enumerate(FAMILY_ORDER):
        for _ in range(repeats_per_family):
            responses = [sample_color(rng, trial.posteriors[true_family]) for trial in trials]
            scores = [
                (fit_family, compute_log_likelihood(trials, responses, fit_family))
                for fit_family in FAMILY_ORDER
            ]
            scores.sort(key=lambda item: item[1], reverse=True)
            best_family, best_ll = scores[0]
            second_ll = scores[1][1]
            all_gaps.append(best_ll - second_ll)
            fit_idx = FAMILY_ORDER.index(best_family)
            counts[true_idx][fit_idx] += 1

    confusion = [[count / repeats_per_family for count in row] for row in counts]
    diagonal_mean = sum(confusion[i][i] for i in range(len(FAMILY_ORDER))) / len(FAMILY_ORDER)
    mean_gap = sum(all_gaps) / len(all_gaps) if all_gaps else 0.0

    return {
        "family_order": list(FAMILY_ORDER),
        "n_trials": len(trials),
        "n_repeats_per_true_family": repeats_per_family,
        "seed": seed,
        "confusion_matrix": confusion,
        "diagonal_mean": diagonal_mean,
        "mean_log_likelihood_gap": mean_gap,
    }


def write_confusion_csv(path: Path, family_order: list[str], matrix: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["true_family", *family_order])
        for family, row in zip(family_order, matrix):
            writer.writerow([family, *[f"{value:.6f}" for value in row]])


def plot_confusion_heatmap(path: Path, family_order: list[str], matrix: list[list[float]]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    image = ax.imshow(matrix, cmap="YlGnBu", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(family_order)), family_order, rotation=30, ha="right")
    ax.set_yticks(range(len(family_order)), family_order)
    ax.set_xlabel("Fitted family")
    ax.set_ylabel("True family")
    ax.set_title("Categorical fitting confusion matrix (heterogeneous top-30)")
    for row_idx, row in enumerate(matrix):
        for col_idx, value in enumerate(row):
            color = "black" if value < 0.6 else "white"
            ax.text(col_idx, row_idx, f"{value:.3f}", ha="center", va="center", fontsize=9, color=color)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def plot_diagonal_bars(path: Path, family_order: list[str], matrix: list[list[float]]) -> None:
    diagonal = [matrix[i][i] for i in range(len(family_order))]
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    ax.bar(family_order, diagonal, color="#2a9d8f")
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Correct identification rate")
    ax.set_title("Diagonal entries by true family")
    for idx, value in enumerate(diagonal):
        ax.text(idx, value + 0.02, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def run(base_dir: Path) -> dict[str, object]:
    top30_csv = base_dir.parent / "analysis01" / "output" / "analysis-5_top30.csv"
    output_dir = base_dir / "output"
    figures_dir = output_dir / "figures"

    trials = load_top30_trials(top30_csv)
    result = run_categorical_confusion(trials=trials, repeats_per_family=200, seed=20260408)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "analysis02_categorical_confusion.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_confusion_csv(
        output_dir / "analysis02_categorical_confusion_matrix.csv",
        result["family_order"],
        result["confusion_matrix"],
    )
    plot_confusion_heatmap(
        figures_dir / "fig_analysis02_confusion_heatmap.png",
        result["family_order"],
        result["confusion_matrix"],
    )
    plot_diagonal_bars(
        figures_dir / "fig_analysis02_diagonal_bars.png",
        result["family_order"],
        result["confusion_matrix"],
    )
    return result


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    result = run(base_dir)
    print("analysis02 done")
    print(f"n_trials={result['n_trials']}")
    print(f"diagonal_mean={result['diagonal_mean']:.6f}")
    print(f"mean_log_likelihood_gap={result['mean_log_likelihood_gap']:.6f}")


if __name__ == "__main__":
    main()
