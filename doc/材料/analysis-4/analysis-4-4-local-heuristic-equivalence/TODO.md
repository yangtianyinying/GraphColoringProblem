# Analysis 4-4: is the local log-evidence heuristic genuinely a new agent family?

## Main question

A proposed alternative agent strategy is to aggregate local neighbour evidence using a simple log-evidence rule and then map this directly to a behavioural output.

The key question is:

> Is this local heuristic genuinely a distinct agent family, or is it mathematically equivalent to the current strictly local model \( M_0 \), possibly up to a response transformation?

## Why this analysis is needed

As the model space grows, it becomes increasingly important not to compare multiple names for what is effectively the same computation.

A student proposal suggests defining an agent that:

1. looks only at the beliefs or evidence from neighbouring nodes;
2. sums local log-evidence contributions;
3. optionally applies a simple inverse, normalisation, or output transform;
4. produces a belief-like behavioural response.

At face value, this sounds like a new heuristic strategy. However, under standard pairwise factor-graph semantics, a target belief that depends only on direct neighbours is already representable as a product of local potentials, which becomes a sum of local log-potentials in log space.

So the proposal may simply restate the \( \rho = 0 \) model in different language.

This analysis is needed to determine whether this heuristic should be:

- absorbed into \( M_0 \),
- represented as \( M_0 \) plus a response distortion layer,
- or retained as a genuinely distinct family.

## Primary goals

### Goal 1. Formalise the proposed heuristic precisely
Write down an explicit mathematical version of the local log-evidence heuristic, including:
- what inputs it takes;
- how each neighbour contributes;
- whether the output is a proper posterior, a score vector, or a choice rule;
- whether any nonlinear output transform is included.

### Goal 2. Compare it to \( M_0 \)
Determine whether, under standard assumptions, the heuristic is mathematically equivalent to the nearest-neighbour-only inference family \( M_0 \).

### Goal 3. Characterise possible non-equivalent extensions
If the heuristic differs from \( M_0 \), identify exactly where the difference lies:
- non-probabilistic weighting;
- clipping;
- inversion;
- nonlinear output remapping;
- state-wise coupling distortions;
- neighbour-specific salience weights.

### Goal 4. Decide how it should enter the broader model taxonomy
Recommend whether the heuristic should be:
- removed as redundant;
- folded into \( M_0 \);
- treated as \( M_0 \) plus a response transform;
- or retained as a distinct heuristic family for future comparison.

## Background intuition

Under a local pairwise model, if the target node \( x_i \) is influenced only by its direct neighbours, then its belief is of the form:

\[
p(x_i \mid \text{local evidence})
\propto
\phi_i(x_i)\prod_{j \in N(i)} \psi_{ij}(x_i, x_j),
\]

possibly with observed neighbour states or neighbour-level summary terms absorbed into the relevant local factors.

Taking logs gives:

\[
\log p(x_i \mid \text{local evidence})
=
\mathrm{const}
+
\log \phi_i(x_i)
+
\sum_{j \in N(i)} \log \psi_{ij}(x_i, x_j).
\]

This is already a sum of local log-evidence terms.

So if the proposed heuristic consists of summing direct-neighbour log-evidence and then normalising, it is likely just another representation of \( M_0 \).

## Planned analyses

## A. Formal specification of the heuristic

Write a clear mathematical definition of the proposed heuristic.

At minimum, specify:
- whether neighbour inputs are observed states, local beliefs, or local evidence summaries;
- whether contributions are additive in log space;
- whether all neighbours are weighted equally;
- whether the output is normalised into a probability distribution.

This step is essential, because many apparent differences disappear once the heuristic is stated precisely.

## B. Equivalence proof under standard assumptions

Attempt to show that if:

1. only direct neighbours contribute;
2. the contributions are additive in log space;
3. the output is formed by exponentiating and normalising the resulting scores;

then the heuristic is equivalent to a local factor model and therefore to \( M_0 \).

The proof need not be long, but it should be explicit and clean.

