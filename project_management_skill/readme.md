project-root/
├── specs/                     ⭐ 权威层（最重要）
│   ├── 范围基线.md
│   ├── 技术需求基线.md
│   ├── 技术基线.md            （若存在）
│   ├── 商务约束基线.md        （可选但高级）
│   └── tender_reference.md     （降级后的招标文件）
│
├── drafts/                    ⭐ 生成与推理层
│   ├── wbs/
│   ├── proposal/
│   ├── diagrams/
│   └── 临时分析.md
│
├── output/                    ⭐ 正式交付层
│   ├── WBS.md
│   ├── 建设方案.md
│   ├── 验收文档.md
│   └── chart/
│
└── SKILL.md / AGENTS.md       ⭐ 行为控制层



商务合同 + 技术合同
        ↓（人工裁决）
specs/范围基线.md        ⭐ 项目责任宪法

技术合同 / 需求确认
        ↓（人工提炼）
specs/技术需求基线.md    ⭐ 系统边界宪法



在 Claude Code / Skill 中的调用逻辑

真正专业的调用方式是：

生成 WBS

按 WBS_RULES Skill，严格依据 specs/范围基线.md 生成项目 WBS。

生成方案

按 proposal-writing Skill，严格依据 specs/技术需求基线.md 生成建设方案。

验收 / 范围争议

校验 output/WBS.md 是否存在超出 specs/范围基线.md 的节点。

👉 注意：Skill 不再直接吃合同

合同是人类世界资产，基线是模型世界资产。