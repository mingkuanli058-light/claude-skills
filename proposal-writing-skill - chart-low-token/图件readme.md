
# 图件系统 V5 架构说明

版本：V5（Renderer v5）
适用范围：建设方案 / 技术方案 / 投标方案图件自动生成
核心升级：专业架构图风格、三体系纵栏、甘特图、三套渲染风格

---

## 一、版本演进对比

| 对比项 | V4 | V5 |
|---|---|---|
| AI 生成内容 | JSON（无坐标） | JSON（无坐标）|
| 布局引擎 | 自动分层布局 | 自动分层布局（同步 pillarsW 适配）|
| 图件类型 | 4 种 | **5 种**（新增 project_gantt 甘特图）|
| 三体系纵栏 | 无 | **pillars 字段 → 右侧纵向贯穿体系栏**|
| 渲染风格 | 单一风格 | **三套风格**（presentation / review / tender）|
| 节点卡片 | 顶部色条 + 矩形边框 | **SVG feDropShadow 阴影 + 展板感设计**|
| 层背景 | 深色背景 | **浅色层背景**（边框半透明，层块退后）|
| 节点尺寸 | 160×76 | **180×88**（更大图标 28×28）|
| 连线样式 | 贝塞尔曲线 | 贝塞尔曲线（network_topology 保留虚线区域加强框）|

---

## 二、系统架构

```
AI 读取 specs/方案需要生成图件确认.md
              ↓
AI 按 chart/chart_schema.md 生成 JSON（仅结构，无坐标）
              ↓
output/json_to_html.py 批量注入 renderer.html → HTML
              ↓
output/html2png.py 批量导出 PNG（1920×1080）
```

---

## 三、目录结构

```
project/
│
├─ specs/
│   ├─ chart_registry.md          # 图件注册表（触发条件 / 输出路径）
│   ├─ chart_spec_schema.md       # JSON 结构规范（简化版）
│   └─ 方案需要生成图件确认.md      # 当前项目图件确认清单
│
├─ chart/                         # 图件引擎目录
│   ├─ chart_schema.md            # AI 生成规范（完整版，含 pillars 规则）
│   ├─ layout_engine.js           # 自动布局引擎（Node.js / 浏览器双模式）
│   └─ renderer.html              # 通用 SVG 渲染器（含图标库 + 三套风格）
│
├─ output/
│   ├─ chart_spec/                # AI 生成的 JSON 文件
│   │   ├─ system_architecture.json
│   │   ├─ network_topology.json
│   │   ├─ deployment_structure.json
│   │   ├─ data_flow.json
│   │   └─ project_gantt.json
│   ├─ chart/                     # 渲染输出的 HTML / PNG
│   ├─ json_to_html.py            # JSON → HTML 批量脚本
│   └─ html2png.py                # HTML → PNG 批量脚本
```

---

## 四、AI 生成 JSON 格式

### system_architecture（含三体系）

```json
{
  "chart_type": "system_architecture",
  "title": "系统总体架构图",
  "meta": {
    "project": "项目名称",
    "company": "建设单位",
    "date": "2026",
    "chart_style": "presentation"
  },
  "layers": ["用户层", "业务应用层", "业务支撑层", "数据层", "网络层", "硬件层"],
  "nodes": [
    {"id": "user1", "type": "user",     "layer": "用户层",   "label": "业务人员"},
    {"id": "app1",  "type": "app",      "layer": "业务应用层", "label": "管理平台"},
    {"id": "db1",   "type": "database", "layer": "数据层",   "label": "业务数据库"}
  ],
  "links": [
    {"from": "user1", "to": "app1"},
    {"from": "app1",  "to": "db1"}
  ],
  "groups": [
    {"id": "g1", "label": "应用系统", "nodes": ["app1"]}
  ],
  "pillars": ["标准规范体系", "信息安全体系", "运行管理体系"]
}
```

**AI 禁止输出：x/y 坐标、HTML、SVG**

---

## 五、支持的图件类型

