# Analysis 4-1：智能体分类与形式化模型空间

## Question

Analysis 4-1 关注：当项目不再局限于单一 attenuation 谱时，应该比较哪些候选家族模型。目标是在当前 bounded graph inference 框架中区分参数近似（parameter approximation）与结构近似（structural approximation）。

## Method

图模型背景与记号按标准处理，见 [Koller2009]。

本分析形式化了六个候选家族，并记录其内部图规则、因子规则、参数集合与心理学解释。最终比较集合为：

\[
M_{\mathrm{exact}},\; M_0,\; M_{\rho},\; M_{\rho,\beta},\; M_{\mathrm{star}},\; M_{\mathrm{cluster}}.
\]

此外，基于 Analysis 3 继承的 selected panel，做了一个 simulation-ready 的小规模检查，确认这些 canonical 原型并非“平凡等价”。

## Results

关键概念结论是：纯 local log-evidence heuristic 不是新家族。在标准 exponentiate-and-normalise 读出下，它与 $M_0$ 完全等价。

保留的六家族集合仍可计算，并在 selected panel 上已出现非零分离。例如：
- $M_0$ vs $M_{\mathrm{cluster}}$ 的平均 JS 为 `0.162905`
- $M_0$ vs $M_{\rho}$ 的平均 JS 为 `0.10859`

图示文件：`analysis-4-1_fig1_family_schematic.pdf`  
图注含义：展示精确推断、真实图上的 attenuation、目标中心 star 改写、局部 cluster 改写之间的概念区别。

## Conclusions against the TODO

1. 家族集合处于要求范围内，且 simulation-ready。  
2. 结构改写与参数变化可以清晰区分。  
3. 纯 local log-evidence heuristic 应并入 $M_0$，不应作为独立家族。  
4. 上述六家族是 Analysis 4-2 的推荐输入。  

## Bibliography

`\bibliographystyle{apalike}`  
`\bibliography{../../manuscript/library}`

