from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])

# Palette
BG_LIGHT = RGBColor(0xEE, 0xEE, 0xEE)
BLACK = RGBColor(0x22, 0x22, 0x22)
GRAY = RGBColor(0x88, 0x88, 0x88)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK_GRAY = RGBColor(0x44, 0x44, 0x44)

def rrect(slide, l, t, w, h, text, fs=13, bold=True, bg=WHITE, border=BLACK):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = bg
    s.line.color.rgb = border; s.line.width = Pt(1.5)
    tf = s.text_frame; tf.word_wrap = True; tf.auto_size = None
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.size = Pt(fs)
    r.font.color.rgb = BLACK; r.font.bold = bold
    return s

def layer_box(slide, l, t, w, h, title, fs=18):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = BG_LIGHT
    s.line.color.rgb = BLACK; s.line.width = Pt(2)
    tf = s.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = title; r.font.size = Pt(fs)
    r.font.color.rgb = BLACK; r.font.bold = True
    return s

def down_arrow(slide, x, y1, y2):
    s = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, x - Inches(0.12), y1, Inches(0.24), y2 - y1)
    s.fill.solid(); s.fill.fore_color.rgb = GRAY; s.line.fill.background()

def right_arrow_shape(slide, x, y, w):
    s = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x, y, w, Inches(0.3))
    s.fill.solid(); s.fill.fore_color.rgb = GRAY; s.line.fill.background()

# === Layout ===
# Left system: x=0.3, width=8.5
# Right K8s: x=9.8, width=3.2
LEFT_X = Inches(0.3)
LEFT_W = Inches(8.5)
RIGHT_X = Inches(9.8)
RIGHT_W = Inches(3.2)
BW = Inches(1.85)  # box width
BH = Inches(0.48)
PAD = Inches(0.45)  # padding top inside layer
LGAP = Inches(0.08)

# ====== 界面层（前端）======
y = Inches(0.15)
h_ui = Inches(0.95)
layer_box(slide, LEFT_X, y, LEFT_W, h_ui, "界面层（前端）")
items = ["策略代码生成", "策略代码评估", "安全策略部署"]
n = len(items)
gap_item = Inches(0.3)
tw = n * BW + (n-1) * gap_item
sx = LEFT_X + (LEFT_W - tw) // 2
for i, t in enumerate(items):
    rrect(slide, sx + i*(BW+gap_item), y+PAD, BW, BH, t, fs=12)
y_ui_end = y + h_ui

down_arrow(slide, LEFT_X + LEFT_W//2, y_ui_end, y_ui_end + LGAP*2)

# ====== 后端服务 大框 ======
y_be = y_ui_end + LGAP*2
h_be = Inches(5.0)
# Outer "后端服务" box
be_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, LEFT_X, y_be, LEFT_W, h_be)
be_box.fill.solid(); be_box.fill.fore_color.rgb = RGBColor(0xF8, 0xF8, 0xF8)
be_box.line.color.rgb = BLACK; be_box.line.width = Pt(2.5)
be_box.line.dash_style = 2  # dashed
tf = be_box.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
r = p.add_run(); r.text = "后端服务"; r.font.size = Pt(16)
r.font.color.rgb = BLACK; r.font.bold = True

inner_x = LEFT_X + Inches(0.15)
inner_w = LEFT_W - Inches(0.3)

# --- 服务层 ---
y_svc = y_be + Inches(0.4)
h_svc = Inches(1.6)
layer_box(slide, inner_x, y_svc, inner_w, h_svc, "服务层", fs=16)
row1 = ["REST API 网关", "任务调度器"]
n1 = len(row1)
tw1 = n1 * BW + (n1-1)*Inches(0.6)
sx1 = inner_x + (inner_w - tw1) // 2
for i, t in enumerate(row1):
    rrect(slide, sx1 + i*(BW+Inches(0.6)), y_svc+PAD, BW, BH, t, fs=12)
row2 = ["知识库构建", "策略生成", "评审与排序", "部署管理"]
n2 = len(row2)
tw2 = n2 * BW + (n2-1)*Inches(0.25)
sx2 = inner_x + (inner_w - tw2) // 2
for i, t in enumerate(row2):
    rrect(slide, sx2 + i*(BW+Inches(0.25)), y_svc+PAD+BH+Inches(0.15), BW, BH, t, fs=12)
y_svc_end = y_svc + h_svc

down_arrow(slide, inner_x + inner_w//2, y_svc_end, y_svc_end + LGAP*2)

# --- 智能引擎层 ---
y_eng = y_svc_end + LGAP*2
h_eng = Inches(0.95)
layer_box(slide, inner_x, y_eng, inner_w, h_eng, "智能引擎层", fs=16)
eng_items = ["大模型接口", "RAG 检索器", "工作流管理", "智能体管理"]
n = len(eng_items)
tw = n * BW + (n-1)*Inches(0.25)
sx = inner_x + (inner_w - tw) // 2
for i, t in enumerate(eng_items):
    rrect(slide, sx + i*(BW+Inches(0.25)), y_eng+PAD, BW, BH, t, fs=12)
y_eng_end = y_eng + h_eng

down_arrow(slide, inner_x + inner_w//2, y_eng_end, y_eng_end + LGAP*2)

# --- 数据层 ---
y_dat = y_eng_end + LGAP*2
h_dat = Inches(0.95)
layer_box(slide, inner_x, y_dat, inner_w, h_dat, "数据层", fs=16)
dat_items = ["会话数据库", "向量数据库"]
n = len(dat_items)
tw = n * BW + (n-1)*Inches(0.6)
sx = inner_x + (inner_w - tw) // 2
for i, t in enumerate(dat_items):
    rrect(slide, sx + i*(BW+Inches(0.6)), y_dat+PAD, BW, BH, t, fs=12)

# ====== 右侧 Kubernetes 集群 ======
k8s_top = y_be + Inches(0.2)
k8s_h = h_be - Inches(0.4)
layer_box(slide, RIGHT_X, k8s_top, RIGHT_W, k8s_h, "Kubernetes 集群", fs=16)

k8s_items = [
    "Falco\n(运行时威胁检测)",
    "OPA\n(策略决策引擎)",
    "Network Policy\n(网络隔离)",
    "Trivy\n(镜像漏洞扫描)",
]
k_bw = Inches(2.6)
k_bh = Inches(0.6)
k_gap = Inches(0.2)
k_sx = RIGHT_X + (RIGHT_W - k_bw) // 2
k_sy = k8s_top + Inches(0.5)
for i, t in enumerate(k8s_items):
    rrect(slide, k_sx, k_sy + i*(k_bh+k_gap), k_bw, k_bh, t, fs=11)

# ====== Arrow: 后端 -> K8s (K8s API / SSH) ======
arrow_y = y_be + h_be // 2 - Inches(0.15)
arrow_x = LEFT_X + LEFT_W + Inches(0.05)
arrow_w = RIGHT_X - arrow_x - Inches(0.05)
right_arrow_shape(slide, arrow_x, arrow_y, arrow_w)

# Label on arrow
from pptx.util import Emu
txBox = slide.shapes.add_textbox(arrow_x, arrow_y - Inches(0.25), arrow_w, Inches(0.25))
tf = txBox.text_frame
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "K8s API / SSH"
r.font.size = Pt(11); r.font.color.rgb = DARK_GRAY; r.font.bold = False

out = r"d:\论文\latex\系统架构图.pptx"
prs.save(out)
print(f"Saved to {out}")
