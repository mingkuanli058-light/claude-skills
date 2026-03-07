"""
render_svg.py  —  工程表达级 SVG 渲染器
符合《图件结构化 JSON 输出规范 V1.1》

用法：
    python render_svg.py <input.json> [output.svg]
"""

import json
import math
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# 配色变量
# ═══════════════════════════════════════════════════════════
PRIMARY_COLOR  = "#2C5282"   # 主色调（深蓝）
DEVICE_COLOR   = "#E53E3E"   # 设备默认色
WARNING_COLOR  = "#C05621"   # 警告色

DEVICE_PALETTE = [
    "#C53030", "#2B6CB0", "#276749", "#6B46C1",
    "#C05621", "#2C7A7B", "#702459", "#2D3748",
]

WALL_COLOR    = "#1A202C"
ROOM_FILL_A   = "#F7FAFC"
ROOM_FILL_B   = "#EDF2F7"
FIXED_GRAD_A  = "#EBF8FF"
FIXED_GRAD_B  = "#63B3ED"
FIXED_STROKE  = "#2B6CB0"
GRID_COLOR    = "#E2E8F0"
ANNOT_BG      = "#FFFFFF"
ANNOT_STROKE  = "#CBD5E0"
FONT          = "Arial, 'Microsoft YaHei', sans-serif"

# ═══════════════════════════════════════════════════════════
# 渲染参数
# ═══════════════════════════════════════════════════════════
SCALE          = 60    # 1m = 60px
MARGIN_LEFT    = 72
MARGIN_TOP     = 58
MARGIN_RIGHT   = 220   # 图例区宽度
MARGIN_BOTTOM  = 90
WALL_W         = 5
CAM_R          = 12    # 摄像机符号半径（symbol viewBox 的 12）
FAN_LEN_DOME   = 110
FAN_LEN_BULLET = 150
FAN_HALF_DOME  = 50    # 度，单侧
FAN_HALF_BULLET = 35   # 度，单侧


def m2px(m: float) -> float:
    return m * SCALE


# ═══════════════════════════════════════════════════════════
# 坐标计算
# ═══════════════════════════════════════════════════════════

def _align_on_axis(room_span, el_span, align, direction):
    if direction == "h":
        if align == "left":   return 0.0
        if align == "right":  return room_span - el_span
    else:
        if align == "top":    return 0.0
        if align == "bottom": return room_span - el_span
    return (room_span - el_span) / 2.0


def fixed_element_xy(space_w, space_l, el):
    ew  = m2px(el["size"]["width_m"])
    ed  = m2px(el["size"]["depth_m"])
    anc = el["position"]["anchor"]
    aln = el["position"]["align"]
    off = m2px(el["position"].get("offset_m", 0))
    W, L = m2px(space_w), m2px(space_l)
    if anc == "north":
        return _align_on_axis(W, ew, aln, "h"), off
    if anc == "south":
        return _align_on_axis(W, ew, aln, "h"), L - ed - off
    if anc == "west":
        return off, _align_on_axis(L, ed, aln, "v")
    if anc == "east":
        return W - ew - off, _align_on_axis(L, ed, aln, "v")
    return (W - ew) / 2, (L - ed) / 2


def _uniform_grid(W, L, n, off):
    if n == 0:
        return []
    cols = max(1, round(math.sqrt(n * W / L)))
    rows = math.ceil(n / cols)
    pts = []
    for r in range(rows):
        for c in range(cols):
            if len(pts) >= n:
                break
            pts.append((
                off + (c + 0.5) * (W - 2 * off) / cols,
                off + (r + 0.5) * (L - 2 * off) / rows,
            ))
    return pts


def _perimeter_t(W, L, o, t):
    top = W - 2*o; right = L - 2*o
    perim = 2 * (top + right)
    d = t * perim
    if d <= top:     return (o + d, o)
    d -= top
    if d <= right:   return (W - o, o + d)
    d -= right
    if d <= top:     return (W - o - d, L - o)
    d -= top
    return (o, L - o - d)


