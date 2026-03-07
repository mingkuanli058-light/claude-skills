"""
将 output/chart_spec/ 中的 JSON 图件数据转换为 HTML 文件，供 html2png.py 渲染。
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
CHART_SPEC_DIR = BASE / "chart_spec"
CHART_DIR = BASE / "chart"
RENDERER_TEMPLATE = BASE.parent / "chart" / "renderer.html"

# 图件配置映射
CHART_CONFIG = {
    "system_architecture.json": {
        "html_name": "系统总体架构图.html",
        "title": "系统总体架构图"
    },
    "network_topology.json": {
        "html_name": "网络拓扑图.html",
        "title": "网络拓扑图"
    },
    "deployment_structure.json": {
        "html_name": "部署结构图.html",
        "title": "部署结构图"
    },
    "data_flow.json": {
        "html_name": "数据流转图.html",
        "title": "数据流转图"
    },
    "current_architecture.json": {
        "html_name": "现网结构图.html",
        "title": "现网结构图"
    },
    "project_gantt.json": {
        "html_name": "实施甘特图.html",
        "title": "实施甘特图"
    }
}

def main():
    # 确保 chart 目录存在
    CHART_DIR.mkdir(exist_ok=True)
    
    # 读取渲染器模板
    with open(RENDERER_TEMPLATE, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 处理每个 JSON 文件
    for json_file, config in CHART_CONFIG.items():
        json_path = CHART_SPEC_DIR / json_file
        if not json_path.exists():
            print(f"SKIP: {json_path} not found")
            continue
        
        # 读取 JSON 数据
        with open(json_path, 'r', encoding='utf-8') as f:
            chart_data = json.load(f)
        
        # 生成 HTML 内容
        html_content = template.replace('{{chart_data}}', json.dumps(chart_data, ensure_ascii=False))
        
        # 保存 HTML 文件
        html_path = CHART_DIR / config["html_name"]
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"OK: {html_path}")

if __name__ == "__main__":
    main()
