"""
投标文件交叉检查工具。

三份投标文件全部生成后运行，检查：
1. 文本相似度（逐段比对，阈值 40%）
2. 数据泄露（A 文件中出现 B/C 的公司信息）
3. 报价模式（是否呈等差/等比/整数倍关系）

用法：
    python cross_check.py
"""
import re
from pathlib import Path
from difflib import SequenceMatcher

BASE = Path(__file__).parent
PROJECTS = ["A", "B", "C"]
SIMILARITY_THRESHOLD = 0.40


def read_company_keywords(project):
    """从公司资料.md提取关键识别词（公司名、联系人、电话、邮箱）"""
    spec_path = BASE / "projects" / project / "specs" / "公司资料.md"
    if not spec_path.exists():
        return set()

    text = spec_path.read_text(encoding="utf-8")
    keywords = set()

    for line in text.split("\n"):
        line = line.strip()
        # 提取表格中的值和键值对中的值
        if "：" in line:
            val = line.split("：", 1)[1].strip()
            if val and len(val) >= 2 and val not in ("", "（  ）", "待填写"):
                keywords.add(val)
        if "|" in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            for cell in cells:
                if len(cell) >= 2 and cell not in ("序号", "姓名", "岗位", "---"):
                    keywords.add(cell)

    return keywords


def read_paragraphs(md_path):
    """读取 Markdown 文件，按段落切分"""
    if not md_path.exists():
        return []
    text = md_path.read_text(encoding="utf-8")
    paras = []
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("|") and line != "---":
            paras.append(line)
    return paras


def check_text_similarity(report_lines):
    """检查任意两份投标文件间的文本相似度"""
    report_lines.append("\n## 一、文本相似度检查\n")

    md_files = ["技术方案.md", "商务方案.md"]
    found_issue = False

    for md_name in md_files:
        for i, p1 in enumerate(PROJECTS):
            for p2 in PROJECTS[i + 1:]:
                path1 = BASE / "projects" / p1 / "output" / md_name
                path2 = BASE / "projects" / p2 / "output" / md_name
                paras1 = read_paragraphs(path1)
                paras2 = read_paragraphs(path2)

                if not paras1 or not paras2:
                    continue

                high_sim = []
                for idx, para1 in enumerate(paras1):
                    for para2 in paras2:
                        ratio = SequenceMatcher(None, para1, para2).ratio()
                        if ratio > SIMILARITY_THRESHOLD:
                            high_sim.append((idx + 1, ratio, para1[:60]))

                if high_sim:
                    found_issue = True
                    report_lines.append(f"### {md_name}: {p1} vs {p2}\n")
                    for line_no, ratio, preview in high_sim[:10]:
                        report_lines.append(
                            f"- **相似度 {ratio:.0%}** 第{line_no}段: {preview}..."
                        )
                    report_lines.append("")

    if not found_issue:
        report_lines.append("未发现超过阈值（40%）的高相似度段落。\n")


def check_data_leakage(report_lines):
    """检查数据泄露：A 文件中不得出现 B/C 的公司信息"""
    report_lines.append("\n## 二、数据泄露检查\n")

    keywords_map = {p: read_company_keywords(p) for p in PROJECTS}
    found_issue = False

    for target in PROJECTS:
        others = [p for p in PROJECTS if p != target]
        other_keywords = set()
        for o in others:
            other_keywords.update(keywords_map[o])

        # 去掉太短或太通用的词
        other_keywords = {k for k in other_keywords if len(k) >= 3}

        if not other_keywords:
            continue

        # 检查 target 的全部 output 文件
        output_dir = BASE / "projects" / target / "output"
        for md_path in output_dir.glob("*.md"):
            text = md_path.read_text(encoding="utf-8")
            for kw in other_keywords:
                if kw in text:
                    found_issue = True
                    report_lines.append(
                        f"- **泄露** {target}/{md_path.name} 中出现其他主体关键词: 「{kw}」"
                    )

    if not found_issue:
        report_lines.append("未发现数据泄露。\n")


def check_price_pattern(report_lines):
    """检查报价模式：三份总价是否呈现可疑规律"""
    report_lines.append("\n## 三、报价模式检查\n")

    prices = {}
    for p in PROJECTS:
        spec_path = BASE / "projects" / p / "specs" / "报价清单.md"
        if not spec_path.exists():
            continue
        text = spec_path.read_text(encoding="utf-8")
        # 尝试提取投标总价
        m = re.search(r"投标总价.*?[：:]\s*([\d.]+)", text)
        if m:
            prices[p] = float(m.group(1))

    if len(prices) < 2:
        report_lines.append("报价数据不足，无法进行模式检查。\n")
        return

    report_lines.append(f"各主体报价: {prices}\n")

    vals = sorted(prices.values())
    if len(vals) >= 2:
        # 检查等差
        if len(vals) == 3:
            diff1 = vals[1] - vals[0]
            diff2 = vals[2] - vals[1]
            if abs(diff1 - diff2) < 0.01 and diff1 > 0:
                report_lines.append(f"- **警告** 三份报价呈等差数列（差值 {diff1}），存在串标嫌疑\n")

            # 检查整数倍
            if vals[0] > 0:
                ratios = [v / vals[0] for v in vals]
                if all(abs(r - round(r)) < 0.01 for r in ratios):
                    report_lines.append(f"- **警告** 报价呈整数倍关系 {ratios}，存在串标嫌疑\n")

        # 检查完全相同
        if len(set(vals)) < len(vals):
            report_lines.append("- **警告** 存在完全相同的报价\n")


def main():
    report_lines = ["# 投标文件交叉检查报告\n"]

    check_text_similarity(report_lines)
    check_data_leakage(report_lines)
    check_price_pattern(report_lines)

    report = "\n".join(report_lines)

    # 输出到每个项目
    for p in PROJECTS:
        out_path = BASE / "projects" / p / "output" / "交叉检查报告.md"
        out_path.write_text(report, encoding="utf-8")

    # 同时输出到根目录
    root_report = BASE / "交叉检查报告.md"
    root_report.write_text(report, encoding="utf-8")
    print(f"Done: {root_report}")


if __name__ == "__main__":
    main()
