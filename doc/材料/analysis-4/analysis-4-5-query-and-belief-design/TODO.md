# Analysis 4-5: does a two-stage query-plus-belief task provide stronger behavioural constraints?

## Main question

Would a richer task format help distinguish between candidate bounded-inference agent families more effectively than the current single-stage belief-report paradigm?

More specifically:

> If participants are first asked to choose **which node to query or fill**, and only then asked to report their belief about that node, does this two-stage design provide stronger leverage for distinguishing between agent families than a standard forced-target belief task?

## Why this analysis is needed

The current paradigm primarily constrains models through target-node belief outputs. This is already useful, but it may not be sufficient to separate all candidate families introduced in Analysis 4-1.

Different agent families may produce similar belief distributions on a queried node while differing substantially in:

- which nodes they regard as most informative or most urgent;
- what local structure they prioritise;
- what elimination or simplification strategy they implicitly favour;
- what they consider easiest or most diagnostic to infer next.

A two-stage task adds a second behavioural signature:

1. **selection behaviour**: which node the participant chooses to act on or query;
2. **belief behaviour**: what belief they report once that node is selected.

This may be especially valuable for separating:
- exact versus bounded agents,
- attenuation-based versus structure-rewrite agents,
- local heuristics versus graph-aware approximations.

## Primary goals

### Goal 1. Formalise candidate behavioural task formats
Define and compare several possible task structures, including:
- **forced-target belief report**: the current baseline;
- **free-query order**: participants choose which node to query next;
- **choose-node then report-belief**: the proposed two-stage paradigm;
- optionally, **choose-node under fixed evidence template**, versus **choose-node with adaptive evidence reveal**.

### Goal 2. Determine whether selection behaviour is family-diagnostic
Assess whether different agent families systematically prefer different target nodes under the same graph/evidence condition.

### Goal 3. Quantify incremental discriminability
Test whether adding node-selection data improves the ability to distinguish candidate families beyond belief reports alone.

### Goal 4. Generate recommendations for future behavioural design
Provide a principled answer to whether this richer paradigm is worth piloting, and if so, in what exact format.

## Candidate task variants

## Variant A. Forced target only

Participants are told which node to judge and report a belief distribution.

### Role
Current benchmark. Serves as the baseline condition against which richer formats should be evaluated.

---

## Variant B. Free query order

Participants are allowed to decide which unknown node to query next across a partially filled graph.

### Role
Connects naturally to elimination-order or information-seeking heuristics.

### Relevance
Already related to earlier ideas in the proposal.

---

## Variant C. Choose node, then report belief

Participants first choose which node they want to act on or infer, then provide a belief report for that node.

### Role
Primary focus of this analysis.

### Hypothesis
Selection behaviour may reveal structural priorities that belief-only paradigms do not.

---

## Variant D. Choose node under adaptive reveal

The environment changes depending on the selected node, e.g. evidence is instantiated or highlighted conditional on the participant's choice.

### Role
A possible future extension, but likely more complex.

### Recommendation
Only consider if simpler versions appear especially promising.

## Important design distinction

A key decision is whether the second-stage belief report should occur under:

1. a **fixed pre-specified evidence configuration**, where all participants see the same graph/evidence state before choosing a target; or
2. a **choice-conditioned evidence reveal**, where the evidence shown depends on the selected target.

The first is cleaner for model comparison, because:
- all participants face the same decision problem;
- node choice and belief report are directly comparable across participants and models.

Therefore, this analysis should treat the **fixed-evidence, choose-node-then-report-belief** design as the primary candidate unless strong reasons emerge otherwise.

## Candidate families to compare

At minimum, use the family set retained after Analyses 4-1 and 4-4, likely including:

- \( M_{\mathrm{exact}} \)
- \( M_0 \)
- \( M_{\rho} \)
- \( M_{\mathrm{star}} \)
- \( M_{\mathrm{cluster}} \)

If parameter uncertainty is relevant, a reduced \( \beta \)-sensitive variant may also be included, but only if this does not overload the design comparison.

## What must be modelled

This analysis should distinguish two components of behaviour:

### 1. Target selection policy
A rule determining which node the agent chooses to query, infer, or fill next.

Possible normative or heuristic principles include:
- highest uncertainty reduction;
- greatest expected effect on the graph;
- easiest local computation;
- smallest expected fill-in;
- strongest local evidence imbalance;
- shortest structural distance to current evidence.

The exact form can vary by family, but selection policy must be made explicit.

### 2. Belief report conditional on selected target
Given the chosen node, the agent produces a belief over its possible states using its own internal approximation scheme.

