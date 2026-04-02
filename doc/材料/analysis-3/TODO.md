# TODO-3: rooted-shell 结构维度与 ρ-separability 的刺激设计分析

## Output targets

This TODO produces:

| Output | Path |
|--------|------|
| Analysis script | `codes/analysis-3.py` |
| Rooted motif catalog | `codes/analysis-3/analysis-3_rooted_motif_catalog.json` |
| Descriptor-level results | `codes/analysis-3/analysis-3_descriptor_results.{json,csv}` |
| Selected stimulus set | `codes/analysis-3/analysis-3_selected_stimuli.{json,csv}` |
| Figures | `Figures/analysis-3_*.pdf` |
| Written report | `pre-analysis/analysis-3.tex` |

`pre-analysis/analysis-3.tex` should follow the same general structure as `analysis-1.tex` and `analysis-2.tex`: standalone, compilable, with sections, figures, tables, and a conclusions section that states whether the success criteria below were met.

---

## 0. Read first

Before starting, read:

- `AGENTS.md` — current project rules and numbering convention
- `Definitions and Notation Guide.md` — all notation remains fixed
- `Design failures.md` — especially the warning against using the wrong design axis
- `TODOs/TODO-2.md` — previous active task and its scientific framing
- `pre-analysis/analysis-2.tex` — completed ρ-agent simulation study
- `codes/analysis-2/analysis-2_graph_catalog.json` — rooted graph catalog from analysis-2
- `codes/analysis-2/analysis-2_strategy_comparison.json` — evidence-strategy comparison
- `codes/generated/analysis-2_simulation_results.json` — full simulation output to be reused where appropriate

The key pivot established by analysis-2 is:

> **Node count is not the primary scientific design axis.**
> What matters for ρ-separability is the rooted structure around the target node X.

This TODO therefore treats graph size only as a minimal implementation detail, not as the explanatory variable of interest.

---

## Scientific focus

This TODO asks:

> **Which target-centred rooted structural dimensions determine whether the ρ-agent family is numerically distinguishable?**

The purpose is to translate the analysis-2 result into a more principled experimental design language: instead of saying “use 5-node graphs” or “use 6-node graphs”, we want to say “use stimuli with this rooted-shell structure”.

---

## 1. Design pivot

### 1.1 Do not organise the next analysis by node count

Do **not** treat `n = 5` versus `n = 6` as the main factor.

Use the smallest graph size necessary to instantiate a rooted motif, but organise all results and all figures around the three rooted dimensions below.

In other words:

- `n` is an implementation detail;
- rooted structure is the scientific variable.

### 1.2 The three primary design dimensions

This TODO fixes the experimental design language to the following **three** dimensions.

#### Dimension D1 — target degree

Let
\[
S_1 = N(X).
\]

The first design dimension is
\[
|S_1|,
\]
that is, the number of direct neighbours of the target node.

#### Dimension D2 — direct coupling among target neighbours

Let
\[
e_{11} = \text{number of edges within } S_1.
\]

This is the second design dimension: how strongly the target’s immediate neighbours constrain each other directly.

Do **not** reduce this to a yes/no variable if a count is available. The analysis may report a binary summary for exposition, but the stored descriptor must remain numeric.

#### Dimension D3 — remote structure beyond the immediate neighbourhood

The third design dimension is whether and how structure extends beyond the target’s immediate neighbours.

At the conceptual level this is the “neighbour-of-neighbour” dimension.

At the computational level, record at least:
\[
|S_2| = \text{number of distance-2 nodes from } X,
\qquad
 e_{12} = \text{number of edges between } S_1 \text{ and } S_2.
\]

Optional refinement: also store
\[
e_{22} = \text{number of edges within } S_2,
\]
if present.

**Important constraint:** the report and the stimulus taxonomy should still be presented as a **three-dimension** design (D1/D2/D3). The extra descriptors such as `e12` and `e22` are computational refinements inside D3, not a fourth main axis.

### 1.3 Fix the evidence strategy

Do **not** reopen the uniform-vs-conflicting evidence design question.

Analysis-2 already showed that the winning design is **adaptive conflicting evidence**. For TODO-3, treat that as fixed.

