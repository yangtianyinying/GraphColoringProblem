# AGENTS.md — AI agent workflow guide

> **Read this file completely before touching anything else.**
> This file explains the folder structure, shared resources, workflow chain,
> and hard rules. Violating the rules wastes work and breaks reproducibility.

---

## 1. Project layout

Every completed analysis lives in its own numbered folder:

```
project-root/
│
├── AGENTS.md                          # This file. Keep current.
├── library.bib                        # Shared bibliography for all LaTeX files.
├── TeX_definitions.sty                # Shared LaTeX macros. Import in all .tex files.
├── Definitions and Notation Guide.md  # All symbols and notation. Do not deviate.
├── Design failures.md                 # Known design traps + resolution status.
│
├── manuscript/                        # Active LaTeX writing (proposals, paper drafts)
│
├── analysis-1/
│   ├── TODO.md                        # Task specification (agreed before coding)
│   ├── analysis-1.tex                 # Standalone compilable LaTeX report
│   ├── README.md                      # Plain-language summary
│   ├── figures/                       # All figures for this analysis
│   └── code/
│       ├── analysis-1.py              # Analysis script
│       └── data/                      # All outputs written by analysis-1.py
│
├── analysis-2/                        # Same structure for every subsequent analysis
│   ├── TODO.md
│   ├── analysis-2.tex
│   ├── README.md
│   ├── figures/
│   └── code/
│       ├── analysis-2.py
│       └── data/
│
├── analysis-N/                        # Next analysis follows same pattern
│   └── ...
│
├── Core-References/                   # Key papers (do not edit)
├── Method-textbooks/                  # Reference texts (do not edit)
├── old-drafts/                        # Archived manuscript drafts (do not edit)
└── old-proposals/                     # Archived earlier proposals (do not edit)
```

---

## 2. How to orient yourself before starting a new task

Work through these steps in order. Do not skip any.

**Step 1 — Read the new TODO carefully.**
Identify the scientific question, the expected outputs, and any hard constraints.
Do not begin writing code or LaTeX until this is clear.

**Step 2 — Read all previous `README.md` files** (from `analysis-1/README.md` upward)
to understand what has already been established, what data already exists, and what
conclusions are fixed.

**Step 3 — Skim the most recent `analysis-N.tex`** to understand the current
experimental design, notation, and model family. Note which design decisions are
fixed and which are open.

**Step 4 — Skim the most recent `analysis-N.py`** and its `code/data/` outputs to
understand what data already exists and how it was generated. Do not recompute
things that already exist.

**Step 5 — Read `Design failures.md`** to know which design choices have already
been made and why alternatives were rejected.

**Step 6 — Read `Definitions and Notation Guide.md`** to confirm the symbols you
will use. Do not introduce new notation without adding it to the Guide first.

**Step 7 — Read `Core-References/`** annotated bibliography to know what the key
papers have already established. Check `old-proposals/` and `old-drafts/` only
if you need to understand why earlier directions were abandoned — do not edit them.

---

## 3. The analysis chain

Every analysis follows a strict numbered chain. **Do not break it.**

```
analysis-N/TODO.md
    └── analysis-N/code/analysis-N.py
            └── analysis-N/code/data/        (all data outputs)
                    └── analysis-N/figures/  (all figures)
                            └── analysis-N/analysis-N.tex
                                    └── analysis-N/README.md
```

| File | Rule |
|------|------|
| `TODO.md` | Written and agreed with PI *before* any code is written. Contains output targets and success criteria. |
| `analysis-N.py` | One script per analysis. Writes all data outputs to `code/data/` and all figures to `figures/`. |
| `code/data/` | All generated files (CSV, JSON, LaTeX table fragments). Nothing outside `analysis-N/`. |
| `figures/` | All figures named `analysis-N_figX_description.ext`. |
| `analysis-N.tex` | Self-contained compilable report. Documents method, results, figures, and conclusions. Conclusions must state whether each success criterion from the TODO was met. |
| `README.md` | Plain-language summary: what was done, what was found, how to run the code, how to read the data, suggested reading path for a student. |

When starting a new analysis: find the highest existing N, use N+1.

---

## 4. What each file should contain

### `TODO.md`
The task specification agreed with the PI *before* any code is written.
Contains: scientific question, success criteria, expected outputs, and any hard constraints.

### `analysis-N.tex`
A self-contained LaTeX report documenting:
- the scientific question and motivation,
- the method (design, model, stimuli),
- the results (tables, figures, interpretation),
- a conclusions section stating whether the TODO success criteria were met.

All figures referenced here must live in `analysis-N/figures/`. Generated table
fragments produced by `analysis-N.py` are `\input`-ted from `analysis-N/code/data/`.

### `README.md`
A plain-language summary for students and collaborators. It must answer:
- What scientific question did this analysis address?
- How do the TODO criteria map to what was actually done?
- How do you run the code and what do the outputs mean?
- Which columns / variables in the CSV / JSON outputs matter, and why?
- What should a student read first, and in what order?

