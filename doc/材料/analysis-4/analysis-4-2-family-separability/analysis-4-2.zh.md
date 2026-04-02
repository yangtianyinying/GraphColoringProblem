# Analysis 4-2：现有刺激库上的家族可分离性

## Question

Analysis 4-2 询问：继承自 Analysis 2 与 Analysis 3 的 rooted-shell 库，是否已经能分离 Analysis 4-1 定义的候选家族。比较目标仍是被查询节点上的家族特异 belief。

## Method

图模型背景与记号按标准处理，见 [Koller2009]。

在 `600` 个 rooted graph/evidence 条件上评估六个 canonical 家族。每个条件计算：
- family posteriors
- pairwise Jensen--Shannon divergences
- noisy synthetic recovery matrix
- descriptor-conditioned summaries
- reduced stimulus panel

## Results

完整库呈现清晰层级：
- 最强平均对比：$M_{\mathrm{exact}}$ vs $M_{\mathrm{star}}$，mean JS `0.113605`
- 次强：$M_{\mathrm{star}}$ vs $M_{\mathrm{cluster}}$，mean JS `0.10413`
- 相比之下，$M_{\rho}$ 与 $M_{\mathrm{exact}}$ 很接近，mean JS `0.009751`

这表明：当前任务家族更擅长区分“结构改写 vs 精确推断”，而不擅长隔离“真实图上细微 attenuation”。

reduced panel 保留 6 个高价值条件：  
`RG119 (high), RG112 (high), RG121 (high), RG114 (high), RG036 (high), RG100 (high)`。  
这些条件覆盖 3 个 D3 class，为后续 identifiability 和 design 分析提供基础。

图示文件：
- `analysis-4-2_fig1_condition_panels.pdf`
- `analysis-4-2_fig2_global_confusion.pdf`

## Conclusions against the TODO

1. 当前 rooted 库已能强分离多组跨家族对比，尤其含 $M_{\mathrm{star}}$ 的对比。  
2. D3-rich remote structure 对家族级对比特别有诊断性。  
3. 已得到可用于后续行为实验的紧凑 reduced panel。  
4. $M_{\rho}$ 与 $M_{\mathrm{exact}}$ 的弱 canonical separation 推动 Analysis 4-3，并可能需要更丰富任务设计。  

## Bibliography

`\bibliographystyle{apalike}`  
`\bibliography{../../manuscript/library}`

