"""
人工评审数据分析与可视化脚本
生成与LLM评审结果对比的图表
"""

import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")  # Use non-GUI backend for reliable font rendering (incl. Chinese)
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path
from scipy.stats import spearmanr, kendalltau
from itertools import combinations

# 设置中文字体和样式（参考 plot.py）
sns.set_style("whitegrid")
sns.set_palette("husl")
matplotlib.rcParams.update({
    "font.sans-serif": [
        "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei",
        "Noto Sans CJK SC",
        "Noto Sans CJK JP",
        "Noto Sans CJK",
        "Microsoft YaHei",
        "SimHei",
        "DejaVu Sans",
    ],
    "font.family": "sans-serif",
    "axes.unicode_minus": False,
    "figure.dpi": 300,
})

# 数据路径
DATA_DIR = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# 维度映射
DIMENSION_MAP = {
    'effectiveness': '有效性',
    'interference': '无干扰性',
    'deployability': '可部署性'
}

# 方法映射
METHOD_MAP = {
    'all': 'All',
    'no_cot': 'W/O CoT',
    'no_feedback': 'W/O Feedback',
    'no_rag': 'W/O RAG'
}

# 生成模型映射
GENERATOR_MAP = {
    'ali-qwen': 'Qwen3',
    'deepseek': 'DeepSeek',
    'glm4.5': 'GLM-4.5',
    'gpt5': 'GPT-5',
    'grok4': 'Grok4'
}


def load_data():
    """加载人工评审数据"""
    result_df = pd.read_csv(DATA_DIR / 'result.csv')
    map_df = pd.read_csv(DATA_DIR / 'map.csv')
    
    # 解析ranking列（JSON字符串）
    result_df['ranking'] = result_df['ranking'].apply(json.loads)
    
    return result_df, map_df


def parse_ranking_to_scores(ranking_list):
    """
    将排名列表转换为得分字典
    排名第1得分最高，排名越后得分越低
    """
    n = len(ranking_list)
    scores = {}
    for rank, candidate_id in enumerate(ranking_list, start=1):
        # 归一化得分：rank 1 -> 1.0, rank n -> 0.0
        scores[candidate_id] = (n - rank) / (n - 1) if n > 1 else 1.0
    return scores


def aggregate_by_method(result_df, map_df):
    """
    按方法（method）聚合不同生成模型的排名
    """
    aggregated_data = []
    
    for _, row in result_df.iterrows():
        cve_id = row['cve_id']
        dimension = row['dimension']
        ranking = row['ranking']
        
        scores = parse_ranking_to_scores(ranking)
        
        # 按method分组统计平均排名
        method_scores = {method: [] for method in METHOD_MAP.keys()}
        
        for candidate_id, score in scores.items():
            candidate_info = map_df[map_df['候选ID'] == candidate_id].iloc[0]
            method = candidate_info['Method']
            method_scores[method].append(score)
        
        # 计算每个method的平均得分
        for method, scores_list in method_scores.items():
            if scores_list:
                aggregated_data.append({
                    'cve_id': cve_id,
                    'dimension': dimension,
                    'method': method,
                    'avg_score': np.mean(scores_list)
                })
    
    return pd.DataFrame(aggregated_data)


def aggregate_by_generator(result_df, map_df):
    """
    按生成模型（generator）聚合不同方法的排名
    """
    aggregated_data = []
    
    for _, row in result_df.iterrows():
        cve_id = row['cve_id']
        dimension = row['dimension']
        ranking = row['ranking']
        
        scores = parse_ranking_to_scores(ranking)
        
        # 按generator分组统计平均排名
        generator_scores = {gen: [] for gen in GENERATOR_MAP.keys()}
        
        for candidate_id, score in scores.items():
            candidate_info = map_df[map_df['候选ID'] == candidate_id].iloc[0]
            generator = candidate_info['Profile']
            generator_scores[generator].append(score)
        
        # 计算每个generator的平均得分
        for generator, scores_list in generator_scores.items():
            if scores_list:
                aggregated_data.append({
                    'cve_id': cve_id,
                    'dimension': dimension,
                    'generator': generator,
                    'avg_score': np.mean(scores_list)
                })
    
    return pd.DataFrame(aggregated_data)


