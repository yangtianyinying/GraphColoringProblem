# 2026-04-05 讨论记录（重写版）

## 1. 初始化设定

现在每一幅图的每个初始信念节点，都会从四类训练节点中随机选择：

- 高：$[0.9, 0.05, 0.05]$
- 中：$[0.7, 0.15, 0.15]$
- 低：$[0.5, 0.25, 0.25]$

与此前“$n-1$ 个初始化节点都属于同一等级（全中 / 全高 / 全低 / 全无）”不同，现在是每个节点独立随机。

考虑规模：$n \in \{5, 6\}$。

## 2. 组合空间规模

每幅图按前文给出的遍历方法，枚举所有可能结构与初始化组合：

- 对于 $n=5$，有 17 种可能结构（非同构、三色可解、全连接）。
- 对于 $n=6$，有 81 种可能结构（非同构、三色可解、全连接）。

总组合数为：

$$
17 \cdot 5 \cdot (4^4) + 81 \cdot 6 \cdot (5^4)
= 17 \cdot 5 \cdot 256 + 81 \cdot 6 \cdot 625
= 21760 + 303750
= 325510.
$$

## 3. 去重与筛选目标

在这 $647750$（不同结构 $\times$ 不同初始化）个候选上，按两条规则去重：

1. 去掉同构图（例如同一幅图选不同初始节点，但在拓扑上等价，通常来自图对称性）。
2. 初始化节点与其相邻节点的“最高权重颜色”不能相同（等级“无”节点不受该约束）。

在此基础上筛选指标最优的 30 幅图。

## 4. Family posterior 定义

设一个 trial 的全部非目标节点线索为 $e_c$，候选 family 集合为：

$$
\mathcal F=
\{M_{\mathrm{exact}},M_0,M_{\rho},M_{\rho,\beta},M_{\mathrm{star}},M_{\mathrm{cluster}}\}.
$$

对每个 family $f \in \mathcal F$，脚本计算目标节点 $X$ 的 posterior：

$$
p_f^{(c)}(y)=P_f(X=y\mid e_c),\qquad y\in\{R,G,B\}.
$$

统一写法：

$$
P_f(\mathbf x\mid e_c)
\propto
\left[\prod_{i\neq X} b_i(x_i)\right]
\left[\prod_{(u,v)} \exp\bigl(-w_{uv}^{(f)}\,\mathbf 1(x_u=x_v)\bigr)\right].
$$

其中：

- $b_i(x_i)$：节点 $i$ 的软线索；
- $w_{uv}^{(f)}$：family $f$ 对边 $(u,v)$ 赋予的有效约束强度；
- $\mathbf 1(x_u=x_v)$：相邻节点同色时的惩罚指示。

脚本对每个 trial 都使用精确枚举计算 posterior，因此当前 summary 中 family 预测是精确输出，而非近似值。

## 5. trial 评分公式

`analysis-5` 不直接依据单一指标选 trial，而是先为每个 condition 计算 3 个核心分数。

### (1) Family separation

对 condition $c$，定义：

$$
S_{\mathrm{sep}}(c)=\sum_{f<g} JS\bigl(p_f^{(c)},p_g^{(c)}\bigr),
$$

其中：

$$
KL(p\|q)=\sum_k p_k\log\frac{p_k}{q_k},
\qquad
JS(p,q)=\frac{1}{2}KL(p\|m)+\frac{1}{2}KL(q\|m),
$$

$$
m=\frac{p+q}{2}.
$$

直观上，$S_{\mathrm{sep}}$ 越大，说明不同 family 对同一 trial 的预测差异越大。

### (2) Argmax disagreement

定义：

$$
S_{\mathrm{arg}}(c)=\left|\left\{\arg\max_y p_f^{(c)}(y): f\in\mathcal F\right\}\right|.
$$

它衡量不同 family 是否会把“最可能颜色”判成不同答案。

### (3) Balance score

如果 posterior 过平（接近均匀分布），trial 往往信息不足；如果 posterior 过尖（接近 one-hot），不同 family 又可能趋同。因此加入 balance 指标。

先定义均匀分布：

$$
u=\left(\frac13,\frac13,\frac13\right)
$$

和 3 个点质量分布：

$$
\delta_R=(1,0,0),\qquad \delta_G=(0,1,0),\qquad \delta_B=(0,0,1).
$$

然后计算：

$$
B_1(c)=\frac{1}{|\mathcal F|}\sum_{f\in\mathcal F}JS\bigl(p_f^{(c)},u\bigr),
$$

$$
B_2(c)=\frac{1}{|\mathcal F|}\sum_{f\in\mathcal F}
\min\Bigl\{JS\bigl(p_f^{(c)},\delta_R\bigr),JS\bigl(p_f^{(c)},\delta_G\bigr),JS\bigl(p_f^{(c)},\delta_B\bigr)\Bigr\},
$$

$$
S_{\mathrm{bal}}(c)=\sqrt{B_1(c)\,B_2(c)}.
$$

该量鼓励 posterior 形状“既不是完全无信息，也不是退化为单点确定”。

### (4) 总评分

脚本先将上述 3 个指标做 z-score 标准化，再按权重组合：

$$
W(c)=z\bigl(S_{\mathrm{sep}}(c)\bigr)+0.6\,z\bigl(S_{\mathrm{arg}}(c)\bigr)+0.8\,z\bigl(S_{\mathrm{bal}}(c)\bigr).
$$

因此高分 trial 同时满足：家族间可分、argmax 有分歧、posterior 形状适于诊断。

## 6. 为什么不直接取全局 Top-30

若直接取分数最高的 30 个 trial，容易出现大量结构重复（只是强度模式不同），会让被试反复看到过于相似的图结构。

因此脚本采用 **mild diversity** 的贪心抽样，而非硬配额抽样：

$$
W_{\mathrm{adj}}(c)=
\frac{W(c)}{
\bigl(1+0.35\,n_{\mathrm{template}}(c)\bigr)
\bigl(1+0.20\,n_{\mathrm{occupancy}}(c)\bigr)
\bigl(1+0.15\,n_{\mathrm{graph}}(c)\bigr)
}.
$$

其中：

- $n_{\mathrm{template}}(c)$：该 major template 已入选次数；
- $n_{\mathrm{occupancy}}(c)$：该 occupancy profile 已入选次数；
- $n_{\mathrm{graph}}(c)$：同一 `graph_id` 已入选次数。

每一步都选当前 $W_{\mathrm{adj}}(c)$ 最大的 trial。直觉是：保留高分 trial 的同时，温和抑制单一结构模板“占满”整个实验面板。