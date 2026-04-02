# Analysis-1 — 数值验证 · 刺激筛选 · 模型可辨认性

## 这个分析做了什么（回答了哪些 TODO 问题）

Analysis-1 是整个项目的数值地基，回答了三件事：

1. **Q1 — 结构利用能否在最小图集上产生可分离预测？** 是的。在 chain vs. cycle 两张最小示例图上，M₀（ρ=0）和 M_exact（ρ=1）的预测在 high evidence 下分离显著（Δp_R ≥ 0.08 阈值满足）。

2. **Q2 — 独立→有界→精确推断能否被实现为连续谱？** 是的。ρ 用 edge-energy decay 实现后，从 ρ=0 到 ρ=1 产生单调、可计算的预测谱，确认了 R1 技术实现的正确性（见 `analysis-1.tex` §2）。

3. **模型可辨认性：** 合成恢复实验结果为 100% 对角准确率，MAE(ρ̂) = 0.017，说明从行为数据中恢复 ρ 是切实可行的。

同时，Phase-1（equal-local, distinct-remote）和 Phase-2（Min-Degree vs. Min-Fill Fill-gap）刺激筛选管线也在本分析中建立，产生了可供后续实验直接使用的 90 个 master trials 和 6 个 balanced lists。

## 文件结构

```
analysis-1/
├── TODO.md           # 原始任务说明（见此文件了解当时的设计意图）
├── analysis-1.tex    # 完整 LaTeX 报告，编译方式见下
├── figures/          # (当前为空；analysis-1 无独立图表文件)
├── code/
│   ├── analysis-1.py                    # 主分析脚本
│   ├── analysis-1_execution_results.json   # 数值验证结果
│   ├── analysis-1_stimulus_library.json    # 筛选后的刺激库
│   ├── analysis-1_experiment_trials.json   # 90 个 master trials
│   ├── analysis-1_experiment_trials.csv
│   ├── analysis-1_balanced_lists.json      # 6 个 balanced participant lists
│   ├── analysis-1_balanced_lists.csv
│   └── analysis-1_model_recovery.json      # 合成模型恢复结果
└── README.md         # 本文件
```

## 如何运行代码

```bash
cd analysis-1/code
python3 analysis-1.py
# 所有输出写到 analysis-1/code/ 目录，文件名以 analysis-1_ 开头
```

## 如何读数据

- `analysis-1_execution_results.json` — 顶层 JSON，包含 local_equivalence_pair、stimulus_screening、model_recovery、experiment_exports 四个顶级 key。
- `analysis-1_stimulus_library.json` — 与 execution_results["stimulus_screening"] 相同内容的单独存档；phase1_pairs 是 equal-local 对，phase2_graphs 是有 Fill-gap 的图。
- `analysis-1_experiment_trials.{json,csv}` — 每行一个试次，字段包括 graph topology、evidence 分配、各模型预测、phase 标签。
- `analysis-1_balanced_lists.{json,csv}` — 6 个 participant lists，每个 15 个 trials，跨 list 做了 counterbalancing。
- `analysis-1_model_recovery.json` — 每个 synthetic participant 的 true ρ、recovered ρ、model_selection_accuracy。

## 学生怎么阅读

先读 `analysis-1.tex` 的 Part I（§1–§3）理解 ρ 的数学形式和 energy-decay 实现。然后读 Part II（§4）了解 Phase-1 和 Phase-2 刺激筛选标准的逻辑。Part III（§5）是模型可辨认性验证，直接回答"实验能不能做"这个问题。

关键概念入口：`Definitions and Notation Guide.md`（项目根目录）给出所有符号。`Design failures.md` 解释了为什么不能用 factor-scaling 实现 ρ（Failure 1）。
