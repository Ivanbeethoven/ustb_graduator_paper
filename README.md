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






## Redis Diagnostics

| Tool | Top commandstats | Details |
| --- | --- | --- |
| dirperf | evalsha: calls=22119, usec/call=27.00<br>hset: calls=22002, usec/call=1.27<br>hexists: calls=11002, usec/call=1.60<br>set: calls=44006, usec/call=0.30<br>get: calls=33137, usec/call=0.29 | diagnostics/redis-dirperf-after.txt |
| dirstress | evalsha: calls=875, usec/call=34.25<br>hget: calls=2571, usec/call=0.95<br>hset: calls=751, usec/call=1.32<br>set: calls=2010, usec/call=0.41<br>get: calls=1600, usec/call=0.33 | diagnostics/redis-dirstress-after.txt |
| stat | 981843.5 | 1 |
| readdir | 67752.7 | 15 |
| rename | 2152.3 | 465 |

## Redis Diagnostics

| Tool | Top commandstats | Details |
| --- | --- | --- |
| dirperf | evalsha: calls=22119, usec/call=27.00<br>hset: calls=22002, usec/call=1.27<br>hexists: calls=11002, usec/call=1.60<br>set: calls=44006, usec/call=0.30<br>get: calls=33137, usec/call=0.29 | diagnostics/redis-dirperf-after.txt |
| dirstress | evalsha: calls=875, usec/call=34.25<br>hget: calls=2571, usec/call=0.95<br>hset: calls=751, usec/call=1.32<br>set: calls=2010, usec/call=0.41<br>get: calls=1600, usec/call=0.33 | diagnostics/redis-dirstress-after.txt |
| fio-bigread | lrange: calls=28, usec/call=254.07<br>evalsha: calls=2, usec/call=67.00<br>config|resetstat: calls=1, usec/call=35.00<br>hget: calls=11, usec/call=2.36<br>get: calls=1, usec/call=5.00 | diagnostics/redis-fio-bigread-after.txt |
| stat | 981843.5 | 1 |
| readdir | 67752.7 | 15 |
| rename | 2152.3 | 465 |

## Redis Diagnostics

| Tool | Top commandstats | Details |
| --- | --- | --- |
| dirperf | evalsha: calls=22119, usec/call=27.00<br>hset: calls=22002, usec/call=1.27<br>hexists: calls=11002, usec/call=1.60<br>set: calls=44006, usec/call=0.30<br>get: calls=33137, usec/call=0.29 | diagnostics/redis-dirperf-after.txt |
| dirstress | evalsha: calls=875, usec/call=34.25<br>hget: calls=2571, usec/call=0.95<br>hset: calls=751, usec/call=1.32<br>set: calls=2010, usec/call=0.41<br>get: calls=1600, usec/call=0.33 | diagnostics/redis-dirstress-after.txt |
| fio-bigread | lrange: calls=28, usec/call=254.07<br>evalsha: calls=2, usec/call=67.00<br>config|resetstat: calls=1, usec/call=35.00<br>hget: calls=11, usec/call=2.36<br>get: calls=1, usec/call=5.00 | diagnostics/redis-fio-bigread-after.txt |
| fio-bigwrite | evalsha: calls=244, usec/call=29.77<br>set: calls=249, usec/call=5.43<br>incrby: calls=236, usec/call=4.99<br>rpush: calls=236, usec/call=2.16<br>get: calls=277, usec/call=0.88 | diagnostics/redis-fio-bigwrite-after.txt |
| fio-randread | evalsha: calls=12, usec/call=60.50<br>lrange: calls=39, usec/call=11.56<br>config|resetstat: calls=1,| readdir | 67752.7 | 15 |
| rename | 2152.3 | 465 |

## Redis Diagnostics

| Tool | Top commandstats | Details |
| --- | --- | --- |
| dirperf | evalsha: calls=22119, usec/call=27.00<br>hset: calls=22002, usec/call=1.27<br>hexists: calls=11002, usec/call=1.60<br>set: calls=44006, usec/call=0.30<br>get: calls=33137, usec/call=0.29 | diagnostics/redis-dirperf-after.txt |
| dirstress | evalsha: calls=875, usec/call=34.25<br>hget: calls=2571, usec/call=0.95<br>hset: calls=751, usec/call=1.32<br>set: calls=2010, usec/call=0.41<br>get: calls=1600, usec/call=0.33 | diagnostics/redis-dirstress-after.txt |
| fio-bigread | lrange: calls=28, usec/call=254.07<br>evalsha: calls=2, usec/call=67.00<br>config|resetstat: calls=1, usec/call=35.00<br>hget: calls=11, usec/call=2.36<br>get: calls=1, usec/call=5.00 | diagnostics/redis-fio-bigread-after.txt |
| fio-bigwrite | evalsha: calls=244, usec/call=29.77<br>set: calls=249, usec/call=5.43<br>incrby: calls=236, usec/call=4.99<br>rpush: calls=236, usec/call=2.16<br>get: calls=277, usec/call=0.88 | diagnostics/redis-fio-bigwrite-after.txt |
| fio-randread | evalsha: calls=12, usec/call=60.50<br>lrange: calls=39, usec/call=11.56<br>config|resetstat: calls=1, usec/call=129.00<br>hget: calls=17, usec/call=5.88<br>ping: calls=30, usec/call=1.93 | diagnostics/redis-fio-randread-after.txt |

