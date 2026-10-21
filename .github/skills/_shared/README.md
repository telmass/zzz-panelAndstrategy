# 共享 references（不是 skill）

这里是多个 skill 共同引用的**唯一事实源**。规则正文只在本目录写一份，各 skill 只留「流程 + 链接」，
避免同一张映射表/命名规范在几处各写一遍后互相漂移。

| 文件 | 内容 | 被谁引用 |
| --- | --- | --- |
| [naming.md](naming.md) | 规范 slug 唯一性、属性/职业/评级 → 图标 slug、图片命名与 `/images/…` 约定 | `agent-strategy` `fix-agent` `do_calculatorModel` `read-zzz-agent-stats` `get-agent-strategy` |
| [editorial-fields.md](editorial-fields.md) | 信息采集矩阵：应该寻找的点 → 修改的文件 → 字段 → 来源 | `agent-strategy` `get-agent-strategy` |
| [deploy-checklist.md](deploy-checklist.md) | 六阶段流程、每阶段闸门命令、技能文本抓取口径（R1–R6）、已知坑 | 全部与代理人流程相关的 skill |

## 技能关系

```
get-agent-strategy          ← 唯一入口：新增代理人 / 修正补充已有代理人
├── agent-strategy          阶段 C/D：抓 WIKI + 写编辑内容 + 算毕业面板
│   ├── read-zzz-agent-stats   官方 Wiki 面板与核心加成（写 data/catalog/agents.json）
│   ├── read-zzz-engine-stats  官方 Wiki 音擎（写 data/catalog/weapons.json）
│   └── read-zzz-drive-disc    官方 Wiki 驱动盘套装（写 data/catalog/drive-discs.json）
├── agent-background        阶段 C：立绘背景（Gachabase）+ 角色框头像（Nanoka）
├── do_calculatorModel      阶段 B：计算器预设（data/catalog/agents.json）
├── fix-agent               阶段 0：修正模式的问题定位
└── refactoring-ui          与代理人流程无关，仅改界面时用
```

各子 skill 仍可单独使用；横幅里写明它们被 `get-agent-strategy` 编排。

## 与仓库文档的关系

- `strategy/README.md` —— 攻略数据契约（字段定义），**不搬家**
- `docs/README.md` —— 项目文档索引
- 本目录 —— **操作规程**（怎么抓、怎么写、怎么校验）
