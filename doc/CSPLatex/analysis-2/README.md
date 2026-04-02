# Analysis-2 — ρ-agent 模拟研究

## 这个分析做了什么（回答了哪些 TODO 问题）

Analysis-2 将 analysis-1 确认的 ρ 实现扩展为完整的模拟研究，回答了 TODO-2 提出的两个核心问题：

1. **Q1 — "结构利用"能否在最小图集上产生可分离的数值预测？** 是的。17 张 5 节点连通 3-colorable 图中有 16 张在 high evidence 下满足 D_KL(b̃₀ ‖ b̃₁) > 0.01，无需扩展到 6 节点。

2. **Q2 — ρ 连续谱能否在完整刺激集上保持单调、可解释？** 是的。ρ ∈ {0, 0.25, 0.5, 0.75, 1} 在所有图上均单调。

额外贡献：**evidence 策略比较**。Uniform、simple-conflicting、adaptive-conflicting 三种策略下，adaptive conflicting 的总 pairwise separability 比 uniform 高 3.74 倍，因此被确定为后续实验的标准 evidence 设计。

**equal-local 判别逻辑**也在本分析中获得完整数值验证：存在 graph pair 满足 b̃₀^A = b̃₀^B 但 b̃₁^A ≠ b̃₁^B，且分离量非常大。

## 文件结构

```
analysis-2/
├── TODO.md               # 原始 TODO-2 任务说明
├── analysis-2.tex        # 完整 LaTeX 报告
├── figures/
│   ├── analysis-2_fig1_separability_panel.pdf   # 5 个 ρ-agent 预测分离面板
│   ├── analysis-2_fig2_entropy_spectrum.pdf      # 熵谱（H 随 ρ 变化）
│   ├── analysis-2_fig3_kl_matrices.pdf           # 5×5 KL 矩阵
│   └── analysis-2_fig4_equal_local_pair.pdf      # equal-local 对示例
├── code/
│   ├── analysis-2.py                        # 主分析脚本（图枚举 + agent + 图表）
│   ├── analysis-2_simulation_results.json   # 全量模拟结果（long-format）
│   ├── analysis-2_simulation_results.csv
│   ├── analysis-2_graph_catalog.json        # 17 张图的 rooted catalog
│   ├── analysis-2_strategy_comparison.json  # 三种 evidence 策略比较
│   └── analysis-2_summary.json             # 成功标准检验摘要
└── README.md              # 本文件
```

## 如何运行代码

```bash
cd analysis-2/code
python3 analysis-2.py
# 数据输出到 analysis-2/code/，图表输出到 analysis-2/figures/
```

## 如何读数据

- `analysis-2_simulation_results.json` — 顶层 key 为 graphs、long_results、strategy_comparison、equal_local_pair、success_criteria 等。long_results 是每条记录对应一个 (graph_id, evidence_level, agent_rho) 组合。
- `analysis-2_simulation_results.csv` — 同 long_results，列：graph_id, evidence_level, agent, agent_rho, p_R, p_G, p_B, entropy, kl_to_A0, kl_to_A4, preferred_color_template, is_tree, edge_count。
- `analysis-2_graph_catalog.json` — 每张图的 adjacency、rooted 距离、descriptors（为 analysis-3 铺垫）。
- `analysis-2_strategy_comparison.json` — uniform vs. conflicting vs. adaptive 三策略的 pairwise separability 汇总，直接给出"winning strategy"字段。
- `analysis-2_summary.json` — 三条成功标准（Q1/Q2/equal-local）的 pass/fail 判断和数值证据。

## 学生怎么阅读

先读 `TODO.md` 理解任务背景和成功标准的精确定义，然后读 `analysis-2.tex` §1 了解图枚举和 agent 设计，§2 看 evidence 策略比较，§3–§4 看模拟结果与图表，§5 结论。

图表的阅读顺序：Fig 1 → Fig 3 → Fig 4 → Fig 2。Fig 1 最直接地展示 5 个 agent 是否可分离；Fig 3 的 KL 矩阵揭示哪对 agent 最难区分；Fig 4 是最重要的理论示例（equal-local 判别逻辑）；Fig 2 展示推断范围如何降低不确定性。

前置阅读：`analysis-1/analysis-1.tex`（ρ 的数学实现），`Definitions and Notation Guide.md`（符号），`Design failures.md`（为什么不用 factor-scaling 和 BP）。
