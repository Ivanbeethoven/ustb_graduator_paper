"""生成分层架构图 — KPEAgent 系统"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Ellipse

# ── 中文字体 ──
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
matplotlib.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(15, 11), dpi=200)
ax.set_xlim(0, 15)
ax.set_ylim(0, 11)
ax.set_aspect('equal')
ax.axis('off')

# ── 颜色方案 ──
LAYER_COLORS = {
    'L1': '#E3F2FD',
    'L2': '#FFF3E0',
    'L3': '#F3E5F5',
    'L4': '#E8F5E9',
}
LAYER_BORDERS = {
    'L1': '#1565C0',
    'L2': '#E65100',
    'L3': '#6A1B9A',
    'L4': '#2E7D32',
}
COMP_COLOR = '#FFFFFF'
COMP_BORDER = '#455A64'
EXT_COLOR = '#ECEFF1'

def draw_layer_band(y, h, label_cn, label_en, layer_key):
    rect = FancyBboxPatch((0.3, y), 14.0, h,
                          boxstyle="round,pad=0.1",
                          facecolor=LAYER_COLORS[layer_key],
                          edgecolor=LAYER_BORDERS[layer_key],
                          linewidth=2.0, zorder=1)
    ax.add_patch(rect)
    ax.text(0.6, y + h - 0.22, f'{label_cn} ({label_en})',
            fontsize=10, fontweight='bold', color=LAYER_BORDERS[layer_key],
            va='top', zorder=5)

def draw_comp(cx, cy, w, h, line1, line2='', is_db=False, color=COMP_COLOR, border=COMP_BORDER):
    if is_db:
        # 简化的圆柱体数据库图标
        body = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                              boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor=border,
                              linewidth=1.3, zorder=3)
        ax.add_patch(body)
        ell_top = Ellipse((cx, cy + h/2), w * 0.98, 0.35,
                          facecolor=color, edgecolor=border,
                          linewidth=1.3, zorder=4)
        ax.add_patch(ell_top)
    else:
        rect = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                              boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor=border,
                              linewidth=1.3, zorder=3)
        ax.add_patch(rect)
    if line2:
        ax.text(cx, cy + 0.14, line1, ha='center', va='center',
                fontsize=8.5, fontweight='bold', zorder=5)
        ax.text(cx, cy - 0.18, line2, ha='center', va='center',
                fontsize=7, color='#666', zorder=5)
    else:
        ax.text(cx, cy, line1, ha='center', va='center',
                fontsize=8.5, fontweight='bold', zorder=5)

def draw_arrow(x1, y1, x2, y2, label='', color='#37474F', ls='-', lbl_offset=(0.15, 0)):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=1.5, linestyle=ls),
                zorder=2)
    if label:
        mx, my = (x1 + x2) / 2 + lbl_offset[0], (y1 + y2) / 2 + lbl_offset[1]
        ax.text(mx, my, label, fontsize=7, color='#555',
                va='center', ha='center', zorder=6,
                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='#ccc', alpha=0.92))

# ═══════════════════════════════════════════
# Layer 1 — 展现层 (y=9.0, h=1.5)
# ═══════════════════════════════════════════
draw_layer_band(9.0, 1.5, '展现层', 'Presentation Layer', 'L1')
draw_comp(2.8, 9.75, 3.0, 0.7, 'Vue3 视图组件')
draw_comp(7.0, 9.75, 3.0, 0.7, 'Pinia 状态管理')
draw_comp(11.2, 9.75, 3.0, 0.7, 'ECharts 可视化图表')

# ═══════════════════════════════════════════
# Layer 2 — 服务层 (y=5.8, h=2.8)
# ═══════════════════════════════════════════
draw_layer_band(5.8, 2.8, '服务层', 'Service Layer', 'L2')
draw_comp(3.5, 8.0, 3.2, 0.7, 'REST API 网关', '(Flask)')
draw_comp(8.5, 8.0, 3.0, 0.7, '任务调度器')
# 核心业务逻辑虚线子框
sub_rect = FancyBboxPatch((1.0, 6.05), 12.6, 1.3,
                          boxstyle="round,pad=0.08",
                          facecolor='#FFF8E1', edgecolor='#F57C00',
                          linewidth=1.0, linestyle='--', zorder=2)
ax.add_patch(sub_rect)
ax.text(1.4, 7.1, '核心业务逻辑', fontsize=8, color='#E65100', zorder=5)
draw_comp(2.8, 6.55, 2.4, 0.6, 'CVE 管理')
draw_comp(5.8, 6.55, 2.4, 0.6, '策略生成')
draw_comp(8.8, 6.55, 2.4, 0.6, '评审控制')
draw_comp(11.8, 6.55, 2.4, 0.6, '部署管理')

# ═══════════════════════════════════════════
# Layer 3 — 智能引擎层 (y=3.0, h=2.3)
# ═══════════════════════════════════════════
draw_layer_band(3.0, 2.3, '智能引擎层', 'Intelligence Layer', 'L3')
draw_comp(3.5, 4.5, 3.2, 0.7, 'KPEAgent 核心引擎')
draw_comp(7.5, 3.7, 2.4, 0.6, 'RAG 检索器')
draw_comp(10.2, 3.7, 2.4, 0.6, 'CoT 推理机')
draw_comp(12.5, 4.5, 2.0, 0.6, '反馈优化器')

# ═══════════════════════════════════════════
# Layer 4 — 数据层 (y=0.8, h=1.7)
# ═══════════════════════════════════════════
draw_layer_band(0.8, 1.7, '数据层', 'Data Layer', 'L4')
draw_comp(4.5, 1.65, 3.5, 0.8, '文件存储', '(JSON / CSV)', is_db=True)
draw_comp(10.5, 1.65, 3.5, 0.8, '向量索引', '(Embedding)', is_db=True)

# ═══════════════════════════════════════════
# 外部系统（右侧独立，不在任何层级内）
# ═══════════════════════════════════════════
# 用虚线框表示外部系统
ext_rect = FancyBboxPatch((12.5, 5.0), 1.5, 0.7,
                          boxstyle="round,pad=0.06",
                          facecolor=EXT_COLOR, edgecolor='#78909C',
                          linewidth=1.2, linestyle='--', zorder=3)
# 不画，因为已在L2内

# ═══════════════════════════════════════════
# 层间接口箭头
# ═══════════════════════════════════════════

# L1 → L2: HTTP/JSON
draw_arrow(7.0, 9.38, 5.5, 8.38, 'HTTP / JSON', lbl_offset=(0.8, 0))

# L2 内部: API网关 → 调度器
draw_arrow(5.1, 8.0, 7.0, 8.0, '', color='#E65100')
# L2 内部: 调度器 → 各业务模块 (扇出)
draw_arrow(8.0, 7.62, 5.8, 6.88, '', color='#E65100')
draw_arrow(8.5, 7.62, 8.8, 6.88, '', color='#E65100')

# L2 → L3: 策略生成 → KPEAgent
draw_arrow(5.8, 6.22, 4.2, 4.88, '生成调用', lbl_offset=(0.6, 0))

# L3 内部: Agent → 子模块
draw_arrow(5.1, 4.3, 6.8, 3.85, '', color='#6A1B9A')
draw_arrow(5.1, 4.3, 9.5, 3.85, '', color='#6A1B9A')
draw_arrow(5.1, 4.5, 11.5, 4.5, '', color='#6A1B9A')

# L3 → L4: 反馈优化器 → 文件存储
draw_arrow(12.5, 4.17, 5.5, 2.1, '持久化', lbl_offset=(2.0, 0.3))
# L3 → L4: RAG → 向量索引
draw_arrow(7.5, 3.37, 10.5, 2.1, '语义检索', ls='--', lbl_offset=(-1.0, 0.2))

# L2 → 外部: 部署管理 → 外部集群 (向右出框)
# 绘制外部系统节点在 L2 右侧外面
draw_comp(14.5, 5.35, 2.0, 0.7, '目标集群', '/ 主机',
          color=EXT_COLOR, border='#78909C')
draw_arrow(12.5, 6.22, 14.2, 5.72, 'K8s / SSH', lbl_offset=(0.3, 0.18))

plt.tight_layout(pad=0.3)
plt.savefig('system_architecture.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('system_architecture.png generated successfully.')