For each selected rooted stimulus, use the best evidence template implied by the adaptive conflicting strategy, and record it explicitly in the output files.

The report should treat this evidence pattern as part of the final stimulus construction, not as a separate competing model.

---

## 2. Enumerate the rooted motif family

Construct a rooted graph catalog over the smallest graph sizes needed to realise the relevant motifs.

### 2.1 Scope

Use the smallest graph size needed to instantiate each rooted structure, with `n = 5` and `n = 6` expected to be sufficient.

Do **not** split the report into a “5-node section” and a “6-node section” as if they were separate scientific conditions.

### 2.2 Deduplication rule

Deduplicate by **rooted isomorphism around the target node X**, not only by unrooted graph isomorphism.

For each rooted graph, record:

- adjacency structure
- rooted distances from X
- `|S1|`
- `e11`
- `|S2|`
- `e12`
- optional `e22`
- graph radius
- whether the graph is tree-like or contains cycles
- the adaptive conflicting evidence template selected for that rooted graph

### 2.3 Rooted motif taxonomy

Group graphs into descriptor classes defined by the three primary dimensions:

- D1: `|S1|`
- D2: `e11`
- D3: remote structure class

For D3, the agent should design the most interpretable coding scheme that preserves the raw descriptor values. One reasonable option is:

- D3-0: no remote structure (`|S2| = 0`)
- D3-1: remote structure present but weakly attached
- D3-2: remote structure present and strongly attached

If a different coding is better, the report must justify it numerically.

---

## 3. Compute rooted-structure separability

For every rooted graph in the catalog, run the same ρ-agent family as in analysis-2:

| Agent | ρ |
|-------|---|
| A0 | 0.00 |
| A1 | 0.25 |
| A2 | 0.50 |
| A3 | 0.75 |
| A4 | 1.00 |

Use the same hard constraints as before:

- energy-decay implementation only
- `β_edge = 4`
- brute-force exact summation only
- no BP approximation inside `M_ρ`

For each rooted graph and evidence level, record:

1. full predictive distribution `\tilde b_ρ`
2. `P_ρ(X=R)`, `P_ρ(X=G)`, `P_ρ(X=B)`
3. entropy `H(\tilde b_ρ)`
4. `D_KL(\tilde b_ρ \| \tilde b_0)`
5. `D_KL(\tilde b_ρ \| \tilde b_1)`
6. total pairwise separability `\sum_{ρ_i<ρ_j} D_KL(\tilde b_{ρ_i} \| \tilde b_{ρ_j})`
7. adjacent-ρ separability `\sum_i D_KL(\tilde b_{ρ_i} \| \tilde b_{ρ_{i+1}})`

The goal is no longer merely “which graph separates”, but “which rooted descriptors explain why separation happens”.

---

## 4. Build matched comparisons by rooted dimensions

This is the central design task of TODO-3.

Construct matched graph sets that vary **one** rooted dimension at a time while holding the others fixed as closely as possible.

### 4.1 D1 matched comparison — target degree effect

Find graph sets where:

- D2 is matched (same or nearest possible `e11` pattern)
- D3 is matched (same remote structure class)
- D1 differs (`|S1|` changes)

Goal: ask whether increasing the target’s immediate branching changes ρ-separability.

### 4.2 D2 matched comparison — neighbour-neighbour coupling effect

Find graph sets where:

- D1 is fixed
- D3 is fixed
- D2 differs (`e11` changes)

Goal: isolate the effect of local closure among target neighbours.

### 4.3 D3 matched comparison — remote structure effect

Find graph sets where:

- D1 is fixed
- D2 is fixed
- D3 differs (`|S2|` and/or `e12` changes)

This is the most theoretically important comparison, because it directly generalises the “equal-local, distinct-remote” logic from analysis-1 and analysis-2.

If an exact match is impossible at the smallest available graph size, extend only as far as necessary to realise the match, and document that explicitly.

---

## 5. Stimulus selection for the future experiment

The output of TODO-3 should not just be a catalog; it should produce a **candidate stimulus set** for the experiment.

For each selected stimulus candidate, record:

