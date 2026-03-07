"""
system_architecture.py - A-01 系统总体架构图

分层结构（从上到下）：
  用户访问层  ─  访问终端
  数据接入层  ─  4 种接入方式（来自 建设方案.md）
  应用服务层  ─  管理与检索平台（运行在应用服务器上），含 5 个功能模块
  数据存储层  ─  达梦数据库 V8.4 | Scale-Out NAS 存储资源池
"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from charts.chart_utils import render_chart_html, write_html, esc

# ── 颜色常量 ─────────────────────────────────────────────────────────────────
_LAYER_COLORS = {
    "access_user": ("#ECEFF1", "#546E7A", "#37474F"),    # 灰蓝：访问层
    "access_in":   ("#EFEBE9", "#6D4C41", "#4E342E"),    # 棕：接入层
    "app":         ("#E3F2FD", "#1565C0", "#0D47A1"),    # 蓝：应用层
    "data":        ("#E8F5E9", "#2E7D32", "#1B5E20"),    # 绿：数据层
}
_MODULE_FILL  = "#BBDEFB"
_MODULE_STROKE= "#1565C0"
_MODULE_TEXT  = "#0D47A1"
_ARROW_COLOR  = "#78909C"


# ── 主入口 ────────────────────────────────────────────────────────────────────

def generate(solution_data, investment_data, output_path: str, template_dir: str = ""):
    """生成 A-01 系统总体架构图 HTML 文件。"""
    svg = _build_svg(solution_data, investment_data)
    html = render_chart_html(
        svg_content=svg,
        badge="A-01",
        title="系统总体架构图",
        system_name=solution_data.system_name,
        note_lines=[
            "• 本图表达系统逻辑架构，不反映物理部署位置。",
            "• 应用服务层全部模块均运行于同一应用服务器（双机冗余），不单独部署。",
            "• 数据存储层：达梦数据库 V8.4 存储元数据；NAS 存储资源池存储音视频原始文件。",
            "• 接入层四种来源数据均经接入节点完整性校验后方可入库，不直接写入存储资源池。",
        ],
        template_dir=template_dir,
    )
    write_html(html, output_path)


# ── SVG 构建 ──────────────────────────────────────────────────────────────────

def _build_svg(solution_data, investment_data) -> str:
    W, H = 1100, 680
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']

    # 共用箭头 marker
    parts.append(_defs())

    # ── 各层 Y 坐标 ──────────────────────────────────────────────────────────
    layers = {
        "user_y":  30,   "user_h":  70,
        "in_y":   140,   "in_h":   80,
        "app_y":  270,   "app_h":  150,
        "data_y": 470,   "data_h": 120,
    }

    # 接入方式列表
    access_types = solution_data.access_types or [
        "5G执法记录仪", "采集站", "执法仪本地导入", "既有执法管理平台"
    ]
    access_sublabels = {
        "5G执法记录仪":   "实时回传",
        "采集站":         "批量导入",
        "执法仪本地导入": "USB 接口直连",
        "既有执法管理平台": "接口归集",
    }

    # 功能模块
    func_modules = getattr(solution_data, "functional_modules", None) or [
        "数据接入模块", "存储管理模块", "检索调阅模块", "生命周期管理模块", "运维监控模块"
    ]

    # NAS 节点数
    nas_qty = _find_device_qty(investment_data, "网络存储") or 2
    app_qty = _find_device_qty(investment_data, "应用服务器") or 1

    # ── 层1：用户访问层 ───────────────────────────────────────────────────────
    fill, stroke, tc = _LAYER_COLORS["access_user"]
    y = layers["user_y"]
    h = layers["user_h"]
    parts += _zone_band(10, y, W-20, h, "用户访问层", fill, stroke, tc)
    # 访问终端节点
    parts.append(_node_rect((W-180)//2, y+15, 180, 44, "访问终端", "检索调阅工作站",
                             stroke, fill, tc, icon="terminal"))

    # ── 层间箭头 1 ────────────────────────────────────────────────────────────
    parts.append(_vline(W//2, y+h, layers["in_y"], "业务网络", "#546E7A"))

    # ── 层2：数据接入层 ───────────────────────────────────────────────────────
    fill, stroke, tc = _LAYER_COLORS["access_in"]
    y = layers["in_y"]
    h = layers["in_h"]
    parts += _zone_band(10, y, W-20, h, "数据接入层", fill, stroke, tc)
    n = len(access_types)
    nw, ng = 200, 16
    total = n * nw + (n-1)*ng
    sx = (W - total) // 2
    for i, name in enumerate(access_types):
        nx = sx + i*(nw+ng)
        parts.append(_node_rect(nx, y+14, nw, 50, name,
                                access_sublabels.get(name, ""),
                                stroke, fill, tc, icon="endpoint"))

    # ── 层间箭头 2 ────────────────────────────────────────────────────────────
    parts.append(_vline(W//2, y+h, layers["app_y"], "接入处理 / 校验", "#6D4C41"))

    # ── 层3：应用服务层 ───────────────────────────────────────────────────────
    fill, stroke, tc = _LAYER_COLORS["app"]
    y = layers["app_y"]
    h = layers["app_h"]
    parts += _zone_band(10, y, W-20, h,
                        f"应用服务层（管理与检索平台，运行于应用服务器 ×{app_qty}）",
                        fill, stroke, tc)
    # 功能模块
    mw = min(170, (W-80) // len(func_modules) - 10)
    mg = max(8, (W - 40 - len(func_modules)*mw) // (len(func_modules)+1))
    mx_start = 20 + mg
    for i, mod in enumerate(func_modules):
        mx = mx_start + i*(mw+mg)
        parts.append(_module_box(mx, y+30, mw, 100, mod))

    # ── 层间箭头 3（左 JDBC / 右 NFS/SMB）────────────────────────────────────
    da_y = layers["app_y"] + layers["app_h"]
    db_x = W // 3
    nas_x = 2 * W // 3
    dy_end = layers["data_y"]
    parts.append(_vline(db_x, da_y, dy_end, "JDBC", "#E65100"))
    parts.append(_vline(nas_x, da_y, dy_end, "NFS/SMB ≥10GbE", "#2E7D32"))

    # ── 层4：数据存储层 ───────────────────────────────────────────────────────
    fill, stroke, tc = _LAYER_COLORS["data"]
    y = layers["data_y"]
    h = layers["data_h"]
    parts += _zone_band(10, y, W-20, h, "数据存储层", fill, stroke, tc)

    # 达梦数据库（左）
    db_box_w = W // 2 - 60
    db_box_x = 30
    parts.append(_data_box(db_box_x, y+18, db_box_w, 86,
                           "达梦数据库 V8.4",
                           "元数据 / 业务数据 / 检索索引 / 审计日志",
                           "#E65100", "#FFF3E0"))

    # NAS 存储资源池（右）
    nas_box_x = W // 2 + 20
    nas_box_w = W // 2 - 50
    parts.append(_data_box(nas_box_x, y+18, nas_box_w, 86,
                           f"Scale-Out NAS 存储资源池（×{nas_qty} 节点）",
                           "执法音视频原始文件存储  |  有效容量 ≥ 700TB",
                           "#2E7D32", "#E8F5E9"))

    parts.append("</svg>")
    return "\n".join(parts)


# ── SVG 辅助函数 ──────────────────────────────────────────────────────────────

def _defs() -> str:
    colors = {"#546E7A": "arrow_grey", "#6D4C41": "arrow_brown",
              "#E65100": "arrow_orange", "#2E7D32": "arrow_green"}
    markers = []
    for color, mid in colors.items():
        markers.append(
            f'<marker id="{mid}" markerWidth="10" markerHeight="7" '
            f'refX="9" refY="3.5" orient="auto">'
            f'<polygon points="0 0,10 3.5,0 7" fill="{color}"/>'
            f'</marker>'
        )
    return "<defs>" + "".join(markers) + "</defs>"


def _zone_band(x, y, w, h, label, fill, stroke, tc) -> list:
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.5" stroke-dasharray="6,3" opacity=".75"/>',
        f'<text x="{x+12}" y="{y+18}" font-size="11" fill="{stroke}" font-weight="700" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(label)}</text>',
    ]


def _node_rect(x, y, w, h, label, sublabel, stroke, fill, tc, icon="") -> str:
    icon_svg = _icon(icon, x+8, y+h//2-10, 20, 20, stroke)
    tx = x + 34
    return (
        f'<rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" rx="7" fill="#0003"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="5" rx="7" fill="{stroke}"/>'
        f'<rect x="{x}" y="{y+3}" width="{w}" height="2" fill="{stroke}"/>'
        + icon_svg +
        f'<text x="{tx}" y="{y+h//2-2}" font-size="12" font-weight="700" fill="{tc}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(label)}</text>'
        f'<text x="{tx}" y="{y+h//2+12}" font-size="10" fill="{tc}" opacity=".75" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(sublabel)}</text>'
    )


def _module_box(x, y, w, h, label) -> str:
    # 功能模块方框（蓝色小卡片）
    lines = label.split("模块")
    line1 = lines[0] + ("模块" if len(lines) > 1 else "")
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
        f'fill="{_MODULE_FILL}" stroke="{_MODULE_STROKE}" stroke-width="1.5"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="4" rx="6" fill="{_MODULE_STROKE}"/>'
        f'<rect x="{x}" y="{y+2}" width="{w}" height="2" fill="{_MODULE_STROKE}"/>'
        # 功能图标（简单圆圈占位）
        f'<circle cx="{x+w//2}" cy="{y+42}" r="16" fill="{_MODULE_STROKE}" opacity=".12"/>'
        f'<text x="{x+w//2}" y="{y+48}" text-anchor="middle" font-size="20" '
        f'fill="{_MODULE_STROKE}" font-family="PingFang SC,Microsoft YaHei,sans-serif">'
        f'{_module_icon(label)}</text>'
        f'<text x="{x+w//2}" y="{y+76}" text-anchor="middle" font-size="11" '
        f'fill="{_MODULE_TEXT}" font-weight="600" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(line1)}</text>'
    )


def _module_icon(label: str) -> str:
    icons = {"接入": "↓", "存储": "⊞", "检索": "⊙", "生命周期": "↻", "运维": "⚙"}
    for k, v in icons.items():
        if k in label:
            return v
    return "□"


def _data_box(x, y, w, h, title, subtitle, stroke, fill) -> str:
    return (
        f'<rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" rx="8" fill="#0002"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="6" rx="8" fill="{stroke}"/>'
        f'<rect x="{x}" y="{y+3}" width="{w}" height="3" fill="{stroke}"/>'
        f'<text x="{x+14}" y="{y+30}" font-size="13" font-weight="700" fill="{stroke}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(title)}</text>'
        f'<text x="{x+14}" y="{y+52}" font-size="10.5" fill="{stroke}" opacity=".8" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(subtitle)}</text>'
    )


def _vline(cx, y1, y2, label, color) -> str:
    mid_y = (y1 + y2) // 2
    mid_x = cx + 6
    arrow_id = {"#546E7A": "arrow_grey", "#6D4C41": "arrow_brown",
                "#E65100": "arrow_orange", "#2E7D32": "arrow_green"}.get(color, "arrow_grey")
    return (
        f'<line x1="{cx}" y1="{y1}" x2="{cx}" y2="{y2-2}" '
        f'stroke="{color}" stroke-width="2" marker-end="url(#{arrow_id})"/>'
        f'<text x="{mid_x}" y="{mid_y+4}" font-size="10" fill="{color}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(label)}</text>'
    )


def _icon(icon_type: str, x, y, w, h, color) -> str:
    cx, cy = x + w//2, y + h//2
    if icon_type == "terminal":
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{int(h*.7)}" rx="2" '
            f'fill="none" stroke="{color}" stroke-width="1.5"/>'
            f'<line x1="{cx}" y1="{y+int(h*.7)}" x2="{cx}" y2="{y+h}" '
            f'stroke="{color}" stroke-width="1.5"/>'
            f'<line x1="{cx-6}" y1="{y+h}" x2="{cx+6}" y2="{y+h}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
    if icon_type == "endpoint":
        return (
            f'<rect x="{x}" y="{y+3}" width="{int(w*.7)}" height="{h-6}" rx="2" '
            f'fill="none" stroke="{color}" stroke-width="1.5"/>'
            f'<polygon points="{x+int(w*.7)},{y+int(h*.3)} {x+w},{y+4} '
            f'{x+w},{y+h-4} {x+int(w*.7)},{y+int(h*.7)}" '
            f'fill="none" stroke="{color}" stroke-width="1.2"/>'
        )
    return f'<circle cx="{cx}" cy="{cy}" r="{min(w,h)//2-1}" fill="none" stroke="{color}" stroke-width="1.5"/>'


def _find_device_qty(investment_data, keyword: str) -> int:
    for d in investment_data.devices:
        if keyword in d.name:
            return d.quantity
    return 0
