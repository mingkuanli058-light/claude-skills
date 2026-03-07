"""
data_flow.py - A-03 数据流转图

双泳道布局：
  左栏：数据写入流程（接入 → 校验 → 存储 → 元数据）
  右栏：数据调阅流程（终端请求 → 查询 → 读取 → 播放）

每个步骤用编号方框表示，步骤间用箭头连接。
共享设备节点（应用服务器、NAS、数据库）用浅色背景强调。
"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from charts.chart_utils import render_chart_html, write_html, esc

# ── 颜色 ──────────────────────────────────────────────────────────────────────
_C_WRITE  = "#1565C0"   # 写入流程主色
_C_READ   = "#2E7D32"   # 调阅流程主色
_C_SHARED = "#6A1B9A"   # 共享节点色
_C_ARROW  = "#78909C"

_WRITE_FILL  = "#E3F2FD"
_READ_FILL   = "#E8F5E9"
_SHARED_FILL = "#F3E5F5"
_DECISION_FILL = "#FFF9C4"

def _build_steps(solution_data):
    """根据解析结果动态构建流程步骤。"""
    access_types = getattr(solution_data, "access_types", []) or [
        "5G回传", "采集站", "本地导入", "既有平台归集"
    ]
    # 最多展示4种，超出时缩短
    access_desc = " / ".join(access_types[:4])

    write_steps = [
        ("W1", "接入节点\n接收数据",         f"来源：{access_desc}",               "process",  _C_WRITE),
        ("W2", "完整性校验\n元数据提取",     "哈希校验 + 时间/设备/人员等元数据",  "decision", _C_WRITE),
        ("W3", "写入\nNAS存储资源池",        "通过存储网络（≥10GbE）写入原始文件", "process",  _C_WRITE),
        ("W4", "达梦数据库\n建立元数据记录", "文件路径 + 校验值 + 生命周期状态",   "process",  "#E65100"),
        ("W5", "接入完成\n数据在线可用",     "原始文件进入只读保护状态",            "end",      _C_WRITE),
    ]
    read_steps = [
        ("R1", "访问终端\n发起检索请求",       "多维度检索：时间 / 设备 / 人员 / 类型",  "process",  _C_READ),
        ("R2", "权限验证\n审批检查",           "基于角色访问控制，审批流程校验",          "decision", _C_READ),
        ("R3", "查询达梦数据库\n获取文件路径", "查询元数据，返回存储资源池访问路径",      "process",  "#E65100"),
        ("R4", "从NAS存储资源池\n读取文件",    "通过存储网络（≥10GbE）读取原始文件",      "process",  _C_READ),
        ("R5", "向终端提供\n播放/下载服务",    "支持 ≥20 路并发播放，审计日志记录",       "end",      _C_READ),
    ]
    return write_steps, read_steps

# ── 主入口 ────────────────────────────────────────────────────────────────────

def generate(solution_data, investment_data, output_path: str, template_dir: str = ""):
    svg = _build_svg(solution_data, investment_data)
    html = render_chart_html(
        svg_content=svg,
        badge="A-03",
        title="数据流转图",
        system_name=solution_data.system_name,
        note_lines=[
            "• 数据写入流程：接入节点是唯一合法入口，所有数据必须通过完整性校验后方可入库。",
            "• 校验失败的数据拒绝入库并记录异常，不写入正式存储区；系统具备断点续传机制。",
            "• 数据调阅流程：访问终端不直接访问存储资源池，所有调阅均经管理与检索平台代理。",
            "• 数据调阅须经审批流程，调阅操作纳入审计日志，审计日志独立存储并防篡改。",
            "• 原始执法音视频数据在存储全周期内保持只读保护，不得压缩、转码或结构重组。",
        ],
        template_dir=template_dir,
    )
    write_html(html, output_path)


# ── SVG 构建 ──────────────────────────────────────────────────────────────────

def _build_svg(solution_data, investment_data) -> str:
    W, H = 1060, 680
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']

    parts.append(_defs())

    _WRITE_STEPS, _READ_STEPS = _build_steps(solution_data)

    # ── 分隔线 & 泳道标题 ────────────────────────────────────────────────────
    cx = W // 2
    # 左泳道背景
    parts.append(
        f'<rect x="0" y="0" width="{cx}" height="{H}" rx="0" fill="{_WRITE_FILL}" opacity=".3"/>'
    )
    # 右泳道背景
    parts.append(
        f'<rect x="{cx}" y="0" width="{cx}" height="{H}" rx="0" fill="{_READ_FILL}" opacity=".3"/>'
    )
    # 中间分隔线
    parts.append(f'<line x1="{cx}" y1="0" x2="{cx}" y2="{H}" stroke="#CFD8DC" stroke-width="2" stroke-dasharray="8,4"/>')

    # 泳道标题栏
    parts.append(
        f'<rect x="0" y="0" width="{cx}" height="42" fill="{_C_WRITE}" opacity=".9" rx="0"/>'
        f'<text x="{cx//2}" y="27" text-anchor="middle" font-size="14" font-weight="700" '
        f'fill="white" font-family="PingFang SC,Microsoft YaHei,sans-serif">数据写入流程</text>'
    )
    parts.append(
        f'<rect x="{cx}" y="0" width="{cx}" height="42" fill="{_C_READ}" opacity=".9" rx="0"/>'
        f'<text x="{cx+cx//2}" y="27" text-anchor="middle" font-size="14" font-weight="700" '
        f'fill="white" font-family="PingFang SC,Microsoft YaHei,sans-serif">数据调阅流程</text>'
    )

    # ── 绘制步骤 ─────────────────────────────────────────────────────────────
    step_w, step_h = 220, 72
    step_gap = 28       # 步骤间隔
    start_y = 68

    lx = cx // 2 - step_w // 2   # 左泳道步骤 x
    rx = cx + cx // 2 - step_w // 2  # 右泳道步骤 x

    write_centers = []
    read_centers = []

    for i, (sid, title, subtitle, stype, color) in enumerate(_WRITE_STEPS):
        y = start_y + i * (step_h + step_gap)
        cx_node = lx + step_w // 2
        parts.append(_step_box(lx, y, step_w, step_h, sid, title, subtitle, stype, color))
        write_centers.append((cx_node, y, step_h))

    for i, (sid, title, subtitle, stype, color) in enumerate(_READ_STEPS):
        y = start_y + i * (step_h + step_gap)
        cx_node = rx + step_w // 2
        parts.append(_step_box(rx, y, step_w, step_h, sid, title, subtitle, stype, color))
        read_centers.append((cx_node, y, step_h))

    # ── 步骤间箭头 ────────────────────────────────────────────────────────────
    for i in range(len(write_centers) - 1):
        x0, y0, h0 = write_centers[i]
        x1, y1, h1 = write_centers[i+1]
        y_from = y0 + h0
        y_to   = y1 - 2
        parts.append(
            f'<line x1="{x0}" y1="{y_from}" x2="{x0}" y2="{y_to}" '
            f'stroke="{_C_WRITE}" stroke-width="2" marker-end="url(#arrow_write)"/>'
        )

    for i in range(len(read_centers) - 1):
        x0, y0, h0 = read_centers[i]
        x1, y1, h1 = read_centers[i+1]
        y_from = y0 + h0
        y_to   = y1 - 2
        parts.append(
            f'<line x1="{x0}" y1="{y_from}" x2="{x0}" y2="{y_to}" '
            f'stroke="{_C_READ}" stroke-width="2" marker-end="url(#arrow_read)"/>'
        )

    # ── 共享节点横向关系标注 ─────────────────────────────────────────────────
    # W4 (write_centers[3]) ↔ R3 (read_centers[2])：达梦数据库
    _add_cross_link(parts, write_centers[3], read_centers[2], W//2,
                    "达梦数据库 V8.4", "#E65100")
    # W3 (write_centers[2]) ↔ R4 (read_centers[3])：NAS存储
    _add_cross_link(parts, write_centers[2], read_centers[3], W//2,
                    "NAS存储资源池", _C_SHARED)

    parts.append("</svg>")
    return "\n".join(parts)


def _step_box(x, y, w, h, sid, title, subtitle, stype, color) -> str:
    """绘制单个步骤框（process=圆角矩形, decision=菱形, end=椭圆）。"""
    if stype == "decision":
        fill_c = _DECISION_FILL
    elif stype == "end":
        fill_c = "#E8F5E9" if color == _C_READ else "#E3F2FD"
    else:
        fill_c = _READ_FILL if color == _C_READ else _WRITE_FILL

    # 编号徽章
    badge_svg = (
        f'<circle cx="{x+16}" cy="{y+16}" r="12" fill="{color}"/>'
        f'<text x="{x+16}" y="{y+21}" text-anchor="middle" font-size="11" '
        f'fill="white" font-weight="700" font-family="sans-serif">{esc(sid)}</text>'
    )

    # 标题文本（支持换行 \n）
    title_lines = title.split("\n")
    ty1 = y + h // 2 - (len(title_lines) - 1) * 7
    title_svg = ""
    for j, line in enumerate(title_lines):
        title_svg += (
            f'<text x="{x+32}" y="{ty1 + j*14}" font-size="12" font-weight="700" '
            f'fill="{color}" font-family="PingFang SC,Microsoft YaHei,sans-serif">'
            f'{esc(line)}</text>'
        )
    sub_svg = (
        f'<text x="{x+8}" y="{y+h-8}" font-size="9.5" fill="{color}" opacity=".7" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(subtitle)}</text>'
    )

    border_style = f'stroke-dasharray="5,3"' if stype == "decision" else ""
    box_svg = (
        f'<rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" rx="8" fill="#0002"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
        f'fill="{fill_c}" stroke="{color}" stroke-width="1.8" {border_style}/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="5" rx="8" fill="{color}"/>'
        f'<rect x="{x}" y="{y+3}" width="{w}" height="2" fill="{color}"/>'
    )

    return box_svg + badge_svg + title_svg + sub_svg


def _add_cross_link(parts, left_center, right_center, mid_x, label, color):
    """在两列步骤之间画横向虚线标注共享节点。"""
    lx, ly, lh = left_center
    rx, ry, rh = right_center
    # 左步骤右中心
    left_cx  = lx + 110     # step_w//2 + some offset
    left_cy  = ly + lh // 2
    # 右步骤左中心
    right_cx = rx - 110
    right_cy = ry + rh // 2
    # 中间连线（折线）
    my = (left_cy + right_cy) // 2
    parts.append(
        f'<path d="M {left_cx} {left_cy} L {mid_x-10} {left_cy} '
        f'L {mid_x-10} {right_cy} L {right_cx} {right_cy}" '
        f'stroke="{color}" stroke-width="1.5" fill="none" stroke-dasharray="5,3" opacity=".7"/>'
    )
    # 标签
    parts.append(
        f'<rect x="{mid_x-52}" y="{(left_cy+right_cy)//2-10}" width="104" height="20" '
        f'rx="4" fill="white" stroke="{color}" stroke-width="1"/>'
        f'<text x="{mid_x}" y="{(left_cy+right_cy)//2+4}" text-anchor="middle" '
        f'font-size="10" fill="{color}" font-weight="600" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(label)}</text>'
    )


def _defs() -> str:
    return (
        '<defs>'
        f'<marker id="arrow_write" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        f'<polygon points="0 0,10 3.5,0 7" fill="{_C_WRITE}"/></marker>'
        f'<marker id="arrow_read" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        f'<polygon points="0 0,10 3.5,0 7" fill="{_C_READ}"/></marker>'
        '</defs>'
    )
