"""
html_renderer.py - 将 Topology 对象渲染为 HTML+SVG 文件。

渲染策略：
  1. 用 Jinja2 加载 templates/topology_template.html
  2. 调用 SVGBuilder 生成 SVG 字符串（节点、边、分区、图例）
  3. 将 SVG 字符串和元信息注入模板，写出最终 HTML

SVG 元素：
  - <defs>        箭头标记 + 节点图标 symbol 定义
  - <rect>        网络分区背景色块
  - <text>        分区标签
  - <path>        连接边（贝塞尔曲线）
  - <g>           节点组（图标 + 矩形 + 文字）
"""

from __future__ import annotations
import os
import math
from typing import List, Tuple

try:
    from jinja2 import Environment, FileSystemLoader
    _HAS_JINJA2 = True
except ImportError:
    _HAS_JINJA2 = False

from topology_builder import Topology, TopoNode, TopoEdge, NetZone


# ─────────────────────────── 颜色与样式常量 ──────────────────────────────────

# 节点配色：(边框, 填充, 文字, 图标色)
_NODE_STYLE = {
    "server":   ("#1565C0", "#E3F2FD", "#0D47A1", "#1565C0"),
    "storage":  ("#2E7D32", "#E8F5E9", "#1B5E20", "#2E7D32"),
    "database": ("#E65100", "#FFF3E0", "#BF360C", "#E65100"),
    "switch":   ("#6A1B9A", "#F3E5F5", "#4A148C", "#6A1B9A"),
    "terminal": ("#37474F", "#ECEFF1", "#263238", "#37474F"),
    "endpoint": ("#795548", "#EFEBE9", "#4E342E", "#795548"),
    "generic":  ("#607D8B", "#F5F5F5", "#455A64", "#607D8B"),
}

# 边样式：(颜色, 线宽, 虚线)
_EDGE_STYLE = {
    "normal":   ("#9E9E9E", 1.5, ""),
    "business": ("#1565C0", 2.0, ""),
    "storage":  ("#2E7D32", 2.0, "6,3"),
    "database": ("#E65100", 1.5, "4,3"),
    "scaleout": ("#2E7D32", 1.5, "4,2"),
}

# 图例描述
_LEGEND_ITEMS = [
    ("应用服务器",  "server"),
    ("NAS存储节点", "storage"),
    ("数据库",      "database"),
    ("交换机",      "switch"),
    ("访问终端",    "terminal"),
    ("接入设备",    "endpoint"),
]

_LEGEND_EDGES = [
    ("业务网络",   "#1565C0", 2.0, ""),
    ("存储网络",   "#2E7D32", 2.0, "6,3"),
    ("数据库连接", "#E65100", 1.5, "4,3"),
    ("Scale-Out互联", "#2E7D32", 1.5, "4,2"),
]


# ─────────────────────────── SVG 构建器 ──────────────────────────────────────