def plot_method_comparison(agg_method_df):
    """
    绘制方法配置在三个维度上的对比图（类似RQ1的图）
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for idx, (dim_en, dim_cn) in enumerate(DIMENSION_MAP.items()):
        ax = axes[idx]
        dim_data = agg_method_df[agg_method_df['dimension'] == dim_en]
        
        # 计算每个method的平均得分
        method_avg = dim_data.groupby('method')['avg_score'].mean().sort_values(ascending=False)
        
        # 映射到中文标签
        x_labels = [METHOD_MAP.get(m, m) for m in method_avg.index]
        y_values = method_avg.values
        
        bars = ax.bar(x_labels, y_values, alpha=0.8, edgecolor='black', linewidth=1.2)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=9)
        
        ax.set_title(f'{dim_cn}维度', fontsize=12, fontweight='bold')
        ax.set_ylabel('人工评审平均得分', fontsize=10)
        ax.set_ylim(0, 1.0)
        ax.grid(axis='y', alpha=0.3)
        ax.tick_params(axis='x', rotation=15)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'human_method_comparison.png', bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ 生成方法对比图: {OUTPUT_DIR / 'human_method_comparison.png'}")


def plot_generator_comparison(agg_gen_df):
    """
    绘制生成模型在三个维度上的对比图（类似RQ2的图）
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for idx, (dim_en, dim_cn) in enumerate(DIMENSION_MAP.items()):
        ax = axes[idx]
        dim_data = agg_gen_df[agg_gen_df['dimension'] == dim_en]
        
        # 计算每个generator的平均得分
        gen_avg = dim_data.groupby('generator')['avg_score'].mean().sort_values(ascending=False)
        
        # 映射到中文标签
        x_labels = [GENERATOR_MAP.get(g, g) for g in gen_avg.index]
        y_values = gen_avg.values
        
        bars = ax.bar(x_labels, y_values, alpha=0.8, edgecolor='black', linewidth=1.2)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=9)
        
        ax.set_title(f'{dim_cn}维度', fontsize=12, fontweight='bold')
        ax.set_ylabel('人工评审平均得分', fontsize=10)
        ax.set_ylim(0, 1.0)
        ax.grid(axis='y', alpha=0.3)
        ax.tick_params(axis='x', rotation=15)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'human_generator_comparison.png', bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ 生成模型对比图: {OUTPUT_DIR / 'human_generator_comparison.png'}")


def plot_dimension_radar(agg_gen_df):
    """
    绘制每个生成模型在三维度上的雷达图
    """
    generators = list(GENERATOR_MAP.keys())
    dimensions = list(DIMENSION_MAP.keys())
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10), subplot_kw=dict(projection='polar'))
    axes = axes.flatten()
    
    for idx, generator in enumerate(generators):
        ax = axes[idx]
        gen_data = agg_gen_df[agg_gen_df['generator'] == generator]
        
        # 获取三个维度的平均得分
        scores = []
        for dim in dimensions:
            dim_score = gen_data[gen_data['dimension'] == dim]['avg_score'].mean()
            scores.append(dim_score)
        
        # 闭合雷达图
        scores += scores[:1]
        angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
        angles += angles[:1]
        
        ax.plot(angles, scores, 'o-', linewidth=2, label=GENERATOR_MAP[generator])
        ax.fill(angles, scores, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([DIMENSION_MAP[d] for d in dimensions], fontsize=10)
        ax.set_ylim(0, 0.7)
        ax.set_title(GENERATOR_MAP[generator], fontsize=12, fontweight='bold', pad=20)
        ax.grid(True)
    
    # 隐藏多余的子图
    if len(generators) < len(axes):
        for idx in range(len(generators), len(axes)):
            axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'human_generator_radar.png', bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ 生成模型雷达图: {OUTPUT_DIR / 'human_generator_radar.png'}")


def plot_overall_radar(agg_gen_df, agg_method_df):
    """
    绘制整体雷达图：生成模型与方法配置（绝对位置标签）
    """
    dim_order_en = list(DIMENSION_MAP.keys())
    dim_order_cn = [DIMENSION_MAP[d] for d in dim_order_en]

    def _plot(df, entity_col, label_map, title, filename, label_positions):
        if df.empty:
            return
        pivot = df.pivot_table(index=entity_col, columns='dimension', values='avg_score', aggfunc='mean')
        pivot = pivot.reindex(columns=dim_order_en)
        pivot = pivot.dropna(how='all')
        if pivot.empty:
            return

        angles = np.linspace(0, 2 * np.pi, len(dim_order_en), endpoint=False).tolist()
        angles += angles[:1]

        plt.figure(figsize=(7.6, 7.6))
        ax = plt.subplot(111, polar=True)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        theta_deg = np.degrees(angles[:-1])
        ax.set_thetagrids(theta_deg, ["" for _ in dim_order_cn], fontsize=11)

        for label, (x, y) in label_positions.items():
            ax.text(x, y, label, transform=ax.transAxes, ha='center', va='center', fontsize=11)

        ax.set_ylim(0, 0.7)
        ax.set_yticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
        ax.set_yticklabels(["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7"], fontsize=9)
        ax.grid(color="#D0D0D0", linestyle="--", linewidth=0.6, alpha=0.9)

        palette = sns.color_palette("husl", n_colors=len(pivot.index))
        for (name, color) in zip(pivot.index.tolist(), palette):
            values = pivot.loc[name].to_numpy(dtype=float)
            if np.all(np.isnan(values)):
                continue
            mean_val = np.nanmean(values)
            if np.isnan(mean_val):
                mean_val = 0.0
            values = np.nan_to_num(values, nan=mean_val).tolist()
            values += values[:1]
            ax.plot(angles, values, color=color, linewidth=3, label=label_map.get(name, name))
            ax.fill(angles, values, color=color, alpha=0.15)

        ax.set_title(title, fontsize=14, pad=20, fontweight='bold')
        ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.10), frameon=False, fontsize=11)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / filename, bbox_inches='tight', dpi=300)
        plt.close()
        print(f"✓ 生成雷达图: {OUTPUT_DIR / filename}")

    generator_label_positions = {
        "有效性": (0.50, 1.02),
        "无干扰性": (1.00, 0.22),
        "可部署性": (0.00, 0.22),
    }
    method_label_positions = {
        "有效性": (0.50, 1.02),
        "无干扰性": (1.00, 0.22),
        "可部署性": (0.00, 0.22),
    }

    _plot(
        agg_gen_df,
        'generator',
        GENERATOR_MAP,
        '生成模型三维度雷达图',
        'human_generator_radar_overall.png',
        generator_label_positions,
    )
    _plot(
        agg_method_df,
        'method',
        METHOD_MAP,
        '方法配置三维度雷达图',
        'human_method_radar_overall.png',
        method_label_positions,
    )


