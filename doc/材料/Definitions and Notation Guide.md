# Definitions and Notation Guide

> Revision note
> - Written from scratch for the CSP project based on `research_plan.md`, `research_plan_execution.tex`, `research_plan_screening_recovery.tex`, and the manuscript source.
> - Centres on factor-graph probabilistic inference, the continuous approximation parameter ρ, and the two-phase experimental design.
> - Open choices: the precise parameterisation of the continuous ρ spectrum (energy-decay vs. factor-scaling); the scoring rule for participant responses (log vs. quadratic); the minimum node count for Phase 2 stimuli (currently 6–8).

---

## Purpose

Use this guide only for concepts and symbols that appear in the current proposal and analysis plan. Do not import notation from unrelated frameworks.

---

## 1. Core distinctions

- **Factor graph**: a bipartite graph with variable nodes ($X_i$) and factor nodes ($f_j$), where each factor connects to the variables in its scope.
- **Exact inference / VE-∞**: computing the true marginal $P(X_i \mid E_\mathrm{obs})$ by variable elimination or exact message passing — possible only for small or tree-structured graphs.
- **Independent inference / M0**: treating each unobserved variable as independent given only its directly observed neighbours; ignores all latent relay paths.
- **Bounded approximate inference / VE-k**: integrating out only the $k$-hop neighbourhood of the target node; a continuous spectrum between M0 and VE-∞ controlled by the diffusion parameter ρ.
- **Loopy belief propagation / BP**: running sum-product message passing on the original pairwise graph; exact on trees, approximate on graphs with cycles.
- **Fill-in**: edges added to the residual graph when a variable is eliminated during VE; the fill-in count at step $t$ is $\mathrm{Fill}_t$.
- **Induced clique size / Ω**: the size of the clique formed when a variable is eliminated; $\Omega_t = |N_t(v_t)| + 1$. Tracks peak intermediate memory in VE.
- **Phase 1 (forced-query)**: fixed node ordering, one-pass, non-revisable sequential probability reports; the standard paradigm for fitting VE models.
- **Phase 2 (free-query)**: participant chooses which node to query next; used to test heuristic strategy (Min-Degree vs. Min-Fill).

---

## 2. Graph and factor notation

$$G = (V, E), \quad |V| \in \{6, 7, 8\}$$

- $X_i \in V$: variable node (map colouring colour $\in$ {R, G, B})
- $E_\mathrm{obs} \subseteq V$: observed (evidence) nodes
- $X_t \in V \setminus E_\mathrm{obs}$: target node at query step $t$
- $\psi_{ij}(x_i, x_j) = \exp\!\left[-\beta_\mathrm{edge}\,\mathbf{1}(x_i = x_j)\right]$: soft inequality factor
- $\phi_i(x_i) = \lambda_e(x_i)$: unary evidence factor at observed node $e$
- $d_G(i,j)$: shortest path distance in the factor graph between nodes $i$ and $j$

---

## 3. Models

$$\mathcal{M} = \{M_0,\; M_\rho,\; M_\mathrm{exact},\; M_\mathrm{BP}\}$$

| Model | Description | Free parameters |
|-------|-------------|-----------------|
| $M_0$ | Independent: only direct observed neighbours | $\beta_\mathrm{edge},\, \kappa$ |
| $M_\rho$ | Bounded VE with energy decay | $\rho,\, \beta_\mathrm{edge},\, \beta_\mathrm{resp},\, \kappa$ |
| $M_\mathrm{exact}$ | Full variable elimination (VE-∞) | $\beta_\mathrm{edge},\, \beta_\mathrm{resp},\, \kappa$ |
| $M_\mathrm{BP}$ | Loopy sum-product belief propagation | $\beta_\mathrm{edge},\, T_\mathrm{bp},\, \alpha_\mathrm{damp},\, \kappa$ |

---

## 4. The diffusion parameter ρ

The core continuous parameter, directly analogous to Wu et al.'s (2021) diffusion α.

**Energy-decay implementation** (identifiable form; use this, not factor-scaling):

$$\psi^{(\rho,i)}_{uv}(x_u, x_v) = \exp\!\left[-\beta_\mathrm{edge}\,\rho^{s_i(u,v)}\,\mathbf{1}(x_u = x_v)\right]$$

where $s_i(u,v) = \min(d(i,u),\, d(i,v))$ is the shell distance from the target node $i$.

| ρ value | Behaviour |
|---------|-----------|
| $\rho = 0$ | Independent inference ($M_0$): only shell-0 edges retained |
| $0 < \rho < 1$ | Bounded approximate inference; remote factors down-weighted |
| $\rho = 1$ | Exact inference ($M_\mathrm{exact}$): full factor graph restored |

