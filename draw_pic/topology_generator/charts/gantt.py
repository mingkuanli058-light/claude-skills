"""
gantt.py - B-01 实施甘特图

解析来源：建设方案.md 第六章"实施计划及保障措施"
  如果解析成功，使用文档中的阶段名称和工作内容；
  否则使用内置的默认值。

时间轴：相对周次（第 1 周 ~ 第 N 周），不使用绝对日期。
"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from charts.chart_utils import render_chart_html, write_html, esc

# ── 默认阶段数据 ──────────────────────────────────────────────────────────────
# (阶段名称, 主要工作描述, 开始周, 结束周, 颜色)
_DEFAULT_PHASES = [
    ("项目准备阶段",     "需求确认 / 技术方案评审 / 设备选型与采购",        1,  4,  "#1565C0"),
    ("基础设施建设阶段", "机房环境准备 / 网络布线 / 设备上架与基础安装",    3,  8,  "#2E7D32"),
    ("系统部署阶段",     "服务器部署 / 存储系统 / 数据库安装 / 软件配置",   7,  12, "#6A1B9A"),
    ("集成与测试阶段",   "系统联调 / 接口对接 / 功能测试 / 性能与安全测试", 10, 16, "#E65100"),
    ("试运行与验收阶段", "系统试运行 / 用户培训 / 问题整改 / 项目验收",     14, 18, "#37474F"),
]
_TOTAL_WEEKS = 18

# ── 关键里程碑 ────────────────────────────────────────────────────────────────
_MILESTONES = [
    (4,  "方案评审通过"),
    (8,  "基础设施就绪"),
    (12, "系统部署完成"),
    (16, "测试验收通过"),
    (18, "项目竣工"),
]

# ── 颜色 ──────────────────────────────────────────────────────────────────────
_BG_EVEN  = "#F5F7FA"
_BG_ODD   = "#FFFFFF"
_GRID_STR = "#E0E0E0"
_LABEL_C  = "#37474F"
_MILE_C   = "#F57C00"

# ── 主入口 ────────────────────────────────────────────────────────────────────

def generate(solution_data, investment_data, output_path: str, template_dir: str = ""):
    phases, total_weeks = _prepare_phases(solution_data)
    svg = _build_svg(phases, total_weeks)
    html = render_chart_html(
        svg_content=svg,
        badge="B-01",
        title="实施甘特图",
        system_name=solution_data.system_name,
        note_lines=[
            "• 时间轴以相对周次表示，实际起始日期由项目合同确定，各阶段存在合理搭接关系。",
            "• 各阶段为顺序依赖关系，后一阶段须在前一阶段完成判定条件满足后方可启动。",
            "• 菱形里程碑节点对应各阶段关键交付物与验收节点，需各方签署确认。",
            "• 集成与测试阶段：功能测试覆盖全部功能项，安全测试无高危漏洞，问题整改闭环。",
            "• 试运行与验收阶段：验收报告由建设单位、监理方、实施方三方共同签署。",
        ],
        template_dir=template_dir,
    )
    write_html(html, output_path)


# ── SVG 构建 ──────────────────────────────────────────────────────────────────

def _prepare_phases(solution_data):
    """尝试从解析数据中获取阶段信息，否则使用默认值。"""
    parsed = getattr(solution_data, "phases", None)
    if parsed and len(parsed) >= 3:
        phases = []
        start_w = 1
        durations = [3, 5, 4, 6, 4]  # 默认各阶段宽度
        colors = [p[4] for p in _DEFAULT_PHASES]
        for i, phase in enumerate(parsed[:5]):
            name = phase.get("name", f"阶段{i+1}")
            work = phase.get("work", "")
            dur = durations[i] if i < len(durations) else 4
            end_w = start_w + dur - 1
            # 允许搭接1周
            next_start = end_w - 1
            phases.append((name, work, start_w, end_w, colors[i % len(colors)]))
            start_w = next_start
        total_w = max(p[3] for p in phases) + 1
        return phases, total_w
    return _DEFAULT_PHASES, _TOTAL_WEEKS


def _build_svg(phases, total_weeks) -> str:
    # 布局参数
    label_w  = 180    # 阶段名列宽
    chart_w  = 740    # 图表区宽度
    row_h    = 70     # 每行高度
    header_h = 50     # 顶部时间轴高度
    footer_h = 60     # 里程碑行高度
    pad      = 20     # 左右边距

    W = pad + label_w + chart_w + pad
    H = header_h + len(phases) * row_h + footer_h + 30

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    parts.append(_defs())

    chart_x = pad + label_w
    col_w   = chart_w / total_weeks   # 每周像素宽

    # ── 背景 ─────────────────────────────────────────────────────────────────
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="white"/>')

    # ── 时间轴（月标题 + 周格线）─────────────────────────────────────────────
    # 月份标题（每4周 = 1个月）
    months_total = (total_weeks + 3) // 4
    for m in range(months_total):
        mx = chart_x + m * 4 * col_w
        mw = min(4 * col_w, chart_w - m * 4 * col_w)
        is_odd = m % 2 == 0
        parts.append(
            f'<rect x="{mx:.1f}" y="0" width="{mw:.1f}" height="{header_h//2}" '
            f'fill="{"#E3F2FD" if is_odd else "#BBDEFB"}" stroke="{_GRID_STR}" stroke-width=".5"/>'
            f'<text x="{mx+mw/2:.1f}" y="{header_h//4+5}" text-anchor="middle" '
            f'font-size="12" font-weight="700" fill="#1565C0" '
            f'font-family="PingFang SC,Microsoft YaHei,sans-serif">第{m+1}月</text>'
        )

    # 周格线 + 周序号
    for w in range(1, total_weeks + 1):
        wx = chart_x + (w - 1) * col_w
        # 格线
        parts.append(
            f'<line x1="{wx:.1f}" y1="{header_h//2}" x2="{wx:.1f}" y2="{H-footer_h}" '
            f'stroke="{_GRID_STR}" stroke-width=".8"/>'
        )
        # 周序号
        parts.append(
            f'<text x="{wx + col_w/2:.1f}" y="{header_h-6}" text-anchor="middle" '
            f'font-size="9.5" fill="#90A4AE" '
            f'font-family="sans-serif">W{w}</text>'
        )
    # 最右边格线
    parts.append(
        f'<line x1="{chart_x + chart_w:.1f}" y1="{header_h//2}" '
        f'x2="{chart_x + chart_w:.1f}" y2="{H-footer_h}" '
        f'stroke="{_GRID_STR}" stroke-width=".8"/>'
    )

    # 阶段名称列标题
    parts.append(
        f'<rect x="{pad}" y="0" width="{label_w}" height="{header_h}" '
        f'fill="#1565C0" rx="0"/>'
        f'<text x="{pad+label_w//2}" y="{header_h//2+5}" text-anchor="middle" '
        f'font-size="12" font-weight="700" fill="white" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">实施阶段</text>'
    )

    # ── 甘特行 ────────────────────────────────────────────────────────────────
    for i, (name, work, start_w, end_w, color) in enumerate(phases):
        ry = header_h + i * row_h
        is_even = i % 2 == 0
        row_fill = _BG_EVEN if is_even else _BG_ODD

        # 行背景
        parts.append(
            f'<rect x="{pad}" y="{ry}" width="{label_w+chart_w}" height="{row_h}" '
            f'fill="{row_fill}" stroke="{_GRID_STR}" stroke-width=".5"/>'
        )

        # 阶段名称标签
        parts.append(
            f'<text x="{pad+14}" y="{ry+row_h//2-4}" font-size="12" font-weight="700" '
            f'fill="{color}" font-family="PingFang SC,Microsoft YaHei,sans-serif">'
            f'{esc(name)}</text>'
        )
        # 工作内容（第二行小字）
        parts.append(
            f'<text x="{pad+14}" y="{ry+row_h//2+11}" font-size="9" fill="{_LABEL_C}" '
            f'opacity=".7" font-family="PingFang SC,Microsoft YaHei,sans-serif">'
            f'{esc(work[:28])}{"…" if len(work)>28 else ""}</text>'
        )

        # Gantt 条形
        bar_x = chart_x + (start_w - 1) * col_w + 2
        bar_w = (end_w - start_w + 1) * col_w - 4
        bar_y = ry + row_h // 4
        bar_h = row_h // 2
        # 阴影
        parts.append(
            f'<rect x="{bar_x+2:.1f}" y="{bar_y+3}" width="{bar_w:.1f}" height="{bar_h}" '
            f'rx="5" fill="#0003"/>'
        )
        # 主条形
        parts.append(
            f'<rect x="{bar_x:.1f}" y="{bar_y}" width="{bar_w:.1f}" height="{bar_h}" '
            f'rx="5" fill="{color}" opacity=".85"/>'
        )
        # 条形内文字（阶段序号）
        seq = f"第{['一','二','三','四','五','六'][i]}阶段" if i < 6 else f"阶段{i+1}"
        parts.append(
            f'<text x="{bar_x + bar_w/2:.1f}" y="{bar_y + bar_h/2 + 4:.1f}" '
            f'text-anchor="middle" font-size="11" fill="white" font-weight="600" '
            f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(seq)}</text>'
        )

    # ── 里程碑行 ──────────────────────────────────────────────────────────────
    mile_y = header_h + len(phases) * row_h + 10
    parts.append(
        f'<text x="{pad+14}" y="{mile_y+20}" font-size="11" font-weight="700" '
        f'fill="{_MILE_C}" font-family="PingFang SC,Microsoft YaHei,sans-serif">关键里程碑</text>'
    )
    for week, label in _MILESTONES:
        if week > total_weeks:
            continue
        mx = chart_x + (week - 1) * col_w
        my = mile_y + 18
        # 菱形
        d_size = 10
        parts.append(
            f'<polygon points="{mx},{my-d_size} {mx+d_size},{my} {mx},{my+d_size} {mx-d_size},{my}" '
            f'fill="{_MILE_C}"/>'
        )
        # 垂直虚线
        parts.append(
            f'<line x1="{mx}" y1="{header_h}" x2="{mx}" y2="{mile_y+8}" '
            f'stroke="{_MILE_C}" stroke-width="1" stroke-dasharray="4,3" opacity=".5"/>'
        )
        # 标签（交错上下）
        label_y = my + 20 if _MILESTONES.index((week, label)) % 2 == 0 else my + 32
        parts.append(
            f'<text x="{mx}" y="{label_y}" text-anchor="middle" font-size="9.5" '
            f'fill="{_MILE_C}" font-weight="600" '
            f'font-family="PingFang SC,Microsoft YaHei,sans-serif">{esc(label)}</text>'
        )

    # ── 图例 ─────────────────────────────────────────────────────────────────
    legend_y = H - 18
    parts.append(
        f'<text x="{pad}" y="{legend_y}" font-size="10" fill="{_LABEL_C}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">'
        f'各阶段时间区间存在合理搭接，后续阶段可在前置任务达到完成条件后提前启动准备工作。</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def _defs() -> str:
    return ""  # 甘特图不需要 marker
