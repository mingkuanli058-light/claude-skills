# Bidding Skill — 投标文件工程化生成

基于 Claude Code Skill 的投标文件自动化生成工具链。支持同一招标项目生成多份不同风格的投标文件。

## 工作流程

```
招标文件 (PDF/Word)
       ↓
解析为 shared/ 结构化文件（人工审核确认）
       ↓
填写各投标主体 projects/X/specs/（公司资料、报价清单、偏离表、style_profile）
       ↓
Claude 逐个生成 A → B → C（上下文隔离）
       ↓
python cross_check.py → 交叉检查
       ↓
build_docx.py → Word 投标文件
```

## 目录结构

```
bidding-skill/
├── SKILL.md                        # 技能定义与行为约束
├── readme.md                       # 本文件
├── cross_check.py                  # ★ 交叉检查工具（相似度/泄露/报价模式）
│
├── shared/                         # ★ 招标侧信息（三份共享，只读）
│   ├── 招标文件摘要.md              # 项目信息、时间节点、废标条款
│   ├── 评分标准.md                  # 评分细则 → 决定写作权重
│   ├── 技术要求.md                  # 技术参数与功能需求（含★标记）
│   ├── 商务要求.md                  # 交付、验收、售后条款
│   └── 资格要求.md                  # 资质、业绩、人员要求
│
├── projects/                       # ★ 各投标主体独立目录（数据隔离）
│   ├── A/
│   │   ├── specs/
│   │   │   ├── 公司资料.md          # A 的公司信息
│   │   │   ├── 报价清单.md          # A 的报价（与 B/C 不同）
│   │   │   ├── 偏离表.md            # A 的偏离声明
│   │   │   └── style_profile.md    # ★ A 的写作风格档案
│   │   ├── output/
│   │   │   ├── 技术方案.md
│   │   │   ├── 商务方案.md
│   │   │   ├── 报价文件.md
│   │   │   ├── 资格文件.md
│   │   │   ├── chart/              # A 的图件（独立配色/布局）
│   │   │   ├── build_docx.py
│   │   │   └── html2png.py
│   │   └── drafts/
│   ├── B/                          # 同 A 结构
│   └── C/                          # 同 A 结构
│
├── specs/                          # 单份模式模板（已废弃，不再使用）
├── rules/                          # 写作规则
│   ├── tone.md                     # 投标语气规则
│   ├── forbidden.md                # 禁止行为
│   ├── scoring_strategy.md         # 评分导向写作策略
│   ├── compliance_rules.md         # 废标红线检查规则
│   └── multi_version.md            # ★ 多版本差异化规则
├── templates/                      # 章节结构模板
│   ├── 技术方案模板.md
│   ├── 商务方案模板.md
│   ├── 报价文件模板.md
│   └── 资格文件模板.md
└── bak/                            # 备份/参考
```

## 使用方法


本 Skill 统一采用 shared/ 权威域模型。

无论单家公司投标还是多主体投标，均必须：

shared/  → 招标侧权威输入  
projects/X/specs/ → 投标侧输入


#### 第一步：填写招标侧信息（共享）

```
按 bidding Skill，解析这份招标文件，提取结构化信息至 shared/ 目录。



以下是在claude 里面的对话：


按 bidding skill 的解析规则，

对我提供的招标文件原文（PDF / Word / 文本）：

只做信息提取，不允许总结、不允许改写、不允许解释，


按以下文件结构输出至 shared/ 目录：

1. 招标文件摘要
2. 评分标准
3. 技术要求（逐条保留原文）
4. 商务要求
5. 资格要求
6. 废标条款

shared/
├── 招标文件摘要.md
├── 评分标准.md
├── 技术要求.md
├── 商务要求.md
├── 资格要求.md
  └── 废标条款.md

保持原句，禁止人类语言优化。



根据招标要求，生成图件用结构化 specs 的提示词：

按 bidding Skill 执行。

不要生成投标文件。
不要输出技术方案 / 商务方案 / 报价文件。

仅允许从 shared/ 权威输入域 提取系统结构信息：

shared/技术要求.md

shared/招标文件摘要.md（若涉及架构描述）

shared/评分标准.md（若影响结构表达）

将结构信息重排为以下文件（唯一合法输出）：

projects/A/specs/系统架构.md

projects/A/specs/网络拓扑.md

projects/A/specs/部署结构.md

projects/A/specs/数据流转.md

约束规则（强制）：

仅允许使用 shared/ 原文中已明确出现的系统元素

禁止新增技术组件、系统角色或连接关系

禁止基于常识或行业经验补全结构

禁止推断隐含架构

若结构信息不足，必须标记为 “待确认”

不得生成图件，仅生成结构化 specs 文件


```

