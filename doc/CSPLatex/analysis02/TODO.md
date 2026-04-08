# TODO

## 假设

### 统一记号

设目标节点为 `X`，节点 `v` 到目标节点的距离为 `d(v, X)`。对任意一条边 `(u, v)`，定义它相对于目标节点的 shell 深度为：

$$
s(u,v)=\min\{d(u,X),d(v,X)\}.
$$

所有 family 的差别，都体现在它们怎样给边赋权 `w_{uv}^{(f)}`。边权越大，表示该 family 认为这条边上的约束越重要。

### `M_exact`：完整使用真实图结构

这个 family 认为图上的全部真实边都同样重要：

$$
w_{uv}^{(\mathrm{exact})}=
\begin{cases}
\beta, & (u,v)\in E,\\
0, & (u,v)\notin E,
\end{cases}
\qquad \beta=4.0.
$$

直觉上，它是“看完整张图”的基准模型。

### `M_0`：只看目标节点的局部邻域

这个 family 只保留直接接到目标节点 `X` 的边：

$$
w_{uv}^{(0)}=\beta\,0^{s(u,v)}.
$$

由于只有 `s(u,v)=0` 时权重不为 0，它等价于：只看 target 与一环邻居之间的局部约束，忽略更远的结构。

### `M_rho`：远端结构会逐层衰减

这个 family 假设远端结构仍然有作用，但会随着离目标越来越远而衰减：

$$
w_{uv}^{(\rho)}=\beta\,\rho^{s(u,v)},\qquad \rho=0.35,\ \beta=4.0.
$$

因此，一环边最强，二环边更弱，三环及更远边更弱。

### `M_rho,beta`：结构衰减与整体强度都可调整

这个 family 使用和 `M_rho` 同样的衰减形式，但整体边强更小：

$$
w_{uv}^{(\rho,\beta)}=\beta\,\rho^{s(u,v)},\qquad \rho=0.35,\ \beta=2.5.
$$

它要表达的不是“结构规则改变了”，而是：同样的衰减机制下，整体约束强度可能不同。  
这就是为什么它最容易和 `M_rho` 混淆：两者在结构上很像，只是强弱不同。

### `M_star`：把整张图重写成 target-centered star

这个 family 不保留真实图的全部边，而是假设所有信息都以目标节点为中心整合。它给目标节点与任意其他节点之间建立一个等效连接：

$$
w_{Xu}^{(\mathrm{star})}=\frac{\beta}{\max\{1,d(u,X)\}},\qquad \beta=4.0,
$$

其余非 `target-node` 边忽略不计。

直觉上，它像是在说：远端信息不是沿真实图逐跳传播，而是被压缩成“它对目标节点的直接影响”。

### `M_cluster`：保留 target 周围的局部簇结构

这个 family 重点保留 `X`、`S1`、`S2` 构成的局部结构。设：

$$
K=\{X\}\cup S_1\cup S_2.
$$

那么它会：

1. 保留所有位于 `K` 内的真实边，权重为 `beta=4.0`；
2. 如果两个一环节点共享同一个二环邻居，则在这两个一环节点之间额外加一条 cluster 式连接。

直觉上，它认为：决定目标节点判断的不是全图，也不是纯局部一环，而是 target 周围的一个局部簇结构。

## 拟合

### 数据与输入

- 使用 `analysis01` 的 `top30` 数据，共 30 个 trial。
- 候选 family 集合：
  - `M_exact`
  - `M_0`
  - `M_rho`
  - `M_rho,beta`
  - `M_star`
  - `M_cluster`
- 对每个 trial `t` 和 family `f`，已知目标节点颜色后验分布 `p_f^{(t)}(y)`，其中 `y in {R, G, B}`。

### Categorical 拟合公式

对一个被试（这里是 synthetic participant）在 30 个 trial 的离散反应 `r_t`，定义 family `f` 的总对数似然：

$$
\mathcal L(f)=\sum_{t=1}^{30}\log p_f^{(t)}(r_t).
$$

拟合输出 family 为：

$$
\hat f=\arg\max_{f\in\mathcal F}\mathcal L(f).
$$

### Confusion Matrix 的生成流程

对每个真实 family `f_true`，执行以下步骤：

1. 固定 `f_true` 为数据生成模型；
2. 在 heterogeneous top-30 的 30 个 trial 上，用 `p_{f_true}^{(t)}` 采样一个 synthetic participant 的离散反应序列；
3. 对该序列计算全部候选 family 的 `\mathcal L(f)`；
4. 取最大值对应的 `\hat f` 作为“拟合出的 family”；
5. 重复多次（建议 `N=200` 次 / 每个真实 family）；
6. 统计频率：

$$
C_{ij}=P(\hat f=j\mid f_{\text{true}}=i).
$$

其中 `i` 是行（真实 family），`j` 是列（拟合 family）。

### 结果表述规范

- 每一行加总应约等于 `1.0`（浮点误差允许极小偏差）。
- 对角线 `C_{ii}` 表示识别正确率；越高越好。
- 非对角线较大的位置表示 family 间混淆边界。

建议同时汇报：

- `diagonal mean = mean_i C_{ii}`
- `mean log-likelihood gap`（第一名与第二名 family 的平均差值）


### 交付清单

- [ ] 生成 `6x6` confusion matrix（行：true，列：fit）
- [ ] 给出 `diagonal mean`
- [ ] 给出 `mean log-likelihood gap`
- [ ] 标注主要混淆对（例如 `M_rho` vs `M_rho,beta`）
- [ ] 可视化导出图片