def calculate_consistency_stats(result_df):
    """
    计算人工评审的一致性统计
    由于人工评审只有一个评审者，这里计算跨CVE的稳定性
    """
    stats = []
    
    for dim_en, dim_cn in DIMENSION_MAP.items():
        dim_data = result_df[result_df['dimension'] == dim_en]
        
        # 提取所有CVE的排名列表
        all_rankings = []
        for _, row in dim_data.iterrows():
            ranking = row['ranking']
            # 转换为数值排名（C1->1, C2->2, ...）
            numeric_ranking = [int(c[1:]) for c in ranking]
            all_rankings.append(numeric_ranking)
        
        if len(all_rankings) > 1:
            # 计算两两Spearman相关性（只对长度相同的排名对进行计算）
            correlations = []
            valid_pairs = 0
            for i, j in combinations(range(len(all_rankings)), 2):
                # 检查长度是否相同
                if len(all_rankings[i]) == len(all_rankings[j]):
                    try:
                        corr, _ = spearmanr(all_rankings[i], all_rankings[j])
                        if not np.isnan(corr):
                            correlations.append(corr)
                            valid_pairs += 1
                    except Exception as e:
                        print(f"警告: CVE对({i},{j})计算相关性失败: {e}")
                        continue
            
            avg_corr = np.mean(correlations) if correlations else 0
            
            stats.append({
                'dimension': dim_cn,
                'n_cves': len(all_rankings),
                'valid_pairs': valid_pairs,
                'avg_spearman': avg_corr
            })
    
    stats_df = pd.DataFrame(stats)
    print("\n人工评审跨CVE一致性统计:")
    print(stats_df.to_string(index=False))
    stats_df.to_csv(OUTPUT_DIR / 'human_consistency_stats.csv', index=False)
    
    return stats_df


