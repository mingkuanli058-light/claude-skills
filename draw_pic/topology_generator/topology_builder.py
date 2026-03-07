"""
topology_builder.py - 根据解析结果构建拓扑图的节点、边和网络分区。

布局策略（从上到下分层）：
  Layer 0 ── 访问终端（用户访问层）
  Layer 1 ── 接入数据源（5G回传 / 采集站 / 本地 / 既有平台）
  Layer 2 ── 核心交换机（公安专网核心层）
  Layer 3 ── 应用服务器（管理与检索平台）
  Layer 4 ── 达梦数据库  |  NAS存储节点×N（数据层）

网络分区（背景色块）：
  - 外部接入区：Layer 0-1（公安专网边界）
  - 业务核心区：Layer 2-3（业务网络）
  - 数据存储区：Layer 4（存储网络）
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from parser import SolutionData, InvestmentData, RegistryData


# ─────────────────────────── 数据模型 ────────────────────────────────────────

@dataclass
class TopoNode:
    id: str
    label: str
    sublabel: str = ""
    node_type: str = "generic"   # server|storage|database|switch|terminal|endpoint
    quantity: int = 1
    layer: int = 0
    # 由布局算法填充
    x: float = 0.0
    y: float = 0.0
    w: float = 140.0
    h: float = 70.0


@dataclass
class TopoEdge:
    src: str            # source node id
    dst: str            # target node id
    label: str = ""
    style: str = "normal"   # normal|business|storage|database|scaleout


@dataclass
class NetZone:
    id: str
    name: str
    color: str          # fill 颜色
    stroke: str         # 边框颜色
    node_ids: List[str] = field(default_factory=list)
    # 由布局算法填充
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0


@dataclass
class Topology:
    title: str = "A-02 网络拓扑图"
    system_name: str = ""
    nodes: List[TopoNode] = field(default_factory=list)
    edges: List[TopoEdge] = field(default_factory=list)
    zones: List[NetZone] = field(default_factory=list)
    canvas_w: int = 1100
    canvas_h: int = 720
    note_lines: List[str] = field(default_factory=list)   # 图面说明文字


# ─────────────────────────── 构建器 ──────────────────────────────────────────

# 各层 Y 轴基准坐标（节点顶边）
_LAYER_Y = {0: 55, 1: 175, 2: 320, 3: 430, 4: 560}

# 节点默认尺寸
_NODE_W = 138
_NODE_H = 68
_SWITCH_W = 180
_SWITCH_H = 46

# 分区内边距
_ZONE_PAD = 18

# 分区配色
_ZONE_COLORS = {
    "access":   ("#FFF8E1", "#F9A825"),   # 浅黄
    "business": ("#E3F2FD", "#1565C0"),   # 浅蓝
    "storage":  ("#E8F5E9", "#2E7D32"),   # 浅绿
}


class TopologyBuilder:
    """将解析数据组装成 Topology 对象。"""

    def __init__(self, solution: SolutionData, investment: InvestmentData, registry: RegistryData):
        self.solution   = solution
        self.investment = investment
        self.registry   = registry

    def build(self) -> Topology:
        topo = Topology(
            system_name=self.solution.system_name or "执法音视频集中存储与管理系统",
        )

        self._add_nodes(topo)
        self._compute_layout(topo)
        self._add_edges(topo)
        self._add_zones(topo)
        self._add_notes(topo)

        return topo

    # ── 节点构建 ──────────────────────────────────────────────────────────────

    def _add_nodes(self, topo: Topology):
        nodes = topo.nodes

        # ── Layer 0: 访问终端 ──
        nodes.append(TopoNode(
            id="terminal", label="访问终端", sublabel="检索调阅工作站",
            node_type="terminal", layer=0, w=_NODE_W, h=_NODE_H,
        ))

        # ── Layer 1: 接入数据源 ──
        # 默认四路接入，可由解析结果控制
        access_sources = self.solution.access_types or [
            "5G执法记录仪", "采集站", "执法仪本地导入", "既有执法管理平台"
        ]
        sublabels = {
            "5G执法记录仪":   "实时回传",
            "采集站":         "批量导入",
            "执法仪本地导入": "USB接口",
            "既有执法管理平台": "接口归集",
        }
        for i, src in enumerate(access_sources):
            nodes.append(TopoNode(
                id=f"src_{i}", label=src, sublabel=sublabels.get(src, ""),
                node_type="endpoint", layer=1, w=_NODE_W, h=_NODE_H,
            ))

        # ── Layer 2: 核心交换机 ──
        nodes.append(TopoNode(
            id="core_switch", label="核心交换机", sublabel="公安专网",
            node_type="switch", layer=2, w=_SWITCH_W, h=_SWITCH_H,
        ))

        # ── Layer 3: 应用服务器 (数量来自 investment_schema) ──
        app = self._find_device("应用服务器") or self._find_device("服务器")
        qty = app.quantity if app else 1
        nodes.append(TopoNode(
            id="app_server",
            label="应用服务器",
            sublabel=f"管理与检索平台  ×{qty}",
            node_type="server", quantity=qty, layer=3, w=_NODE_W, h=_NODE_H,
        ))

        # ── Layer 4: 达梦数据库 ──
        nodes.append(TopoNode(
            id="dameng_db", label="达梦数据库", sublabel="V8.4  元数据存储",
            node_type="database", layer=4, w=_NODE_W, h=_NODE_H,
        ))

        # ── Layer 4: NAS 存储节点 (数量来自 investment_schema) ──
        nas = self._find_device("网络存储") or self._find_device("NAS") or self._find_device("存储")
        nas_qty = nas.quantity if nas else 2
        for i in range(nas_qty):
            nodes.append(TopoNode(
                id=f"nas_{i+1}",
                label=f"NAS存储节点 {i+1}",
                sublabel="Scale-Out NAS",
                node_type="storage", layer=4, w=_NODE_W, h=_NODE_H,
            ))

    # ── 布局计算 ──────────────────────────────────────────────────────────────

    def _compute_layout(self, topo: Topology):
        """
        按层将节点水平均匀分布：
          - 每层节点居中排列，相邻节点间距 = gap
          - Layer 2（交换机）独自居中
        """
        canvas_w = topo.canvas_w

        # 按层分组
        layers: Dict[int, List[TopoNode]] = {}
        for n in topo.nodes:
            layers.setdefault(n.layer, []).append(n)

        for layer_idx, nodes in layers.items():
            y = _LAYER_Y.get(layer_idx, 55 + layer_idx * 130)
            count = len(nodes)

            if count == 1:
                n = nodes[0]
                n.x = (canvas_w - n.w) / 2
                n.y = y
            else:
                total_w = sum(n.w for n in nodes)
                gap = min(40, (canvas_w - 80 - total_w) / (count - 1))
                gap = max(10, gap)
                start_x = (canvas_w - total_w - gap * (count - 1)) / 2
                x = start_x
                for n in nodes:
                    n.x = x
                    n.y = y
                    x += n.w + gap

        # 动态调整画布高度
        max_y = max(n.y + n.h for n in topo.nodes)
        topo.canvas_h = int(max_y) + 100

    # ── 边构建 ────────────────────────────────────────────────────────────────

    def _add_edges(self, topo: Topology):
        edges = topo.edges
        node_ids = {n.id for n in topo.nodes}

        # 访问终端 → 核心交换机（业务网络）
        edges.append(TopoEdge("terminal", "core_switch", label="业务网络", style="business"))

        # 各接入源 → 核心交换机（公安专网）
        for n in topo.nodes:
            if n.id.startswith("src_"):
                edges.append(TopoEdge(n.id, "core_switch", style="normal"))

        # 核心交换机 → 应用服务器（业务网络）
        edges.append(TopoEdge("core_switch", "app_server", label="业务网络", style="business"))

        # 应用服务器 → 达梦数据库（JDBC）
        edges.append(TopoEdge("app_server", "dameng_db", label="JDBC", style="database"))

        # 应用服务器 → NAS 节点（存储网络 NFS/SMB）
        nas_nodes = [n for n in topo.nodes if n.id.startswith("nas_")]
        for nas in nas_nodes:
            edges.append(TopoEdge("app_server", nas.id, label="NFS/SMB", style="storage"))

        # NAS 节点互联（Scale-Out 横向扩展）
        for i in range(len(nas_nodes) - 1):
            edges.append(TopoEdge(
                nas_nodes[i].id, nas_nodes[i+1].id,
                label="≥10GbE", style="scaleout",
            ))

    # ── 分区构建 ──────────────────────────────────────────────────────────────

    def _add_zones(self, topo: Topology):
        def zone_rect(node_ids: List[str], pad: int) -> Tuple[float, float, float, float]:
            ns = [n for n in topo.nodes if n.id in node_ids]
            if not ns:
                return 0, 0, 0, 0
            min_x = min(n.x for n in ns) - pad
            min_y = min(n.y for n in ns) - pad - 20   # 标题预留
            max_x = max(n.x + n.w for n in ns) + pad
            max_y = max(n.y + n.h for n in ns) + pad
            return min_x, min_y, max_x - min_x, max_y - min_y

        # 接入区（Layer 0-1）
        access_ids = ["terminal"] + [n.id for n in topo.nodes if n.id.startswith("src_")]
        x, y, w, h = zone_rect(access_ids, _ZONE_PAD)
        fill, stroke = _ZONE_COLORS["access"]
        topo.zones.append(NetZone(
            id="zone_access", name="接入层（公安专网）",
            color=fill, stroke=stroke,
            node_ids=access_ids, x=x, y=y, w=w, h=h,
        ))

        # 业务核心区（Layer 2-3）
        biz_ids = ["core_switch", "app_server"]
        x, y, w, h = zone_rect(biz_ids, _ZONE_PAD)
        fill, stroke = _ZONE_COLORS["business"]
        topo.zones.append(NetZone(
            id="zone_business", name="业务核心区（业务网络）",
            color=fill, stroke=stroke,
            node_ids=biz_ids, x=x, y=y, w=w, h=h,
        ))

        # 数据存储区（Layer 4）
        data_ids = ["dameng_db"] + [n.id for n in topo.nodes if n.id.startswith("nas_")]
        x, y, w, h = zone_rect(data_ids, _ZONE_PAD)
        fill, stroke = _ZONE_COLORS["storage"]
        topo.zones.append(NetZone(
            id="zone_storage", name="数据存储区（存储网络 ≥10GbE）",
            color=fill, stroke=stroke,
            node_ids=data_ids, x=x, y=y, w=w, h=h,
        ))

    # ── 说明文字 ──────────────────────────────────────────────────────────────

    def _add_notes(self, topo: Topology):
        topo.note_lines = [
            "• 系统部署于公安专网环境，不涉及互联网连接。",
            "• 存储资源池采用 Scale-Out NAS 横向扩展架构，有效容量 ≥ 700TB。",
            "• 应用服务器通过 NFS/SMB 协议挂载存储资源池，通过 JDBC 连接达梦数据库。",
            "• 数据调阅路径：访问终端 → 应用服务器 → 存储资源池，终端不直接访问存储。",
            "• 图件遵循 chart_registry A-02 规范，不含 IP 地址，设备来源于 investment_schema。",
        ]

    # ── 工具 ──────────────────────────────────────────────────────────────────

    def _find_device(self, keyword: str):
        for d in self.investment.devices:
            if keyword in d.name:
                return d
        return None