class SVGBuilder:
    """将 Topology 对象转换为 SVG 字符串。"""

    def __init__(self, topo: Topology):
        self.topo = topo
        self._node_map = {n.id: n for n in topo.nodes}

    def build(self) -> str:
        parts: List[str] = []
        w, h = self.topo.canvas_w, self.topo.canvas_h

        parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
        parts.append(self._defs())
        parts.append(self._zones())
        parts.append(self._edges())
        parts.append(self._nodes())
        parts.append('</svg>')
        return "\n".join(parts)

    # ── defs：箭头标记 ────────────────────────────────────────────────────────

    def _defs(self) -> str:
        markers = []
        for style_key, (color, lw, dash) in _EDGE_STYLE.items():
            mid = f"arrow_{style_key}"
            markers.append(
                f'<marker id="{mid}" markerWidth="10" markerHeight="7" '
                f'refX="9" refY="3.5" orient="auto">'
                f'<polygon points="0 0, 10 3.5, 0 7" fill="{color}" opacity="0.9"/>'
                f'</marker>'
            )
        return "<defs>\n" + "\n".join(markers) + "\n</defs>"

    # ── 分区背景 ──────────────────────────────────────────────────────────────

    def _zones(self) -> str:
        lines = []
        for z in self.topo.zones:
            rx = max(0, z.x)
            ry = max(0, z.y)
            rw = min(z.w, self.topo.canvas_w - rx)
            rh = min(z.h, self.topo.canvas_h - ry)
            lines.append(
                f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
                f'rx="10" fill="{z.color}" stroke="{z.stroke}" '
                f'stroke-width="1.5" stroke-dasharray="6,3" opacity="0.7"/>'
            )
            # 分区标签（左上角）
            lines.append(
                f'<text x="{rx+10:.1f}" y="{ry+16:.1f}" '
                f'font-size="11" fill="{z.stroke}" font-weight="600" '
                f'font-family="PingFang SC, Microsoft YaHei, sans-serif">'
                f'{self._esc(z.name)}</text>'
            )
        return "\n".join(lines)

    # ── 连接边 ────────────────────────────────────────────────────────────────

    def _edges(self) -> str:
        lines = []
        for e in self.topo.edges:
            src = self._node_map.get(e.src)
            dst = self._node_map.get(e.dst)
            if not src or not dst:
                continue

            color, lw, dash = _EDGE_STYLE.get(e.style, _EDGE_STYLE["normal"])
            dash_attr = f'stroke-dasharray="{dash}"' if dash else ""
            marker = f'marker-end="url(#arrow_{e.style})"'

            path_d, lx, ly = self._edge_path(src, dst)

            lines.append(
                f'<path d="{path_d}" stroke="{color}" stroke-width="{lw}" '
                f'fill="none" {dash_attr} {marker} opacity="0.85"/>'
            )
            # 边标签
            if e.label:
                lines.append(
                    f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
                    f'font-size="10" fill="{color}" font-weight="500" '
                    f'font-family="PingFang SC, Microsoft YaHei, sans-serif">'
                    f'<rect/>{self._esc(e.label)}</text>'
                )

        return "\n".join(lines)

    def _edge_path(self, src: TopoNode, dst: TopoNode) -> Tuple[str, float, float]:
        """计算从 src 到 dst 的贝塞尔曲线路径，以及标签中心点。"""
        # 同层（scaleout 互联）：水平连线
        if src.layer == dst.layer:
            x1 = src.x + src.w
            y1 = src.y + src.h / 2
            x2 = dst.x
            y2 = dst.y + dst.h / 2
            # 中段略微弓起
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2 - 18
            d = f"M {x1:.1f} {y1:.1f} Q {mx:.1f} {my:.1f} {x2:.1f} {y2:.1f}"
            lx = mx
            ly = my - 6
        else:
            # 纵向连线：从 src 底边中点 → dst 顶边中点
            x1 = src.x + src.w / 2
            y1 = src.y + src.h
            x2 = dst.x + dst.w / 2
            y2 = dst.y - 2  # 稍微留一点 marker 空间
            cy = (y1 + y2) / 2
            d = f"M {x1:.1f} {y1:.1f} C {x1:.1f} {cy:.1f} {x2:.1f} {cy:.1f} {x2:.1f} {y2:.1f}"
            lx = (x1 + x2) / 2
            ly = cy - 4

        return d, lx, ly

    # ── 节点组 ────────────────────────────────────────────────────────────────

    def _nodes(self) -> str:
        lines = []
        for n in self.topo.nodes:
            lines.append(self._node_g(n))
        return "\n".join(lines)

    def _node_g(self, n: TopoNode) -> str:
        border, fill, text_color, icon_color = _NODE_STYLE.get(n.node_type, _NODE_STYLE["generic"])
        x, y, w, h = n.x, n.y, n.w, n.h
        parts = [f'<g id="{n.id}" class="topo-node">']

        # 阴影矩形（偏移2px）
        parts.append(
            f'<rect x="{x+2:.1f}" y="{y+2:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="8" fill="#00000022"/>'
        )
        # 主矩形
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="8" fill="{fill}" stroke="{border}" stroke-width="2"/>'
        )
        # 顶部色条
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="6" '
            f'rx="8" fill="{border}"/>'
        )
        # 修正顶部色条圆角（底部直角）
        parts.append(
            f'<rect x="{x:.1f}" y="{y+3:.1f}" width="{w:.1f}" height="3" fill="{border}"/>'
        )

        # 设备图标（左侧小图标区域）
        icon_svg = self._icon(n.node_type, x + 8, y + h/2 - 12, 24, 24, icon_color)
        parts.append(icon_svg)

        # 主标签
        parts.append(
            f'<text x="{x+38:.1f}" y="{y+h/2-4:.1f}" '
            f'font-size="12" font-weight="700" fill="{text_color}" '
            f'font-family="PingFang SC, Microsoft YaHei, sans-serif">'
            f'{self._esc(n.label)}</text>'
        )
        # 副标签
        if n.sublabel:
            parts.append(
                f'<text x="{x+38:.1f}" y="{y+h/2+10:.1f}" '
                f'font-size="10" fill="{text_color}" opacity="0.75" '
                f'font-family="PingFang SC, Microsoft YaHei, sans-serif">'
                f'{self._esc(n.sublabel)}</text>'
            )

        parts.append('</g>')
        return "\n".join(parts)

    # ── 设备图标 ──────────────────────────────────────────────────────────────

    def _icon(self, node_type: str, x: float, y: float, w: float, h: float, color: str) -> str:
        """返回对应设备类型的 SVG 图标片段（纯几何，无品牌）。"""
        cx, cy = x + w/2, y + h/2

        if node_type == "server":
            # 机架式服务器：矩形+横线
            lines = [
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" '
                f'fill="none" stroke="{color}" stroke-width="1.8"/>',
            ]
            for i in range(3):
                yl = y + 5 + i * 6
                lines.append(f'<line x1="{x+3:.1f}" y1="{yl:.1f}" x2="{x+w-3:.1f}" y2="{yl:.1f}" '
                              f'stroke="{color}" stroke-width="1.2"/>')
            return "\n".join(lines)

        elif node_type == "storage":
            # 存储阵列：多层矩形堆叠
            layers_s = []
            for i in range(3):
                yl = y + i * 7
                layers_s.append(
                    f'<rect x="{x:.1f}" y="{yl:.1f}" width="{w:.1f}" height="6" rx="1" '
                    f'fill="none" stroke="{color}" stroke-width="1.5"/>'
                )
            return "\n".join(layers_s)

        elif node_type == "database":
            # 数据库：圆柱体（椭圆+矩形+椭圆）
            ew, eh = w, 6
            return (
                f'<rect x="{x:.1f}" y="{y+eh/2:.1f}" width="{w:.1f}" height="{h-eh:.1f}" '
                f'fill="{color}" opacity="0.15" stroke="{color}" stroke-width="1.5"/>'
                f'<ellipse cx="{cx:.1f}" cy="{y+eh/2:.1f}" rx="{ew/2:.1f}" ry="{eh/2:.1f}" '
                f'fill="{color}" opacity="0.25" stroke="{color}" stroke-width="1.5"/>'
                f'<ellipse cx="{cx:.1f}" cy="{y+h-eh/2:.1f}" rx="{ew/2:.1f}" ry="{eh/2:.1f}" '
                f'fill="{color}" opacity="0.15" stroke="{color}" stroke-width="1.5"/>'
            )

        elif node_type == "switch":
            # 交换机：扁平矩形+圆点
            dots = "".join(
                f'<circle cx="{x+5+i*5:.1f}" cy="{cy:.1f}" r="1.5" fill="{color}"/>'
                for i in range(4)
            )
            return (
                f'<rect x="{x:.1f}" y="{y+4:.1f}" width="{w:.1f}" height="{h-8:.1f}" rx="2" '
                f'fill="none" stroke="{color}" stroke-width="1.8"/>'
                + dots
            )

        elif node_type == "terminal":
            # 显示器轮廓
            mw, mh = w, h * 0.7
            return (
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{mw:.1f}" height="{mh:.1f}" rx="2" '
                f'fill="none" stroke="{color}" stroke-width="1.8"/>'
                f'<rect x="{cx-3:.1f}" y="{y+mh:.1f}" width="6" height="{h*0.3:.1f}" '
                f'fill="{color}" opacity="0.5"/>'
                f'<line x1="{cx-8:.1f}" y1="{y+h:.1f}" x2="{cx+8:.1f}" y2="{y+h:.1f}" '
                f'stroke="{color}" stroke-width="2"/>'
            )

        elif node_type == "endpoint":
            # 执法记录仪/终端采集设备：摄像机轮廓
            return (
                f'<rect x="{x:.1f}" y="{y+3:.1f}" width="{w*0.7:.1f}" height="{h-6:.1f}" rx="2" '
                f'fill="none" stroke="{color}" stroke-width="1.8"/>'
                f'<polygon points="{x+w*0.7:.1f},{y+h*0.3:.1f} {x+w:.1f},{y+4:.1f} '
                f'{x+w:.1f},{y+h-4:.1f} {x+w*0.7:.1f},{y+h*0.7:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="1.5"/>'
            )

        else:
            return (
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="3" '
                f'fill="none" stroke="{color}" stroke-width="1.5"/>'
            )

    # ── 工具 ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _esc(s: str) -> str:
        """HTML/XML 转义。"""
        return (s.replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;")
                  .replace('"', "&quot;"))


