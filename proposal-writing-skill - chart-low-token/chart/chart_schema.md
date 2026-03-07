# Chart Data Schema v4

**AI 生成图件 JSON 的完整规范**

本文件定义 AI 生成 `chart_data.json` 时**必须遵守**的结构。

渲染引擎：`chart/renderer.html`
布局引擎：`chart/layout_engine.js`

---

## 核心原则

| 规则 | 说明 |
|---|---|
| AI 只生成结构 | 禁止输出坐标、HTML、SVG |
| 布局全由引擎计算 | x、y 坐标由 `layout_engine.js` 自动计算 |
| 节点按层归属 | 每个节点必须声明所属 `layer` |
| 层顺序即渲染顺序 | `layers` 数组顺序 = 从上到下（垂直布局）|

---

## 一、完整结构

```json
{
  "chart_type": "system_architecture",
  "title": "图件标题",
  "meta": {
    "project": "项目名称",
    "company": "建设单位",
    "date": "2026"
  },
 "layers": [
  "用户层",
  "业务应用层",
  "业务支撑层",
  "数据层",
  "网络层",
  "硬件层"
],
 "nodes": [
    {"id": "唯一ID", "type": "节点类型", "layer": "所属层", "label": "显示名称"}
  ],
  "links": [
    {"from": "节点ID", "to": "节点ID", "label": "可选标注"}
  ],
  "groups": [
    {"id": "组ID", "label": "组名称", "nodes": ["节点ID列表"]}
  ],
  "pillars": [
    "标准规范体系", "信息安全体系", "运行管理体系"
  ]
}
```
---

## 二、字段说明

### chart_type（必填）

| 值 | 图件类型 | 布局方式 |
|---|---|---|
| `system_architecture` | 系统总体架构图 | 垂直分层 |
| `network_topology` | 网络拓扑图 | 垂直分层 |
| `data_flow` | 数据流图 | 垂直分层 |
| `deployment_structure` | 部署结构图 | 水平分区 |
| `project_gantt` | 实施甘特图 | 日期横轴 |

### layers（必填）

- 字符串数组，定义分层名称
- 数组顺序 = 渲染顺序（垂直布局：第一项在最上方）
- `deployment_structure` 中，每一层代表一台服务器或部署区域

**层名称建议（system_architecture）：**

```
system_architecture 推荐层名称：

用户层
业务应用层
业务支撑层
数据层
网络层
硬件层

说明：

1. layers 数组顺序 = 图件自上而下的渲染顺序。
2. system_architecture 图件建议使用六层结构。
3. 层级顺序应与 Chart Registry 中 A-01 系统总体架构图保持一致。
4. 不建议新增或删除层级。

```

**层名称建议（network_topology）：**

```
互联网 / 核心网络区 / 业务服务区 / 接入终端区
```

**层名称建议（deployment_structure）：**

```
应用服务器 / 数据库服务器 / 存储服务器
```

**层名称建议（data_flow）：**

```
数据采集 / 数据处理 / 数据存储 / 数据应用
```

### nodes（必填）

每个节点：

```json
{
  "id":    "唯一英文ID，不含空格",
  "type":  "节点类型（见下表）",
  "layer": "所属层名称（必须与 layers 中的值完全一致）",
  "label": "图中显示的中文名称"
}
```

#### type 允许值（图标对照表）

| type | 图标 | 适用场景 |
|---|---|---|
| `camera` | 摄像机 | 视频监控 |
| `server` | 服务器 | 应用/业务服务器 |
| `switch` | 交换机 | 核心/汇聚交换机 |
| `router` | 路由器 | 网络路由 |
| `firewall` | 防火墙 | 安全设备 |
| `storage` | 存储（NAS/SAN） | 共享存储 |
| `database` | 数据库 | 数据存储 |
| `cloud` | 云 | 云平台/互联网 |
| `terminal` | 电脑终端 | PC、工作站 |
| `user` | 用户 | 操作人员 |
| `sensor` | 传感器 | IoT 设备 |
| `mobile` | 手机 | 移动终端 |
| `gateway` | 网关 | 协议转换 |
| `app` | 应用模块 | 软件功能模块 |
| `platform` | 平台 | 中间件平台 |
| `display` | 显示屏 | 大屏/显示设备 |
| `nvr` | NVR/录像机 | 视频存储设备 |
| `rfid` | RFID | 定位/标签读写 |
| `process` | 处理节点 | 数据流处理步骤 |

