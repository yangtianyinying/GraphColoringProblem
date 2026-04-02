# Analysis 4-2: family separability on the existing stimulus library

## Main question

Given the candidate agent families defined in Analysis 4-1, can the **existing rooted-shell stimulus library** already distinguish them?

More specifically:

> Are there graph structures and evidence conditions already available in the current task space that reliably separate fixed-graph attenuation agents, structure-rewrite agents, and exact inference agents at the level of target-node belief outputs?

## Why this analysis is needed

Analysis 4-1 expands the model space beyond the current \( \rho \)-family. However, introducing new candidate agent families is only useful if they are **behaviourally distinguishable** on task instances that we can actually present.

At present, we do not yet know whether:

- the current graph library is rich enough to separate these agent classes;
- rooted dimensions such as D1/D2/D3 are diagnostic of **family-level** differences, rather than only differences within the \( \rho \)-family;
- the proposed structure-rewrite agents produce predictions that are meaningfully different from attenuation-based agents on the existing stimulus set.

This analysis therefore asks whether the current paradigm already contains enough information to discriminate between the newly defined agent families, before we consider generating new stimuli or redesigning the task.

## Primary goals

### Goal 1. Evaluate family-level separability on the current library
Using the candidate families defined in Analysis 4-1, compute target-belief predictions across the existing graph/evidence library and quantify pairwise family separation.

### Goal 2. Identify the most diagnostic graph/evidence conditions
Find which rooted graph structures and evidence placements maximise behavioural differences between families.

### Goal 3. Relate family separability to rooted graph descriptors
Determine whether dimensions like:
- target degree / shell profile,
- neighbour-neighbour connectivity,
- distal closure / long-range interaction structure,

are systematically associated with stronger discrimination between specific agent-family pairs.

### Goal 4. Produce reusable visual diagnostics
Establish a standard output suite showing family-level KL structure across candidate stimuli, so that future stimulus selection can be guided by these diagnostics.

## Candidate families to compare

The analysis should begin with the minimal family set recommended by Analysis 4-1:

- \( M_{\mathrm{exact}} \)
- \( M_0 \)
- \( M_{\rho} \)
- \( M_{\rho,\beta} \) or a provisional \( \beta \)-extended attenuation family
- \( M_{\mathrm{star}} \)
- \( M_{\mathrm{cluster}} \)

If the \( \beta \)-extended family is not yet simulation-ready, it may be held fixed or replaced by a provisional coarse-grid variant for this analysis, provided this is clearly stated.

If \( M_{\mathrm{cluster}} \) is not yet operational, a temporary lightweight local-structure approximation may be substituted, but this should be explicitly marked as provisional.

## Core empirical object

For each agent family and each stimulus condition, the key object of comparison is the predicted target-node belief distribution:

\[
b^{(m)}(x_i \mid G, E),
\]

where:
- \( m \) indexes the agent family,
- \( G \) is the graph instance,
- \( E \) is the evidence configuration,
- \( x_i \) is the queried target node state.

All family comparisons should ultimately be defined over these belief outputs.

## Stimulus set

This analysis should start from the **existing rooted-shell graph and evidence library** developed in Analyses 2 and 3.

At minimum, the stimulus inventory should preserve:

- rooted graph distinctions already used in previous analyses;
- evidence conditions that produced strong exact-vs-local or exact-vs-attenuated separations;
- matched graph comparisons that hold local properties fixed while changing distal structure.

If the current library is too large, a reduced diagnostic subset may be used initially, but it should still span the major rooted descriptor dimensions identified earlier.

## Distance metrics and comparison measures

### Primary metric
Use pairwise KL divergence between target belief distributions:

\[
D_{\mathrm{KL}}\!\left(b^{(m_1)} \,\|\, b^{(m_2)}\right)
\]

as the primary directional separation measure.

### Secondary metrics
Where useful, also compute:
- symmetrised KL;
- Jensen-Shannon divergence;
- total variation distance;
- rank-order agreement over target states.

If only one secondary metric is retained, prefer JS divergence for visual summaries.

## Planned analyses

## A. Family-by-family KL matrices

For each graph/evidence condition, compute a family-by-family divergence matrix over target beliefs.

This should answer:
- which family pairs are well separated on that condition;
- which conditions collapse multiple families into near-equivalence.

## B. Family confusion / recovery analysis

Simulate synthetic observations from each family and ask whether they can be recovered from the family set using the current stimulus inventory.

This can be done either via:
- aggregate divergence over stimulus panels;
- likelihood-based family recovery on noiseless or noisy synthetic responses.

The main question is not full participant fitting, but whether the current task space is informative enough in principle.

## C. Descriptor-conditioned separation analysis

