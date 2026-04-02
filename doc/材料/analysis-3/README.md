# Analysis-3 — Rooted-shell 结构维度与 ρ-separability 的刺激设计分析

## 这个分析做了什么（回答了哪些 TODO 问题）

Analysis-3 将 analysis-2 的"图集 → 可分离"结论翻译为实验设计语言，回答了 TODO-3 提出的核心问题：

> **哪些 target-centred rooted structural dimensions 决定 ρ-agent family 是否数值可分离？**

四条成功标准全部满足：

- **S1：** Rooted descriptor framing（D1/D2/D3）比 raw node count 有更强的解释力。D3 class（remote structure）是 separability 的主要预测变量，远优于"5 节点 vs. 6 节点"。
- **S2：** D1（target degree）、D2（neighbour coupling）、D3（remote structure）三个维度均构造出了数值上有效的 matched comparison set。
- **S3：** 产生了 rooted stimulus taxonomy（32 个 main families, 98 个 raw classes）和 candidate stimulus set，可直接用于后续实验设计。
- **S4：** TikZ stimulus sketches 已生成，selected stimuli 的 winning evidence template 已直接可视化。

## 文件结构

```
analysis-3/
├── TODO.md               # 原始 TODO-3 任务说明
├── analysis-3.tex        # 完整 LaTeX 报告
├── figures/
│   ├── analysis-3_fig1_design_schematic.pdf           # 三维设计示意图（TikZ）
│   ├── analysis-3_fig2_rooted_stimulus_gallery.pdf    # Rooted motif 图集（TikZ）
│   ├── analysis-3_fig3_matched_comparisons.pdf        # D1/D2/D3 matched comparison（TikZ）
│   ├── analysis-3_fig4_selected_stimuli_with_evidence.pdf  # 选定刺激 + evidence 标注（TikZ）
│   └── analysis-3_fig5_descriptor_effects.pdf         # Descriptor separability 统计图
├── code/
│   ├── analysis-3.py                          # 主分析脚本
│   ├── analysis-3_rooted_motif_catalog.json   # 200 个 rooted graph motifs
│   ├── analysis-3_descriptor_results.json     # 每个 motif 的 descriptor + separability
│   ├── analysis-3_descriptor_results.csv
│   ├── analysis-3_selected_stimuli.json       # 候选实验刺激集
│   └── analysis-3_selected_stimuli.csv
└── README.md              # 本文件
```

## 如何运行代码

```bash
cd analysis-3/code
python3 analysis-3.py
# 数据输出到 analysis-3/code/，图表输出到 analysis-3/figures/
# 注意：TikZ 图表生成需要系统安装 pdflatex 和 tikz 包
```

## 如何读数据

- `analysis-3_rooted_motif_catalog.json` — 200 个 rooted motifs，每条记录含 adjacency、rooted_distances、D1/D2/D3 descriptor、adaptive evidence template。
- `analysis-3_descriptor_results.json` — 每个 motif 在各 evidence level 下的 separability 指标（kl_A0_to_A4、total_pairwise_kl 等），以及 D1/D2/D3 matched comparison sets。
- `analysis-3_descriptor_results.csv` — 同上，long-format，便于统计分析。列：graph_id, n_nodes, D1_target_degree, D2_neighbor_coupling, D3_remote_class, S2_count, e12, e22, evidence_level, kl_A0_to_A4, total_pairwise_kl, is_monotone 等。
- `analysis-3_selected_stimuli.json` — 最终候选刺激集，每条记录含 descriptor class、graph topology、winning evidence template（high/medium/low 三个版本）、separability 数值、matched comparison 归属。
- `analysis-3_selected_stimuli.csv` — 同上，列：graph_id, D1/D2/D3, S2_count, e12, e22, high_kl_A0_to_A4, selection_reasons, preferred_color_template。

## 学生怎么阅读

先读 `TODO.md` 的 §1（设计转向：为什么不用 node count）和 §2（三维 descriptor 的定义），理解 D1/D2/D3 框架的含义。然后看 `figures/analysis-3_fig1_design_schematic.pdf` 建立直觉。

读 `analysis-3.tex` 时建议顺序：§1 执行目标 → §2 方法（rooted 枚举和三维 descriptor）→ §3 matched comparison 结果 → §4 stimulus selection → §5 结论。

Fig 3（matched comparisons）是最重要的图：它直接展示当且仅当 D3 变化时 separability 如何改变。Fig 4 是实验实施的直接参考：选定刺激 + evidence 颜色标注。

前置阅读：`analysis-2/README.md`（理解为什么 adaptive conflicting evidence 是固定选择），`Definitions and Notation Guide.md`，`Design failures.md`。