# ─────────────────────────── 图例 SVG ────────────────────────────────────────

def build_legend_svg() -> str:
    """生成独立的图例 SVG 片段（节点类型 + 线型说明）。"""
    parts = []
    item_w, item_h = 160, 34
    pad = 12

    # 节点图例
    for i, (label, ntype) in enumerate(_LEGEND_ITEMS):
        border, fill, text_c, icon_c = _NODE_STYLE.get(ntype, _NODE_STYLE["generic"])
        x = pad + (i % 3) * (item_w + 8)
        y = pad + (i // 3) * (item_h + 6)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{item_w}" height="{item_h}" rx="6" '
            f'fill="{fill}" stroke="{border}" stroke-width="1.5"/>'
            f'<rect x="{x}" y="{y}" width="{item_w}" height="4" rx="6" fill="{border}"/>'
            f'<rect x="{x}" y="{y+2}" width="{item_w}" height="2" fill="{border}"/>'
            f'<text x="{x+10}" y="{y+22}" font-size="11" fill="{text_c}" '
            f'font-weight="600" font-family="PingFang SC, Microsoft YaHei, sans-serif">'
            f'{label}</text>'
        )

    # 线型图例
    ly_base = pad + 2 * (item_h + 6) + 10
    for i, (label, color, lw, dash) in enumerate(_LEGEND_EDGES):
        x = pad + i * 190
        y = ly_base
        dash_attr = f'stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<line x1="{x}" y1="{y+10}" x2="{x+50}" y2="{y+10}" '
            f'stroke="{color}" stroke-width="{lw}" {dash_attr}/>'
            f'<text x="{x+58}" y="{y+14}" font-size="11" fill="#333" '
            f'font-family="PingFang SC, Microsoft YaHei, sans-serif">{label}</text>'
        )

    total_h = ly_base + 30
    total_w = pad * 2 + 3 * (item_w + 8)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}">'
        + "\n".join(parts)
        + "</svg>"
    )


