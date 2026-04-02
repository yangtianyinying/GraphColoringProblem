# Analysis 4-4：local log-evidence heuristic 是否真是新家族

## Question

Analysis 4-4 询问：提出的 local log-evidence heuristic 是否定义了新智能体家族，还是仅仅复述了项目中已有的 shell-0 local model。

## Method

图模型背景与记号按标准处理，见 [Koller2009]。

将该 heuristic 形式化为：直接邻居 log message 求和，再 exponentiation + normalisation。  
然后在完整 rooted 库上将其输出与 $M_0$ 对比，并额外模拟两种“刻意非等价”变体：
- neighbour-specific weighting
- score clipping

## Results

数值结论非常明确：
- pure heuristic 与 $M_0$ 的最大绝对差 = `0.0`
- pure heuristic 到 $M_0$ 的 mean JS = `0.0`

按构造，weighted 与 clipped 变体会偏离 $M_0$：
- weighted 变体 mean JS = `0.0114248243`
- clipped 变体 mean JS = `0.014439751`

图示文件：`analysis-4-4_fig1_equivalence_check.pdf`  
图注含义：pure heuristic 与 $M_0$ 完全重合，而失真变体出现可见偏离。

## Conclusions against the TODO

1. 该 heuristic 现在有了精确数学表述。  
2. 在标准归一化读出下，它与 $M_0$ 完全等价。  
3. 只有加权、截断或响应失真版本才构成真正不同模型。  
4. pure heuristic 应从核心家族集中移除，而非作为第七个推断家族。  

## Bibliography

`\bibliographystyle{apalike}`  
`\bibliography{../../manuscript/library}`

