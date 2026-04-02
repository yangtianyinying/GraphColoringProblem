# Analysis 4-3: parameter identifiability of structural attenuation and factor strength

## Main question

To what extent are behavioural effects attributed to structural approximation actually distinguishable from changes in factor strength?

More specifically:

> Can the attenuation parameter \( \rho \) be identified separately from the coupling-strength parameter \( \beta \), and can family-level structural approximations still be distinguished once \( \beta \) is allowed to vary?

## Why this analysis is needed

The current modelling framework has largely treated edge or factor strength as fixed, while using \( \rho \) to control the effective influence of more distal structure.

This is analytically convenient, but potentially misleading.

In many graph-structured inference tasks, weaker long-range effects can arise for at least two different reasons:

1. the agent structurally discounts or truncates distal influences;
2. the underlying pairwise or factor couplings are simply weaker overall.

If these two possibilities generate similar target-belief outputs, then conclusions about bounded structural approximation may be partly confounded with unmodelled factor-strength variation.

Before fitting richer models or interpreting the meaning of \( \rho \), we therefore need to establish whether \( \rho \) and \( \beta \) are identifiable in principle on the current stimulus space.

## Primary goals

### Goal 1. Test identifiability of \( \rho \) and \( \beta \)
Determine whether variation in \( \rho \) and variation in \( \beta \) produce distinguishable belief outputs across the existing graph/evidence library.

### Goal 2. Characterise tradeoffs and degeneracies
Identify regions of parameter space where:
- different \( (\rho, \beta) \) combinations produce near-equivalent predictions;
- apparent structural approximation may be mimicked by reduced factor strength;
- identifiability depends strongly on graph structure or evidence placement.

### Goal 3. Assess consequences for family comparisons
Determine whether family-level comparisons from Analysis 4-2 remain meaningful when \( \beta \) is allowed to vary.

In particular:
- does \( M_{\rho} \) remain distinct from \( M_{\mathrm{star}} \) after optimising over \( \beta \)?
- do some family differences collapse once factor strength is treated as free?

### Goal 4. Generate modelling recommendations
Provide a principled recommendation for future analyses and experiments:
- should \( \beta \) be fixed?
- jointly fit with \( \rho \)?
- shared across families?
- treated as a nuisance parameter in discrimination studies?

## Candidate models to analyse

At minimum, this analysis should consider:

- \( M_{\rho} \)
- \( M_{\rho,\beta} \) or equivalent two-parameter attenuation family
- \( M_{\mathrm{exact},\beta} \), if exact inference is to be compared across multiple coupling strengths
- optionally, \( M_{\mathrm{star},\beta} \) if the star family also includes an interpretable strength parameter

The initial focus should remain on whether \( \rho \) and \( \beta \) are distinguishable within the fixed-graph family, before extending the same logic to structure-rewrite families.

## Parameters of interest

### Structural attenuation
\( \rho \) — controls the effective contribution of distal structure, message depth, or factor influence decay under the bounded-inference family.

### Coupling strength
\( \beta \) — controls the strength of local compatibility or incompatibility imposed by pairwise or factor potentials.

### Important conceptual distinction

This analysis should explicitly distinguish:

- **weaker propagation because the structure is approximated**, and
- **weaker propagation because each factor is intrinsically weaker**.

These are not the same theoretical hypothesis, even when they may sometimes be behaviourally similar.

## Core empirical object

As in Analysis 4-2, the basic object of comparison is the predicted target-node belief distribution:

\[
b(x_i \mid G, E;\, \rho, \beta).
\]

Parameter identifiability is therefore defined with respect to whether different parameter settings produce distinguishable target beliefs over a useful set of graph/evidence conditions.

## Planned analyses

## A. Parameter-grid sweep

Construct a grid over \( \rho \) and \( \beta \), and compute target-belief predictions across the current stimulus library.

This should provide an initial map of:
- smoothness of prediction changes;
- regions of strong versus weak parameter sensitivity;
- possible ridges of approximate equivalence.

## B. Pairwise parameter divergence map

For pairs of parameter settings \( (\rho_1,\beta_1) \) and \( (\rho_2,\beta_2) \), compute the divergence between their predicted belief panels.

This can be summarised by:
- average KL or JS divergence across the library;
- minimum or median divergence across selected diagnostic stimuli;
- confusion-style matrices over parameter grid points.

The goal is to determine whether the parameter map is locally and globally distinguishable.

## C. Recovery analysis from synthetic data

Generate synthetic responses from known \( (\rho,\beta) \) settings and attempt to recover them using the same model family.

This should be done under at least two regimes:

1. noiseless or near-noiseless synthetic outputs;
2. noisy outputs approximating plausible participant variability.

The key question is whether the true generating parameters can be approximately recovered, and where recovery fails.

## D. Profile-likelihood or best-match analysis

For each true \( (\rho^\ast,\beta^\ast) \), identify alternative parameter settings that generate near-equivalent outputs.