### links（必填）

```json
{"from": "节点ID", "to": "节点ID"}
```

可选字段：
- `label`：连线上的文字标注（如协议名称）
- `color`：连线颜色（十六进制，默认 `#64748b`）

### groups（可选）

将多个节点框在同一模块边界框内：

```json
{
  "id": "group_business",
  "label": "业务处理模块",
  "nodes": ["app_platform", "process_service"]
}
```

### pillars（可选，仅 system_architecture）

渲染为右侧纵向贯穿体系栏，固定写法：

```json
"pillars": ["标准规范体系", "信息安全体系", "运行管理体系"]
```

规则：
- 仅 `system_architecture` 图件支持 `pillars` 字段
- 固定三条，顺序固定：标准规范体系 / 信息安全体系 / 运行管理体系
- 纵栏贯穿所有层，渲染在层区域右侧，不与节点重叠
- 层区域宽度自动缩减，节点布局自动适配
- 其他图件类型禁止使用 `pillars`
- 若项目无需展示三体系，可省略此字段

### meta（可选）

```json
{
  "project": "执法视音频系统扩容项目",
  "company": "北京××科技有限公司",
  "date": "2026",
  "chart_style": "presentation"
}
```

#### meta.chart_style（可选字段）

| 值 | 风格 | 适用场景 |
|---|---|---|
| `presentation` | 汇报增强风（默认） | 领导汇报、专题汇报 |
| `review` | 内部工程风 | 立项审批、技术备案、内部审查 |
| `tender` | 投标结构强化风 | 投标文件、专家评审 |

- 缺省时默认 `presentation`
- AI 生成 JSON 时可按场景填写此字段，也可省略
- 旧 JSON 不含此字段时，渲染器自动使用 `presentation`

---

## 三、图件生成规则

### 3.1 通用规则

AI 必须：

1. 先读取 `specs/方案需要生成图件确认.md` 确认需要生成的图件
2. 根据 `chart_type` 生成对应 JSON
3. 每个节点必须有 `layer` 字段（与 `layers` 数组值完全匹配）
4. `id` 使用英文，不含空格和特殊字符
5. 节点数量控制在 **3～12 个**（保证图面清晰）
6. 每层节点数控制在 **1～5 个**（避免排列过密）

AI 禁止：

- 输出 x、y 坐标
- 输出 HTML / SVG 代码
- 生成超出规范的字段
- 每层超过 5 个节点
- 总节点超过 15 个

---

#### 3.1.1 chart_type 节点类型限制

不同 chart_type 允许的节点类型不同。

system_architecture：

允许：

user
terminal
mobile
platform
app
process
database


允许设备类型（抽象）：
storage
display
gateway

禁止：
server
switch
router
firewall
camera
nvr
rfid
sensor


system_architecture 图件必须使用六层结构，不得新增或删除层级,layers 顺序固定如下：
用户层
业务应用层
业务支撑层
数据层
网络层
硬件层

system_architecture 图件必须包含 pillars 字段，固定写法：

```json
"pillars": ["标准规范体系", "信息安全体系", "运行管理体系"]
```

- 禁止修改 pillars 条目的顺序或名称
- 禁止在其他 chart_type 中使用 pillars 字段

system_architecture 示例节点不得包含 server / switch / camera 等实体设备。

---


### 3.2 system_architecture 软件模块生成规则

在 `system_architecture` 图件生成时，平台层允许生成软件模块节点，但必须同时满足以下条件：

