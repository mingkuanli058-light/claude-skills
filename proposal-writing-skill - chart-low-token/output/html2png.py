"""
将 output/chart/ 中所有 HTML 图件渲染为高分辨率 PNG。
依赖: playwright (pip install playwright && python -m playwright install chromium)
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

CHART_DIR = Path(__file__).parent / "chart"
# 需要转换的 HTML 文件（不含旧版 网络拓扑结构图）
HTML_FILES = [
    "系统总体架构图.html",
    "网络拓扑图.html",
    "数据流转图.html",
    "部署结构图.html",
    "现网结构图.html",
    "实施甘特图.html",
]

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name in HTML_FILES:
            html_path = CHART_DIR / name
            png_path = CHART_DIR / name.replace(".html", ".png")
            if not html_path.exists():
                print(f"SKIP: {html_path} not found")
                continue

            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(html_path.as_uri())
            page.wait_for_load_state("networkidle")

            # 获取实际内容高度，全页截图
            height = page.evaluate("() => document.documentElement.scrollHeight")
            page.set_viewport_size({"width": 1920, "height": height + 40})
            page.screenshot(path=str(png_path), full_page=True)
            print(f"OK: {png_path} ({1920}x{height})")
            page.close()

        browser.close()

if __name__ == "__main__":
    main()