## Redis Diagnostics

| Tool | Top commandstats | Details |
## Redis Diagnostics

| Tool | Top commandstats | Details |
| --- | --- | --- |
| dirperf | evalsha: calls=22119, usec/call=27.00<br>hset: calls=22002, usec/call=1.27<br>hexists: calls=11002, usec/call=1.60<br>set: calls=44006, usec/call=0.30<br>get: calls=33137, usec/call=0.29 | diagnostics/redis-dirperf-after.txt |
| dirstress | evalsha: calls=875, usec/call=34.25<br>hget: calls=2571, usec/call=0.95<br>hset: calls=751, usec/call=1.32<br>set: calls=2010, usec/call=0.41<br>get: calls=1600, usec/call=0.33 | diagnostics/redis-dirstress-after.txt |
| fio-bigread | lrange: calls=28, usec/call=254.07<br>evalsha: calls=2, usec/call=67.00<br>config|resetstat: calls=1, usec/call=35.00<br>hget: calls=11, usec/call=2.36<br>get: calls=1, usec/call=5.00 | diagnostics/redis-fio-bigread-after.txt |
| fio-bigwrite | evalsha: calls=244, usec/call=29.77<br>set: calls=249, usec/call=5.43<br>incrby: calls=236, usec/call=4.99<br>rpush: calls=236, usec/call=2.16<br>get: calls=277, usec/call=0.88 | diagnostics/redis-fio-bigwrite-after.txt |
| fio-randread | evalsha: calls=12, usec/call=60.50<br>lrange: calls=39, usec/call=11.56<br>config|resetstat: calls=1, usec/call=129.00<br>hget: calls=17, usec/call=5.88<br>ping: calls=30, usec/call=1.93 | diagnostics/redis-fio-randread-after.txt |
| dirperf | evalsha: calls=22119, usec/call=27.00<br>hset: calls=22002, usec/call=1.27<br>hexists: calls=11002, usec/call=1.60<br>set: calls=44006, usec/call=0.30<br>get: calls=33137, usec/call=0.29 | diagnostics/redis-dirperf-after.txt |
| dirstress | evalsha: calls=875, usec/call=34.25<br>hget: calls=2571, usec/call=0.95<br>hset: calls=751, usec/call=1.32<br>set: calls=2010, usec/call=0.41<br>get: calls=1600, usec/call=0.33 | diagnostics/redis-dirstress-after.txt |
| fio-bigread | lrange: calls=28, usec/call=254.07<br>evalsha: calls=2, usec/call=67.00<br>config|resetstat: calls=1, usec/call=35.00<br>hget: calls=11, usec/call=2.36<br>get: calls=1, usec/call=5.00 | diagnostics/redis-fio-bigread-after.txt |
| fio-bigwrite | evalsha: calls=244, usec/call=29.77<br>set: calls=249, usec/call=5.43<br>incrby: calls=236, usec/call=4.99<br>rpush: calls=236, usec/call=2.16<br>get: calls=277, usec/call=0.88 | diagnostics/redis-fio-bigwrite-after.txt |
| fio-randread | evalsha: calls=12, usec/call=60.50<br>lrange: calls=39, usec/call=11.56<br>config|resetstat: calls=1, usec/call=129.00<br>hget: calls=17, usec/call=5.88<br>ping: calls=30, usec/call=1.93 | diagnostics/redis-fio-randread-after.txt |
| dirstress | evalsha: calls=875, usec/call=34.25<br>hget: calls=2571, usec/call=0.95<br>hset: calls=751, usec/call=1.32<br>set: calls=2010, usec/call=0.41<br>get: calls=1600, usec/call=0.33 | diagnostics/redis-dirstress-after.txt |
| fio-bigread | lrange: calls=28, usec/call=254.07<br>evalsha: calls=2, usec/call=67.00<br>config|resetstat: calls=1, usec/call=35.00<br>hget: calls=11, usec/call=2.36<br>get: calls=1, usec/call=5.00 | diagnostics/redis-fio-bigread-after.txt |
| fio-bigwrite | evalsha: calls=244, usec/call=29.77<br>set: calls=249, usec/call=5.43<br>incrby: calls=236, usec/call=4.99<br>rpush: calls=236, usec/call=2.16<br>get: calls=277, usec/call=0.88 | diagnostics/redis-fio-bigwrite-after.txt |
| fio-randread | evalsha: calls=12, usec/call=60.50<br>lrange: calls=39, usec/call=11.56<br>config|resetstat: calls=1, usec/call=129.00<br>hget: calls=17, usec/call=5.88<br>ping: calls=30, usec/call=1.93 | diagnostics/redis-fio-randread-after.txt |
lls=2010, usec/call=0.41<br>get: calls=1600, usec/call=0.33 | diagnostics/redis-dirstress-after.txt |
| fio-bigread | lrange: calls=28, usec/call=254.07<br>evalsha: calls=2, usec/call=67.00<br>config|resetstat: calls=1, usec/call=35.00<br>hget: calls=11, usec/call=2.36<br>get: calls=1, usec/call=5.00 | diagnostics/redis-fio-bigread-after.txt |
| fio-bigwrite | evalsha: calls=244, usec/call=29.77<br>set: calls=249, usec/call=5.43<br>incrby: calls=236, usec/call=4.99<br>rpush: calls=236, usec/call=2.16<br>get: calls=277, usec/call=0.88 | diagnostics/redis-fio-bigwrite-after.txt |
| fio-randread | evalsha: calls=12, usec/call=60.50<br>lrange: calls=39, usec/call=11.56<br>config|resetstat: calls=1, usec/call=129.00<br>hget: calls=17, usse:l||||| stat | 981843.5 | | | stat | 981843.5 | 1 |
| stat | 981843.5 | 1 |
| stat | 981843.5 | 1 |
| stat | 981843.5 | 1 |
| stat | 981843.5 | 1 |
| stat | 981843.5 | 1 |
| stat | 981843.5 | 1 |
| stat | 981843.5 | 1 |
| stat | 981843.5 | 1 |
| readdir | 67752.7 | 15 |
| rename | 2152.3 | 465 |

