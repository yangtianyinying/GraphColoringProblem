# TODO-2: ρ-agent simulation study

## Output targets

This TODO produces:

| Output | Path |
|--------|------|
| Analysis script | `codes/analysis-2.py` |
| Simulation results | `codes/generated/analysis-2_simulation_results.json` |
| Figures | `Figures/analysis-2_*.pdf` (or `.png`) |
| Written report | `pre-analysis/analysis-2.tex` |

`pre-analysis/analysis-2.tex` should follow the same structure as `pre-analysis/analysis-1.tex`: a standalone compilable document with sections, figures, and tables documenting what was done and what was found.

---

## 0. Read first

Before starting, read:

- `proposal_1.tex` — scientific question overview
- `Definitions and Notation Guide.md` — all notation, especially §4 (ρ energy-decay implementation)
- `Design failures.md` — Failure 2 (why factor-scaling is not identifiable; always use energy-decay)
- `pre-analysis/analysis-1.tex` — the verified ρ implementation and minimal graph panel results
- `codes/research_plan_execution.py` — existing code for exact inference and ρ-spectrum

The key result already established: ρ must be implemented as **edge-energy decay**, not factor scaling. The formula is confirmed to produce a monotone, identifiable spectrum from independent (ρ=0) to exact (ρ=1).

---

## Scientific focus

**Ignore** question 3 (Min-Degree vs. Min-Fill; Phase 2 heuristics) entirely for this TODO.

Focus only on:

> **Q1.** Can the "structure utilisation" proposed in `research_plan.md` produce separable numerical predictions on a minimal graph set?
> **Q2.** Can independent → bounded approximate → globally exact inference be implemented as a computable continuous spectrum?

The answer to Q2 is already yes (verified in `research_plan_execution.tex`). The goal of this TODO is to turn that into a **complete simulation study**: enumerate a well-defined stimulus set, run all ρ-agents on it, and produce figures that show whether behaviour is distinguishable across ρ levels.

---

## 1. Fix the design logic

### 1.1 Target node placement

Place the target node **X at the centre** of every graph. All other nodes are soft-evidence nodes with known (but uncertain) colour distributions. This removes the need for a separate "evidence vs. latent" distinction: every non-target node is observed with some uncertainty, and the question is purely how far the ρ-agent integrates that evidence.

Formally: $E_\mathrm{obs} = V \setminus \{X\}$. Every non-target node $X_j$ has a unary factor $\phi_j(x_j) = \lambda_j(x_j)$ drawn from the evidence-strength set below.

### 1.2 Fix node count

Use **$|V| = 5$** (i.e. target $X$ plus 4 evidence nodes). This is small enough to enumerate all connected 3-colorable graphs exactly, and the exact marginals can be computed by brute force ($3^5 = 243$ configurations).

If the analysis reveals insufficient structural variety at $n=5$, extend to $n=6$ as a secondary condition.

### 1.3 Evidence assignment — an open design question for the agent

The three available evidence levels are:

| Label | $\lambda_j$ |
|-------|------------|
| High  | $(0.9, 0.05, 0.05)$ |
| Mid   | $(0.6, 0.2, 0.2)$ |
| Low   | $(0.4, 0.3, 0.3)$ |

**The choice of how to assign these to the non-target nodes is itself a design variable, and the agent must resolve it.** Two candidate strategies:

- **Uniform assignment**: all non-target nodes get the same level. Clean factorial design; easy to interpret. But neighbouring nodes may weakly constrain each other — potentially reducing ρ-separability.
- **Conflicting assignment**: nodes at different distances from $X$, or on different sides of $X$, get different (and potentially contradictory) colour tendencies. Conflict is expected to amplify the difference between a low-ρ agent (which integrates only the nearest evidence, missing the contradiction) and a high-ρ agent (which resolves the global constraint). This is likely the more powerful design.

**Optimisation criterion**: whichever assignment strategy maximises $\sum_{\rho_i < \rho_j} D_\mathrm{KL}(\tilde{b}_{\rho_i} \| \tilde{b}_{\rho_j})$ — the total pairwise separability across adjacent ρ levels — is the better design.

**What the agent should do**:
1. Implement both uniform and conflicting assignment.
2. For a representative sample of graphs, compute the separability criterion under both strategies.
3. Report which wins and by how much.
4. Use the winning strategy for all subsequent simulations. Document the decision and the numerical justification in `pre-analysis/rho_simulation.tex`.

The hypothesis (stated here so it can be checked) is that **conflicting evidence wins**, because the global resolution of a contradiction is precisely what a high-ρ agent can do and a low-ρ agent cannot.

### 1.4 Graph enumeration

Enumerate **all non-isomorphic connected graphs on 5 nodes** that are 3-colorable. (There are at most a few dozen; pre-compute and deduplicate by graph isomorphism.) This is the complete stimulus set — no random sampling needed.

For each graph, record:
- adjacency structure
- distance from each evidence node to $X$
- whether the graph is a tree (BP exact) or contains cycles (BP approximate)
- the exact marginal $P(X \mid E_\mathrm{obs})$ under each evidence-strength level

---

## 2. Implement the ρ-agent family

Build five agents at fixed ρ values:

