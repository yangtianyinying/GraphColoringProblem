# Core References

## Tier 1 — Core

### Wu et al. (2021)
**Citation:** Wu, C. M., Schulz, E., Speekenbrink, M., Nelson, J. D., & Meder, B. (2021). *Inference and Search on Graph-Structured Spaces*. **Computational Brain & Behavior, 4**, 125–147. https://doi.org/10.1007/s42113-021-00100-7
**Contribution:** Models human function learning on graphs using a Gaussian Process with a diffusion kernel. The diffusion parameter α continuously controls how far information propagates along graph edges — from α→0 (local/independent) to α→∞ (global). Key finding: fitted α values are systematically below the true generative value (undergeneralization), showing humans exploit graph structure but only partially.
**Why central:** This paper provides the direct methodological template for the present project. Our factor-graph diffusion parameter ρ is the direct analogue of their α, and our model comparison strategy (leave-one-trial-out CV + protected exceedance probability) mirrors their analysis pipeline exactly.
**Tags:** graph-structured inference, Gaussian process, diffusion kernel, model comparison, approximate inference

### Mézard & Montanari (2009) / Mézard (2008)
**Citation:** Mézard, M. (2008). *Constraint satisfaction problems and neural networks: a statistical physics perspective*. **arXiv**. [PDF in this folder]
**Contribution:** Reviews the statistical physics perspective on constraint satisfaction problems, including factor graphs, belief propagation, and the relationship between CSP hardness and inference complexity. Introduces the cavity method and replica framework.
**Why central:** Provides the theoretical backbone for why factor graph inference is computationally hard (NP-complete in general), motivating the hypothesis that humans use bounded/approximate inference rather than exact marginalization.
**Tags:** constraint satisfaction, factor graphs, belief propagation, statistical physics, complexity

---

## Tier 2 — Methods textbooks

### Barber (2012) — BRML
**Location:** `Method-textbooks/BRML-ch2-3.pdf`, `BRML-ch5.pdf`, `BRML-ch6.pdf`
**Contribution:** Chapters 2–3 cover graphical models and factor graphs; Chapter 5 covers belief propagation and the sum-product algorithm; Chapter 6 covers the junction tree algorithm and exact inference. These are the primary technical references for the VE agent and BP agent implementations.
**Key results used:** Ch.5: sum-product message passing on pairwise graphs; exact on trees, approximate on loopy graphs. Ch.6: variable elimination, fill-in edges, induced cliques — the source of the Fill$_t$ and $\Omega_t$ complexity measures.

---

## Tier 3 — To be added

> *Suggested additions as the project develops:*
> - Rigoux et al. (2014) — protected exceedance probability (pxp) — needed for group model comparison
> - Yedidia, Freeman & Weiss (2005) — loopy BP convergence — for M_BP specification
> - Working memory and cognitive capacity literature (for the ρ–WM correlation prediction)
> - Dirichlet likelihood / probability reporting methodology (for response model justification)

---

## Key methodological mappings

| Wu et al. (2021) | Present project |
|---|---|
| Function values on graph nodes | Color probability beliefs on factor graph nodes |
| GP diffusion parameter α (information spread) | Bounded VE diffusion parameter ρ (inference range) |
| GP vs dNN vs kNN model comparison | VE-∞ vs VE-k vs M0 (independent) comparison |
| Leave-one-round-out CV + pxp | Leave-one-trial-out CV + pxp |
| Undergeneralization (α̂ < α_true) | Predicted: ρ̂ < 1 (approximate, not globally exact) |
| Confidence ~ GP uncertainty | Response entropy ~ Fill_t, Ω_t |
| Individual α (individual differences) | Individual ρ (factor graph exploitation depth) |

---

## One-sentence thesis

The project asks whether human belief propagation over factor graphs is globally exact or bounded/approximate, and if approximate, what continuous parameter ρ characterises the effective range of inference — with the prediction (from Wu et al.'s undergeneralization finding) that ρ̂ < 1 systematically.