- rooted descriptor class
- graph topology
- evidence template chosen by adaptive conflicting evidence
- high / medium / low evidence versions
- high-evidence `D_KL(\tilde b_0 \| \tilde b_1)`
- whether the ρ-spectrum is monotone
- whether the graph belongs to a matched comparison set for D1, D2, or D3

The selected stimulus set should prefer:

- graphs with strong separability
- graphs belonging to matched comparison families
- graphs that are easy to explain visually in a participant-facing task

---

## 6. Required figures

This TODO must contain a substantial visual design component. Use TikZ for the structure figures.

### Figure 1 — Three-dimension design schematic (TikZ)

Draw a clean conceptual schematic showing the three experimental dimensions:

- D1: target degree
- D2: neighbour-neighbour direct coupling
- D3: remote structure beyond the first shell

This figure should be a design map, not a numerical result plot.

### Figure 2 — Rooted stimulus type gallery (TikZ)

Create a panel of example rooted motifs, grouped by descriptor class.

Each example should display:

- target node X at the centre
- shell-1 and shell-2 structure visually separated
- a short type label (e.g. stimulus family / motif type)
- the rooted descriptor values

### Figure 3 — Matched comparison panels (TikZ + numerical labels)

For each of D1, D2, and D3, create at least one matched comparison panel where only that dimension changes.

This figure should make it visually obvious how the stimulus manipulation is defined.

### Figure 4 — Selected separable stimulus set with best evidence labels (TikZ)

For the final selected stimuli, draw the graph and annotate the nodes with the winning adaptive-conflicting evidence template.

At minimum, each node should indicate its preferred colour label (`R/G/B`) under the selected evidence assignment. If useful, also annotate the evidence strength condition in the caption or a corner label.

This figure is meant as a direct bridge to future experiment implementation.

### Figure 5 — Descriptor-level separability plot

Use matplotlib/seaborn to show how separability varies across the rooted descriptor classes.

Examples:

- dot plots or box plots of `D_KL(\tilde b_0 \| \tilde b_1)` by descriptor class
- matched-set line plots across D1 / D2 / D3 manipulations
- additive summary plots for the selected motif family

---

## 7. Deliverables

Produce:

1. `codes/analysis-3.py`
2. `codes/analysis-3/analysis-3_rooted_motif_catalog.json`
3. `codes/analysis-3/analysis-3_descriptor_results.json`
4. `codes/analysis-3/analysis-3_descriptor_results.csv`
5. `codes/analysis-3/analysis-3_selected_stimuli.json`
6. `codes/analysis-3/analysis-3_selected_stimuli.csv`
7. `Figures/analysis-3_*.pdf`
8. `pre-analysis/analysis-3.tex`

---

## 8. Success criteria

TODO-3 is successful if all of the following are achieved:

### S1 — Descriptor framing beats node-count framing

The report must show clearly that rooted descriptor classes explain separability more meaningfully than raw node count.

It is acceptable to demonstrate this qualitatively or quantitatively, but the report must make the point explicit.

### S2 — At least one matched comparison for each of D1 / D2 / D3

There must be at least one numerically useful matched comparison set for:

- D1 (target degree)
- D2 (neighbour-neighbour coupling)
- D3 (remote structure)

“Numerically useful” means the manipulation produces a visible change in separability or in the ρ-spectrum.

### S3 — A rooted stimulus taxonomy is produced

The report must end with a practical stimulus taxonomy suitable for later experimental design.

That taxonomy must be organised by rooted descriptor class, not by node count.

### S4 — Visual stimulus sketches are ready

The TikZ figures must make it possible to understand what the candidate experimental stimuli actually look like.

In particular, the selected separable stimuli must be shown together with their best evidence template.

---

## 9. What not to do

- Do not organise the analysis primarily by `n=5` versus `n=6`
- Do not reopen the evidence-strategy comparison as the main scientific question
- Do not use BP as an approximation to `M_ρ`
- Do not fit human data yet
- Do not collapse D2 or D3 to yes/no variables if a count-based descriptor is available
- Do not produce only numerical tables without TikZ stimulus sketches
- Do not forget to label the final selected stimuli with the winning evidence template