# ─────────────────────────── 渲染器 ──────────────────────────────────────────

class HTMLRenderer:
    """将 Topology 渲染为 HTML 文件，使用 Jinja2 模板（可选）。"""

    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self._jinja_env = None
        if _HAS_JINJA2 and os.path.isdir(template_dir):
            self._jinja_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=False,
            )

    def render(self, topo: Topology, output_path: str):
        svg_content = SVGBuilder(topo).build()
        legend_svg  = build_legend_svg()

        if self._jinja_env:
            tmpl = self._jinja_env.get_template("topology_template.html")
            html = tmpl.render(
                title=topo.title,
                system_name=topo.system_name,
                svg_content=svg_content,
                legend_svg=legend_svg,
                note_lines=topo.note_lines,
            )
        else:
            # 没有 Jinja2 时，用内联模板降级
            html = self._fallback_html(topo, svg_content, legend_svg)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    @staticmethod
    def _fallback_html(topo: Topology, svg_content: str, legend_svg: str) -> str:
        notes_html = "\n".join(f"<li>{n}</li>" for n in topo.note_lines)
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{topo.title} - {topo.system_name}</title>
<style>
  body {{ font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
         background:#f5f7fa; margin:0; padding:24px; color:#333; }}
  .page-title {{ font-size:20px; font-weight:700; color:#1565C0; margin-bottom:4px; }}
  .system-name {{ font-size:13px; color:#666; margin-bottom:20px; }}
  .card {{ background:#fff; border-radius:12px; box-shadow:0 2px 12px #0002;
           padding:20px; margin-bottom:20px; }}
  .section-label {{ font-size:13px; font-weight:600; color:#1565C0;
                    border-left:3px solid #1565C0; padding-left:8px; margin-bottom:14px; }}
  svg {{ display:block; overflow:visible; }}
  ul.notes {{ font-size:12px; color:#555; line-height:1.9; margin:0; padding-left:18px; }}
</style>
</head>
<body>
<div class="page-title">A-02 &nbsp;网络拓扑图</div>
<div class="system-name">{topo.system_name}</div>

<div class="card">
  <div class="section-label">网络拓扑结构</div>
  {svg_content}
</div>

<div class="card">
  <div class="section-label">图例说明</div>
  {legend_svg}
</div>

<div class="card">
  <div class="section-label">说明</div>
  <ul class="notes">{notes_html}</ul>
</div>
</body>
</html>"""
