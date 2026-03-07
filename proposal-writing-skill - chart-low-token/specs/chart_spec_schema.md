# Chart Spec Schema v5

本文件定义图件结构 JSON 的统一格式。

AI 生成图件时**必须遵循本结构**。

完整规范见：chart/chart_schema.md

---

# 一、统一结构

```json
{
  "chart_type": "",
  "title": "",
  "meta": {
    "project": "",
    "company": "",
    "date": "",
    "chart_style": "presentation"
  },
  "layers": [],
  "nodes": [],
  "links": [],
  "groups": [],
  "pillars": []
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| chart_type | 是 | 图件类型 |
| title | 是 | 图件标题 |
| meta | 否 | 项目信息（用于底栏） |
| meta.project | 否 | 项目名称 |
| meta.company | 否 | 建设单位 |
| meta.date | 否 | 年份 |
| meta.chart_style | 否 | 渲染风格：`presentation`（默认）\| `review` \| `tender` |
| layers | 是 | 分层名称列表（顺序即渲染顺序） |
| nodes | 是 | 节点列表 |
| links | 是 | 连线列表 |
| groups | 否 | 模块分组（显示为虚线边界框） |
| pillars | 否 | 三体系纵栏（仅 system_architecture，固定三条，右侧贯穿显示） |

---

# 二、节点结构

```json
{
  "id": "唯一英文ID",
  "type": "节点类型",
  "layer": "所属层名称",
  "label": "显示名称"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| id | 是 | 唯一标识（英文，无空格） |
| type | 是 | 节点类型（决定图标，见 chart_schema.md） |
| layer | 是 | 所属层（必须与 layers 数组中的值完全一致） |
| label | 是 | 图中显示名称 |

**AI 禁止填写：x、y 坐标（由布局引擎自动计算）**

---

# 三、连线结构

```json
{
  "from": "node_id",
  "to": "node_id",
  "label": "可选标注"
}
```

---

# 四、chart_type 允许值

| 类型 | 图件 | 布局方式 |
|---|---|---|
| `system_architecture` | 系统架构图 | 垂直分层 |
| `network_topology` | 网络拓扑图 | 垂直分层 |
| `deployment_structure` | 部署结构图 | 水平分区 |
| `data_flow` | 数据流图 | 垂直分层 |

---

# 五、生成规则

AI 生成图件时：

必须：

1. 读取 chart_registry.md 确认图件类型
2. 读取 chart/chart_schema.md 了解字段规范
3. 生成符合本 Schema 的 JSON
4. 每个节点必须包含 `layer` 字段

禁止：

- 输出 x / y 坐标
- 输出 HTML 或 SVG
- 每层超过 5 个节点
- 总节点超过 15 个
- 生成未在 chart_schema.md 中定义的 type

---

# 六、渲染引擎

图件渲染使用：

chart/renderer.html

将生成的 JSON 替换 `{{chart_data}}` 后在浏览器打开即可渲染。

布局坐标由 chart/layout_engine.js 自动计算。
