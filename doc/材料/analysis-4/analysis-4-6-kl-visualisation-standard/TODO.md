# Analysis 4-6: standardising KL-based visual diagnostics for graph and evidence conditions

## Main question

How should future analyses and stimulus design decisions be visually standardised so that graph and evidence conditions can be compared consistently across agent families?

More specifically:

> Can we define a reusable visual diagnostic standard—centred on KL and related divergence heatmaps—that makes it easier to compare candidate graph/evidence conditions, judge family separability, and communicate why specific stimuli are diagnostically valuable?

## Why this analysis is needed

Earlier analyses have already shown that KL-based comparisons are highly informative for evaluating how different graph structures and evidence configurations separate inference regimes.

However, these visual diagnostics have not yet been fully standardised.

As a result:
- some analyses include rich pairwise KL visualisations while others do not;
- it is harder to compare results across analyses;
- the rationale for selecting specific stimuli is sometimes implicit rather than visibly documented;
- family-level separability and parameter-level identifiability are not always displayed in comparable formats.

If the project is going to rely on diagnostic graph/evidence design in a systematic way, it needs a consistent visual language.

## Primary goals

### Goal 1. Define a standard visual output suite
Specify a minimal set of figures that should accompany future graph/evidence analyses.

### Goal 2. Link visual diagnostics to scientific questions
Ensure that each standard figure answers a clear question, such as:
- Which agent families are separated by this condition?
- Which parameters are confusable on this condition?
- Which rooted structural feature appears responsible?
- Which conditions are globally most diagnostic?

### Goal 3. Make outputs reusable for stimulus selection
Create a visual standard that can support:
- future analysis reports;
- pilot stimulus selection;
- model-recovery planning;
- communication with collaborators and students.

### Goal 4. Ensure continuity with earlier rooted-descriptor analyses
The standard should not replace rooted structural summaries, but integrate with them.

## Scope of the standard

This analysis is not about creating one specific plot for one specific result.

Instead, it should define a **portable figure specification** that can be used whenever we evaluate:
- a graph;
- an evidence condition;
- an agent-family comparison;
- a parameter-grid comparison;
- or a reduced stimulus panel.

## Core figure types to standardise

## Figure type A. Condition-specific family divergence heatmap

For a single graph/evidence condition, show a heatmap of pairwise divergences between candidate agent families.

### Purpose
Answers which family pairs are strongly separated by this condition, and which families collapse under this condition.

### Recommended content
- one panel per condition;
- symmetric or directed KL clearly indicated;
- family labels in a fixed order across all analyses.

## Figure type B. Target-belief profile panel

For the same graph/evidence condition, show the predicted target belief vectors for the main candidate families.

### Purpose
Makes the divergence heatmap interpretable by showing the underlying behavioural predictions directly.

### Recommended content
- graph visualisation;
- evidence annotation;
- target marker;
- belief bars or line profiles for each family.

## Figure type C. Global family confusion summary

Aggregate over a library or candidate panel and show how distinguishable the families are overall.

### Purpose
Answers which families are globally hard to tell apart and whether the current panel is sufficient for model discrimination.

### Recommended content
- average KL or JS matrix;
- optionally, synthetic family-recovery matrix.

## Figure type D. Parameter-grid separability map

For analyses involving free parameters such as \( \rho \) and \( \beta \), show divergence or recovery across the parameter grid.

### Purpose
Answers where parameters are identifiable and where they trade off or collapse.

### Recommended content
- heatmap over parameter pairs;
- optional true-versus-recovered plots as companion figures.

## Figure type E. Rooted-descriptor linkage figure

Show how divergence-based discriminability varies as a function of rooted graph descriptors such as D1/D2/D3.

### Purpose
Connects visual diagnostics back to the rooted structural logic of Analyses 2 and 3.

### Recommended content
- scatterplots, grouped means, or binned summaries;
- one panel per descriptor or descriptor family.

