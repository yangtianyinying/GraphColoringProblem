# Analysis 4-7: beyond map-colouring — towards task-general tests of structural approximation

## Main question

If our real scientific goal is to understand what kind of structural approximation people use when performing probabilistic inference on graphs, is the current map-colouring paradigm sufficient?

More specifically:

> Does the current map-colouring task confound the question of structural approximation with the special properties of anti-coordination constraints, and should future work include additional task domains with different local potential structures?

## Why this analysis is needed

The current paradigm is highly useful because it is intuitive, graph-structured, and naturally expressible using pairwise incompatibility constraints.

However, map-colouring has a strong built-in property:
- neighbouring nodes tend to prefer **different** states.

This makes it a task with predominantly **repulsive** or anti-coordination local interactions.

If we ultimately want to answer the broader question:

> What structural approximation do humans use when reasoning on graphical models?

then we should ask whether the observed approximation patterns are:
- general properties of human graph-based inference,
- or task-specific heuristics adapted to repulsive local constraints.

A participant strategy that works well for map-colouring may not generalise to tasks in which:
- neighbouring nodes tend to prefer the **same** state;
- local evidence propagates cooperatively rather than competitively;
- graph structure supports cluster formation rather than exclusion.

So this analysis is needed as a forward-looking theoretical step: to clarify whether a broader scientific answer requires a broader task family.

## Primary goals

### Goal 1. Clarify the domain-specific limitations of map-colouring
Identify which aspects of the current paradigm are likely specific to anti-coordination or colouring-style constraints.

### Goal 2. Define alternative task domains
Propose a small set of alternative graph-based inference tasks with different local potential structures, especially tasks with attractive or cooperative couplings.

### Goal 3. Ask whether the same agent taxonomy transfers
Assess how the candidate agent families from Analysis 4-1 might behave under these alternative tasks, and whether some families are only meaningful in the current map-colouring setting.

### Goal 4. Recommend future directions for task-general structure-approximation research
Provide a principled argument for whether future experiments should remain within map-colouring or expand to additional domains.

## Why map-colouring may be too narrow

In map-colouring-like tasks:
- adjacent nodes prefer different labels;
- local evidence often propagates through exclusion;
- parity, shell alternation, and conflict structure can become especially salient.

This means that some apparent structural strategies may actually be exploiting special features of repulsive couplings, such as:
- alternating sign effects by graph distance;
- local conflict counting;
- shell-parity heuristics;
- "avoid same colour as neighbour" rules that do not require general-purpose probabilistic inference.

Therefore, if we want to understand structural approximation rather than colouring-specific reasoning, we should consider tasks where:
- local couplings are attractive rather than repulsive,
- or at least vary in sign and interpretation.

## Candidate alternative task domains

## Domain A. Attractive graph labelling / smoothing task

Neighbouring nodes tend to prefer the same state.

### Example framing
Connected regions tend to share the same category, language, terrain type, species, or affiliation.

### Why useful
This flips the local rule while preserving much of the same graph-based inference structure.

### Relevance
Provides a direct contrast to map-colouring with minimal change in interface logic.

---

## Domain B. Social consensus / opinion inference

Nodes represent agents in a network, and linked agents tend to have similar opinions, preferences, or hidden states.

### Example framing
Infer the likely opinion of an unobserved person given the observed opinions of connected others.

### Why useful
Highly intuitive, naturally attractive, and easy to explain behaviourally.

### Relevance
May better test whether participants internally use clusters or community-like approximations.

---

## Domain C. Diffusion / contagion-style graph inference

Linked nodes increase the probability of shared latent state because of transmission or spread.

### Example framing
Infer which locations or people are likely infected, activated, informed, or contaminated.

### Why useful
Preserves graph structure but changes the semantics of local interaction from exclusion to transmission.

### Relevance
Allows testing whether structural approximation generalises to propagation tasks.

---

## Domain D. Mixed-sign or heterogeneous local-coupling task

Some links encourage similarity, others encourage dissimilarity.

### Example framing
Some relationships are cooperative, others competitive.

### Why useful
This is a more demanding test of general structural inference and may reveal whether participants truly represent edge semantics.

