# 策略生成综合评估报告
生成时间: 2026-04-17 21:31:33
---
## 1. 方法对比排名
### 排名表格（数值越小越好）
          方法  有效性  无干扰性  可部署性
         all  1.0   1.0   1.0
     w/o cot  3.0   3.0   2.0
w/o feedback  4.0   4.0   4.0
     w/o rag  2.0   2.0   3.0
### 综合平均排名
          方法     平均排名
         all 1.000000
     w/o rag 2.333333
     w/o cot 2.666667
w/o feedback 4.000000
### LaTeX表格代码
```latex
\begin{table}[htbp]
\centering
\caption{方法对比排名结果}
\begin{tabular}{lcccc}
\hline
方法 & 有效性 & 无干扰性 & 可部署性 & 平均排名 \\
\hline
all & 1.0 & 1.0 & 1.0 & 1.00 \\
w/o rag & 2.0 & 2.0 & 3.0 & 2.33 \\
w/o cot & 3.0 & 3.0 & 2.0 & 2.67 \\
w/o feedback & 4.0 & 4.0 & 4.0 & 4.00 \\
\hline
\end{tabular}
\end{table}
```

## 2. 生成模型对比排名
### 排名表格（数值越小越好）
      模型  有效性  无干扰性  可部署性
ali-qwen  4.0   2.0   2.0
deepseek  3.0   1.0   1.0
  glm4.5  2.0   4.0   4.0
    gpt5  1.0   5.0   5.0
   grok4  5.0   3.0   3.0
### 综合平均排名
      模型     平均排名
deepseek 1.666667
ali-qwen 2.666667
  glm4.5 3.333333
    gpt5 3.666667
   grok4 3.666667
### LaTeX表格代码
```latex
\begin{table}[htbp]
\centering
\caption{生成模型对比排名结果}
\begin{tabular}{lcccc}
\hline
模型 & 有效性 & 无干扰性 & 可部署性 & 平均排名 \\
\hline
deepseek & 3.0 & 1.0 & 1.0 & 1.67 \\
ali-qwen & 4.0 & 2.0 & 2.0 & 2.67 \\
glm4.5 & 2.0 & 4.0 & 4.0 & 3.33 \\
gpt5 & 1.0 & 5.0 & 5.0 & 3.67 \\
grok4 & 5.0 & 3.0 & 3.0 & 3.67 \\
\hline
\end{tabular}
\end{table}
```

## 3. 关键发现
- **最佳方法**: all (平均排名: 1.00)
- **有效性最佳**: all (排名: 1.0)
- **无干扰性最佳**: all (排名: 1.0)
- **可部署性最佳**: all (排名: 1.0)

- **最佳生成模型**: deepseek (平均排名: 1.67)
- **有效性最佳模型**: gpt5 (排名: 1.0)
- **无干扰性最佳模型**: deepseek (排名: 1.0)
- **可部署性最佳模型**: deepseek (排名: 1.0)

---
*本报告由plot_rank_order.py自动生成*