| Agent | ρ | Description |
|-------|---|-------------|
| A0 | 0.00 | Fully independent (M₀) |
| A1 | 0.25 | Weakly bounded |
| A2 | 0.50 | Moderately bounded |
| A3 | 0.75 | Strongly bounded |
| A4 | 1.00 | Exact (VE-∞) |

Each agent computes $P_\rho(X \mid E_\mathrm{obs})$ using the energy-decay formula:

$$\psi^{(\rho)}_{uv}(x_u, x_v) = \exp\!\left[-\beta_\mathrm{edge}\,\rho^{s(u,v)}\,\mathbf{1}(x_u = x_v)\right]$$

where $s(u,v) = \min(d(X,u),\, d(X,v))$ is the shell index and $\beta_\mathrm{edge} = 4$ (use the value from `research_plan_execution.tex`).

Use **brute-force exact summation** over all $3^{|V|}$ colour assignments for each agent. Do not use BP or VE approximations inside the ρ-agent — the ρ parameter already controls the approximation, and exact summation of the modified model is exact.

---

## 3. Run the simulation

For each combination of (graph, evidence level, agent):
1. Compute $P_\rho(X = R)$, $P_\rho(X = G)$, $P_\rho(X = B)$.
2. Record the full predictive distribution $\tilde{b}_\rho$.
3. Compute $H(\tilde{b}_\rho)$ (response entropy).
4. Compute $D_\mathrm{KL}(\tilde{b}_\rho \,\|\, \tilde{b}_0)$ — divergence from the independent baseline.
5. Compute $D_\mathrm{KL}(\tilde{b}_\rho \,\|\, \tilde{b}_1)$ — divergence from the exact agent.

Store results in a long-format data frame: one row per (graph_id, evidence_level, agent_rho).

---

## 4. Figures

The LLM agent should propose the specific figure layouts. The following are **required figure types**; the agent should decide the exact visual form.

### Figure 1 — Separability panel

Show that the five ρ-agents produce distinct predictions. One natural approach: for each evidence-strength level, plot $P_\rho(X=R)$ as a function of ρ (x-axis: ρ ∈ {0, 0.25, 0.5, 0.75, 1}; y-axis: predicted $p_R$), with one curve per graph. The curves should spread out — the agent should check whether there is meaningful separation and flag any graphs where all curves collapse.

### Figure 2 — Entropy spectrum

Plot $H(\tilde{b}_\rho)$ as a function of ρ for each graph and evidence level. This visualises how quickly uncertainty decreases as the inference range expands.

### Figure 3 — KL divergence heat map or matrix

For each graph and evidence level, show $D_\mathrm{KL}(\tilde{b}_{\rho_i} \| \tilde{b}_{\rho_j})$ for all pairs of agents. This is a 5×5 matrix per graph. The goal is to identify which pairs of ρ levels are hardest to distinguish — this will inform power analysis for the human experiment.

### Figure 4 — "Equal-local, distinct-remote" demonstration

For the best pair of graphs that differ only in remote structure (chain vs. cycle, as in `research_plan_execution.tex`), show side-by-side predictions of all five agents under all three evidence levels. This is the minimal demonstration that ρ > 0 produces a different prediction from ρ = 0 even when the immediate neighbourhood is identical.

### Figure 5 (optional) — Individual graph geometry

For each graph in the enumerated set, draw the graph with $X$ at the centre, colour-code the evidence nodes by distance from $X$, and annotate with the exact $p_R$ value under the A4 (exact) agent. This is a reference panel, not a main result figure.

---

## 5. Deliverables

Produce:

1. `codes/rho_simulation.py` — all code for steps 1–3 (graph enumeration, agent computation, data frame generation).
2. `codes/generated/rho_simulation_results.json` — full results data frame.
3. `codes/rho_figures.py` — all figure code; save figures to `Figures/`.
4. A short LaTeX write-up `pre-analysis/rho_simulation.tex` documenting what was done and the key results. This does not need to be a full paper section — a few pages with the figures embedded is sufficient.

---

## 6. Success criteria

The simulation is successful if:

- At least 10 non-isomorphic graphs show meaningful separation ($D_\mathrm{KL}(\tilde{b}_0 \| \tilde{b}_1) > 0.01$ under high evidence) — confirming Q1.
- The ρ spectrum is monotone in $p_R$ and $H(\tilde{b}_\rho)$ for all graphs — confirming Q2.
- At least one "equal-local" graph pair exists at $n=5$ where $\tilde{b}_0^A = \tilde{b}_0^B$ but $\tilde{b}_1^A \neq \tilde{b}_1^B$ — confirming the H0/H1 discrimination logic.

If the $n=5$ graphs are insufficient (all separation measures below threshold), repeat with $n=6$ and document the minimum required graph size.

---

## 7. What not to do

- Do not implement Min-Degree or Min-Fill heuristics — that is Phase 2 / Q3, excluded from this TODO.
- Do not use loopy BP as the ρ-agent implementation — BP is a separate model ($M_\mathrm{BP}$), not an approximation of the ρ model.
- Do not fit to human data yet — this is a pure simulation study.
- Do not add more than 5 ρ levels unless the figures are unreadable; 5 is sufficient to show the spectrum.
