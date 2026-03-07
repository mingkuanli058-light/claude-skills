"""
chart_utils.py - 所有图件共用的 HTML 渲染工具。

提供：
  - render_chart_html()  将 SVG 字符串包装为完整 HTML 页面
  - write_html()         写出 HTML 文件
  - esc()                XML 实体转义
"""

from __future__ import annotations
import os

try:
    from jinja2 import Environment, FileSystemLoader
    _HAS_JINJA2 = True
except ImportError:
    _HAS_JINJA2 = False

# ─── 共用 CSS（嵌入 fallback HTML 时使用）────────────────────────────────────
_BASE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:"PingFang SC","Microsoft YaHei","Hiragino Sans GB",sans-serif;
     background:#f0f4f8;color:#2c3e50;padding:28px 32px;min-height:100vh}
.page-header{display:flex;align-items:baseline;gap:14px;margin-bottom:22px}
.badge{background:#1565C0;color:#fff;font-size:12px;font-weight:700;
       padding:3px 10px;border-radius:4px;letter-spacing:.5px}
.page-title{font-size:20px;font-weight:700;color:#1565C0}
.system-name{font-size:13px;color:#888;font-weight:400}
.card{background:#fff;border-radius:12px;box-shadow:0 2px 14px rgba(0,0,0,.08);
      padding:22px 24px;margin-bottom:20px;overflow:hidden}
.section-label{font-size:13px;font-weight:700;color:#1565C0;
               border-left:3px solid #1565C0;padding-left:9px;margin-bottom:16px}
.svg-wrap{overflow-x:auto;padding:4px 0}
svg{display:block;overflow:visible}
ul.notes{list-style:disc;padding-left:20px;font-size:12.5px;color:#555;line-height:2}
.page-footer{text-align:right;font-size:11px;color:#bbb;margin-top:10px}
"""


def render_chart_html(
    svg_content: str,
    badge: str,
    title: str,
    system_name: str,
    note_lines: list | None = None,
    legend_svg: str = "",
    template_dir: str | None = None,
) -> str:
    """
    将 SVG 包装为完整 HTML 页面。
    优先使用 Jinja2 模板；不可用时降级为内联 HTML。
    """
    note_lines = note_lines or []

    # ── Jinja2 路径 ──────────────────────────────────────────────────────────
    if _HAS_JINJA2 and template_dir and os.path.isdir(template_dir):
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
        # 复用 topology_template.html（接口完全兼容）
        tmpl = env.get_template("topology_template.html")
        return tmpl.render(
            title=f"{badge}\u3000{title}",
            system_name=system_name,
            svg_content=svg_content,
            legend_svg=legend_svg,
            note_lines=note_lines,
        )

    # ── 内联降级 ─────────────────────────────────────────────────────────────
    notes_html = "".join(f"<li>{n}</li>" for n in note_lines)
    legend_block = (
        f'<div class="card"><div class="section-label">图例说明</div>{legend_svg}</div>'
        if legend_svg else ""
    )
    notes_block = (
        f'<div class="card"><div class="section-label">说明</div>'
        f'<ul class="notes">{notes_html}</ul></div>'
        if notes_html else ""
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>{badge} {title} — {system_name}</title>
  <style>{_BASE_CSS}</style>
</head>
<body>
  <div class="page-header">
    <span class="badge">{badge}</span>
    <span class="page-title">{title}</span>
    <span class="system-name">{system_name}</span>
  </div>
  <div class="card">
    <div class="section-label">图件内容</div>
    <div class="svg-wrap">{svg_content}</div>
  </div>
  {legend_block}
  {notes_block}
  <div class="page-footer">
    依据 chart_registry 规范生成 &nbsp;|&nbsp; 不含品牌标识 &nbsp;|&nbsp; 不含 IP 地址
  </div>
</body>
</html>"""


def write_html(html: str, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def esc(s: str) -> str:
    """HTML/XML 实体转义。"""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))