def plot_score_distribution(agg_method_df, agg_gen_df):
    """
    绘制得分分布箱线图
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    
    # 方法配置得分分布
    for idx, (dim_en, dim_cn) in enumerate(DIMENSION_MAP.items()):
        ax = axes[0, idx]
        dim_data = agg_method_df[agg_method_df['dimension'] == dim_en]
        
        data_to_plot = [dim_data[dim_data['method'] == m]['avg_score'].values 
                        for m in METHOD_MAP.keys()]
        x_labels = [METHOD_MAP[m] for m in METHOD_MAP.keys()]
        
        bp = ax.boxplot(data_to_plot, labels=x_labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
            patch.set_alpha(0.7)
        
        ax.set_title(f'{dim_cn} - 方法配置', fontsize=11, fontweight='bold')
        ax.set_ylabel('人工评审得分', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        ax.tick_params(axis='x', rotation=15)
    
    # 生成模型得分分布
    for idx, (dim_en, dim_cn) in enumerate(DIMENSION_MAP.items()):
        ax = axes[1, idx]
        dim_data = agg_gen_df[agg_gen_df['dimension'] == dim_en]
        
        data_to_plot = [dim_data[dim_data['generator'] == g]['avg_score'].values 
                        for g in GENERATOR_MAP.keys()]
        x_labels = [GENERATOR_MAP[g] for g in GENERATOR_MAP.keys()]
        
        bp = ax.boxplot(data_to_plot, labels=x_labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightcoral')
            patch.set_alpha(0.7)
        
        ax.set_title(f'{dim_cn} - 生成模型', fontsize=11, fontweight='bold')
        ax.set_ylabel('人工评审得分', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        ax.tick_params(axis='x', rotation=15)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'human_score_distribution.png', bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ 得分分布箱线图: {OUTPUT_DIR / 'human_score_distribution.png'}")


def generate_summary_table(agg_method_df, agg_gen_df):
    """
    生成汇总统计表
    """
    # 方法配置汇总
    method_summary = []
    for method in METHOD_MAP.keys():
        method_data = agg_method_df[agg_method_df['method'] == method]
        row = {'Method': METHOD_MAP[method]}
        for dim_en, dim_cn in DIMENSION_MAP.items():
            dim_scores = method_data[method_data['dimension'] == dim_en]['avg_score']
            row[dim_cn] = f"{dim_scores.mean():.3f}"
        method_summary.append(row)
    
    method_summary_df = pd.DataFrame(method_summary)
    print("\n方法配置在三维度的人工评审平均得分:")
    print(method_summary_df.to_string(index=False))
    method_summary_df.to_csv(OUTPUT_DIR / 'human_method_summary.csv', index=False)
    
    # 生成模型汇总
    gen_summary = []
    for generator in GENERATOR_MAP.keys():
        gen_data = agg_gen_df[agg_gen_df['generator'] == generator]
        row = {'Generator': GENERATOR_MAP[generator]}
        for dim_en, dim_cn in DIMENSION_MAP.items():
            dim_scores = gen_data[gen_data['dimension'] == dim_en]['avg_score']
            row[dim_cn] = f"{dim_scores.mean():.3f}"
        gen_summary.append(row)
    
    gen_summary_df = pd.DataFrame(gen_summary)
    print("\n生成模型在三维度的人工评审平均得分:")
    print(gen_summary_df.to_string(index=False))
    gen_summary_df.to_csv(OUTPUT_DIR / 'human_generator_summary.csv', index=False)


def main():
    """主函数"""
    print("=" * 60)
    print("人工评审数据分析")
    print("=" * 60)
    
    # 加载数据
    print("\n[1/8] 加载数据...")
    result_df, map_df = load_data()
    print(f"  - 评审记录数: {len(result_df)}")
    print(f"  - CVE数量: {result_df['cve_id'].nunique()}")
    print(f"  - 候选策略数: {len(map_df)}")
    
    # 按方法聚合
    print("\n[2/8] 按方法配置聚合数据...")
    agg_method_df = aggregate_by_method(result_df, map_df)
    
    # 按生成模型聚合
    print("\n[3/8] 按生成模型聚合数据...")
    agg_gen_df = aggregate_by_generator(result_df, map_df)
    
    # 绘制方法对比图
    print("\n[4/8] 绘制方法配置对比图...")
    plot_method_comparison(agg_method_df)
    
    # 绘制生成模型对比图
    print("\n[5/8] 绘制生成模型对比图...")
    plot_generator_comparison(agg_gen_df)
    
    # 绘制雷达图
    print("\n[6/8] 绘制生成模型雷达图...")
    plot_dimension_radar(agg_gen_df)
    print("\n[6.1/8] 绘制整体雷达图...")
    plot_overall_radar(agg_gen_df, agg_method_df)
    
    # 绘制得分分布
    print("\n[7/8] 绘制得分分布箱线图...")
    plot_score_distribution(agg_method_df, agg_gen_df)
    
    # 生成汇总表
    print("\n[8/8] 生成汇总统计表...")
    generate_summary_table(agg_method_df, agg_gen_df)
    
    # 计算一致性统计
    calculate_consistency_stats(result_df)
    
    print("\n" + "=" * 60)
    print("✓ 分析完成！所有结果已保存到:", OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
