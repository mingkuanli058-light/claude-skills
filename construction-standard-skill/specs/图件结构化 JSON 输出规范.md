一、规范目的

本规范用于统一模型在“空间布点图生成场景”中的 JSON 输出结构。

目标：

保证输出结构固定

保证 Python 渲染程序长期稳定运行

避免模型自由扩展字段

实现低 Token、可校验、可扩展

支持可计算空间定位规则

本规范属于：

图件逻辑输出层标准文件

二、总体原则

输出必须为标准 JSON

不得输出 JSON 以外的任何文本

字段名称必须固定

字段不得缺失

不得新增未定义字段

优化建议必须受控

模型不得输出坐标结果

三、顶层结构（固定）

模型输出必须严格符合以下结构：

{
  "schema_version": "1.1",
  "drawing_type": "string",
  "layout_data": {},
  "validation": {},
  "optimization_suggestions": []
}

顶层字段不得增减。

四、字段说明
1️⃣ schema_version（必填）

固定值：

"schema_version": "1.1"

用于版本控制。

2️⃣ drawing_type（必填）

表示图件类型，例如：

空间平面布点

机房布置图

设备安装图

视频监控布点

必须为字符串。

3️⃣ layout_data（必填）

图件逻辑层数据。

3.1 space（必填）
{
  "space": {
    "count": 1,
    "name": "空间名称",
    "size": {
      "length_m": 0,
      "width_m": 0,
      "height_m": 0
    },
    "coordinate_system": {
      "origin": "top_left",
      "x_direction": "right",
      "y_direction": "down"
    }
  }
}

说明：

coordinate_system 为 V1.1 新增字段（可选）

不属于坐标

仅用于统一渲染计算方向

3.2 fixed_elements（可选）

V1.1 升级结构：

{
  "fixed_elements": [
    {
      "name": "设施名称",
      "size": {
        "width_m": 0,
        "depth_m": 0
      },
      "position": {
        "anchor": "north",
        "align": "center",
        "offset_m": 0
      }
    }
  ]
}

若无固定设施：

"fixed_elements": []
anchor 枚举值

north

south

east

west

center

align 枚举值

left

center

right

top

bottom

说明：

position 字段为 V1.1 新增字段。
模型不得输出具体坐标，仅输出定位规则。

3.3 devices（必填）

V1.1 升级结构：

{
  "devices": [
    {
      "type": "设备类型",
      "count": 0,
      "install_method": "安装方式",
      "layout_strategy": "diagonal",
      "constraints": {
        "offset_from_wall_mm": 0,
        "install_height_m": 0,
        "target_elements": [],
        "avoid_elements": []
      }
    }
  ]
}
layout_strategy 枚举值（统一英文）

diagonal

four_corners

single_side

perimeter

uniform

radial

constraints 字段说明

offset_from_wall_mm：距离墙体

install_height_m：安装高度

target_elements：优先覆盖对象

avoid_elements：避让对象

constraints 为可选字段。

五、validation（必填）

固定结构：

{
  "coverage_check": "通过/存在风险",
  "blind_area_risk": "简短说明",
  "structure_conflict": "无/存在冲突",
  "risk_notes": []
}

规则：

所有字段必须存在

risk_notes 必须为数组

若无风险：

"risk_notes": []
六、optimization_suggestions（必填）

数组结构。

规则：

不超过 3 条

每条不超过 25 个字

不得使用段落

不得包含解释性说明

若无建议：

[]
七、严格禁止内容

模型不得：

输出 SVG

输出 HTML

输出坐标

输出样式

输出自然语言说明段落

输出 JSON 外文本

输出未定义字段

若输入不符合参数规范：

必须输出：

{
  "error": "输入参数不符合规范"
}

不得生成图件结构。

八、渲染职责划分

模型职责：

参数解析

布点逻辑判断

合理性校验

输出结构化规则

Python 职责：

坐标计算

图形绘制

样式定义

文件输出

模型不得参与渲染。

九、长期稳定性说明

只要：

输入符合《通用空间布点参数规范 V1.0》

输出符合本规范

则系统具备：

长期稳定运行能力

低 Token 消耗

可批量生成

可扩展多空间类型

支持精确布局计算

十、系统成熟度说明

当：

输入层规范固定

输出层 JSON 固定

渲染层程序固定

则图件系统进入：

工程级可计算空间布点引擎状态

模型不再“画图”。

模型只做：

结构生成

规则输出

合理性判断

渲染程序负责视觉呈现。