# Analysis 4-7：超越 map-colouring

## Question

Analysis 4-7 询问：当前研究方案能在多大程度上推广到 repulsive map-colouring 之外。若真实科学目标是理解人类在图上的结构近似，那么任务域本身会影响结论外推。

## Method

图模型背景与记号按标准处理，见 [Koller2009]。

将 map-colouring 与 4 个替代图推断任务域比较，并按以下维度打分：
- 理论价值
- 实验简洁性
- 与当前范式连续性
- 预期家族可分离性

同时记录 Analysis 4 家族 taxonomy 在各任务域上的迁移性。

## Results

下一优先任务域是 `attractive_graph_labelling`。其主要优势是：将局部语义从 repulsive 翻转为 attractive，同时保留了当前图任务接口的大部分结构。

加权优先级前三为：
- `attractive_graph_labelling`：`4.75`
- `map_colouring`：`4.1`
- `social_consensus`：`4.0`

图示文件：`analysis-4-7_fig1_domain_comparison.pdf`  
图注含义：超越 map-colouring 的候选任务域比较。

## Conclusions against the TODO

1. map-colouring 仍是强有力首个 testbed，但结论应限定在 repulsive 局部耦合范围。  
2. attractive graph labelling 是最干净的第一扩展方向。  
3. 当前家族 taxonomy 可较好迁移到 attractive 与 consensus 风格任务，尤其是 $M_{\rho}$、$M_{\mathrm{star}}$、$M_{\mathrm{cluster}}$。  
4. mixed-sign 任务科学上有价值，但应在完成更简单的 attractive 扩展后再推进。  

## Bibliography

`\bibliographystyle{apalike}`  
`\bibliography{../../manuscript/library}`

