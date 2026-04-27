质量向量的计算可分为三个步骤。第一步，对每个评审主体在三个维度上返回的排序结果提取策略 $\pi$ 的秩 $r_{\delta}^{(h)}(\pi)$；第二步，将秩线性映射到区间 $[0,1]$，得到单个评审主体在维度 $\delta$ 上的标准化得分 $s_{\delta}^{(h)}(\pi)$，其中得分越高表示该策略在该维度上的相对质量越好；第三步，对所有评审主体的标准化得分取平均，得到共识得分，并据此组成策略的三维质量向量 $q(\pi)$。


\begin{flatdefinition}{质量向量函数}\label{def:ranking}
设 $\mathcal{H}$ 为评审主体集合，$h\in\mathcal{H}$ 为参与独立评审的大语言模型配置，$n_v=|\Pi_v|$ 为候选策略数量。在维度 $\delta\in\{E,I,D\}$ 上，记 $r_{\delta}^{(h)}(\pi)$ 为评审主体 $h$ 给出的策略 $\pi$ 的秩，则其标准化得分定义为：
\begin{equation}\label{eq:rank-score}
s_{\delta}^{(h)}(\pi)=
\begin{cases}
1, & n_v=1 \\
\dfrac{n_v-r_{\delta}^{(h)}(\pi)}{n_v-1}, & n_v>1
\end{cases}
\in[0,1]
\end{equation}
对所有评审主体取均值，得维度 $\delta$ 的共识得分：
\begin{equation}\label{eq:consensus-score}
\hat S_{\delta}(\pi)=\frac{1}{|\mathcal{H}|}\sum_{h\in\mathcal{H}}s_{\delta}^{(h)}(\pi)
\end{equation}
三维质量向量各分量由对应维度的共识得分给出，即 $E(\pi)=\hat S_E(\pi)$，$I(\pi)=\hat S_I(\pi)$，$D(\pi)=\hat S_D(\pi)$。
\end{flatdefinition}


在得到 $q(\pi)$ 后，还需进一步计算总体质量。其过程同样分为两个步骤：先根据业务场景设定三个维度的权重 $\alpha_E,\alpha_I,\alpha_D$，再将三维共识得分按加权求和方式聚合为单一总体质量值 $Q(\pi)$。当场景更强调应急处置效果时，可适当提高有效性权重；当场景更强调生产稳定性时，则可提高无干扰性权重。若无特殊需求，本文默认采用 $\alpha_E=0.5,\alpha_I=0.3,\alpha_D=0.2$。


\begin{flatdefinition}{总体质量函数}
\label{def:overall-quality}
总体质量函数 $Q\colon\Pi_v\to[0,1]$ 定义为：
\begin{equation}\label{eq:quality-func}
Q(\pi)=\alpha_E\hat S_E(\pi)+\alpha_I\hat S_I(\pi)+\alpha_D\hat S_D(\pi),\quad \alpha_E+\alpha_I+\alpha_D=1
\end{equation}
其中 $\alpha_E,\alpha_I,\alpha_D$ 为三个维度对应的权重。
\end{flatdefinition}

按 $Q(\pi)$ 降序排列即可得到候选策略的总体排序 $\bar R^{\tau}$，并据此选出综合质量最优的候选策略。
