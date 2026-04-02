# Analysis 4 series: beyond rho

## Overview

Analyses 1–3 established that bounded probabilistic inference on graph-structured tasks can be meaningfully described by a family of approximate agents indexed by a structural attenuation parameter \( \rho \), and that rooted-graph stimulus design can produce diagnostically useful separations between exact and approximate inference regimes.

The next step is to move beyond a single approximation family. In particular, we now want to ask whether participants' behaviour is better characterised not merely by weaker propagation on the true graph, but by qualitatively different **internal structural approximations**.

This motivates **Analysis 4**, which is organised as a series of linked sub-analyses.

## Core scientific question

When people perform bounded probabilistic inference on graph-structured tasks, are they best described as:

1. carrying out inference on the correct graph but with attenuated long-range influence;
2. rewriting the graph into a simpler internal structure before inference;
3. using local summary heuristics that only mimic probabilistic inference in restricted cases;
4. or combining these forms of approximation with additional parameter uncertainty over factor strength?

In short:

> Is bounded human inference best described by a continuous approximation on the true graph, or by a change in the graph that is internally represented?

## Why this series is needed now

Analyses 1–3 support the usefulness of rooted local graph descriptors and KL-based stimulus diagnostics, but they leave open several important possibilities:

- the current \( \rho \)-family may be too narrow;
- some candidate heuristics may be mathematically equivalent to \( \rho = 0 \) rather than genuinely new agent types;
- variation attributed to structural approximation may instead reflect differences in factor strength \( \beta \);
- the current task format may not impose enough behavioural constraints to distinguish between structurally distinct agents.

Analysis 4 addresses these issues systematically.

## Structure of the series

### 4-1. Agent taxonomy and formal model space

Define a unified taxonomy of candidate agent families, including:

- exact inference agents;
- fixed-graph attenuation agents;
- structure-rewrite agents;
- local heuristic agents.

This analysis provides the formal modelling language used by the rest of the series.

### 4-2. Family separability on the existing stimulus library

Evaluate whether the current rooted-shell graph and evidence library can already discriminate these candidate families.

Main outputs:

- family-by-family KL heatmaps;
- confusion matrices;
- ranked diagnostic graph/evidence conditions.

### 4-3. Parameter identifiability: \( \rho \) versus \( \beta \)

Test whether structural attenuation and factor-strength variation are distinguishable in principle on the current task family.

Main outputs:

- recovery analyses;
- \( \rho \)-\( \beta \) tradeoff plots;
- recommendations for future fitting.

### 4-4. Local heuristic equivalence

Formalise the proposed direct-neighbour log-evidence heuristic and determine whether it is equivalent to the current \( \rho = 0 \) agent, or whether it defines a genuinely distinct family.

### 4-5. Selection plus belief as a richer behavioural paradigm

Evaluate whether a two-stage task format—choosing a target node and then reporting belief—provides stronger model discrimination than forced-target or simple free-query designs.

### 4-6. Visual diagnostic standardisation

Establish a standard visual output suite for future graph/evidence analyses, including KL heatmaps and descriptor-linked summaries.

### 4-7. Beyond map-colouring

Discuss whether answering the broader question of human structural approximation requires moving beyond anti-coordination tasks such as map-colouring to additional task domains with attractive local couplings.

## Working model families

The series will initially focus on a minimal but theoretically meaningful set of candidate agent families:

- \( M_{\mathrm{exact}} \): exact inference on the true graph;
- \( M_0 \): strictly local inference / nearest-neighbour-only approximation;
- \( M_{\rho} \): fixed-graph attenuation family;
- \( M_{\rho,\beta} \): attenuation plus factor-strength variation;
- \( M_{\mathrm{star}} \): target-centred star-network approximation;
- \( M_{\mathrm{cluster}} \): local cluster / clique / junction-lite approximation.

Additional families may be added later only if they are theoretically distinct and experimentally identifiable.

## General principles for the series

Across all sub-analyses, the following principles should hold:

1. **Do not multiply model families unnecessarily.**
   A candidate family should only be retained if it is formally distinct, psychologically interpretable, and not obviously reducible to an existing family.

2. **All proposed family differences should be tested on behaviourally relevant outputs.**
   The key object of comparison remains the predicted belief over target node states.

3. **Visual diagnostics should be standardised.**
   Any new graph/evidence condition considered for future experiments should ideally come with KL-based family separation visualisation.

4. **The existing rooted descriptor framework should be reused whenever possible.**
   New model families should be related back to the D1/D2/D3 logic already developed in earlier analyses.

## Expected outcomes of Analysis 4

By the end of the Analysis 4 series, we aim to have:

- a coherent taxonomy of bounded-inference agent families;
- a clearer view of which families are distinguishable on current tasks;
- an assessment of whether \( \beta \) must be explicitly modelled;
- a decision on whether the local log-evidence heuristic is genuinely new;
- recommendations for future experimental designs and future task domains.

## Relationship to previous analyses

- **Analysis 1** established the core bounded-inference framing.
- **Analysis 2** showed that rooted stimulus dimensions and KL separability can guide diagnostic design.
- **Analysis 3** linked discriminability to rooted graph structure more explicitly.

**Analysis 4** generalises the modelling space itself: it asks not only *how much* people approximate, but *what kind* of approximation they may be using.

## Recommended execution order

The sub-analyses in Analysis 4 are logically related, but not all of them need to be completed strictly sequentially.

A recommended execution order is:

1. **4-1 Agent taxonomy and formal model space**  
   This should come first, because it defines the candidate family set and the formal language used throughout the rest of the series.

2. **4-2 Family separability on the existing stimulus library**  
   Once the core family set is defined, the next priority is to determine whether the current graph/evidence library can already discriminate these families.

3. **4-4 Local heuristic equivalence**  
   This can proceed in parallel with late-stage work on 4-2, but should ideally be completed early so that redundant heuristics are not unnecessarily carried forward as separate families.

4. **4-3 Parameter identifiability: \( \rho \) versus \( \beta \)**  
   After the main family-level separability picture is clear, the next step is to determine whether structural attenuation can be distinguished from factor-strength variation.

5. **4-5 Selection plus belief as a richer behavioural paradigm**  
   This should be informed by the results of 4-2 and 4-3. If current family separability or parameter identifiability is weak, this analysis becomes especially important.

6. **4-6 Visual diagnostic standardisation**  
   This can be developed partly in parallel with 4-2 and 4-3, but it is most useful once a stable family-comparison workflow is in place.

7. **4-7 Beyond map-colouring**  
   This is the most forward-looking sub-analysis and does not need to be completed before the others. It is best treated as a strategic extension of the programme once the current task family has been analysed more fully.

### Parallelisation guidance

The following parallel structure is recommended where useful:

- **Primary track:** 4-1 → 4-2 → 4-3  
- **Supporting track:** 4-4 can run alongside 4-2  
- **Design track:** 4-5 can begin once 4-2 gives a first picture of family separability  
- **Standardisation track:** 4-6 can be developed gradually as figures emerge from 4-2 and 4-3  
- **Outlook track:** 4-7 can be postponed until the main model-space questions are clearer

### Minimal core path

If time is limited, the minimum high-value path through Analysis 4 is:

1. **4-1**
2. **4-2**
3. **4-4**
4. **4-3**

These four analyses are sufficient to establish:
- the candidate model space,
- whether the current stimulus library separates it,
- whether one proposed heuristic is actually redundant,
- and whether \( \rho \) remains interpretable once \( \beta \) is allowed to vary.