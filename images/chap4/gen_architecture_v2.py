"""
gen_architecture_v2.py -- KPEAgent 系统架构图（UML 组件图）
依据 system_architecture_plan.txt 绘制
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse, Rectangle

# -- 中文字体 --
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans', 'Arial']
matplotlib.rcParams['axes.unicode_minus'] = False

# -- 画布 --
FIG_W, FIG_H = 18, 11
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=200)
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_aspect('equal')
ax.axis('off')

# -- 颜色方案 --
LAYER = {
    'L1': ('#E3F2FD', '#1565C0'),
    'L2': ('#FFF3E0', '#E65100'),
    'L3': ('#F3E5F5', '#6A1B9A'),
    'L4': ('#E8F5E9', '#2E7D32'),
}
COMP_FILL   = 'white'
COMP_BORDER = '#546E7A'
EXT_FILL    = '#ECEFF1'
EXT_BORDER  = '#78909C'
ARROW_CLR   = '#263238'
LBL_CLR     = '#37474F'


# ─────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────

def draw_layer_band(x0, y0, w, h, label_cn, label_en, fcolor, bcolor):
    rect = FancyBboxPatch((x0, y0), w, h,
                          boxstyle='round,pad=0.12',
                          facecolor=fcolor, edgecolor=bcolor,
                          linewidth=2.0, zorder=1)
    ax.add_patch(rect)
    ax.text(x0 + 0.25, y0 + h - 0.18,
            f'<<layer>>  {label_cn}  ({label_en})',
            fontsize=9.5, fontweight='bold', color=bcolor,
            va='top', ha='left', zorder=5)


def draw_comp_icon(x_right, y_top, color=COMP_BORDER):
    bw, bh = 0.19, 0.23
    tw, th = 0.08, 0.066
    bx = x_right - bw - 0.03
    by = y_top - bh - 0.04
    ax.add_patch(Rectangle((bx, by), bw, bh,
                            facecolor='white', edgecolor=color, lw=0.8, zorder=8))
    ax.add_patch(Rectangle((bx - tw / 2, by + bh - th - 0.02), tw, th,
                            facecolor='white', edgecolor=color, lw=0.8, zorder=9))
    ax.add_patch(Rectangle((bx - tw / 2, by + th - 0.01), tw, th,
                            facecolor='white', edgecolor=color, lw=0.8, zorder=9))


def draw_component(cx, cy, w, h, name, sub='',
                   border=COMP_BORDER, fill=COMP_FILL):
    x0, y0 = cx - w / 2, cy - h / 2
    ax.add_patch(FancyBboxPatch((x0, y0), w, h,
                                boxstyle='square,pad=0',
                                facecolor=fill, edgecolor=border,
                                linewidth=1.2, zorder=5))
    draw_comp_icon(x0 + w, y0 + h, color=border)
    ax.text(cx, y0 + h - 0.04, '<<component>>',
            ha='center', va='top',
            fontsize=7, style='italic', color='#555', zorder=6)
    name_y = cy + (0.1 if sub else 0.0)
    ax.text(cx, name_y, name,
            ha='center', va='center',
            fontsize=9, fontweight='bold', color='#1A1A2E', zorder=6)
    if sub:
        ax.text(cx, cy - 0.18, sub,
                ha='center', va='center',
                fontsize=7.5, color='#555', zorder=6)


def draw_datastore(cx, cy, w, h, name, sub='',
                   fcolor='#E8F5E9', bcolor='#2E7D32'):
    eh = 0.32
    x0 = cx - w / 2
    y0 = cy - h / 2
    ax.add_patch(Rectangle((x0, y0), w, h,
                            facecolor=fcolor, edgecolor=bcolor,
                            linewidth=1.2, zorder=5))
    ax.add_patch(Ellipse((cx, y0), w, eh,
                         facecolor=fcolor, edgecolor=bcolor,
                         linewidth=1.2, zorder=6))
    ax.add_patch(Ellipse((cx, y0 + h), w, eh,
                         facecolor=fcolor, edgecolor=bcolor,
                         linewidth=1.2, zorder=6))
    ax.text(cx, cy + 0.15, '<<datastore>>',
            ha='center', va='center',
            fontsize=7, style='italic', color=bcolor, zorder=7)
    ax.text(cx, cy - 0.1, name,
            ha='center', va='center',
            fontsize=9, fontweight='bold', color='#1A1A2E', zorder=7)
    if sub:
        ax.text(cx, cy - 0.3, sub,
                ha='center', va='center',
                fontsize=7.5, color='#555', zorder=7)


def draw_external(cx, cy, w, h, name, sub=''):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle='round,pad=0.08',
                                facecolor=EXT_FILL, edgecolor=EXT_BORDER,
                                linewidth=1.3, linestyle='--', zorder=5))
    ax.text(cx, cy + h / 2 - 0.04, '<<external system>>',
            ha='center', va='top',
            fontsize=7, style='italic', color=EXT_BORDER, zorder=6)
    ax.text(cx, cy + 0.06, name,
            ha='center', va='center',
            fontsize=9, fontweight='bold', color='#1A1A2E', zorder=6)
    if sub:
        ax.text(cx, cy - 0.18, sub,
                ha='center', va='center',
                fontsize=7.5, color='#555', zorder=6)


def _lbl_box(x, y, text, fontsize=8):
    ax.text(x, y, text,
            ha='center', va='center', fontsize=fontsize, color=LBL_CLR, zorder=10,
            bbox=dict(boxstyle='round,pad=0.22', fc='white', ec='#BDBDBD',
                      linewidth=0.8, alpha=0.95))


def draw_line_arrow(pts, label='', ls='-', color=ARROW_CLR, lw=1.5,
                    lx=None, ly=None):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for i in range(len(pts) - 2):
        ax.plot([xs[i], xs[i + 1]], [ys[i], ys[i + 1]],
                color=color, lw=lw, ls=ls, solid_capstyle='round', zorder=4)
    ax.annotate('', xy=(xs[-1], ys[-1]), xytext=(xs[-2], ys[-2]),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=lw, linestyle=ls),
                zorder=4)
    if label:
        if lx is not None and ly is not None:
            _lbl_box(lx, ly, label)
        else:
            mid = len(pts) // 2
            _lbl_box((xs[mid - 1] + xs[mid]) / 2,
                     (ys[mid - 1] + ys[mid]) / 2, label)


def draw_curve_arrow(x1, y1, x2, y2, label='', rad=-0.35,
                     color=ARROW_CLR, lw=1.5, lx=None, ly=None):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                connectionstyle=f'arc3,rad={rad}'),
                zorder=4)
    if label:
        _lx = lx if lx is not None else (x1 + x2) / 2
        _ly = ly if ly is not None else (y1 + y2) / 2
        _lbl_box(_lx, _ly, label)


# ─────────────────────────────────────────────
# 1. 层带
# ─────────────────────────────────────────────
BX0, BW = 0.3, 14.1

draw_layer_band(BX0, 8.70, BW, 1.90, '展现层',    'Presentation Layer', *LAYER['L1'])
draw_layer_band(BX0, 5.20, BW, 3.25, '服务层',    'Service Layer',      *LAYER['L2'])
draw_layer_band(BX0, 2.65, BW, 2.30, '智能引擎层', 'Intelligence Layer', *LAYER['L3'])
draw_layer_band(BX0, 0.40, BW, 2.00, '数据层',    'Data Layer',         *LAYER['L4'])

# L2 内子框（核心业务逻辑）
ax.add_patch(FancyBboxPatch((0.55, 5.42), 13.55, 1.63,
                            boxstyle='round,pad=0.08',
                            facecolor='#FFF8E1', edgecolor='#F57C00',
                            linewidth=1.0, linestyle='--', zorder=2))
ax.text(0.85, 6.85, '核心业务逻辑',
        fontsize=8.5, color='#E65100', va='top', ha='left', zorder=5)

# ─────────────────────────────────────────────
# 2. 展现层组件 (cy=9.65)
# ─────────────────────────────────────────────
draw_component(2.5,  9.65, 3.0, 0.88, 'Vue3 视图组件')
draw_component(7.2,  9.65, 3.0, 0.88, 'Pinia 状态管理')
draw_component(11.9, 9.65, 3.0, 0.88, 'ECharts 可视化图表')

# ─────────────────────────────────────────────
# 3. 服务层组件
# ─────────────────────────────────────────────
draw_component(3.6,  7.75, 3.5, 0.88, 'REST API 网关', '(Flask)')
draw_component(9.8,  7.75, 3.0, 0.88, '任务调度器')

draw_component(2.0,  6.20, 2.5, 0.85, 'CVE 管理')
draw_component(5.0,  6.20, 2.5, 0.85, '策略生成')
draw_component(8.0,  6.20, 2.5, 0.85, '评审控制')
draw_component(11.0, 6.20, 2.5, 0.85, '部署管理')

# ─────────────────────────────────────────────
# 4. 智能引擎层组件 (cy=3.8)
# ─────────────────────────────────────────────
draw_component(2.8,  3.8, 3.8, 1.05, 'KPEAgent 核心引擎',
               border='#6A1B9A', fill='#F9F0FF')
draw_component(7.2,  3.8, 2.5, 0.85, 'RAG 检索器')
draw_component(10.2, 3.8, 2.5, 0.85, 'CoT 推理机')
draw_component(13.0, 3.8, 2.5, 0.85, '反馈优化器')

# ─────────────────────────────────────────────
# 5. 数据层圆柱体 (cy=1.35)
# ─────────────────────────────────────────────
draw_datastore(4.0,  1.35, 3.2, 1.05, '文件存储', '(JSON / CSV)')
draw_datastore(10.5, 1.35, 3.2, 1.05, '向量索引', '(Embedding)')

# ─────────────────────────────────────────────
# 6. 外部系统
# ─────────────────────────────────────────────
draw_external(16.0, 6.20, 2.6, 1.10, '目标集群', '/ 主机')

# ─────────────────────────────────────────────
# 7. 接口箭头
# ─────────────────────────────────────────────

# A1: Vue3 -> REST API  "HTTP / JSON"  (L1->L2)
draw_line_arrow([(2.5,  9.21), (2.5,  8.58), (3.6,  8.58), (3.6,  8.19)],
                label='HTTP / JSON', lx=3.05, ly=8.58)

# A2: REST API -> 调度器（内部横向连接）
draw_line_arrow([(5.35, 7.75), (8.30, 7.75)])

# A3: 调度器 -> 策略生成  "任务分发"
draw_line_arrow([(9.80, 7.31), (9.80, 7.05), (5.0,  7.05), (5.0,  6.625)],
                label='任务分发', lx=7.4, ly=7.05)

# A4: 策略生成 -> KPEAgent  "生成调用"  (L2->L3)
draw_line_arrow([(5.0,  5.775), (5.0,  5.08), (2.8,  5.08), (2.8,  4.325)],
                label='生成调用', lx=3.9, ly=5.08)

# A5-A7: KPEAgent 扇出到 RAG / CoT / 反馈优化器
# 使用「总线分支」路由：从 KPEAgent 底部引出，沿 y=3.08 横向总线延伸，再分支向上
BUS_Y = 3.08
BUS_X0 = 4.70    # KPEAgent 右侧边 x
BUS_X1 = 13.0    # 反馈优化器 中心 x
RAG_CX, COT_CX, FBK_CX = 7.2, 10.2, 13.0
BOX_BOT = 3.375  # RAG/CoT/反馈 底边 y (cy=3.8, h=0.85)
KPE_BOT = 3.275  # KPEAgent 底边 y (cy=3.8, h=1.05)

# 竖向引出线（KPEAgent 底 -> 总线）
ax.plot([BUS_X0, BUS_X0], [KPE_BOT, BUS_Y],
        color=ARROW_CLR, lw=1.5, solid_capstyle='round', zorder=4)
# 横向总线
ax.plot([BUS_X0, BUS_X1], [BUS_Y, BUS_Y],
        color=ARROW_CLR, lw=1.5, solid_capstyle='round', zorder=4)
# 三条分支（含箭头）
for cx_t in [RAG_CX, COT_CX, FBK_CX]:
    ax.annotate('', xy=(cx_t, BOX_BOT), xytext=(cx_t, BUS_Y),
                arrowprops=dict(arrowstyle='->', color=ARROW_CLR, lw=1.5), zorder=4)
    # 总线上的分叉圆点
    ax.plot(cx_t, BUS_Y, 'o', color=ARROW_CLR, ms=4, zorder=5)

# A8: 反馈优化器 -> 文件存储  "持久化"  曲线（避免与 A9 交叉）
draw_curve_arrow(13.0, 3.325, 4.0, 1.905,
                 label='持久化', rad=-0.28,
                 lx=9.2, ly=2.0)

# A9: RAG -> 向量索引  "语义检索"  虚线 (L3->L4)  从 RAG 右侧出发，避开总线
draw_line_arrow([(8.45, 3.80), (8.45, 2.52), (10.5, 2.52), (10.5, 1.905)],
                label='语义检索', ls='--', lx=9.48, ly=2.52)

# A10: 部署管理 -> 目标集群  "K8s API / SSH"
draw_line_arrow([(12.25, 6.20), (14.70, 6.20)],
                label='K8s API / SSH', lx=13.5, ly=6.43)

# ─────────────────────────────────────────────
# 8. 输出
# ─────────────────────────────────────────────
plt.tight_layout(pad=0.2)
plt.savefig('system_architecture.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('system_architecture.png generated successfully.')