## Figure type F. Ranked diagnostic condition summary

A compact display of the best graph/evidence conditions for separating specific family pairs.

### Purpose
Supports practical stimulus selection.

### Recommended content
- top-N ranked conditions;
- small multiples showing graph thumbnails plus summary divergence scores.

## Questions this analysis should answer

1. What figures should every future diagnostic analysis include by default?
2. How should family divergence be displayed consistently across conditions?
3. How should parameter identifiability plots be aligned with family-separability plots?
4. How should rooted structural descriptors be integrated into these visual summaries?
5. What visual outputs are most useful for selecting future experimental stimuli?

## Planned analyses

## A. Audit previous figure styles

Review the KL-related figures used in Analyses 2 and 3 and identify:
- what worked well;
- what was missing;
- what was hard to compare across analyses.

This does not need to be exhaustive, but it should be concrete enough to motivate a standard.

## B. Define canonical figure templates

For each core figure type listed above, specify:
- required inputs;
- required annotations;
- recommended layout;
- naming conventions;
- colour-scale conventions;
- whether KL is directional or symmetrised.

## C. Define minimal mandatory visual outputs

Specify the smallest set of figures that should accompany any future graph/evidence diagnostic study.

A likely minimum set is:

1. condition-specific family divergence heatmap;
2. belief profile panel;
3. global family confusion summary;
4. rooted-descriptor linkage summary.

## D. Produce one worked example panel

Construct a worked example using one existing graph/evidence condition and one small family set.

The purpose is not scientific novelty, but demonstrating the standard.

## E. Establish naming and storage conventions

Recommend a standard directory or filename structure so that figures are easy to compare across analyses.

Examples:
- `family_kl_condition_X.png`
- `belief_profiles_condition_X.png`
- `descriptor_vs_separation_D2.png`

## Deliverables

### D1. Visual standard document
A short document specifying the standard figure suite and what each figure type is for.

### D2. Template figure list
A checklist of figure types that future analyses should produce.

### D3. Worked example
One fully annotated example showing how a graph/evidence condition should be visually reported.

### D4. Conventions guide
A brief guide for:
- family ordering;
- metric naming;
- colour scales;
- annotation standards;
- filename and directory conventions.

## Success criteria

This analysis is successful if it results in:

1. a reusable visual standard for future diagnostic analyses;
2. clear figure types linked to clear scientific questions;
3. continuity with earlier rooted-descriptor logic;
4. a practical worked example that others can follow;
5. easier cross-analysis comparison of graph/evidence diagnostics.

## Recommended default conventions

Unless strong reasons emerge otherwise, the standard should adopt the following defaults:

- fixed family ordering across all plots;
- JS or symmetrised KL for overview heatmaps;
- directional KL only when asymmetry is scientifically relevant;
- consistent colour maps and scales across comparable figure types;
- rooted descriptor labels aligned with the terminology from Analyses 2 and 3.

## Out of scope

This analysis should **not**:

- optimise every visual detail for publication;
- redesign all previous figures retrospectively;
- replace substantive analysis with visualisation alone;
- introduce a large number of bespoke plots that are hard to reuse.

## Dependencies

This analysis is informed by:
- **Analysis 4-2**, which produces family-level divergence structure;
- **Analysis 4-3**, which produces parameter-grid diagnostics;
- earlier rooted-descriptor analyses in Analyses 2 and 3.

## Relationship to later work

The outcome of this analysis should become a standing standard for:
- future analysis documents;
- future stimulus screening;
- family-comparison summaries;
- pilot design figures.

## Recommended implementation order

1. identify the most useful KL-related figure patterns from earlier analyses;
2. define a small set of standard figure types;
3. specify required annotations and naming conventions;
4. build a worked example;
5. adopt the standard in subsequent analyses.

## Practical recommendation

Keep the standard compact. A small number of clear, reusable figure types is better than a large number of highly customised visualisations that will not scale across analyses.