def device_positions(space_w, space_l, device):
    W = m2px(space_w); L = m2px(space_l)
    n = device["count"]
    strat = device["layout_strategy"]
    off = m2px(device.get("constraints", {}).get("offset_from_wall_mm", 500) / 1000)
    if strat == "diagonal":
        if n == 1:  return [(off, off)]
        if n == 2:  return [(off, off), (W - off, L - off)]
        return [(off + i/(n-1)*(W-2*off), off + i/(n-1)*(L-2*off)) for i in range(n)]
    if strat == "four_corners":
        base = [(off, off), (W-off, off), (off, L-off), (W-off, L-off)]
        return (base[:n] if n <= 4 else base + _uniform_grid(W, L, n-4, off))
    if strat == "single_side":
        return [(off + (i+1)*(W-2*off)/(n+1), off) for i in range(n)]
    if strat == "perimeter":
        return [_perimeter_t(W, L, off, i/n) for i in range(n)]
    if strat == "radial":
        cx, cy = W/2, L/2; r = min(W, L)/2*0.6
        return [(cx + r*math.cos(2*math.pi*i/n - math.pi/2),
                 cy + r*math.sin(2*math.pi*i/n - math.pi/2)) for i in range(n)]
    return _uniform_grid(W, L, n, off)


# ═══════════════════════════════════════════════════════════
# 摄像机方向 & 视场扇形
# ═══════════════════════════════════════════════════════════

def camera_angle_deg(px, py, W, L):
    """
    计算摄像机朝向角（标准数学坐标：0=右，90=上，逆时针）。
    规则：指向房间中心。
    """
    cx, cy = W / 2, L / 2
    dx, dy = cx - px, cy - py
    if abs(dx) < 0.5 and abs(dy) < 0.5:
        return 270.0
    return math.degrees(math.atan2(-dy, dx)) % 360


def fan_path(cx, cy, angle_deg, fan_half_deg, length):
    """
    返回视场扇形 SVG path。
    angle_deg: 标准数学角（0=右，90=上，逆时针）。
    sweep-flag=1（SVG 顺时针=标准逆时针），使扇形覆盖中间方向。
    """
    a1 = math.radians(angle_deg - fan_half_deg)
    a2 = math.radians(angle_deg + fan_half_deg)
    x1 = cx + length * math.cos(a1)
    y1 = cy - length * math.sin(a1)
    x2 = cx + length * math.cos(a2)
    y2 = cy - length * math.sin(a2)
    laf = 1 if fan_half_deg * 2 > 180 else 0
    return f"M {cx:.1f},{cy:.1f} L {x1:.1f},{y1:.1f} A {length:.1f},{length:.1f} 0 {laf},1 {x2:.1f},{y2:.1f} Z"


def direction_arrow(cx, cy, angle_deg, arm, color):
    """返回朝向箭头的 SVG 元素列表（线 + 三角箭头）。"""
    a = math.radians(angle_deg)
    tx = cx + arm * math.cos(a)
    ty = cy - arm * math.sin(a)
    head, spread = 8, math.radians(30)
    lb_x = tx - head * math.cos(a - spread)
    lb_y = ty + head * math.sin(a - spread)
    rb_x = tx - head * math.cos(a + spread)
    rb_y = ty + head * math.sin(a + spread)
    return [
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" '
        f'stroke="{color}" stroke-width="1.8" opacity="0.85"/>',
        f'<polygon points="{tx:.1f},{ty:.1f} {lb_x:.1f},{lb_y:.1f} {rb_x:.1f},{rb_y:.1f}" '
        f'fill="{color}" opacity="0.85"/>',
    ]


# ═══════════════════════════════════════════════════════════
# SVG 辅助函数
# ═══════════════════════════════════════════════════════════

def _esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")


def _text_w(text, size):
    """估算文本像素宽（CJK≈size*0.95，ASCII≈size*0.6）。"""
    return sum(size*0.95 if ord(c) > 127 else size*0.6 for c in text)


