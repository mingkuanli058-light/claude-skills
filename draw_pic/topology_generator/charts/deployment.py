"""
deployment.py - A-04 部署结构图

表达系统在公安专网机房内的物理/逻辑部署方式：
  ┌─ 机房机柜区 ──────────────────────────────────────────────┐
  │                                                           │
  │  [核心交换机]                                              │
  │       │  业务网络              存储网络 (≥10GbE)           │
  │  [应用服务器×1]  ←─────────────────→  [NAS存储节点×2]     │
  │  ├─ 管理与检索平台                     [Scale-Out NAS]     │
  │  └─ 达梦数据库 V8.4（软件）                                │
  │                                                           │
  └───────────────────────────────────────────────────────────┘
  外部（公安专网）：访问终端 / 接入设备
"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from charts.chart_utils import render_chart_html, write_html, esc

# ── 颜色 ──────────────────────────────────────────────────────────────────────
_C_ROOM      = "#E3F2FD"   # 机房背景
_C_ROOM_STR  = "#1565C0"
_C_NET_ZONE  = "#F3E5F5"   # 网络区
_C_NET_STR   = "#6A1B9A"
_C_SERVER    = "#BBDEFB"   # 服务器
_C_SERVER_S  = "#1565C0"
_C_STORAGE   = "#C8E6C9"   # 存储
_C_STORAGE_S = "#2E7D32"
_C_DB        = "#FFE0B2"   # 数据库
_C_DB_S      = "#E65100"
_C_EXT       = "#ECEFF1"   # 外部区
_C_EXT_S     = "#546E7A"
_C_BIZ_NET   = "#1565C0"   # 业务网络线
_C_STO_NET   = "#2E7D32"   # 存储网络线

# ── 主入口 ────────────────────────────────────────────────────────────────────

def generate(solution_data, investment_data, output_path: str, template_dir: str = ""):
    svg = _build_svg(solution_data, investment_data)
    html = render_chart_html(
        svg_content=svg,
        badge="A-04",
        title="部署结构图",
        system_name=solution_data.system_name,
        note_lines=[
            "• 系统采用中心化部署模式，全部设备集中部署于公安专网机房，不涉及双中心或异地容灾。",
            "• 应用服务器采用国产 CPU 架构（鲲鹏920）与国产操作系统，达梦数据库 V8.4 运行于其上。",
            "• 业务网络承载接入、调阅、管理等应用层流量；存储网络专用于应用服务器与 NAS 间文件读写。",
            "• 两个 NAS 存储节点构成 Scale-Out 资源池，节点互联带宽 ≥10GbE，扩容无需停机。",
            "• 部署边界：不含 IP 地址、不引入双中心、不引入灾备结构。",
        ],
        template_dir=template_dir,
    )
    write_html(html, output_path)


# ── SVG 构建 ──────────────────────────────────────────────────────────────────

def _build_svg(solution_data, investment_data) -> str:
    W, H = 980, 620
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    parts.append(_defs())

    # ── 外部区（公安专网侧）─────────────────────────────────────────────────
    ext_h = 80
    parts += [
        f'<rect x="0" y="0" width="{W}" height="{ext_h}" rx="0" '
        f'fill="{_C_EXT}" stroke="{_C_EXT_S}" stroke-width="1" stroke-dasharray="6,4"/>',
        f'<text x="14" y="18" font-size="11" font-weight="700" fill="{_C_EXT_S}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">公安专网（外部接入侧）</text>',
    ]

    # 外部节点：访问终端 + 来自 solution_data 的接入方式
    _access_sublabels = {
        "5G执法记录仪":      "实时回传",
        "采集站":            "批量导入",
        "执法仪本地导入":    "本地导入",
        "既有执法管理平台":  "接口归集",
    }
    _default_access = ["5G执法记录仪", "采集站", "执法仪本地导入", "既有执法管理平台"]
    access_types = (solution_data.access_types if solution_data.access_types else _default_access)
    ext_items = [("访问终端", "检索调阅")] + [
        (at, _access_sublabels.get(at, "")) for at in access_types
    ]
    _node_w = 140
    _total_count = len(ext_items)
    _spacing = max(_node_w + 10, (W - 20) // _total_count)
    _start_x = (W - _spacing * (_total_count - 1) - _node_w) // 2
    for i, (label, sub) in enumerate(ext_items):
        ex = _start_x + i * _spacing
        parts.append(_small_node(ex, 22, label, sub, _C_EXT_S, _C_EXT))

    # ── 机房边框 ─────────────────────────────────────────────────────────────
    room_y = ext_h + 20
    room_h = H - room_y - 20
    parts += [
        f'<rect x="10" y="{room_y}" width="{W-20}" height="{room_h}" rx="12" '
        f'fill="{_C_ROOM}" stroke="{_C_ROOM_STR}" stroke-width="2"/>',
        f'<text x="24" y="{room_y+20}" font-size="12" font-weight="700" fill="{_C_ROOM_STR}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">公安专网机房（集中部署）</text>',
    ]

    # ── 核心交换机 ────────────────────────────────────────────────────────────
    sw_w, sw_h = 280, 46
    sw_x = (W - sw_w) // 2
    sw_y = room_y + 36
    parts.append(_rack_box(sw_x, sw_y, sw_w, sw_h,
                           "核心交换机", "公安专网  |  业务/存储网络汇聚",
                           _C_NET_STR, _C_NET_ZONE, icon="switch"))

    # ── 从外部到交换机的公网虚线（代表多路接入）─────────────────────────────
    parts.append(
        f'<line x1="{W//2}" y1="{ext_h}" x2="{W//2}" y2="{sw_y}" '
        f'stroke="{_C_EXT_S}" stroke-width="1.5" stroke-dasharray="6,4" '
        f'marker-end="url(#arrow_ext)"/>'
        f'<text x="{W//2+6}" y="{(ext_h+sw_y)//2+4}" font-size="10" fill="{_C_EXT_S}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">公安专网接入</text>'
    )

    # ── 应用服务器区 ─────────────────────────────────────────────────────────
    app_qty = _find_qty(investment_data, "应用服务器") or 1
    srv_x, srv_y = 60, sw_y + sw_h + 60
    srv_w, srv_h = 330, 180

    # 区域背景
    parts += [
        f'<rect x="{srv_x}" y="{srv_y}" width="{srv_w}" height="{srv_h}" rx="10" '
        f'fill="{_C_SERVER}" fill-opacity=".5" stroke="{_C_SERVER_S}" stroke-width="1.5"/>',
        f'<text x="{srv_x+12}" y="{srv_y+18}" font-size="11" fill="{_C_SERVER_S}" '
        f'font-weight="700" font-family="PingFang SC,Microsoft YaHei,sans-serif">'
        f'应用服务器 ×{app_qty}（鲲鹏920 + 国产OS）</text>',
    ]
    # 应用服务器主机图标
    parts.append(_rack_box(srv_x+14, srv_y+26, srv_w-28, 54,
                           "管理与检索平台", "数据接入 / 检索调阅 / 生命周期管理 / 运维监控",
                           _C_SERVER_S, "white", icon="server"))
    # 达梦数据库（软件，运行于服务器上）
    parts.append(_rack_box(srv_x+14, srv_y+94, srv_w-28, 72,
                           "达梦数据库 V8.4", "元数据存储 / 业务数据 / 检索索引 / 审计日志\n（软件，运行于应用服务器）",
                           _C_DB_S, _C_DB, icon="database"))

    # ── NAS 存储区 ────────────────────────────────────────────────────────────
    nas_qty = _find_qty(investment_data, "网络存储") or 2
    nas_zone_x = W - 380
    nas_zone_y = sw_y + sw_h + 60
    nas_zone_w = 310
    nas_zone_h = 180
    # NAS 区域背景
    parts += [
        f'<rect x="{nas_zone_x}" y="{nas_zone_y}" width="{nas_zone_w}" height="{nas_zone_h}" '
        f'rx="10" fill="{_C_STORAGE}" fill-opacity=".5" stroke="{_C_STORAGE_S}" stroke-width="1.5"/>',
        f'<text x="{nas_zone_x+12}" y="{nas_zone_y+18}" font-size="11" '
        f'fill="{_C_STORAGE_S}" font-weight="700" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">'
        f'Scale-Out NAS 存储资源池（×{nas_qty} 节点）</text>',
    ]
    # 每个 NAS 节点
    node_h = 60
    node_gap = 14
    for i in range(nas_qty):
        ny = nas_zone_y + 28 + i * (node_h + node_gap)
        parts.append(_rack_box(nas_zone_x+14, ny, nas_zone_w-28, node_h,
                               f"NAS 存储节点 {i+1}",
                               "8U / 48盘位  |  Scale-Out NAS  |  RAID保护",
                               _C_STORAGE_S, "white", icon="storage"))

    # ── 网络连接线 ────────────────────────────────────────────────────────────
    sw_cx = sw_x + sw_w // 2
    sw_by = sw_y + sw_h
    srv_cx = srv_x + srv_w // 2
    srv_ty = srv_y
    nas_cx = nas_zone_x + nas_zone_w // 2
    nas_ty = nas_zone_y

    # 交换机 → 应用服务器（业务网络，蓝色实线）
    parts.append(_connector(sw_cx - 40, sw_by, srv_cx, srv_ty,
                             "业务网络", _C_BIZ_NET, dash=""))
    # 交换机 → NAS（存储网络，绿色虚线）
    parts.append(_connector(sw_cx + 40, sw_by, nas_cx, nas_ty,
                             "存储网络 ≥10GbE", _C_STO_NET, dash="6,3"))
    # 应用服务器 → NAS（双向存储网络，绿色虚线）
    srv_rx = srv_x + srv_w
    srv_my = srv_y + srv_h // 2
    nas_lx = nas_zone_x
    nas_my = nas_zone_y + nas_zone_h // 2
    parts.append(
        f'<path d="M {srv_rx} {srv_my} C {srv_rx+30} {srv_my} {nas_lx-30} {nas_my} {nas_lx} {nas_my}" '
        f'stroke="{_C_STO_NET}" stroke-width="2" fill="none" stroke-dasharray="6,3" '
        f'marker-end="url(#arrow_storage)" marker-start="url(#arrow_storage_r)"/>'
        f'<text x="{(srv_rx+nas_lx)//2}" y="{(srv_my+nas_my)//2-6}" '
        f'text-anchor="middle" font-size="10" fill="{_C_STO_NET}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">NFS/SMB ≥10GbE</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


# ── SVG 辅助 ──────────────────────────────────────────────────────────────────

def _defs() -> str:
    return (
        '<defs>'
        f'<marker id="arrow_biz" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        f'<polygon points="0 0,8 3,0 6" fill="{_C_BIZ_NET}"/></marker>'
        f'<marker id="arrow_storage" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        f'<polygon points="0 0,8 3,0 6" fill="{_C_STO_NET}"/></marker>'
        f'<marker id="arrow_storage_r" markerWidth="8" markerHeight="6" refX="1" refY="3" orient="auto-start-reverse">'
        f'<polygon points="0 0,8 3,0 6" fill="{_C_STO_NET}"/></marker>'
        f'<marker id="arrow_ext" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        f'<polygon points="0 0,8 3,0 6" fill="{_C_EXT_S}"/></marker>'
        '</defs>'
    )


def _rack_box(x, y, w, h, label, sublabel, stroke, fill, icon="server") -> str:
    icon_svg = _device_icon(icon, x+8, y+h//2-11, 22, 22, stroke)
    ty1 = y + h//2 - 3
    lines = sublabel.split("\n")
    sub_svgs = ""
    for i, line in enumerate(lines):
        sub_svgs += (
            f'<text x="{x+36}" y="{ty1+13+i*11}" font-size="9.5" fill="{stroke}" opacity=".75" '
            f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(line)}</text>'
        )
    return (
        f'<rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" rx="6" fill="#0002"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="5" rx="6" fill="{stroke}"/>'
        f'<rect x="{x}" y="{y+3}" width="{w}" height="2" fill="{stroke}"/>'
        + icon_svg +
        f'<text x="{x+36}" y="{ty1}" font-size="12" font-weight="700" fill="{stroke}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(label)}</text>'
        + sub_svgs
    )


def _small_node(x, y, label, sub, stroke, fill) -> str:
    w, h = 140, 44
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
        f'<text x="{x+8}" y="{y+17}" font-size="11" font-weight="600" fill="{stroke}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(label)}</text>'
        f'<text x="{x+8}" y="{y+32}" font-size="9.5" fill="{stroke}" opacity=".7" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(sub)}</text>'
    )


def _connector(x1, y1, x2, y2, label, color, dash="") -> str:
    mid_x = (x1 + x2) // 2
    mid_y = (y1 + y2) // 2
    dash_attr = f'stroke-dasharray="{dash}"' if dash else ""
    arrow_id = "arrow_storage" if "存储" in label or "绿" in label else "arrow_biz"
    if color == _C_STO_NET:
        arrow_id = "arrow_storage"
    else:
        arrow_id = "arrow_biz"
    return (
        f'<path d="M {x1} {y1} C {x1} {mid_y} {x2} {mid_y} {x2} {y2}" '
        f'stroke="{color}" stroke-width="2" fill="none" {dash_attr} '
        f'marker-end="url(#{arrow_id})"/>'
        f'<text x="{mid_x+6}" y="{mid_y}" font-size="10" fill="{color}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(label)}</text>'
    )


def _device_icon(icon_type: str, x, y, w, h, color) -> str:
    cx, cy = x + w//2, y + h//2
    if icon_type == "server":
        lines = "".join(
            f'<line x1="{x+2}" y1="{y+4+i*6}" x2="{x+w-2}" y2="{y+4+i*6}" '
            f'stroke="{color}" stroke-width="1.2"/>' for i in range(3)
        )
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" '
                f'fill="none" stroke="{color}" stroke-width="1.5"/>' + lines)
    if icon_type == "storage":
        rows = "".join(
            f'<rect x="{x}" y="{y+i*8}" width="{w}" height="7" rx="1" '
            f'fill="none" stroke="{color}" stroke-width="1.3"/>' for i in range(3)
        )
        return rows
    if icon_type == "database":
        return (
            f'<rect x="{x}" y="{y+4}" width="{w}" height="{h-8}" '
            f'fill="{color}" opacity=".12" stroke="{color}" stroke-width="1.4"/>'
            f'<ellipse cx="{cx}" cy="{y+4}" rx="{w//2}" ry="4" '
            f'fill="{color}" opacity=".25" stroke="{color}" stroke-width="1.4"/>'
        )
    if icon_type == "switch":
        dots = "".join(
            f'<circle cx="{x+4+i*6}" cy="{cy}" r="2" fill="{color}"/>'
            for i in range(4)
        )
        return (f'<rect x="{x}" y="{cy-6}" width="{w}" height="12" rx="2" '
                f'fill="none" stroke="{color}" stroke-width="1.5"/>' + dots)
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="none" stroke="{color}" stroke-width="1.4"/>'


def _find_qty(investment_data, keyword: str) -> int:
    for d in investment_data.devices:
        if keyword in d.name:
            return d.quantity
    return 0