| chart_type | 名称 | 布局方式 | 特性 |
|---|---|---|---|
| `system_architecture` | 系统总体架构图 | 垂直分层（上→下）| 固定六层 + pillars 三体系纵栏 |
| `network_topology` | 网络拓扑图 | 垂直分层（上→下）| 虚线区域加强框 |
| `deployment_structure` | 部署结构图 | 水平分区（左→右）| 顶部区域标签条 |
| `data_flow` | 数据流图 | 垂直分层（上→下）| process 节点左侧竖条 + 步骤编号 |
| `project_gantt` | 实施甘特图 | 日期横轴 | 阶段条 + 子任务条 + 里程碑菱形 |

---

## 六、三套渲染风格

通过 `meta.chart_style` 控制，缺省为 `presentation`：

| 值 | 名称 | 适用场景 |
|---|---|---|
| `presentation` | 汇报增强风 | 领导汇报、专题展示（默认）|
| `review` | 内部工程风 | 立项审批、技术备案、内部审查 |
| `tender` | 投标结构强化风 | 投标文件、专家评审 |

---

## 七、节点类型 → 图标

| type | 图标含义 | type | 图标含义 |
|---|---|---|---|
| `camera` | 摄像机 | `user` | 用户/人员 |
| `server` | 服务器 | `sensor` | 传感器 |
| `switch` | 交换机 | `mobile` | 手机/移动端 |
| `router` | 路由器 | `gateway` | 网关 |
| `firewall` | 防火墙 | `app` | 应用模块 |
| `storage` | 存储/NAS | `platform` | 平台 |
| `database` | 数据库 | `display` | 显示屏/大屏 |
| `cloud` | 云/互联网 | `nvr` | 录像机 |
| `terminal` | 电脑终端 | `rfid` | RFID 读写器 |
| `process` | 处理节点（数据流）| | |

---

## 八、渲染操作

**批量渲染 HTML：**

```bash
python output/json_to_html.py
```

**批量导出 PNG：**

```bash
python output/html2png.py
```

单文件渲染时，将 JSON 内容嵌入 `renderer.html` 中的 `{{chart_data}}` 占位符，浏览器打开后点击"导出 PNG"。

---

## 九、视觉规范（V5 展板感）

- 白色背景，深蓝标题栏（font-weight 600，字间距 3）
- 层背景：浅色填充 + 半透明边框（stroke-opacity 0.35）→ 层块退到第二视觉层
- 左侧层标签条：实色填充（深色），旋转白色文字
- 节点卡片：白底 + 彩色顶条 + SVG feDropShadow 阴影 + 图标（28×28）+ 文字
- 三体系纵栏：右侧独立区域，贯穿所有层，深蓝 / 深红 / 深绿三色
- 连线：贝塞尔曲线 + 箭头标记
- 分组：虚线边界框（各风格略有差异）
- 甘特图：阶段色条 + 子任务色条 + 菱形里程碑 + 日期网格
- 输出分辨率：1920×1080（html2png.py 可按需调整缩放）

---

## 十、规范文件索引

| 文件 | 用途 |
|---|---|
| `chart/chart_schema.md` | AI 生成 JSON 的完整规范（含 pillars / gantt 规则）|
| `specs/chart_spec_schema.md` | JSON 字段简明说明 |
| `specs/chart_registry.md` | 图件触发条件与输出路径 |
| `specs/方案需要生成图件确认.md` | 当前项目图件确认清单 |

---

## 工作流提示词

**Step 1 — 生成图件 JSON：**

```
按 chart/chart_schema.md，
先读取 specs/方案需要生成图件确认.md，
根据 specs/需求.md、specs/investment_schema.md、output/建设方案.md，
生成确认清单中标记为"必须生成"的全部图件 JSON，
输出到 output/chart_spec/，逐个文件生成。
```

**Step 2 — 渲染 HTML + 导出 PNG：**

```
读取 output/chart_spec/ 中的 JSON，
使用 chart/renderer.html 渲染 HTML 图件，输出到 output/chart/，
然后将 HTML 图件导出 PNG。
```
