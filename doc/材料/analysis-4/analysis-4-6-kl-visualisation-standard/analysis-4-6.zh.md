# Analysis 4-6：KL 可视化诊断的标准化

## Question

Analysis 4-6 将 family-separation 工作流整理为可复用的可视化标准。目标不是产出新的科学推断，而是让未来分析的报告更可复现、可比较。

## Method

图模型背景与记号按标准处理，见 [Koller2009]。

对 Analysis 4-2 与 4-3 的输出进行审计，并提炼成紧凑的图形规范。标准内容包括：
- figure type 列表
- mandatory 状态
- 必要标注
- 默认指标
- 文件命名规则
- worked example panel

## Results

mandatory 默认套件包含 4 种图：
- `condition_specific_family_divergence_heatmap`
- `target_belief_profile_panel`
- `global_family_confusion_summary`
- `rooted_descriptor_linkage_summary`

worked example 使用 `RG112`（high evidence），推荐面板堆栈为：
1) graph/evidence 可视化  
2) family divergence heatmap  
3) belief profile bars

图示文件：`analysis-4-6_fig1_worked_example_panel.pdf`  
图注含义：标准 condition-specific 可视化报告的完整示例。

## Conclusions against the TODO

1. 后续诊断现已具备紧凑、默认的图形套件。  
2. 每种图都被绑定到明确的科学问题。  
3. 保留 Analysis 3 的 D1/D2/D3 术语体系。  
4. worked example 已足以让合作者与学生复现目标风格。  

## Bibliography

`\bibliographystyle{apalike}`  
`\bibliography{../../manuscript/library}`

