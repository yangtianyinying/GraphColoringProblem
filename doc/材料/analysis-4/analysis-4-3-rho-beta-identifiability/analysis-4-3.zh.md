# Analysis 4-3：结构衰减与因子强度的参数可辨识性

## Question

Analysis 4-3 询问：真实图上的 attenuation 是否可与更弱的 pairwise coupling 区分。若 $\rho$ 只是吸收 $\beta_{\mathrm{edge}}$ 变化，则 $M_{\rho}$ 的结构解释不成立。

## Method

图模型背景与记号按标准处理，见 [Koller2009]。

本分析在 $\rho$ 与 $\beta$ 的联合网格上计算：
- panel-level divergences
- local identifiability scores
- diagnostic recovery panel
- synthetic noiseless/noisy recovery
- $\beta$ 优化后的 best-case cross-family matches

## Results

diagnostic recovery panel 保留 8 个高价值条件：  
`RG031 (high), RG100 (high), RG088 (high), RG087 (high), RG091 (high), RG111 (high), RG112 (high), RG114 (high)`。

在该 panel 上：
- noiseless exact-match rate = `1.0`（原则上可辨识）
- noisy synthetic responses 下 exact-match rate = `0.3`
- MAE：$\rho$ 为 `0.136587`，$\beta$ 为 `0.584921`

结论是：联合建模有必要，但 tradeoff 真实存在。

家族鲁棒性结果也关键：在 $\beta$ 优化后，attenuation 在精确端点可完全贴合 exact inference；但 attenuation vs star 的最佳匹配仍有 mean JS `0.027041`。说明结构改写对比比“图内细微 attenuation 对比”更稳健。

图示文件：
- `analysis-4-3_fig1_parameter_atlas.pdf`
- `analysis-4-3_fig2_recovery.pdf`

## Conclusions against the TODO

1. 在有针对性的 panel 上，$\rho$ 与 $\beta$ 在原则上可辨识。  
2. noisy 场景下存在真实 tradeoff，尤其体现在 $\beta$。  
3. 涉及 star rewrite 的家族级结论比 exact-vs-attenuation 的细微对比更稳健。  
4. 后续拟合应联合估计 $\rho$ 与 $\beta$，或限制在本分析识别的 diagnostic panel。  

## Bibliography

`\bibliographystyle{apalike}`  
`\bibliography{../../manuscript/library}`