def label_box(x, y, text, size=9, tc="#2D3748", bg=ANNOT_BG, padding=5):
    """白底圆角标注框，居中于 (x, y)。"""
    tw = _text_w(text, size) + padding * 2
    th = size + padding * 2
    rx, ry = x - tw/2, y - th/2
    return [
        f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{tw:.1f}" height="{th:.1f}" '
        f'rx="3" fill="{bg}" stroke="{ANNOT_STROKE}" stroke-width="0.8" opacity="0.92"/>',
        f'<text x="{x:.1f}" y="{y + size*0.37:.1f}" text-anchor="middle" '
        f'font-size="{size}" fill="{tc}">{_esc(text)}</text>',
    ]


# ═══════════════════════════════════════════════════════════
# SVG <defs>
# ═══════════════════════════════════════════════════════════

def build_defs(devices, ox, oy, W_px, L_px):
    d = ["<defs>"]

    # ── 滤镜 ──
    d += [
        '<filter id="drop_shadow" x="-15%" y="-15%" width="130%" height="130%">',
        '  <feDropShadow dx="3" dy="4" stdDeviation="4" flood-color="#00000028"/>',
        '</filter>',
        '<filter id="soft_shadow" x="-10%" y="-10%" width="120%" height="120%">',
        '  <feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="#00000020"/>',
        '</filter>',
    ]

    # ── 固定设施渐变 ──
    d += [
        '<linearGradient id="fixed_grad" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'  <stop offset="0%"   stop-color="{FIXED_GRAD_A}"/>',
        f'  <stop offset="100%" stop-color="{FIXED_GRAD_B}" stop-opacity="0.5"/>',
        '</linearGradient>',
    ]

    # ── 房间背景渐变 ──
    d += [
        '<linearGradient id="room_grad" x1="0%" y1="0%" x2="100%" y2="100%">',
        f'  <stop offset="0%"   stop-color="{ROOM_FILL_A}"/>',
        f'  <stop offset="100%" stop-color="{ROOM_FILL_B}"/>',
        '</linearGradient>',
    ]

    # ── 视场扇形渐变（每设备一个） ──
    for idx, _ in enumerate(devices):
        color = DEVICE_PALETTE[idx % len(DEVICE_PALETTE)]
        d += [
            f'<radialGradient id="fan_grad_{idx}" cx="0%" cy="50%" r="100%" '
            f'gradientTransform="rotate(0)">',
            f'  <stop offset="0%"   stop-color="{color}" stop-opacity="0.30"/>',
            f'  <stop offset="100%" stop-color="{color}" stop-opacity="0.03"/>',
            f'</radialGradient>',
        ]

    # ── 房间裁剪框 ──
    d += [
        '<clipPath id="room_clip">',
        f'  <rect x="{ox}" y="{oy}" width="{W_px:.0f}" height="{L_px:.0f}"/>',
        '</clipPath>',
    ]

    # ── 半球摄像机 symbol（viewBox="-12 -12 24 24"，中心在原点） ──
    d += [
        '<symbol id="sym_dome" viewBox="-12 -12 24 24" overflow="visible">',
        '  <!-- 外环：currentColor -->',
        '  <circle cx="0" cy="0" r="11" fill="none" stroke="currentColor" stroke-width="2.2"/>',
        '  <!-- 灰色穹顶外壳 -->',
        '  <circle cx="0" cy="0" r="8.5" fill="#4A5568"/>',
        '  <!-- 深色镜头 -->',
        '  <circle cx="0" cy="0" r="5.2" fill="#1A365D"/>',
        '  <!-- 底座 -->',
        '  <rect x="-7" y="5.5" width="14" height="3" rx="1.5" fill="#2D3748"/>',
        '  <!-- 镜头高光 -->',
        '  <circle cx="-1.8" cy="-1.8" r="1.6" fill="white" opacity="0.55"/>',
        '</symbol>',
    ]

    # ── 枪式摄像机 symbol（viewBox="-12 -12 24 24"） ──
    d += [
        '<symbol id="sym_bullet" viewBox="-12 -12 24 24" overflow="visible">',
        '  <!-- 机身 -->',
        '  <rect x="-11" y="-4.5" width="18" height="9" rx="2.5" fill="#4A5568"/>',
        '  <!-- 镜头端盖 -->',
        '  <rect x="5.5" y="-3.5" width="6.5" height="7" rx="2" fill="#2D3748"/>',
        '  <!-- 镜头玻璃 -->',
        '  <circle cx="9" cy="0" r="2.8" fill="#1A365D"/>',
        '  <!-- 安装支架 -->',
        '  <rect x="-3" y="4.5" width="6" height="4.5" rx="1" fill="#2D3748"/>',
        '  <!-- 机身描边：currentColor -->',
        '  <rect x="-11" y="-4.5" width="18" height="9" rx="2.5" fill="none"',
        '        stroke="currentColor" stroke-width="1.8"/>',
        '  <!-- 镜头高光 -->',
        '  <circle cx="8" cy="-1.2" r="0.9" fill="white" opacity="0.6"/>',
        '</symbol>',
    ]

    d.append("</defs>")
    return d