This is useful for exposing:
- narrow versus broad ridges;
- whether \( \beta \) can absorb changes in \( \rho \);
- whether identifiability is only possible on certain stimulus subsets.

## E. Stimulus-level identifiability contribution

Determine which graph/evidence conditions contribute most strongly to separating \( \rho \) from \( \beta \).

Some conditions may be:
- highly diagnostic of structural attenuation,
- weakly informative about coupling strength,
- or vice versa.

This analysis should help define a future stimulus panel optimised not only for family separability but also for parameter identifiability.

## F. Family robustness under \( \beta \)-optimisation

Take the family comparisons from Analysis 4-2 and test whether they remain after allowing each family to optimise over \( \beta \).

For example:
- compare \( M_{\rho} \) with \( M_{\mathrm{star}} \) after both are allowed family-specific best-fitting \( \beta \);
- test whether separability observed under fixed \( \beta \) survives this additional flexibility.

## Deliverables

### D1. \( \rho \)-\( \beta \) prediction atlas
A visual summary of how target-belief predictions vary across the parameter grid.

### D2. Parameter-grid separability heatmaps
Heatmaps showing average divergence between parameter settings across the stimulus library.

### D3. Recovery plots
Plots comparing true versus recovered values of \( \rho \) and \( \beta \) under synthetic data generation.

### D4. Tradeoff and ridge summaries
A concise description of major degeneracy patterns, such as low-\( \beta \), high-\( \rho \) mimicking high-\( \beta \), low-\( \rho \); regions where one parameter is recoverable only if the other is fixed.

### D5. Diagnostic stimulus ranking for identifiability
A ranked list of graph/evidence conditions that most strongly help distinguish \( \rho \) from \( \beta \).

### D6. Recommendation for downstream modelling
An explicit recommendation on whether future work should fix \( \beta \), jointly fit \( \rho \) and \( \beta \), regularise one using the other, or restrict analyses to stimulus panels that improve identifiability.

## Visual output standard

At minimum, include:

1. parameter-grid heatmaps over average panel divergence;
2. true-versus-recovered scatterplots for \( \rho \) and \( \beta \);
3. examples of belief panels where \( \rho \)-variation and \( \beta \)-variation look similar;
4. examples where they clearly differ;
5. a summary plot linking rooted graph descriptors to \( \rho \)-\( \beta \) identifiability.

## Success criteria

This analysis is successful if it establishes all of the following:

1. whether \( \rho \) and \( \beta \) are identifiable in principle on the current task family;
2. where major confounds or near-degeneracies occur;
3. whether family separability from Analysis 4-2 survives once \( \beta \) is allowed to vary;
4. which stimuli are most useful for disentangling structural attenuation from factor-strength variation;
5. a clear recommendation for how \( \beta \) should be treated in future modelling.

## Possible outcomes and interpretation

### Outcome 1. Strong identifiability
If \( \rho \) and \( \beta \) are well separated across a broad stimulus set, then future modelling can safely include both parameters. This would strengthen the interpretation of \( \rho \) as a genuinely structural approximation parameter.

### Outcome 2. Conditional identifiability
If \( \rho \) and \( \beta \) are identifiable only on a subset of diagnostic conditions, then future experiments should preferentially use those conditions. This is still a useful result.

### Outcome 3. Weak identifiability
If many \( (\rho,\beta) \) settings collapse behaviourally, then \( \rho \)-based interpretations should be weakened, stronger priors or constraints may be needed, or the task must be redesigned to improve parameter separation.

## Out of scope

This analysis should **not** yet:

- fit participant-level hierarchical models;
- resolve the final best family of human inference;
- expand to cross-task comparisons beyond the current paradigm;
- add many extra free parameters beyond \( \rho \) and \( \beta \).

## Dependencies

This analysis depends on:
- **Analysis 4-1** for formal model definitions;
- **Analysis 4-2** for the core diagnostic stimulus library and initial family separation results.

## Relationship to later analyses

- **Analysis 4-4** will clarify whether some local heuristics are merely \( \rho = 0 \) special cases and therefore should not be given extra parameter freedom.
- **Analysis 4-5** may use identifiability failures discovered here as motivation for richer behavioural task formats.

## Recommended implementation order

1. choose a practical grid over \( \rho \) and \( \beta \);
2. compute belief outputs on a representative diagnostic stimulus panel;
3. build parameter-grid divergence maps;
4. run recovery from synthetic data;
5. test family separability under \( \beta \)-optimisation;
6. summarise implications for future model fitting and design.

## Practical fallback

If full joint analysis of \( \rho \) and \( \beta \) is too heavy initially, begin with:
- a coarse \( \rho \times \beta \) grid;
- a reduced diagnostic stimulus panel from Analysis 4-2;
- noiseless recovery only.

Then expand only if clear nontrivial tradeoffs are observed.