## Redis Diagnostics

| Tool | Top commandstats | Details |
| --- | --- | --- |
| dirperf | evalsha: calls=22119, usec/call=27.00<br>hset: calls=22002, usec/call=1.27<br>hexists: calls=11002, usec/call=1.60<br>set: calls=44006, usec/call=0.30<br>get: calls=33137, usec/call=0.29 | diagnostics/redis-dirperf-after.txt |
| dirstress | evalsha: calls=875, usec/call=34.25<br>hget: calls=2571, usec/call=0.95<br>hset: calls=751, usec/call=1.32<br>set: calls=2010, usec/call=0.41<br>get: calls=1600, usec/call=0.33 | diagnostics/redis-dirstress-after.txt |
| fio-bigread | lrange: calls=28, usec/call=254.07<br>evalsha: calls=2, usec/call=67.00<br>config|resetstat: calls=1, usec/call=35.00<br>hget: calls=11, usec/call=2.36<br>get: calls=1, usec/call=5.00 | diagnostics/redis-fio-bigread-after.txt |
| fio-bigwrite | evalsha: calls=244, usec/call=29.77<br>set: calls=249, usec/call=5.43<br>incrby: calls=236, usec/call=4.99<br>rpush: calls=236, usec/call=2.16<br>get: calls=277, usec/call=0.88 | diagnostics/redis-fio-bigwrite-after.txt |
| fio-randread | evalsha: calls=12, usec/call=60.50<br>lrange: calls=39, usec/call=11.56<br>config|resetstat: calls=1, usec/call=129.00<br>hget: calls=17, usec/call=5.88<br>ping: calls=30, usec/call=1.93 | diagnostics/redis-fio-randread-after.txt |
| fio-randrw | evalsha: calls=1187, usec/call=58.72<br>set: calls=799, usec/call=10.46<br>incrby: calls=1297, usec/call=5.72<br>rpush: calls=1175, usec/call=4.74<br>get: calls=1331, usec/call=1.79 | diagnostics/redis-fio-randrw-after.txt |
| fio-randwrite | evalsha: calls=1909, usec/call=30.59<br>incrby: calls=1891, usec/call=2.55<br>rpush: calls=1891, usec/call=2.23<br>set: calls=923, usec/call=3.63<br>get: calls=2137, usec/call=0.89 | diagnostics/redis-fio-randwrite-after.txt |
| fio-seqread | evalsha: calls=12, usec/call=54.42<br>lrange: calls=64, usec/call=8.80<br>hget: calls=14, usec/call=8.21<br>ping: calls=29, usec/call=1.93<br>zadd: calls=2, usec/call=18.00 | diagnostics/redis-fio-seqread-after.txt |
| fio-seqwrite | evalsha: calls=1132, usec/call=29.22<br>incrby: calls=1117, usec/call=4.38<br>set: calls=679, usec/call=5.96<br>rpush: calls=1117, usec/call=2.09<br>get: calls=1143, usec/call=0.60 | diagnostics/redis-fio-seqwrite-after.txt |
| looptest | set: calls=495, usec/call=0.29<br>evalsha: calls=1, usec/call=95.00<br>config|resetstat: calls=1, usec/call=62.00<br>hset: calls=1, usec/call=4.00<br>get: calls=1, usec/call=2.00 | diagnostics/redis-looptest-after.txt |
| metaperf | evalsha: calls=106386, usec/call=26.35<br>get: calls=347734, usec/call=0.24<br>hget: calls=371820, usec/call=0.20<br>set: calls=282363, usec/call=0.26<br>hset: calls=169492, usec/call=0.43 | diagnostics/redis-metaperf-after.txt |