### Recommendation
Interesting in principle, but likely too complex for the first extension beyond map-colouring.

## Candidate domains to deprioritise

### Conway's Game of Life
Although superficially graph-like and local, this is primarily a deterministic dynamical update system rather than a straightforward static probabilistic graphical inference task.

### Recommendation
Do not prioritise it as the first generalisation target unless the task is substantially reformulated.

## Questions this analysis should answer

1. Which features of the current findings may be specific to repulsive local constraints?
2. Which alternative graph-based tasks best preserve experimental tractability while changing local potential structure?
3. Would the current agent taxonomy still make sense in those tasks?
4. Which future domain provides the cleanest first test of task-general structural approximation?
5. What theoretical claims should we avoid making if we stay only within map-colouring?

## Planned analyses

## A. Theoretical comparison of task classes

Compare the current map-colouring paradigm to a small number of alternative task families in terms of:
- local coupling semantics;
- expected propagation profile;
- likely participant intuitions;
- suitability for graph-based Bayesian or factor-graph formalisation;
- similarity to the current interface and experimental workflow.

## B. Agent-taxonomy transfer analysis

For each candidate family from Analysis 4-1, ask whether its interpretation transfers naturally to an attractive-coupling task.

Examples:
- does \( M_{\rho} \) still make sense? likely yes;
- does \( M_{\mathrm{star}} \) still make sense? likely yes;
- are shell-parity-based intuitions still meaningful? perhaps not;
- does \( M_{\mathrm{cluster}} \) become more or less plausible? potentially more plausible.

## C. Candidate-task ranking

Rank alternative task domains according to:
- theoretical value,
- experimental simplicity,
- continuity with the current paradigm,
- expected ability to distinguish structural approximation families.

## D. Recommendation for the first non-colouring extension

Make a concrete recommendation for the next task domain to explore.

A likely candidate is a simple attractive graph-labelling task, because it changes local potential structure while preserving much of the existing graph and inference logic.

## Deliverables

### D1. Limitation statement
A concise statement of what can and cannot be concluded about human structural approximation from the map-colouring paradigm alone.

### D2. Alternative-task comparison table
A table comparing map-colouring with a small set of alternative task domains.

### D3. Taxonomy-transfer summary
A summary of how the current candidate agent families would carry over to those domains.

### D4. Future-task recommendation
A recommendation for the most promising next task domain and why.

### D5. Prospect section draft
A short future-directions text that could later be reused in papers, preregistrations, or proposals.

## Success criteria

This analysis is successful if it provides:

1. a clear articulation of the limits of map-colouring as a general testbed;
2. a small set of theoretically motivated alternative task domains;
3. a reasoned argument for which domain should be prioritised next;
4. a cleaner scientific framing of what the present programme can and cannot claim.

## Likely expected conclusion

A likely conclusion is:
- map-colouring remains an excellent first testbed for bounded graph inference;
- however, it is not sufficient on its own to establish domain-general claims about human structural approximation;
- the most natural next step is to add a task with **attractive local couplings** while preserving as much of the graph-based inference structure as possible.

## Out of scope

This analysis should **not**:

- build a full new experiment immediately;
- implement all alternative task domains;
- run new participant studies;
- claim cross-domain generality without further evidence.

## Dependencies

This analysis depends conceptually on:
- **Analysis 4-1**, because the relevance of alternative tasks depends on the current agent taxonomy;
- the broader findings of Analyses 1–3, because these motivate why structural approximation is worth studying in the first place.

## Relationship to the rest of Analysis 4

This analysis is intentionally more forward-looking than the others.

Whereas Analyses 4-1 to 4-6 focus on the current task family, this analysis asks how the broader research programme should evolve if the long-term goal is to understand human structure approximation rather than only map-colouring performance.

## Recommended implementation order

1. state clearly what is specific about map-colouring;
2. define a small candidate set of alternative task classes;
3. compare them using the existing agent taxonomy as a lens;
4. recommend one first extension domain;
5. write a short reusable outlook section.

## Practical recommendation

Do not overcomplicate this stage.

A strong conceptual comparison between:
- the current repulsive map-colouring task,
- and one attractive graph-labelling alternative,

is likely more useful than a long list of speculative future paradigms.
