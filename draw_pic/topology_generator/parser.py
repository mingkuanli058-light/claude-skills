"""
parser.py - 解析三个 Markdown 文档，提取所有图件所需的结构化数据。

解析策略：
- 建设方案.md  → 系统组件、网络分区、接入方式、功能模块、实施阶段
- investment_schema.md → 真实设备清单（名称、数量、类型）
- chart_registry.md   → 图件注册校验

政府方案兼容解析：
支持以下列表格式（详见各方法注释）：
  - Markdown 无序列表：- item / • item
  - 数字编号列表：1. item / 1、item / （1）item
  - 圆圈编号列表：① ② ③ ...
  - 粗体列表项：**item** 或 **item：**
  - 粗体段落标题：**xxx模块：**
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ─────────────────────────── 数据结构 ────────────────────────────────────────

@dataclass
class Device:
    """来自投资清单的真实设备"""
    name: str
    device_type: str   # server | storage | database | disk | generic
    quantity: int = 1
    spec_note: str = ""


@dataclass
class SolutionData:
    """从建设方案文档提取的结构化信息"""
    system_name: str = ""
    components: List[str] = field(default_factory=list)         # 系统组成部件名称
    network_zones: List[str] = field(default_factory=list)      # 网络分区
    access_types: List[str] = field(default_factory=list)       # 接入方式
    data_paths: List[Dict] = field(default_factory=list)        # 数据流路径描述
    functional_modules: List[str] = field(default_factory=list) # 应用功能模块（A-01用）
    phases: List[Dict] = field(default_factory=list)            # 实施阶段（B-01用）


@dataclass
class InvestmentData:
    """从投资规划文档提取的设备清单"""
    devices: List[Device] = field(default_factory=list)


@dataclass
class RegistryData:
    """从图件注册表提取的配置信息"""
    has_network_topology: bool = False   # A-02 是否已注册
    output_path: str = "output/network_topology.html"
    chart_types: Dict[str, str] = field(default_factory=dict)  # id -> 名称


# ─────────────────────────── 解析器 ──────────────────────────────────────────

class DocumentParser:
    """Markdown 文档解析器（政府方案兼容版）"""

    # 设备名称关键词 → 设备类型
    _DEVICE_TYPE_MAP = {
        "应用服务器": "server",
        "服务器":     "server",
        "网络存储":   "storage",
        "NAS":        "storage",
        "存储":       "storage",
        "硬盘":       "disk",
        "达梦":       "database",
        "数据库":     "database",
        "交换机":     "switch",
    }

    # 接入方式关键词兜底列表（当动态提取失败时使用）
    _ACCESS_SOURCES = [
        ("5G执法记录仪",      r"5G\s*执法记录仪"),
        ("采集站",            r"采集站"),
        ("执法仪本地导入",    r"执法仪[^，。\n]*本地导入|本地[接口导入]+"),
        ("既有执法管理平台",  r"既有执法管理平台"),
    ]

    # 网络分区关键词（政府方案兼容：内网/专网/机房网络等）
    _NETWORK_ZONE_KEYWORDS = [
        "业务网络", "存储网络", "公安专网",
        "内网", "专网", "机房网络", "核心交换网络",
        "管理网络", "视频专网", "政务外网",
    ]

    # ── 建设方案 ──────────────────────────────────────────────────────────────

    def parse_solution(self, filepath: str) -> SolutionData:
        """解析建设方案，提取系统名称、组件清单、网络分区和接入类型。"""
        content = self._read(filepath)
        data = SolutionData()

        # 系统名称（第一个一级标题）
        m = re.search(r'^#\s+(.+)', content, re.MULTILINE)
        if m:
            data.system_name = m.group(1).strip()

        # 接入方式（动态提取优先，关键词兜底）
        data.access_types = self._extract_access_types(content)

        # 系统组件（多格式动态提取，关键词兜底）
        data.components = self._extract_components(content)

        # 网络分区（扩展关键词集合）
        for zone in self._NETWORK_ZONE_KEYWORDS:
            if zone in content and zone not in data.network_zones:
                data.network_zones.append(zone)

        # 功能模块（多格式动态提取，关键词兜底）
        data.functional_modules = self._extract_modules(content)

        # 实施阶段（从实施进度表格提取）
        data.phases = self._parse_phases(content)

        # 数据路径描述（用于注释，非布局）
        for path_type, keyword in [("write", "数据写入路径"), ("read", "数据调阅路径")]:
            m = re.search(rf'{keyword}[：:]\s*(.{{10,200}}?)(?=\n\n|\d+\.|$)', content, re.DOTALL)
            if m:
                data.data_paths.append({"type": path_type, "desc": m.group(1).strip()[:120]})

        return data

    # ── 接入方式提取 ──────────────────────────────────────────────────────────

    def _extract_access_types(self, content: str) -> List[str]:
        """
        动态提取接入方式，依次尝试以下策略：
          1. 枚举句式：'主要来源于 X、Y、Z 等途径'
          2. 来源冒号后接列表：'数据来源：\\n- A\\n- B'
          3. 章节列表（多格式）
          4. 关键词兜底
        """
        # 策略1：枚举句式 '主要来源于 X、Y 等途径/方式'
        m = re.search(
            r'(?:主要来源于|数据来源[包含有为]*|接入来源[包含有为]*)\s*([^。\n]{6,200}?)'
            r'(?:四种|三种|两种|多种|等途径|等方式|等来源)',
            content,
        )
        if m:
            items = self._split_enum(m.group(1))
            if len(items) >= 2:
                return items

        # 策略2：'数据来源[包括/为/有]：' 或 '接入方式[包括]：' 后紧跟列表
        # 政府方案兼容解析：支持冒号后换行枚举
        m = re.search(
            r'(?:数据来源|数据接入|接入方式|接入来源|来源包括|来源[为有])[^：:\n]*[：:]\s*\n'
            r'((?:[ \t]*[-•①-⑩\d（(].*\n){2,})',
            content,
        )
        if m:
            items = self._extract_list_items(m.group(1), min_len=2, max_len=25)
            if len(items) >= 2:
                return items

        # 策略3：从接入相关章节提取（支持数字编号列表、圆圈编号、粗体列表）
        section = self._extract_section(content, r"接入节点|接入方式|数据来源|数据接入")
        if section:
            items = self._extract_list_items(section, min_len=2, max_len=25)
            if len(items) >= 2:
                return items

        # 策略4：关键词模式兜底
        found = []
        for label, pattern in self._ACCESS_SOURCES:
            if re.search(pattern, content):
                found.append(label)
        return found

    # ── 组件提取 ──────────────────────────────────────────────────────────────

    def _extract_components(self, content: str) -> List[str]:
        """
        从建设内容章节提取系统组件，支持以下格式：
          - **组件名称**（粗体列表项）
          - - 组件名称（普通列表项）
          - 1. 组件名称（数字编号列表）
          - ① 组件名称（圆圈编号列表）
          - **组件名称：**（粗体段落标题）
        """
        section = self._extract_section(content, r"总体框架|建设内容|系统架构|主要建设内容|系统组成")
        if section:
            # 优先：**粗体** 列表项（含独立粗体段落标题）
            items = self._extract_bold_items(section, min_len=3, max_len=30)
            if items:
                return items

            # 次选：所有格式的列表项（数字编号、圆圈、普通列表）
            items = self._extract_list_items(section, min_len=4, max_len=30)
            if items:
                return items

        # 关键词兜底
        components = []
        component_keywords = [
            (r"执法音视频接入节点",          "执法音视频接入节点"),
            (r"管理与检索平台",              "管理与检索平台"),
            (r"Scale-Out NAS存储资源池|NAS存储资源池|存储资源池", "NAS存储资源池"),
            (r"访问与调阅终端|访问终端",     "访问终端"),
            (r"网络交换[与和]传输链路|核心交换", "网络交换链路"),
            (r"达梦数据库",                  "达梦数据库"),
        ]
        for pattern, canonical in component_keywords:
            if re.search(pattern, content):
                if canonical not in components:
                    components.append(canonical)
        return components

    # ── 功能模块提取 ──────────────────────────────────────────────────────────

    def _extract_modules(self, content: str) -> List[str]:
        """
        从功能模块章节提取模块名，支持以下格式：
          - ### xxx模块（三级标题）
          - **xxx模块：**（粗体段落标题）
          - - xxx模块（列表项含'模块'关键词）
          - 1. xxx模块（数字编号列表）
          - ① xxx功能（圆圈编号）
        """
        section = self._extract_section(
            content,
            r"功能模块|应用功能|软件功能|系统功能|应用软件建设|功能设计|业务功能",
        )
        if section:
            # 优先：子标题（## ### ####）
            items = re.findall(
                r'^#{2,4}\s*(?:\d+[、.）\s]+)?(.{2,25}?(?:模块|功能|服务|管理|系统)[^\n]*)',
                section, re.MULTILINE,
            )
            if items:
                return [_clean(i)[:25] for i in items[:8]]

            # 次选：粗体段落标题 **xxx模块：** 或 **xxx模块**
            # 支持数字编号粗体：**1. xxx模块**
            # 政府方案兼容解析：支持粗体模块标题
            items = self._extract_bold_items(section, min_len=3, max_len=25,
                                             require_keyword=r"模块|功能|服务|管理")
            if items:
                return items[:8]

            # 再次选：所有格式列表项（含'模块/功能'关键词）
            all_items = self._extract_list_items(section, min_len=3, max_len=25)
            items = [i for i in all_items if re.search(r"模块|功能|服务|管理|系统", i)]
            if items:
                return items[:8]

            # 最后：所有列表项（章节内即为模块）
            if all_items:
                return all_items[:8]

        # 关键词兜底
        found = []
        module_patterns = [
            r"数据接入模块", r"存储管理模块", r"检索调阅模块",
            r"生命周期管理模块", r"运维监控模块",
        ]
        for pattern in module_patterns:
            if re.search(pattern, content):
                found.append(re.sub(r'\\', '', pattern))
        return found

    # ── 投资规划 ──────────────────────────────────────────────────────────────

    def parse_investment(self, filepath: str) -> InvestmentData:
        """
        解析投资规划，从 Markdown 表格提取设备名称、数量和类型。
        重点识别：应用服务器、网络存储设备、达梦数据库。
        """
        content = self._read(filepath)
        data = InvestmentData()

        # 逐行扫描表格数据行（格式：| 序号 | 名称 | 单价 | 单位 | 数量 | 金额 | 备注 |）
        for line in content.splitlines():
            if not line.startswith("|"):
                continue
            cols = [c.strip().strip("*") for c in line.split("|") if c.strip()]
            if len(cols) < 4:
                continue

            # 跳过表头/汇总行
            if any(kw in cols[0] for kw in ("序号", "费用", "合计", "总计", "小计", "─", "-")):
                continue
            if not cols[0].isdigit():
                continue

            name = cols[1].strip()
            if not name or len(name) < 2:
                continue

            # 解析数量（第5列，index=4）
            qty_str = cols[4] if len(cols) > 4 else "1"
            qty = self._parse_qty(qty_str)

            # 确定设备类型
            dev_type = "generic"
            for kw, dtype in self._DEVICE_TYPE_MAP.items():
                if kw in name:
                    dev_type = dtype
                    break

            # 只记录实际设备（排除纯硬盘等配件，保留主要设备节点）
            if dev_type in ("server", "storage", "database", "switch"):
                device = Device(
                    name=name,
                    device_type=dev_type,
                    quantity=qty,
                    spec_note=cols[6].strip()[:60] if len(cols) > 6 else "",
                )
                if not any(d.name == device.name for d in data.devices):
                    data.devices.append(device)

        return data

    # ── 图件注册表 ────────────────────────────────────────────────────────────

    def parse_registry(self, filepath: str) -> RegistryData:
        """解析图件注册表，验证 A-02 网络拓扑图是否已注册。"""
        content = self._read(filepath)
        data = RegistryData()

        # 检测 A-02 注册
        data.has_network_topology = bool(re.search(r"A-02", content) and "网络拓扑" in content)

        # 提取输出路径
        m = re.search(r"output[/\\](?:chart[/\\])?network_topology\.html", content)
        if m:
            data.output_path = m.group(0)

        # 收集所有注册图件
        for m in re.finditer(r"([A-D]-\d+)\s+([\u4e00-\u9fff]{2,10}图)", content):
            data.chart_types[m.group(1)] = m.group(2)

        return data

    # ── 工具方法 ──────────────────────────────────────────────────────────────

    @staticmethod
    def _read(filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _parse_qty(s: str) -> int:
        """将数量字符串（'1', '2', '0.54' 等）转换为整数（至少为1）。"""
        s = s.strip()
        try:
            v = float(s)
            return max(1, round(v))
        except ValueError:
            m = re.search(r"\d+", s)
            return int(m.group()) if m else 1

    @staticmethod
    def _parse_phases(content: str) -> list:
        """
        从实施进度表格提取阶段信息。
        表格格式：| 阶段 | 主要工作 | 交付物 | 阶段完成判定条件 |
        返回：[{"name": ..., "work": ..., "deliverables": ...}, ...]
        """
        phases = []
        # 定位实施进度章节
        section_match = re.search(
            r"实施进度[^\n]*\n(.*?)(?=###\s|##\s|\Z)", content, re.DOTALL
        )
        if not section_match:
            return phases

        section = section_match.group(1)
        # 逐行扫描表格
        for line in section.splitlines():
            if not line.startswith("|"):
                continue
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) < 2:
                continue
            name = cols[0].strip("-─ ")
            # 跳过表头
            if name in ("阶段", "---", "─") or "阶段" not in name:
                continue
            work = cols[1] if len(cols) > 1 else ""
            deliverables = cols[2] if len(cols) > 2 else ""
            phases.append({
                "name": name,
                "work": work.strip()[:40],
                "deliverables": deliverables.strip()[:40],
            })
        return phases

    @staticmethod
    def _extract_section(content: str, section_pattern: str) -> Optional[str]:
        """提取匹配的章节内容（到下一个同级标题为止）。

        注意：
        - 不能用 rf"...{1,3}..." —— f-string 会把 {1,3} 求值为 (1, 3)
        - lookahead 必须锚定 ^ (行首) + re.MULTILINE，否则 #### 内部的
          '###' + 空格 也会误触发截止条件。
        """
        pattern = (
            r"(?:^#{1,3}[^#\n]*(?:" + section_pattern + r")[^\n]*\n)"
            r"(.*?)"
            r"(?=^#{1,3} |\Z)"
        )
        m = re.search(pattern, content, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        return m.group(1) if m else None

    @staticmethod
    def _split_enum(raw: str) -> List[str]:
        """
        将 '执法办案平台、NAS存储、智能设备' 这类枚举字符串
        按中文分隔符拆分，去除括号注释和空白。
        """
        parts = re.split(r'[、，,及和]+', raw)
        items = []
        for p in parts:
            p = re.sub(r'（[^）]*）|\([^)]*\)', '', p).strip()
            if 2 <= len(p) <= 25:
                items.append(p)
        return items

    @staticmethod
    def _extract_list_items(text: str, min_len: int = 2, max_len: int = 30) -> List[str]:
        """
        从文本中提取所有格式的列表项，返回去重有序列表。

        支持以下格式（政府方案兼容解析）：
          - Markdown 无序列表：  '- item' / '• item' / '* item'
          - 支持数字编号列表：   '1. item' / '1、item' / '（1）item'
          - 支持圆圈编号列表：   '① item' / '② item' ...（U+2460-U+2469）
          - 粗体列表项：         '**item**' / '**item：**'（去掉 ** 和尾部冒号）
        """
        # 统一匹配模式：各类列表前缀 + 内容
        pattern = re.compile(
            r'^\s*(?:'
            r'[-•*]\s+'                      # 无序列表：- • *
            r'|\d+[.、）)]\s+'              # 数字编号：1. 1、 1）
            r'|[（(]\d+[）)]\s*'            # 括号编号：（1）(1)
            r'|[①②③④⑤⑥⑦⑧⑨⑩]\s*'     # 圆圈编号：① ② ...
            r'|\*\*'                         # 粗体开头（会在后续处理中去掉 **）
            r')'
            r'(.+?)(?:\*\*)?[：:。\n]?$',   # 内容部分（去掉尾部 ** 和标点）
            re.MULTILINE,
        )
        seen = set()
        items = []
        for m in pattern.finditer(text):
            raw = m.group(1).strip()
            # 去掉内联的 ** 标记
            raw = re.sub(r'\*\*', '', raw).strip()
            # 去掉尾部冒号/标点
            raw = raw.rstrip('：:。，,').strip()
            if min_len <= len(raw) <= max_len and raw not in seen:
                seen.add(raw)
                items.append(raw)
        return items

    @staticmethod
    def _extract_bold_items(
        text: str,
        min_len: int = 3,
        max_len: int = 30,
        require_keyword: Optional[str] = None,
    ) -> List[str]:
        """
        提取文本中所有粗体项：
          - **item**（列表项或段落标题）
          - **item：**（带冒号的粗体段落标题）
          - **数字. item**（含编号的粗体项，去掉编号前缀）

        政府方案兼容解析：支持粗体模块标题
        """
        pattern = re.compile(r'\*\*([^*\n]{2,40}?)\*\*')
        seen = set()
        items = []
        for m in pattern.finditer(text):
            raw = m.group(1).strip()
            # 去掉前缀数字编号（如 '1. ' '① '）
            raw = re.sub(r'^\d+[.、）)\s]+', '', raw).strip()
            raw = re.sub(r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*', '', raw).strip()
            # 去掉尾部冒号
            raw = raw.rstrip('：:').strip()
            if not (min_len <= len(raw) <= max_len):
                continue
            if require_keyword and not re.search(require_keyword, raw):
                continue
            if raw not in seen:
                seen.add(raw)
                items.append(raw)
        return items


# ── 模块级工具 ────────────────────────────────────────────────────────────────

def _clean(s: str) -> str:
    """去除首尾空白和常见标点。"""
    return s.strip().rstrip('：:。，,').strip()
