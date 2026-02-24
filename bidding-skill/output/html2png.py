"""
将 output/chart/ 下的 HTML 图件转换为 PNG 图片。
基于 Playwright 实现浏览器截图。

用法：
    python html2png.py              # 转换全部 HTML
    python html2png.py 系统架构图    # 转换指定图件
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

CHART_DIR = Path(__file__).parent / "chart"


def html_to_png(html_path: Path, width=1920):
    png_path = html_path.with_suffix('.png')
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1080})
        page.goto(f"file:///{html_path.resolve()}")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()
    print(f"Done: {png_path}")


def main():
    if not CHART_DIR.exists():
        print(f"Chart directory not found: {CHART_DIR}")
        return

    if len(sys.argv) > 1:
        name = sys.argv[1]
        html_path = CHART_DIR / f"{name}.html"
        if html_path.exists():
            html_to_png(html_path)
        else:
            print(f"Not found: {html_path}")
    else:
        for html_path in sorted(CHART_DIR.glob("*.html")):
            html_to_png(html_path)


if __name__ == '__main__':
    main()