**Critical note**: Multiplying an entire factor by a distance-dependent constant is not identifiable (normalisation cancels it). Always apply decay to the **edge energy** $\beta_\mathrm{edge}$, not to the factor itself.

---

## 5. Complexity measures

Defined at elimination step $t$ when node $v_t$ is eliminated from the residual graph $G_t$:

$$\mathrm{Fill}_t = \left|\{(a,b) : a, b \in N_t(v_t),\, a \neq b,\, (a,b) \notin E_t\}\right|$$

$$\Omega_t = |N_t(v_t)| + 1$$

- $\mathrm{Fill}_t$: number of new edges added to the residual graph (intermediate complexity cost).
- $\Omega_t$: clique size at elimination (memory cost; proportional to the table size in bucket elimination).
- These are the operationalisation of **VE complexity** and map onto RT, response entropy, and KL divergence in the three predictions.

---

## 6. Stimulus design

**"Equal-local, distinct-remote" (局部等价图对)** for H0 vs. H1 test:

- Graph A and Graph B share the same local neighbourhood structure around the target $X_t$ (same $d_G(E_\mathrm{obs}, X_t)$ and same immediate neighbour structure).
- But their global topology differs (e.g., chain vs. cycle).
- $M_0$ predicts equal responses on both; $M_\mathrm{exact}$ predicts systematically different responses.

**Evidence strength** — three levels of the evidence factor $\lambda_e$:

| Strength | $\lambda_e$ |
|----------|------------|
| High | $(0.9, 0.05, 0.05)$ |
| Medium | $(0.6, 0.2, 0.2)$ |
| Low | $(0.4, 0.3, 0.3)$ |

---

## 7. Response model

Participant response $y_t \in \Delta^2$ (a 3-colour probability vector) is modelled as:

$$y_t \sim \mathrm{Dirichlet}\!\left(\kappa \cdot \tilde{b}_t(\Theta)\right)$$

where $\tilde{b}_t$ is the model posterior softened at response temperature $\beta_\mathrm{resp}$, and $\kappa$ is the Dirichlet concentration.

---

## 8. Inference and model comparison

**Individual-level fitting**: leave-one-trial-out cross-validation, maximising:

$$\mathcal{L}(\Theta; \mathbf{y}) = \sum_t \log p_\mathrm{Dirichlet}(y_t;\, \kappa \cdot \tilde{b}_t(\Theta))$$

**Group-level model comparison**: protected exceedance probability (pxp; Rigoux et al., 2014) over per-subject BIC values — identical to Wu et al. (2021) Fig. 3d.

**Predicted group-level finding** (analogous to Wu et al.'s undergeneralization):

$$\hat{\rho} < 1 \quad \text{(bounded, not globally exact)}$$

---

## 9. Phase 2 heuristics (free-query)

At each step $t$, participant chooses next node $X_i$ from the unqueried set $F_t$. Three heuristic strategies:

- **Min-Degree**: choose $\arg\min_{X_i \in F_t} \deg_{G_t}(X_i)$
- **Min-Fill**: choose $\arg\min_{X_i \in F_t} \mathrm{Fill}(X_i \mid G_t)$ (one-step look-ahead)
- **Random**: uniform selection

Fitted via softmax with inverse temperature $\beta_\mathrm{heur}$.

---

## 10. Summary table

| Symbol | Meaning |
|--------|---------|
| $G = (V,E)$ | factor graph |
| $X_i$ | variable node (colour) |
| $E_\mathrm{obs}$ | observed nodes |
| $X_t$ | target node at step $t$ |
| $\psi_{ij}$ | pairwise factor (inequality constraint) |
| $\lambda_e$ | evidence strength |
| $\rho$ | diffusion parameter (inference range, 0–1) |
| $\beta_\mathrm{edge}$ | edge constraint strength |
| $\beta_\mathrm{resp}$ | response temperature |
| $\kappa$ | Dirichlet concentration |
| $\mathrm{Fill}_t$ | fill-in count at VE step $t$ |
| $\Omega_t$ | induced clique size at VE step $t$ |
| $M_0$ | independent inference model |
| $M_\rho$ | bounded VE model |
| $M_\mathrm{exact}$ | full VE (exact) model |
| $M_\mathrm{BP}$ | loopy belief propagation model |
| $y_t$ | participant response (3D probability vector) |
| $\tilde{b}_t$ | model posterior prediction |
| pxp | protected exceedance probability |

---

## 11. One-sentence thesis

The project asks whether human belief propagation over factor graphs is globally exact or bounded/approximate, and if approximate, what continuous parameter ρ characterises the effective range of inference — with the prediction, by analogy with Wu et al.'s undergeneralization finding, that $\hat{\rho} < 1$ systematically.