1. 软件模块名称必须能够直接来源于 `output/建设方案.md` 中已明确出现的模块、服务、平台或系统名称。
2. 不得根据业务描述、功能描述或模型推理自行抽象、合并、拆分或新增软件模块。
3. 软件模块节点仅允许放置在“平台层”，不得放置在其他层级。
4. 软件模块节点 `type` 仅允许使用：`app`、`platform`、`process`。
5. 若 `output/建设方案.md` 中未明确出现可直接提取的软件模块名称，则平台层不得生成软件模块节点。
6. 软件模块节点数量应控制在 **1～4 个**，超过时应按已写明的一级模块进行归并，不得细化到功能点级别。
7. 软件模块节点 `label` 必须与 `output/建设方案.md` 中原文表述保持基本一致，允许仅做“模块 / 服务 / 平台 / 系统”级别的名称规范化，不得改变原意。
8. 软件模块节点属于结构表达，不得替代服务器、数据库、存储、终端、摄像机等实体节点。
9. 若加入软件模块节点会导致图面拥挤或主结构失真，则应优先保证系统层次、核心节点与主链路表达清晰。

---

## 四、示例

### 4.1 系统总体架构图

```json
{
  "chart_type": "system_architecture",
  "title": "执法视音频管理系统总体架构",
  "meta": {
    "project": "执法视音频系统扩容项目",
    "company": "北京宽和精英科技",
    "date": "2026"
  },
"layers": [
  "用户层",
  "业务应用层",
  "业务支撑层",
  "数据层",
  "网络层",
  "硬件层"
],
"nodes": [
  {"id": "user_terminal", "type": "terminal", "layer": "用户层", "label": "业务终端"},
  {"id": "mobile_user", "type": "mobile", "layer": "用户层", "label": "移动端"},
  {"id": "app_platform", "type": "platform", "layer": "业务应用层", "label": "执法管理平台"},
  {"id": "process_service", "type": "process", "layer": "业务支撑层", "label": "业务处理服务"},
  {"id": "data_db", "type": "database", "layer": "数据层", "label": "业务数据库"},
  {"id": "storage_sys", "type": "storage", "layer": "硬件层", "label": "存储设备"}
],
"links": [
  {"from": "user_terminal", "to": "app_platform"},
  {"from": "mobile_user", "to": "app_platform"},
  {"from": "app_platform", "to": "process_service"},
  {"from": "process_service", "to": "data_db"},
  {"from": "data_db", "to": "storage_sys"}
],
   "groups": [
  {"id": "g_app", "label": "业务应用系统", "nodes": ["app_platform", "process_service"]}
],
"pillars": ["标准规范体系", "信息安全体系", "运行管理体系"]
}
```

### 4.2 网络拓扑图

```json
{
  "chart_type": "network_topology",
  "title": "网络拓扑图",
  "meta": {"project": "执法视音频系统扩容项目", "date": "2026"},
  "layers": ["接入终端区", "核心网络区", "业务服务区"],
  "nodes": [
    {"id": "terminal_01", "type": "terminal", "layer": "接入终端区", "label": "业务终端"},
    {"id": "core_sw",     "type": "switch",   "layer": "核心网络区", "label": "核心交换机"},
    {"id": "fw_01",       "type": "firewall", "layer": "核心网络区", "label": "防火墙"},
    {"id": "app_srv",     "type": "server",   "layer": "业务服务区", "label": "应用服务器"},
    {"id": "nas_01",      "type": "storage",  "layer": "业务服务区", "label": "网络存储"}
  ],
  "links": [
    {"from": "terminal_01", "to": "core_sw"},
    {"from": "core_sw",     "to": "fw_01"},
    {"from": "fw_01",       "to": "app_srv"},
    {"from": "app_srv",     "to": "nas_01"}
  ]
}
```

### 4.3 部署结构图

```json
{
  "chart_type": "deployment_structure",
  "title": "系统部署结构图",
  "meta": {"project": "执法视音频系统扩容项目", "date": "2026"},
  "layers": ["应用服务器", "数据库服务器", "存储服务器"],
  "nodes": [
    {"id": "app1", "type": "app",      "layer": "应用服务器", "label": "视频管理服务"},
    {"id": "app2", "type": "app",      "layer": "应用服务器", "label": "业务处理服务"},
    {"id": "db1",  "type": "database", "layer": "数据库服务器", "label": "主数据库"},
    {"id": "db2",  "type": "database", "layer": "数据库服务器", "label": "备数据库"},
    {"id": "nas1", "type": "storage",  "layer": "存储服务器", "label": "视频存储阵列"}
  ],
  "links": [
    {"from": "app1", "to": "db1"},
    {"from": "app2", "to": "db1"},
    {"from": "db1",  "to": "db2", "label": "同步"},
    {"from": "app1", "to": "nas1"}
  ]
}
```