shared/ 下的文件三份共用，只需填写一次。

#### 第二步：填写各投标主体信息

分别填写 projects/A/specs/、projects/B/specs/、projects/C/specs/：

- **公司资料.md** — 三家不同公司的信息
- **报价清单.md** — 三份不同报价
- **偏离表.md** — 允许不同偏离策略
- **style_profile.md** — 三种不同写作风格


#### 第三步：逐个生成（上下文隔离）

```
按 bidding Skill，
基于 shared/ 招标信息 + projects/A/specs/ 投标信息，
按 projects/A/specs/style_profile.md 风格，
生成 A 的技术方案至 projects/A/output/。
```

**重要：** 一次对话只处理一个投标主体。完成 A 后，新开对话处理 B。

#### 第四步：交叉检查

三份全部完成后运行：

```
python cross_check.py
```

检查内容：
- 文本相似度（逐段比对，阈值 40%）
- 数据泄露（A 文件中搜索 B/C 的公司关键词）
- 报价模式（是否呈等差/等比/整数倍关系）

#### 第五步：差异化修改

根据交叉检查报告，修改相似度过高的段落。

#### 第六步：转为 Word

```
python projects/A/output/build_docx.py --all
python projects/B/output/build_docx.py --all
python projects/C/output/build_docx.py --all
```

## 风格差异化维度

| 维度 | A 示例 | B 示例 | C 示例 |
|------|--------|--------|--------|
| 风格名称 | 架构导向型 | 实施细节型 | 案例佐证型 |
| 句式 | 长句复合结构 | 短句清单化 | 中等+表格混排 |
| 论述角度 | 从需求推导方案 | 从方案映射需求 | 从对比说明优势 |
| 图件配色 | 蓝色系 | 绿色系 | 灰色系 |
| 图件布局 | 横向 | 纵向 | 矩阵 |
| 表格密度 | 低（偏文字） | 高（偏表格） | 中（混合） |
| 行距 | 28磅 | 29磅 | 27磅 |

## 防串标检查清单

- [ ] 三份文件无交叉公司信息泄露
- [ ] 同一章节文本相似度 <40%
- [ ] 三份报价无等差/等比/整数倍规律
- [ ] 图件配色与布局可区分
- [ ] Word 文件属性（作者/公司）分别设置
- [ ] 文件名无版本序号（不叫 A版/B版）

## 依赖

```
pip install python-docx playwright
playwright install chromium
```



## rules/multi_version.md — 多版本核心规则，包含：

约束维度	具体规则
项目隔离	shared/（招标侧共享）+ projects/A|B|C/（投标侧隔离），生成 A 时禁止读取 B、C
风格差异化	6 个维度强制差异：句式、论述角度、图件配色布局、表格密度、强调手法、章节详略
文本相似度	同一章节任意两份之间逐段相似度不超过 40%
防串标红线	不得出现其他主体公司名/人名/电话；报价不得呈等差/等比/整数倍规律
元数据清洁	Word 作者/公司属性必须分别设置；文件名不含版本序号
构建顺序	逐个生成（A→B→C），禁止同一对话处理多个主体
specs/style_profile.md — 风格档案模板（每个主体一份）

cross_check.py — 交叉检查工具：

文本相似度比对（difflib，阈值 40%）
数据泄露检测（提取公司关键词交叉搜索）
报价模式分析（等差/等比/整数倍检测）





按 bidding Skill，

权威输入来源：

权威输入来源：

  - shared/招标文件摘要.md
  - shared/技术要求.md
  - shared/评分标准.md
  - shared/商务要求.md
  - shared/资格要求.md
  - projects/A/specs/style_profile.md
  - projects/A/specs/系统架构.md
  - projects/A/specs/网络拓扑.md
  - projects/A/specs/部署结构.md
  - projects/A/specs/数据流转.md

任务目标：

依据上述 specs 文件中已定义的系统元素与关系，

生成 A 公司正式图件：

1. 系统总体架构图
2. 网络拓扑图
3. 部署结构图
4. 数据流转图

图件规则（不可违反）：

- 严格遵循 SKILL.md 图件生成规则
- 禁止引入 specs 未定义的节点或组件
- 图件源格式必须为 HTML
- 输出路径：projects/A/output/chart/
- PNG/SVG 仅作为派生格式
- 图件表达风格必须服从 style_profile.md
- 图件复杂度必须最小化，优先专家阅读效率

禁止行为：

- 禁止基于行业常识补充结构
- 禁止优化或重构系统设计
- 禁止改变 specs 已定义关系