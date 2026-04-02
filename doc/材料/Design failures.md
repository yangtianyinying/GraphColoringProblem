# Design Failures and Pivots

> This document records the design problems identified in the current CSP project, organised as a diagnostic log. It is updated whenever a new problem is found or resolved. Use it as a checklist before building new stimuli, writing new code, or extending the analysis.

---

## Core verdict

The current design has five interrelated failure modes, all diagnosed in `TODOs/research_plan.md`. They share a common root: **the experimental paradigm, the theoretical model, and the stimulus library were designed in partial isolation and have not yet been unified into a coherent pipeline**.

The pivot required is not a change in the scientific question (the three-level hierarchy in `科学问题.pdf` is sound) but a systematic alignment of:
1. the **paradigm** (what participants do),
2. the **model** (how behaviour is formalised),
3. the **stimuli** (what graphs are used and why), and
4. the **analysis** (how individual and group inference are performed).

---

## Failure 1: Paradigm–model mismatch

### What the model assumed

The VE agent in `Methods.tex` assumes **fixed elimination order, one-pass, non-revisable** sequential probability reports. The fill-in sequence $\{\mathrm{Fill}_t\}$ and the clique sequence $\{\Omega_t\}$ are only well-defined for a fixed elimination ordering.

### What the experiment actually had

The experiment design PPT showed a **free-exploration interface** where participants can (a) choose which node to query in any order, and (b) **revise earlier responses**. This breaks the Markov structure that the VE model depends on. The fill sequence is no longer interpretable, and the response model cannot be fitted.

### Resolution

Phase 1 must use **fixed ordering, non-revisable reports**. The "can revise" feature must be removed from the interface. Phase 2 (free-query) is permitted to have free ordering but **not** response revision; once a node is reported, the report is final.

---

## Failure 2: No continuous approximation parameter

### What the model space looked like

The original model set was binary: exact inference (global VE / exact BP) vs. heuristic search (CSP solver, SA, Min-conflicts). This is a yes/no question about structure use.

### Why it is wrong

The central scientific question — **by how much do humans approximate** global probabilistic inference — requires a continuous spectrum, not a binary contrast. Wu et al. (2021) demonstrated exactly this using a GP diffusion parameter α; the present project needs an equivalent.

### Resolution

Introduce the bounded VE model $M_\rho$ with diffusion parameter $\rho \in [0, 1]$. The model set becomes $\{M_0, M_\rho, M_\mathrm{exact}, M_\mathrm{BP}\}$. See `Definitions and Notation Guide.md` §4 for the energy-decay implementation (the factor-scaling version is **not** identifiable and must not be used).

---

## Failure 3: Graphs too small (5 nodes)

### The symptom

On 5-node graphs, Min-Degree and Min-Fill produce different orderings in only 6% of cases and **never produce different total fill counts**. Stimuli designed on 5-node graphs cannot support Phase 2 (heuristic comparison).

### The deeper problem

5-node graphs also limit the distance between evidence and target nodes, reducing the range over which the ρ spectrum is distinguishable. The structural separation between the equal-local graph pairs is also smaller.

### Resolution

Use 6–8 node graphs. Numerical analysis (`research_plan_execution.tex`) confirms:
- 4-node minimum graphs are sufficient for the H0/H1 minimal demonstration.
- 6-node graphs begin to separate Min-Degree and Min-Fill in 17.6% of cases.
- 8-node graphs provide robust separation and the strongest Phase 1 structural signal.

Stimuli must be **pre-screened** using the script `codes/research_plan_execution.py` before being entered into the experiment. The current stimulus library is in `codes/generated/research_plan_stimulus_library.json`.

---

## Failure 4: Phase 1 and Phase 2 data not jointly modelled

### The symptom

Phase 1 (forced-query) and Phase 2 (free-query) are designed as separate tasks with no shared parameter space at the individual level. There is no way to ask whether a participant who fits a high-ρ model in Phase 1 also shows a Min-Fill heuristic in Phase 2.

### The scientific cost

The cross-phase prediction is one of the most theoretically interesting aspects of the design: deeper graph exploitation in belief computation (high $\hat{\rho}$) should predict deeper look-ahead in heuristic selection (Min-Fill preference). Without a joint individual-level fit, this cannot be tested.

### Resolution

Fit Phase 1 and Phase 2 separately but record both sets of individual parameter estimates $(\hat{\rho}, \hat{\beta}_\mathrm{heur})$ per participant. The cross-phase analysis is then a between-estimate correlation (scatterplot + regression), not a joint model. This is sufficient for a correlational test and is analogous to the individual-difference analysis in Wu et al. (2021).

---

## Failure 5: Scoring rule and training absent

### The symptom

The experiment PPT had no calibration training for probability wheel responses and no scoring rule. Participants had no incentive to report calibrated probability distributions; they may have collapsed to point estimates.

### The scientific cost

The Dirichlet response model assumes well-calibrated distributional responses. If participants treat the colour wheel as a point estimate (e.g., always dragging to a corner), the Dirichlet concentration κ will be inflated and model fit will be poor.

### Resolution

Add to the experiment:
1. A probability wheel **training block** (≥10 practice trials) demonstrating the difference between uncertain and certain distributions.
2. A **log scoring rule** incentive: participants are told their bonus depends on the accuracy of the full probability distribution, not just the modal colour.
3. A **comprehension check** after training before the main experiment begins.

---

## Cross-failure lessons

The five failures share a pattern: **each component was designed in isolation**. The paradigm was designed by an experimenter thinking about task flow; the model was built by a modeller thinking about VE; the stimuli were chosen without systematic pre-screening. The research plan unifies these three components.

Do not:
- Change the paradigm without re-checking the model's identifiability.
- Add new stimuli without running them through the pre-screening pipeline.
- Interpret Phase 2 heuristic results without confirming that Phase 1 ρ estimates are reliable.
- Treat the H0/H1 comparison as sufficient evidence on its own — the ρ distribution is the main result.

---

## Status

| Failure | Status | Notes |
|---------|--------|-------|
| 1. Paradigm–model mismatch | **Resolved in plan** | Remove response revision; use fixed-order Phase 1 |
| 2. No continuous ρ parameter | **Resolved in plan** | Energy-decay $M_\rho$ implemented and verified (`research_plan_execution.tex`) |
| 3. Graphs too small | **Resolved in plan** | 6–8 node library pre-screened; library in `codes/generated/` |
| 4. Phase 1–2 not jointly modelled | **Resolved in plan** | Correlation-based cross-phase analysis; no joint likelihood required |
| 5. Scoring rule absent | **Not yet implemented** | Needs task interface update and training block |