## C. Identify departures from \( M_0 \)

Analyse what extra ingredients would break the equivalence.

Examples include:
- neighbour-specific arbitrary weights;
- statewise transforms that do not correspond to log-potentials;
- clipping or saturation;
- inversion rules not derivable from a product of local factors;
- post-hoc behavioural mappings that distort the posterior.

This should produce a taxonomy of "ways the heuristic could become nontrivially different".

## D. Simulation check on representative conditions

If useful, implement the proposed heuristic and compare its outputs numerically to \( M_0 \) on a small diagnostic panel.

This is not a substitute for the mathematical argument, but it can help confirm:
- exact equivalence in the simple case;
- how strongly outputs diverge when nonlinear extensions are added.

## E. Recommendation for the agent taxonomy

Based on the results, decide whether the heuristic belongs in Analysis 4-1's model space as:
- no new family;
- a parameterisation of \( M_0 \);
- a response-distorted variant of \( M_0 \);
- or a distinct heuristic family.

## Questions this analysis should answer

1. What exactly is the proposed local log-evidence heuristic?
2. Under what assumptions is it mathematically equivalent to \( M_0 \)?
3. What modifications would make it genuinely distinct?
4. If distinct, is the distinction theoretically meaningful or merely ad hoc?
5. Should it be carried forward into later family-comparison analyses?

## Deliverables

### D1. Formal heuristic definition
A precise mathematical description of the local log-evidence rule.

### D2. Equivalence statement
A concise argument showing whether and when the heuristic is equivalent to \( M_0 \).

### D3. Distortion taxonomy
A structured list of modifications that would turn the heuristic into something genuinely different from \( M_0 \).

### D4. Optional simulation comparison
A small numerical check comparing:
- \( M_0 \)
- the pure local log-evidence heuristic
- one or two nonlinearly modified versions, if relevant

### D5. Taxonomy recommendation
A short recommendation to the broader Analysis 4 series stating how this heuristic should be treated.

## Success criteria

This analysis is successful if it provides:

1. a precise formalisation of the heuristic;
2. a clear answer to whether it is equivalent to \( M_0 \);
3. a principled account of what would make it genuinely different;
4. a recommendation that prevents unnecessary duplication in the model space.

## Likely expected conclusion

The most likely outcome is:
- the pure local log-evidence heuristic is equivalent to \( M_0 \);
- only after adding a distinct response transform or non-probabilistic weighting does it become meaningfully different.

If so, future analyses should avoid treating the plain heuristic as a new core agent family.

## Possible alternative outcome

If the student's intended heuristic includes a genuinely non-factorisable operation—such as a statewise inverse rule or neighbour-belief combination that cannot be written as local log-potentials—then it may define a separate heuristic family.

In that case, it should be compared not as a new probabilistic structural approximation, but as a **non-probabilistic local summary model**.

## Out of scope

This analysis should **not**:

- introduce a large family of arbitrary local heuristics;
- perform full participant fitting;
- replace the broader structural approximation programme;
- attempt to justify an ad hoc heuristic without a clean formal definition.

## Dependencies

This analysis is conceptually linked to:
- **Analysis 4-1**, because it determines whether the heuristic deserves family-level status;
- **Analysis 4-2**, because redundant families should not be carried into separability analyses unnecessarily.

## Relationship to later analyses

If the heuristic is found to be redundant with \( M_0 \), then it should be removed from the candidate family set used in later analyses.

If it is instead found to be \( M_0 \) plus a response transform, this may motivate a later distinction between inference model and response model.

## Recommended implementation order

1. obtain the clearest possible verbal specification of the student's proposal;
2. write the heuristic in equations;
3. compare the equations to \( M_0 \);
4. identify exactly where equivalence holds or breaks;
5. write a short recommendation for the master taxonomy.

## Practical recommendation

Unless the heuristic contains a clear non-factorisable or non-normalised operation, treat it as presumptively equivalent to \( M_0 \) until shown otherwise.
