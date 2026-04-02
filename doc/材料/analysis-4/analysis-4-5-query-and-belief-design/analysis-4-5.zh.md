# Analysis 4-5：两阶段 query-plus-belief 任务是否提供更强行为约束

## Question

Analysis 4-5 询问：更丰富的行为范式能否提升模型区分力。被测候选范式是固定证据任务：被试先选择回答哪个节点，再报告该节点的 belief。

## Method

图模型背景与记号按标准处理，见 [Koller2009]。

基于 Analysis 4-2 的 reduced panel 构建 partial-evidence 版本。每个家族先在自身 posterior 下最大化确定性来选目标节点，再在该节点上给出 belief 报告。比较三种设计：
- forced-target belief only
- selection only
- selection-plus-belief（联合设计）

## Results

平均 pairwise family separation：
- belief-only: `0.003211`
- selection-only: `0.030576`
- combined design: `0.054955`

即联合设计提供了第二个诊断通道，相比 forced-target baseline 显著提高平均分离度。

但 recovery 结果更谨慎：在当前简单 synthetic-noise 模型下，mean recovery diagonal 在 belief-only 下高于 combined design。说明两阶段任务作为定向扩展有前景，但尚不足以直接完全替代。

图示文件：`analysis-4-5_fig2_design_comparison.pdf`  
图注含义：三种行为设计下平均分离度与 synthetic recovery 的比较。

## Conclusions against the TODO

1. 在 partial-evidence panel 上，selection 行为具有家族诊断性。  
2. 联合设计相对 belief-only 提高了平均 pairwise family separation。  
3. 固定证据下“先选节点再报 belief”是当前最干净的 richer extension。  
4. 现有证据支持把它作为 forced-target trials 的补充，而非立即替代。  

## Bibliography

`\bibliographystyle{apalike}`  
`\bibliography{../../manuscript/library}`