### 4.4 数据流图

```json
{
  "chart_type": "data_flow",
  "title": "数据流图",
  "meta": {"project": "执法视音频系统扩容项目", "date": "2026"},
  "layers": ["数据采集", "数据处理", "数据存储", "数据应用"],
  "nodes": [
    {"id": "camera",    "type": "camera",   "layer": "数据采集", "label": "视频采集"},
    {"id": "gateway",   "type": "gateway",  "layer": "数据采集", "label": "数据网关"},
    {"id": "processor", "type": "process",  "layer": "数据处理", "label": "流媒体处理"},
    {"id": "analyze",   "type": "process",  "layer": "数据处理", "label": "智能分析"},
    {"id": "db",        "type": "database", "layer": "数据存储", "label": "结构化数据库"},
    {"id": "nas",       "type": "storage",  "layer": "数据存储", "label": "视频存储"},
    {"id": "client",    "type": "terminal", "layer": "数据应用", "label": "客户端"}
  ],
  "links": [
    {"from": "camera",    "to": "gateway"},
    {"from": "gateway",   "to": "processor"},
    {"from": "processor", "to": "analyze"},
    {"from": "processor", "to": "nas"},
    {"from": "analyze",   "to": "db"},
    {"from": "db",        "to": "client"},
    {"from": "nas",       "to": "client"}
  ]
}
```

### 4.5 实施甘特图（project_gantt）

```json
{
  "chart_type": "project_gantt",
  "title": "实施甘特图",
  "meta": {
    "project": "项目名称",
    "company": "建设单位",
    "date": "2026",
    "chart_style": "presentation"
  },
  "tasks": [
    {
      "id": "task_1",
      "name": "项目准备阶段",
      "start_date": "2026-03-01",
      "end_date": "2026-03-31",
      "duration": 31,
      "dependencies": [],
      "milestone": true,
      "progress": 0,
      "resources": "项目管理团队"
    },
    {
      "id": "task_1_1",
      "name": "需求分析与确认",
      "start_date": "2026-03-01",
      "end_date": "2026-03-10",
      "duration": 10,
      "dependencies": [],
      "milestone": false,
      "progress": 0,
      "resources": "需求分析团队"
    }
  ],
  "milestones": [
    {
      "id": "milestone_1",
      "name": "项目启动",
      "date": "2026-03-01",
      "description": "项目正式启动"
    }
  ]
}
```

#### tasks 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 唯一英文 ID（阶段：`task_1`；子任务：`task_1_1`） |
| `name` | string | 任务名称（中文，建议 ≤ 12 字） |
| `start_date` | string | 开始日期，格式 `YYYY-MM-DD` |
| `end_date` | string | 结束日期，格式 `YYYY-MM-DD` |
| `duration` | number | 工期天数 |
| `dependencies` | array | 前置任务 ID 列表（可为空数组） |
| `milestone` | boolean | `true` 表示阶段级任务（粗体深色条），`false` 表示子任务 |
| `progress` | number | 完成百分比（0–100），尚未开始填 0 |
| `resources` | string | 负责团队（可省略） |

#### milestones 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 唯一 ID |
| `name` | string | 里程碑名称（≤ 8 字） |
| `date` | string | 日期，格式 `YYYY-MM-DD` |
| `description` | string | 简短描述（可省略） |

#### AI 生成规则（project_gantt）

- 阶段数建议 4–6 个（milestone: true 的任务）
- 每阶段子任务建议 2–4 个
- 日期必须连续合理，不得出现逻辑矛盾
- duration 必须与 start_date / end_date 一致
- milestones 标记关键交付节点，建议 4–6 个
- 禁止输出 x / y 坐标或 HTML

---

## 五、输出规范

生成后保存到：

```
output/chart_spec/<图件类型>.json
```

例如：
```
output/chart_spec/system_architecture.json
output/chart_spec/network_topology.json
output/chart_spec/deployment_structure.json
output/chart_spec/data_flow.json
output/chart_spec/project_gantt.json
```

渲染时替换 `chart/renderer.html` 中的 `{{chart_data}}` 即可。