# ═══════════════════════════════════════════════════════════
# 主构建函数
# ═══════════════════════════════════════════════════════════

def build_svg(data: dict) -> str:
    ld    = data["layout_data"]
    space = ld["space"]
    sl    = space["size"]["length_m"]
    sw    = space["size"]["width_m"]
    sh    = space["size"].get("height_m", 0)

    W_px     = m2px(sw)
    L_px     = m2px(sl)
    canvas_w = W_px + MARGIN_LEFT + MARGIN_RIGHT
    canvas_h = L_px + MARGIN_TOP  + MARGIN_BOTTOM

    ox, oy = MARGIN_LEFT, MARGIN_TOP   # 房间原点
    devices = ld.get("devices", [])

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{canvas_w:.0f}" height="{canvas_h:.0f}" '
        f'font-family="{FONT}">'
    )
    out += build_defs(devices, ox, oy, W_px, L_px)

    # ═══════════════════════════════
    # LAYER 1: background_layer
    # ═══════════════════════════════
    out.append('<g id="background_layer">')
    out.append(f'<rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" fill="white"/>')
    # 1m 网格
    grid_step = m2px(1)
    xi = 0
    while xi <= W_px + 0.5:
        lx = ox + xi
        out.append(f'<line x1="{lx:.1f}" y1="{oy}" x2="{lx:.1f}" y2="{oy+L_px}" '
                   f'stroke="{GRID_COLOR}" stroke-width="0.5"/>')
        xi += grid_step
    yi = 0
    while yi <= L_px + 0.5:
        ly = oy + yi
        out.append(f'<line x1="{ox}" y1="{ly:.1f}" x2="{ox+W_px}" y2="{ly:.1f}" '
                   f'stroke="{GRID_COLOR}" stroke-width="0.5"/>')
        yi += grid_step
    out.append('</g>')

    # ═══════════════════════════════
    # LAYER 2: architecture_layer
    # ═══════════════════════════════
    out.append('<g id="architecture_layer">')
    # 房间本体（渐变 + 投影）
    out.append(
        f'<rect x="{ox}" y="{oy}" width="{W_px:.0f}" height="{L_px:.0f}" '
        f'fill="url(#room_grad)" stroke="{WALL_COLOR}" stroke-width="{WALL_W}" '
        f'filter="url(#drop_shadow)"/>'
    )
    # 内墙线（轻描）
    out.append(
        f'<rect x="{ox}" y="{oy}" width="{W_px:.0f}" height="{L_px:.0f}" '
        f'fill="none" stroke="{WALL_COLOR}" stroke-width="1.2" opacity="0.25"/>'
    )
    # 标题
    title = f'{_esc(data.get("drawing_type","图件"))} — {_esc(space["name"])}'
    out.append(
        f'<text x="{canvas_w/2:.1f}" y="22" text-anchor="middle" '
        f'font-size="16" font-weight="bold" fill="{PRIMARY_COLOR}">{title}</text>'
    )
    note = f'空间尺寸：{sl}m（长）× {sw}m（宽）' + (f'× {sh}m（层高）' if sh else '')
    out.append(
        f'<text x="{canvas_w/2:.1f}" y="40" text-anchor="middle" '
        f'font-size="10" fill="#718096">{_esc(note)}</text>'
    )
    # 尺寸标注
    ay = oy - 14
    out.append(f'<line x1="{ox}" y1="{ay}" x2="{ox+W_px}" y2="{ay}" '
               f'stroke="#A0AEC0" stroke-width="1" stroke-dasharray="3,2"/>')
    out.append(f'<line x1="{ox}" y1="{ay-4}" x2="{ox}" y2="{ay+4}" stroke="#A0AEC0" stroke-width="1.2"/>')
    out.append(f'<line x1="{ox+W_px}" y1="{ay-4}" x2="{ox+W_px}" y2="{ay+4}" stroke="#A0AEC0" stroke-width="1.2"/>')
    out += label_box(ox + W_px/2, ay, f'{sw}m', size=9, tc="#718096")

    ax = ox - 18
    out.append(f'<line x1="{ax}" y1="{oy}" x2="{ax}" y2="{oy+L_px}" '
               f'stroke="#A0AEC0" stroke-width="1" stroke-dasharray="3,2"/>')
    out.append(f'<line x1="{ax-4}" y1="{oy}" x2="{ax+4}" y2="{oy}" stroke="#A0AEC0" stroke-width="1.2"/>')
    out.append(f'<line x1="{ax-4}" y1="{oy+L_px}" x2="{ax+4}" y2="{oy+L_px}" stroke="#A0AEC0" stroke-width="1.2"/>')
    out.append(
        f'<text x="{ax-6:.1f}" y="{oy+L_px/2:.1f}" text-anchor="middle" '
        f'font-size="9" fill="#718096" '
        f'transform="rotate(-90,{ax-6:.1f},{oy+L_px/2:.1f})">{sl}m</text>'
    )
    # 北向箭头
    nx, ny = ox + W_px - 24, oy + 26
    out.append(
        f'<polygon points="{nx},{ny-14} {nx-7},{ny+5} {nx},{ny+1} {nx+7},{ny+5}" '
        f'fill="{PRIMARY_COLOR}" opacity="0.85"/>'
    )
    out.append(f'<text x="{nx}" y="{ny+20}" text-anchor="middle" '
               f'font-size="9" font-weight="bold" fill="{PRIMARY_COLOR}">N</text>')
    # 比例尺（左下，5m 带刻度）
    sb_w = m2px(5)
    sbx, sby = ox + 6, oy + L_px + 18
    for k in range(5):
        fc = "#4A5568" if k % 2 == 0 else "white"
        out.append(f'<rect x="{sbx+k*sb_w/5:.1f}" y="{sby-5}" width="{sb_w/5:.1f}" height="10" '
                   f'fill="{fc}"/>')
    out.append(f'<rect x="{sbx}" y="{sby-5}" width="{sb_w:.0f}" height="10" '
               f'rx="2" fill="none" stroke="#A0AEC0" stroke-width="1"/>')
    out.append(f'<text x="{sbx}" y="{sby+16}" font-size="8" fill="#A0AEC0">0</text>')
    out.append(f'<text x="{sbx+sb_w:.1f}" y="{sby+16}" text-anchor="end" '
               f'font-size="8" fill="#A0AEC0">5m</text>')
    out.append('</g>')

    # ═══════════════════════════════
    # LAYER 3: fixed_element_layer
    # ═══════════════════════════════
    out.append('<g id="fixed_element_layer">')
    for el in ld.get("fixed_elements", []):
        fx, fy = fixed_element_xy(sw, sl, el)
        fw = m2px(el["size"]["width_m"])
        fd = m2px(el["size"]["depth_m"])
        out.append(
            f'<rect x="{ox+fx:.1f}" y="{oy+fy:.1f}" width="{fw:.1f}" height="{fd:.1f}" '
            f'rx="3" fill="url(#fixed_grad)" stroke="{FIXED_STROKE}" stroke-width="1.5" '
            f'filter="url(#soft_shadow)"/>'
        )
        cx_el = ox + fx + fw / 2
        cy_el = oy + fy + fd / 2
        out += label_box(cx_el, cy_el, el["name"], size=9, tc=FIXED_STROKE)
    out.append('</g>')

    # ═══════════════════════════════
    # LAYER 4: device_layer
    # ═══════════════════════════════
    out.append('<g id="device_layer">')
    legend_items = []

    for idx, dev in enumerate(devices):
        color    = DEVICE_PALETTE[idx % len(DEVICE_PALETTE)]
        pts      = device_positions(sw, sl, dev)
        dev_type = dev["type"]
        is_dome  = not ("枪" in dev_type or "bullet" in dev_type.lower())
        fan_len  = FAN_LEN_DOME  if is_dome else FAN_LEN_BULLET
        fan_half = FAN_HALF_DOME if is_dome else FAN_HALF_BULLET
        h_label  = dev.get("constraints", {}).get("install_height_m")

        # ── 视场扇形（先画，置于最底层）──
        out.append(f'<g id="device_fans_{idx}" clip-path="url(#room_clip)">')
        for px_c, py_c in pts:
            cx = ox + px_c
            cy = oy + py_c
            ang = camera_angle_deg(px_c, py_c, W_px, L_px)
            fp = fan_path(cx, cy, ang, fan_half, fan_len)
            out.append(
                f'<path d="{fp}" fill="url(#fan_grad_{idx})" '
                f'stroke="{color}" stroke-width="0.6" stroke-opacity="0.25"/>'
            )
        out.append('</g>')

        # ── 朝向箭头 ──
        out.append(f'<g id="device_arrows_{idx}">')
        for px_c, py_c in pts:
            cx  = ox + px_c
            cy  = oy + py_c
            ang = camera_angle_deg(px_c, py_c, W_px, L_px)
            out += direction_arrow(cx, cy, ang, CAM_R + 22, color)
        out.append('</g>')

        # ── 摄像机图标 ──
        out.append(f'<g id="device_icons_{idx}">')
        for px_c, py_c in pts:
            cx  = ox + px_c
            cy  = oy + py_c
            ang = camera_angle_deg(px_c, py_c, W_px, L_px)
            # 光晕圆
            out.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{CAM_R+5}" '
                f'fill="{color}" opacity="0.12"/>'
            )
            # 枪机需要按朝向旋转，球机不需要
            if is_dome:
                out.append(
                    f'<g style="color:{color}">'
                    f'<use href="#sym_dome" x="{cx-CAM_R:.1f}" y="{cy-CAM_R:.1f}" '
                    f'width="{CAM_R*2}" height="{CAM_R*2}"/>'
                    f'</g>'
                )
            else:
                svg_rot = -ang   # 标准数学角→SVG 旋转角
                out.append(
                    f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({svg_rot:.1f})" '
                    f'style="color:{color}">'
                    f'<use href="#sym_bullet" x="-{CAM_R}" y="-{CAM_R}" '
                    f'width="{CAM_R*2}" height="{CAM_R*2}"/>'
                    f'</g>'
                )
        out.append('</g>')

        # ── 安装高度标注 ──
        if h_label:
            out.append(f'<g id="device_labels_{idx}">')
            for px_c, py_c in pts:
                cx = ox + px_c
                cy = oy + py_c
                out += label_box(cx, cy - CAM_R - 13, f'H={h_label}m',
                                 size=8, tc=color)
            out.append('</g>')

        legend_items.append({
            "color":    color,
            "type":     dev_type,
            "count":    dev["count"],
            "method":   dev.get("install_method", ""),
            "strategy": dev["layout_strategy"],
            "is_dome":  is_dome,
        })

    out.append('</g>')  # device_layer

    # ═══════════════════════════════
    # LAYER 5: annotation_layer
    # ═══════════════════════════════
    out.append('<g id="annotation_layer">')
    val = data.get("validation", {})
    risk_notes = val.get("risk_notes", [])
    if risk_notes:
        vy = oy + L_px + 46
        for k, note_text in enumerate(risk_notes[:3]):
            out.append(
                f'<text x="{ox}" y="{vy + k*14}" font-size="8" '
                f'fill="{WARNING_COLOR}">&#9888; {_esc(note_text)}</text>'
            )
    out.append('</g>')

    # ═══════════════════════════════
    # LAYER 6: legend_layer
    # ═══════════════════════════════
    out.append('<g id="legend_layer">')
    lx0 = ox + W_px + 18
    ly0 = oy
    lw  = MARGIN_RIGHT - 26

    n_items = len(legend_items)
    n_sugs  = len(data.get("optimization_suggestions", [])[:3])
    leg_h   = 32 + n_items * 52 + 14 + (22 + n_sugs * 18 if n_sugs else 0) + 30

    # 图例背景
    out.append(
        f'<rect x="{lx0}" y="{ly0}" width="{lw}" height="{leg_h}" '
        f'rx="6" fill="white" stroke="{GRID_COLOR}" stroke-width="1.2" '
        f'filter="url(#soft_shadow)"/>'
    )
    # 图例标题
    out.append(
        f'<text x="{lx0+10}" y="{ly0+20}" font-size="11" font-weight="bold" '
        f'fill="{PRIMARY_COLOR}">图 例</text>'
    )
    out.append(
        f'<line x1="{lx0+8}" y1="{ly0+26}" x2="{lx0+lw-8}" y2="{ly0+26}" '
        f'stroke="{GRID_COLOR}" stroke-width="1"/>'
    )

    # 每个设备图例
    for j, item in enumerate(legend_items):
        liy  = ly0 + 36 + j * 52
        color = item["color"]
        sym  = "sym_dome" if item["is_dome"] else "sym_bullet"
        # 彩色圆底
        out.append(
            f'<circle cx="{lx0+18}" cy="{liy+12}" r="14" '
            f'fill="{color}" opacity="0.12"/>'
        )
        # 摄像机图标
        out.append(
            f'<g style="color:{color}">'
            f'<use href="#{sym}" x="{lx0+6}" y="{liy}" width="24" height="24"/>'
            f'</g>'
        )
        out.append(
            f'<text x="{lx0+34}" y="{liy+9}" font-size="10" font-weight="bold" '
            f'fill="#2D3748">{_esc(item["type"])}</text>'
        )
        out.append(
            f'<text x="{lx0+34}" y="{liy+21}" font-size="9" fill="#718096">'
            f'×{item["count"]}  {_esc(item["method"])}</text>'
        )
        out.append(
            f'<text x="{lx0+34}" y="{liy+33}" font-size="8" fill="#A0AEC0">'
            f'[{_esc(item["strategy"])}]</text>'
        )

    # 分隔线
    sep_y = ly0 + 36 + n_items * 52
    out.append(
        f'<line x1="{lx0+8}" y1="{sep_y}" x2="{lx0+lw-8}" y2="{sep_y}" '
        f'stroke="{GRID_COLOR}" stroke-width="1"/>'
    )

    # 优化建议
    suggestions = data.get("optimization_suggestions", [])
    if suggestions:
        out.append(
            f'<text x="{lx0+10}" y="{sep_y+16}" font-size="9" font-weight="bold" '
            f'fill="#718096">建议</text>'
        )
        for k, sug in enumerate(suggestions[:3]):
            out.append(
                f'<text x="{lx0+12}" y="{sep_y+32+k*18}" font-size="8" '
                f'fill="#A0AEC0">&#8226; {_esc(sug)}</text>'
            )

    # 校验摘要
    val_y = sep_y + (34 + n_sugs * 18 if suggestions else 14)
    coverage = val.get("coverage_check", "")
    conflict = val.get("structure_conflict", "")
    cov_color = PRIMARY_COLOR if "通过" in coverage else WARNING_COLOR
    out.append(
        f'<text x="{lx0+10}" y="{val_y}" font-size="8" fill="{cov_color}">'
        f'覆盖：{_esc(coverage)}</text>'
    )
    out.append(
        f'<text x="{lx0+10}" y="{val_y+13}" font-size="8" fill="#A0AEC0">'
        f'冲突：{_esc(conflict)}</text>'
    )

    out.append('</g>')  # legend_layer
    out.append('</svg>')
    return "\n".join(out)


# ═══════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("用法：python render_svg.py <input.json> [output.svg]")
        sys.exit(1)
    json_path = Path(sys.argv[1])
    svg_path  = Path(sys.argv[2]) if len(sys.argv) >= 3 else json_path.with_suffix(".svg")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    if "error" in data:
        print(f"[错误] JSON error 字段：{data['error']}")
        sys.exit(1)
    svg_path.write_text(build_svg(data), encoding="utf-8")
    print(f"SVG 已生成：{svg_path}")


if __name__ == "__main__":
    main()