### `figures/`
All figures for this analysis — TikZ diagrams, matplotlib PDFs, PNG task diagrams.
Named `analysis-N_figX_description.ext`.

### `code/analysis-N.py`
One script per analysis. Writes **all** outputs to `code/data/`. No outputs
should be written outside the `analysis-N/` subfolder.

### `code/data/`
All files generated by `analysis-N.py`: CSVs, JSONs, LaTeX table fragments,
codebooks, session schedules, etc.

---

## 5. Build instructions

**Compile an analysis report:**
```bash
cd analysis-N
pdflatex -interaction=nonstopmode -halt-on-error analysis-N.tex
bibtex analysis-N
pdflatex -interaction=nonstopmode analysis-N.tex
pdflatex -interaction=nonstopmode analysis-N.tex   # third pass to resolve all refs
```

**Run an analysis script:**
```bash
cd analysis-N/code
python3 analysis-N.py
# All outputs are written to analysis-N/code/data/
```

**Compile slides (if present):**
```bash
cd analysis-N
pdflatex -interaction=nonstopmode slides.tex
```

---

## 6. Path conventions in scripts

All scripts use `Path(__file__).resolve().parent` as the base for output paths,
so they run correctly from any working directory:

```python
from pathlib import Path

code_dir    = Path(__file__).resolve().parent          # analysis-N/code/
data_dir    = code_dir / "data"                        # analysis-N/code/data/
figures_dir = code_dir.parent / "figures"              # analysis-N/figures/

output_path = data_dir / "analysis-N_something.json"   # data output
figure_path = figures_dir / "analysis-N_fig1_name.pdf" # figure output
```

Do not hardcode absolute paths or assume a specific working directory.

---

## 7. LaTeX conventions

- `\usepackage{TeX_definitions}` must appear in every new `.tex` file. Copy the
  `.sty` file from the project root into the `analysis-N/` folder at creation time.
- Reference the shared bibliography: `\bibliography{../library}`.
- Use `\graphicspath{{figures/}}` to resolve figures in `analysis-N.tex`.
- Generated table fragments from `code/data/` are included with `\input`:
  `\input{code/data/some_table.tex}`.
- Use TikZ for structural diagrams and model schematics.
- Use matplotlib/seaborn for data figures, exported as PDF.
- Reuse `tikzset` styles from the earliest analysis that defines them — avoid
  redefining across files.

---

## 8. Project-specific scientific constraints

> **This section must be filled in at project setup and kept current.**
> The entries below are the hard rules for *this* project. Violating them
> produces invalid or unidentifiable results. See `Design failures.md` for
> the full history of each decision.

<!-- Replace the placeholder entries below with the actual constraints for this project. -->

| ID | Constraint | Rationale |
|----|-----------|-----------|
| R1 | *(describe constraint)* | *(why it is non-negotiable)* |
| R2 | *(describe constraint)* | *(why it is non-negotiable)* |

---

## 9. Notation rules

All notation is fixed in `Definitions and Notation Guide.md`. When writing code
or LaTeX:

- Do not rename any symbol that is already defined in the Guide.
- If a new symbol is genuinely needed, add it to the Guide *first*, then use it.
- Keep variable names in code consistent with the notation in the Guide.

---

## 10. What counts as "done"

An analysis is complete only when all of the following are true:

- `code/analysis-N.py` runs without errors and produces all expected output files
  in `code/data/`.
- `analysis-N.tex` compiles cleanly and contains: method, numerical results,
  figures, and a conclusions section that states whether each success criterion
  from `TODO.md` was met.
- `figures/` contains all figures referenced in the `.tex` file.
- `README.md` is written and answers the five questions in §4.
- `AGENTS.md` has been updated: add the new analysis folder to the layout in §1.

---

## 11. When to stop and ask the PI

Stop and ask before proceeding if:

- The TODO requires a design choice and you are uncertain which option is
  scientifically preferable.
- A simulation or analysis result is qualitatively inconsistent with what the
  TODO predicted (e.g., model recovery falls below the expected threshold).
- You need a model, parameter, or design element not covered by the current
  constraints in §8.
- You want to change any value marked as fixed in the TODO or in a previous
  `analysis-N.tex`.
- The TODO is ambiguous in a way that would change the scientific conclusion.
- You find a conflict between the TODO and the conclusions of a prior analysis.

---

## 12. What not to do

| Do not | Why |
|--------|-----|
| Write code before the TODO is agreed | The TODO defines the success criteria |
| Put data outputs outside `analysis-N/code/data/` | Breaks the chain; clutters the project |
| Hardcode absolute paths in scripts | Scripts must run from any working directory (§6) |
| Skip reading previous `README.md` files | You will duplicate or contradict prior work |
| Start a new analysis without checking the highest existing N | Creates a numbering conflict |
| Introduce new notation without updating `Definitions and Notation Guide.md` | Creates silent inconsistencies |
| Violate any constraint in §8 | Produces invalid or unidentifiable results |
| Edit `old-drafts/` or `old-proposals/` | They are archives |