The main question is whether combining these two behavioural signatures improves family identifiability.

## Planned analyses

## A. Formalise selection rules for candidate families

For each family, define at least one plausible target-selection rule.

Examples:
- exact or graph-aware agents may choose based on expected informativeness or uncertainty;
- local agents may prefer nodes with stronger local evidence imbalance;
- star agents may prioritise nodes whose shell summaries are simplest or strongest;
- cluster agents may prefer clique-boundary or cluster-central nodes.

This analysis does not require that each family have a unique policy, but it should explore whether plausible policy differences exist and matter.

## B. Simulate node-selection behaviour

On a representative graph/evidence panel, simulate which target each family would choose under the proposed task.

Main outputs:
- choice distributions over candidate nodes;
- agreement versus disagreement between families;
- graph motifs where selection is especially divergent.

## C. Simulate belief outputs after self-selected query

For each family, condition on its selected node and compute the resulting belief report.

Then compare:
- belief-only discriminability under forced targets;
- combined selection-plus-belief discriminability under self-chosen targets.

## D. Compare design informativeness

Construct quantitative comparisons of how much model discrimination is available under:
- forced-target belief only;
- free query order only;
- choose-node then report-belief.

Possible comparison measures:
- family confusion rates;
- expected KL or JS separation;
- synthetic family recovery;
- mutual-information-style summaries, if practical.

## E. Identify optimal task conditions

Determine which graph/evidence conditions make node choice especially informative, and whether these conditions overlap with those already diagnostic for belief outputs.

This helps answer whether the two-stage design:
- merely duplicates existing information,
- or adds genuinely new constraints.

## Deliverables

### D1. Formal task-design comparison
A clear description of the candidate behavioural paradigms and what behavioural outputs each provides.

### D2. Selection-policy summary
A table describing plausible target-selection rules for each candidate family.

### D3. Simulated choice distributions
Plots showing which nodes different families select under representative conditions.

### D4. Combined discriminability summary
A comparison of family separability under:
- belief-only,
- selection-only,
- and combined selection-plus-belief data.

### D5. Design recommendation
A short recommendation stating whether the two-stage task is worth pursuing, and if so, in what exact form.

## Success criteria

This analysis is successful if it determines:

1. whether target-selection behaviour is meaningfully family-diagnostic;
2. whether combining selection and belief improves family separability over belief alone;
3. which exact two-stage design is cleanest and most promising;
4. whether the gain in discriminability justifies the added experimental complexity.

## Possible outcomes and interpretation

### Outcome 1. Strong added value
If node choice differs strongly across families and improves recovery substantially, then the two-stage design should be prioritised for future piloting.

### Outcome 2. Modest added value
If node choice adds some information but only in a limited set of conditions, then the two-stage design may still be useful as a targeted extension rather than a full replacement.

### Outcome 3. Little added value
If node choice mostly mirrors what is already implied by belief outputs, then the simpler forced-target paradigm may remain preferable.

## Important caution

The analysis should avoid conflating two different questions:

1. whether a family predicts a different belief on a target;
2. whether a family prefers to choose a different target.

These are distinct diagnostic channels and should be evaluated separately before combining them.

## Out of scope

This analysis should **not** yet:

- implement a full adaptive experimental platform;
- optimise the final user interface;
- fit participant choice behaviour;
- redesign the entire experiment around active information gathering.

## Dependencies

This analysis depends on:
- **Analysis 4-1** for the candidate family set;
- **Analysis 4-2** for knowledge of which conditions are already belief-diagnostic;
- optionally **Analysis 4-3** if parameter uncertainty needs to be incorporated in the design comparison.

## Relationship to later work

If this analysis finds strong value in the two-stage design, it can motivate a dedicated pilot experiment, explicit modelling of query policies, and broader comparisons between inference models and active-structure heuristics.

If it finds limited value, it still clarifies that the current belief-report paradigm is likely sufficient for the near term.

## Recommended implementation order

1. choose a fixed-evidence version of the two-stage task as the main candidate;
2. define plausible selection rules for each family;
3. simulate node choices on a reduced diagnostic graph panel;
4. compute resulting belief outputs after self-selected query;
5. compare discriminability to the current forced-target design;
6. write a recommendation for future piloting.

## Practical recommendation

Start with the simplest version:
- fixed graph,
- fixed evidence,
- participant chooses one target node,
- participant reports belief for that chosen node.

Only consider adaptive evidence reveal if this simple version clearly provides substantial added diagnostic value.