Relate family separability to rooted graph descriptors developed earlier.

Examples:
- Does neighbour-neighbour coupling selectively separate \( M_{\mathrm{cluster}} \) from \( M_{\rho} \)?
- Does distal closure selectively separate \( M_{\mathrm{star}} \) from \( M_{\mathrm{exact}} \)?
- Are some rooted dimensions mainly informative within attenuation families but not across family classes?

## D. Matched-comparison analysis

Construct or reuse matched pairs/triples of graph conditions that preserve some local statistics while changing one higher-order structural property.

This is especially important for distinguishing:
- fixed-graph attenuation from structure-rewrite approximations;
- local cluster models from target-centred star approximations.

## E. Candidate panel construction

Identify a compact subset of graph/evidence conditions that jointly maximise separation across the family set.

This subset can later support:
- behavioural pilot design;
- family-recovery studies;
- richer task-design analyses in Analysis 4-5.

## Deliverables

### D1. Family separation heatmaps
For each selected graph/evidence condition, produce a heatmap of pairwise family divergence.

### D2. Global confusion summary
Produce a summary matrix showing how distinguishable families are when evidence is aggregated across the current stimulus library.

### D3. Rooted-descriptor linkage summary
Provide plots or tables showing how family separation varies as a function of rooted graph descriptors.

### D4. Ranked diagnostic conditions
Produce a ranked list of graph/evidence conditions by their usefulness for separating:
- \( M_{\mathrm{exact}} \) vs \( M_{\rho} \)
- \( M_{\rho} \) vs \( M_{\mathrm{star}} \)
- \( M_{\mathrm{star}} \) vs \( M_{\mathrm{cluster}} \)
- \( M_0 \) vs all nonlocal families

### D5. Recommended reduced stimulus panel
Propose a small, high-value subset of conditions for future use.

## Visual output standard

At minimum, each selected condition should have:

1. a graph visualisation;
2. evidence annotation;
3. family-by-family KL or JS heatmap;
4. predicted target-belief vectors for the main families.

For descriptor-level summaries, include:
- scatterplots or binned summaries linking descriptor values to family separation;
- at least one figure showing how separability is distributed across the rooted design space.

## Success criteria

This analysis is successful if it shows all of the following:

1. at least some of the new family pairs are clearly separable on the current stimulus library;
2. the most diagnostic conditions can be described in rooted structural terms;
3. there is a principled reduced set of conditions worth carrying forward;
4. the current library's limitations, if any, are clearly identified;
5. the analysis yields reusable family-level KL diagnostics for future work.

## Possible outcomes and how to interpret them

### Outcome 1. Strong separability
If the current library strongly separates the main family pairs, then the existing task space is already rich enough to support broader agent comparisons. This would justify moving directly to parameter identifiability analyses, behavioural family fitting, and richer query-format design.

### Outcome 2. Partial separability
If some family pairs are distinguishable but others are not, then the result will guide targeted stimulus augmentation. This is still highly useful.

### Outcome 3. Weak separability
If most family pairs collapse on the current library, then this implies that the current task space is mostly diagnostic within the \( \rho \)-family, additional graph motifs or evidence placements will be needed, or a richer behavioural paradigm will be required. This would directly motivate Analysis 4-5.

## Out of scope

This analysis should **not** yet:

- fit participant data with full hierarchical models;
- settle the final value or treatment of \( \beta \);
- redesign the entire task from scratch;
- evaluate cross-task generalisation beyond map-colouring.

## Dependencies

This analysis depends on Analysis 4-1 for:
- the formal family definitions;
- the decision about which families are simulation-ready;
- the redundancy assessment of the local heuristic proposal.

## Relationship to later analyses

- **Analysis 4-3** will ask whether separations involving \( \rho \) remain meaningful once \( \beta \) is allowed to vary.
- **Analysis 4-5** will ask whether a richer behavioural paradigm provides better family discrimination if current separability is insufficient.
- **Analysis 4-6** will formalise the visual diagnostic standards partly developed here.

## Recommended implementation order

1. finalise the minimal family set from Analysis 4-1;
2. choose a manageable but representative graph/evidence subset;
3. compute family belief predictions;
4. build pairwise KL / JS matrices;
5. identify diagnostic conditions;
6. summarise results by rooted descriptor dimensions.

## Practical recommendation

If implementation time is limited, begin with the following family subset:

- \( M_{\mathrm{exact}} \)
- \( M_0 \)
- \( M_{\rho} \)
- \( M_{\mathrm{star}} \)
- \( M_{\mathrm{cluster}} \) or a provisional local-structure surrogate

and only then add the \( \beta \)-extended family once the core family-level separability picture is clear.