## BrewFS Stats

| Tool | Cache hit | FUSE read | FUSE write | Dirty | Read buffer | S3 ops | Details |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| dirperf | 100.0% (2474228/2474318) | 134687.6 MiB | 17580.0 MiB | 0.0 MiB | 0.0 MiB | GET=29, PUT=7931 | diagnostics/stats-dirperf-after.txt |
| dirstress | 100.0% (2474228/2474318) | 134687.6 MiB | 17580.0 MiB | 230.4 MiB | 0.0 MiB | GET=29, PUT=7890 | diagnostics/stats-dirstress-after.txt |
| fio-bigread | 100.0% (14713/14713) | 1024.0 MiB | 2048.0 MiB | 0.0 MiB | 0.0 MiB | GET=0, PUT=754 | diagnostics/stats-fio-bigread-after.txt |
| fio-bigwrite | 0.0% (0/0) | 0.0 MiB | 1024.0 MiB | 37.0 MiB | 0.0 MiB | GET=0, PUT=356 | diagnostics/stats-fio-bigwrite-after.txt |
| fio-randread | 100.0% (2258803/2258882) | 127400.2 MiB | 9244.0 MiB | 0.0 MiB | 0.0 MiB | GET=25, PUT=3700 | diagnostics/stats-fio-randread-after.txt |
| fio-randrw | 100.0% (2474228/2474318) | 134687.6 MiB | 17580.0 MiB | 233.4 MiB | 0.0 MiB | GET=29, PUT=7887 | diagnostics/stats-fio-randrw-after.txt |
| fio-randwrite | 100.0% (2258803/2258882) | 127400.2 MiB | 13180.0 MiB | 43.6 MiB | 0.0 MiB | GET=25, PUT=5668 | diagnostics/stats-fio-randwrite-after.txt |
| fio-seqread | 100.0% (1428596/1428596) | 100356.2 MiB | 3072.0 MiB | 0.0 MiB | 0.0 MiB | GET=0, PUT=1141 | diagnostics/stats-fio-seqread-after.txt |
| fio-seqwrite | 100.0% (1428596/1428596) | 100356.2 MiB | 7196.0 MiB | 26.6 MiB | 0.0 MiB | GET=0, PUT=2706 | diagnostics/stats-fio-seqwrite-after.txt |
| looptest | 100.0% (2478412/2478618) | 134687.6 MiB | 17608.9 MiB | 0.0 MiB | 0.0 MiB | GET=145, PUT=16611 | diagnostics/stats-looptest-after.txt |
| metaperf | 100.0% (2478412/2478618) | 134687.6 MiB | 17608.9 MiB | 0.0 MiB | 0.0 MiB | GET=145, PUT=16611 | diagnostics/stats-metaperf-after.txt |

## Bottleneck Analysis

- **fio-bigread**: Read tail latency p99/p50=5.9x (25.6ms→152ms). Likely S3 retry or cache miss.
- **fio-bigwrite**: Write P99=1200ms > 500ms — consider increasing write buffer or S3 concurrency.
- **fio-randread**: Read tail latency p99/p50=8.7x (20.1ms→175ms). Likely S3 retry or cache miss.
- **fio-randrw**: Read tail latency p99/p50=16.0x (49.0ms→784ms). Likely S3 retry or cache miss.
- **fio-randrw**: Write stall p50=2.8ms p99=1569ms — auto_flush/buffer-limit triggers S3 upload backpressure.
- **fio-randwrite**: Write P99=5536ms > 500ms — consider increasing write buffer or S3 concurrency.
- **fio-seqwrite**: Write stall p50=2.2ms p99=279ms — auto_flush/buffer-limit triggers S3 upload backpressure.