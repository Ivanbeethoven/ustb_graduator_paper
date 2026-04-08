## 绘图脚本使用说明

本仓库包含用于生成实验图表的脚本：`images/analysis/plot.py`。

依赖（Python 环境）：

- Python 3.8+
- pandas
- numpy
- matplotlib
- seaborn

安装依赖（推荐在虚拟环境中执行）：

```bash
pip install pandas numpy matplotlib seaborn
```

运行脚本：

-- 从项目根目录运行，指定数据目录（脚本会在 `--out-dir` 下创建 `plots/` 子目录并写入图片与报告）：

```bash
python images\analysis\plot.py --out-dir images\analysis
```

示例（使用 `uv` 工具运行，如果你已配置 `uv`）：

```bash
uv run python images\analysis\plot.py --out-dir images\analysis
```

输出位置说明：

- 所有生成的图片和文本报告会写入：`images/analysis/plots/` 下的子目录（按维度与图表类型分类）。
- 文本摘要报告示例：`images/analysis/plots/summary_report.txt`

常见问题：

- 如果缺少库导致无法运行（例如 `ModuleNotFoundError: No module named 'pandas'`），请先安装依赖。 
- 如果需要 y 轴从 0 开始的柱状图，脚本中已处理（`_apply_y_padding` 会将 y 轴下界设为 0）。

如需我把 README 中的说明翻译为英文、或把依赖写入 `requirements.txt` / `pyproject.toml`，告诉我即可。
