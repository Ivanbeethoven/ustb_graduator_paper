## 绘图脚本使用说明

本仓库包含用于生成实验图表的脚本：`images/analysis/plot.py`。

### 依赖（Python 环境）

- Python 3.8+
- pandas
- numpy
- matplotlib
- seaborn

安装依赖（推荐在虚拟环境中执行）：

```bash
pip install pandas numpy matplotlib seaborn
```

### 输入文件

脚本从 `--in-dir` 目录下读取以下 CSV 文件（均由 `images/analysis/main.py` 生成）：

| 文件名 | 说明 |
|--------|------|
| `analysis_summary.csv` | 按维度汇总的方法/生成模型总体排名 |
| `analysis_summary_by_judge.csv` | 按维度 × 评委模型细分的汇总排名 |
| `analysis_summary_3d.csv` | 三维（生成模型 × 方法 × 评委模型 × 维度）完整数据 |
| `analysis_summary_{维度}.csv` | 各维度单独汇总（如 `analysis_summary_有效性.csv`） |
| `analysis_summary_by_judge_{维度}.csv` | 各维度按评委细分汇总 |

所有排名列（`avg_rank`、`min_rank`、`max_rank`）在读入后会经过如下公式转换为 0–1 得分，使"越大越好"：

$$s = \frac{n - r}{n - 1}$$

其中 $r$ 为原始排名（第1名最好），$n$ 为参与比较的总数。

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--in-dir` | `images\analysis` | 输入 CSV 文件所在目录 |
| `--out-dir` | `images` | 图表输出根目录（图表实际写入 `{out-dir}/plots/`） |
| `--dimensions` | 全部 | 指定要处理的维度名列表（空格分隔） |
| `--single-dim` | 无 | 仅生成指定维度的单维度总结图，跳过完整的分组柱状图等 |

当只传 `--out-dir` 而不传 `--in-dir` 时，仍需显式指定 `--in-dir`；使用默认值直接运行则无需任何参数。

### 运行示例

使用默认目录（输入 `images\analysis`，输出 `images\plots`）：

```bash
python images\analysis\plot.py
```

自定义目录：

```bash
python images\analysis\plot.py --in-dir images\analysis --out-dir images\plots
```

仅生成"有效性"维度的总结图：

```bash
python images\analysis\plot.py --single-dim 有效性
```

使用 `uv` 工具运行（如果你已配置 `uv`）：

```bash
uv run python images\analysis\plot.py
```

### 生成的图表

脚本包含以下绘图函数，默认全部执行：

| 函数 | 说明 | 输出路径示例 |
|------|------|------------|
| `plot_grouped_bar` | 按评委模型分组的柱状图（x=方法，hue=评委） | `plots/{维度}/generator/{生成模型}/grouped_bar_*.png` |
| `plot_heatmap` | 评委模型 × 方法热力图（按生成模型分） | `plots/{维度}/heatmap/{生成模型}/heatmap_*.png` |
| `plot_per_method` | 每个方法的热力图 + 按评委/生成模型汇总柱状图 | `plots/{维度}/method/{方法}/` |
| `plot_per_generator` | 每个生成模型的热力图 + 按方法/评委汇总柱状图 | `plots/{维度}/generator/{生成模型}/` |
| `plot_single_dimension` | 单维度总结：方法/生成模型平均得分柱状图 + 评委细分分组柱状图 | `plots/{维度}/summary/single_dim_*.png` |
| `plot_method_report` | 方法总览柱状图 + 方法 × 生成模型得分矩阵热力图 | `plots/{维度}/method_report/` |
| `plot_generator_report` | 生成模型总览柱状图 + 生成模型 × 方法得分矩阵热力图 | `plots/{维度}/generator_report/` |
| `plot_judge_report` | 评委模型总览柱状图 + 评委 × 方法/生成模型得分矩阵 | `plots/{维度}/judge_report/` |
| `plot_radar_overall` | 所有维度雷达图（生成模型维度 & 方法维度各一张） | `plots/summary/radar_generator_overall.png` 等 |
| `plot_radar_for_judge` | 指定评委的三维度雷达图 | `plots/summary/radar_generator_gpt5.png` 等 |
| `plot_judge_consistency` | 评委相关性热力图 + 按维度一致性标准差柱状图 | `plots/judge_consistency/` |
| `plot_judge_consistency_extended` | Kendall's W 柱状图 + Spearman 两两相关箱线图 | `plots/judge_consistency/` |
| `write_text_report` | 数值摘要文本报告 | `plots/summary_report.txt` |

评估维度固定为三项（按图表坐标顺序）：**有效性**、**无干扰性**、**可部署性**。

### 输出位置说明

- 默认输出根目录：`images`（即 `--out-dir` 默认值）
- 所有图片按 `images/plots/{维度}/{图表类型}/` 层级存放，与 LaTeX 引用路径一致
- 文本摘要报告：`images/plots/summary_report.txt`

### 常见问题

- 缺少库（`ModuleNotFoundError`）：先执行依赖安装命令。
- y 轴从 0 开始：脚本中 `_apply_y_padding` 已将 y 轴下界固定为 0。
- 中文字体乱码：脚本运行时会优先加载 WenQuanYi / Noto CJK / Microsoft YaHei 等字体，确保系统已安装其中任意一款。
