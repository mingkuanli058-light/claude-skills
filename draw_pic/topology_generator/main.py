"""
main.py - 项目文档图件自动生成工具入口

一次运行生成全部已注册图件：
  A-01  系统总体架构图       → output/system_architecture.html
  A-02  网络拓扑图           → output/network_topology.html
  A-03  数据流转图           → output/data_flow.html
  A-04  部署结构图           → output/deployment_structure.html
  B-01  实施甘特图           → output/project_gantt.html

用法：
  python main.py \\
      --solution 建设方案.md \\
      --investment investment_schema.md \\
      --registry chart_registry.md
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from parser import DocumentParser
from topology_builder import TopologyBuilder
from html_renderer import HTMLRenderer

# 各专项图件生成模块
from charts.system_architecture import generate as gen_a01
from charts.data_flow            import generate as gen_a03
from charts.deployment           import generate as gen_a04
from charts.gantt                import generate as gen_b01


def main():
    arg_parser = argparse.ArgumentParser(
        description="根据项目文档自动生成全套图件（A-01 ~ A-04 / B-01）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    arg_parser.add_argument("--solution",    required=True, help="建设方案 Markdown 文件路径")
    arg_parser.add_argument("--investment",  required=True, help="投资规划 Markdown 文件路径")
    arg_parser.add_argument("--registry",    required=True, help="图件注册表 Markdown 文件路径")
    arg_parser.add_argument("--output-dir",  default="output", help="输出目录（默认: output）")

    args = arg_parser.parse_args()

    for label, path in [("--solution", args.solution),
                         ("--investment", args.investment),
                         ("--registry", args.registry)]:
        if not os.path.exists(path):
            print(f"[错误] 文件不存在: {path}  (参数: {label})")
            sys.exit(1)

    out = args.output_dir
    os.makedirs(out, exist_ok=True)
    tmpl_dir = os.path.join(os.path.dirname(__file__), "templates")

    # ── 1. 解析文档 ──────────────────────────────────────────────────────────
    print("[1/7] 解析文档...")
    doc_parser = DocumentParser()
    solution   = doc_parser.parse_solution(args.solution)
    investment = doc_parser.parse_investment(args.investment)
    registry   = doc_parser.parse_registry(args.registry)

    print(f"      系统名称  : {solution.system_name[:40] or '(未提取)'}")
    print(f"      设备清单  : {[(d.name, d.quantity) for d in investment.devices] or '(未提取)'}")
    print(f"      接入方式  : {solution.access_types or '(未提取)'}")
    print(f"      功能模块  : {solution.functional_modules or '(未提取)'}")
    print(f"      实施阶段  : {[p['name'] for p in solution.phases] or '(未提取)'}")
    print(f"      注册图件  : {list(registry.chart_types.keys())}")

    # ── 校验：关键字段为空时警告（图件将使用内置默认值）────────────────────
    _missing = []
    if not solution.system_name:
        _missing.append("系统名称（需要文档中有一级标题 # ...）")
    if not solution.access_types:
        _missing.append("接入方式（需要'主要来源于X、Y途径'句式或接入节点章节列表）")
    if not solution.functional_modules:
        _missing.append("功能模块（需要功能模块/应用软件建设章节）")
    if not solution.phases:
        _missing.append("实施阶段（需要实施进度表格）")
    if not investment.devices:
        _missing.append("设备清单（investment_schema.md 表格格式是否正确？）")

    if _missing:
        print()
        print("  [警告] 以下字段解析为空，对应图件将使用内置默认值，")
        print("         图件内容将与输入文档无关：")
        for f in _missing:
            print(f"    - {f}")
        print()

    # ── 2. A-01 系统总体架构图 ────────────────────────────────────────────────
    print("[2/7] 生成 A-01 系统总体架构图...")
    gen_a01(solution, investment,
            output_path=os.path.join(out, "system_architecture.html"),
            template_dir=tmpl_dir)

    # ── 3. A-02 网络拓扑图 ────────────────────────────────────────────────────
    print("[3/7] 生成 A-02 网络拓扑图...")
    topology = TopologyBuilder(solution, investment, registry).build()
    renderer = HTMLRenderer(template_dir=tmpl_dir)
    renderer.render(topology, os.path.join(out, "network_topology.html"))

    # ── 4. A-03 数据流转图 ────────────────────────────────────────────────────
    print("[4/7] 生成 A-03 数据流转图...")
    gen_a03(solution, investment,
            output_path=os.path.join(out, "data_flow.html"),
            template_dir=tmpl_dir)

    # ── 5. A-04 部署结构图 ────────────────────────────────────────────────────
    print("[5/7] 生成 A-04 部署结构图...")
    gen_a04(solution, investment,
            output_path=os.path.join(out, "deployment_structure.html"),
            template_dir=tmpl_dir)

    # ── 6. B-01 实施甘特图 ────────────────────────────────────────────────────
    print("[6/7] 生成 B-01 实施甘特图...")
    gen_b01(solution, investment,
            output_path=os.path.join(out, "project_gantt.html"),
            template_dir=tmpl_dir)

    # ── 7. 汇总 ──────────────────────────────────────────────────────────────
    print("[7/7] 全部完成！\n")
    outputs = [
        ("A-01", "system_architecture.html",  "系统总体架构图"),
        ("A-02", "network_topology.html",      "网络拓扑图"),
        ("A-03", "data_flow.html",             "数据流转图"),
        ("A-04", "deployment_structure.html",  "部署结构图"),
        ("B-01", "project_gantt.html",         "实施甘特图"),
    ]
    for badge, fname, title in outputs:
        full_path = os.path.abspath(os.path.join(out, fname))
        size_kb = os.path.getsize(full_path) // 1024
        print(f"  [{badge}] {title:<16s}  {full_path}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
