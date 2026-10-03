# Listing 文案师

> **①视觉员工的配套另一半——图和文案是同一次上架的两半**

[![Stage](https://img.shields.io/badge/stage-P0-orange)](https://github.com/bangwozuo)
[![Asset](https://img.shields.io/badge/asset-prompt%20%2B%20script-blueviolet)](#资产形态)
[![NoKey](https://img.shields.io/badge/API%20Key-not%20required-success)](#资产形态)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

![仓库演示](docs/demo.mp4)

*演示视频：5 个代表资产的真实执行录屏（关键词组合 → 卖点文案 → 广告法预审 → 标题工作流 → CTR 追踪），每支截图均为脚本实跑产出，非摆拍。*

---

## 它是谁

面向 **电商小卖家** 的数字员工资产包。

| 项目 | 内容 |
|------|------|
| 目标用户 | 月上新频繁、标题 SEO 靠抄的一人店 |
| 交付物 | 标题生成→上架 ≤10 分钟；合规扫描覆盖率 100%；CTR 环比提升 |
| 技能数 | 5 |
| 工作流数 | 5 |
| 旧名存档 | `上架文案专员·小文` |

### 数字员工总览

| 项 | 内容 |
|---|---|
| 身份 | Listing 文案师——图和文案是同一次上架的两半 |
| 做什么 | 标题组合、卖点、详情页文案、合规扫描、A/B 迭代 |
| 不做什么 | 不做虚假功效宣称、极限词擦边；不刷量、不拉踩竞品 |
| 边界 | 所有输出 AI 辅助生成，交付前人工确认；连接器只走官方 API 与用户导出数据 |
| KPI | 标题生成→上架 ≤10 分钟；合规扫描覆盖率 100%；CTR 环比提升 |

---

## 资产形态

**纯提示词 + 离线校验脚本** —— 这是理解本仓库的关键：

| 特性 | 说明 |
|------|------|
| ✅ 无需 API Key | 一个 Key 都不需要 |
| ✅ 无需部署 | 提示词直接粘贴；脚本用本机 Python 跑 |
| ✅ 平台无关 | 粘贴到任何 AI 工具即可使用 |
| ✅ 用户自备算力 | 模型来自你自己的订阅 |
| ✅ 确定性校验 | 每个资产自带脚本，字数/违禁词/样本量等可计算项以脚本为准 |

---

## 快速开始

```text
1. 打开 skills/keyword-combination/prompt.txt
2. 全文复制
3. 粘贴到你常用的 AI 工具（Coze / WorkBuddy / Dify / Claude / ChatGPT）
4. 按 SKILL.md 的输入规格提供数据
```

就这四步。完整指引见 [使用手册](docs/04-usage.md)。

---

## 仓库结构

```text
listing-copy-zh/
├── README.md / employee.md / package.yaml     # 入口与 12 字段定义卡
├── docs/01~07                                 # 员工级文档（架构/流程/场景/手册/示例/录像/测试）
├── skills/                                    # 5 个原子技能
│   └── <skill>/
│       ├── README.md  SKILL.md  prompt.txt  schema.json  examples/
│       └── docs/                              # 该技能自己的 10 项文档 + 配图
├── workflows/                                 # 5 条工作流（复合技能）
│   └── <workflow>/
│       ├── README.md  SKILL.md  prompt.txt  schema.json  examples/
│       └── docs/                              # 该工作流自己的 10 项文档 + 配图
├── knowledge/                                 # RAG wiki 知识库
│   ├── README.md  RAG-接入指南.md  template.md
│   └── wiki/(index.md, _template.md, entries/)
├── connectors/                                # 连接器说明 + 合规红线
├── quality/                                   # 效果基线与追踪日志
└── tests/                                     # 资产校验测试（离线，无需密钥）
```

### 每个技能 / 工作流自带的 docs

| 文档 | 内容 |
|------|------|
| `README.md` | 资产速览与快速开始 |
| `docs/01-usage-manual.md` | 安装使用手册 |
| `docs/02-architecture.md` | 业务架构图 |
| `docs/03-flow.md` | 流程图（Mermaid + 配图） |
| `docs/04-examples.md` | 使用示例 |
| `docs/05-media.md` | 截图和录屏（清单 + 分镜脚本） |
| `docs/06-scenarios.md` | 使用场景（适用 / 不适用） |
| `docs/07-audience.md` | 用户群体 |
| `docs/08-value.md` | 解决问题与价值 |
| `docs/09-test-report.md` | 测试报告 |
| `docs/assets/overview.svg` | 自动生成的流程示意图 |

---

## 交付物导航

| 文档 | 内容 |
|------|------|
| [业务架构](docs/01-architecture.md) | 四层架构 + 数据流 + 能力边界 |
| [工作流流程](docs/02-workflow.md) | 5 条工作流的 DAG 可视化 |
| [使用场景](docs/03-scenarios.md) | 3 个真实场景（含前后对比） |
| [使用手册](docs/04-usage.md) | 各平台导入指引 + 常见问题 |
| [示例库](docs/05-examples.md) | 5 组输入输出示例 |
| [录像脚本](docs/06-recording-script.md) | 7 镜头分镜 + 旁白稿 |
| [校验报告](docs/07-test-report.md) | 资产质量校验结果 |

---

## 技能清单（5 个）

| # | 技能 | 一句话 | 阶段 | README |
|---|------|--------|------|--------|
| 1 | [关键词组合](skills/keyword-combination/README.md) | 类目词×平台规则→标题候选 + 三处落位表（6 平台字数硬上限，KD 两档阈值） | `P0` | [README](skills/keyword-combination/README.md) |
| 2 | [卖点文案](skills/selling-point-copy/README.md) | FAB 三层追问把参数翻译成收益（Amazon 单条 ≤500 字符，4 级证据分级） | `P0` | [README](skills/selling-point-copy/README.md) |
| 3 | [广告法合规预审](skills/adlaw-compliance-precheck/README.md) | 四类规则扫描 + 三级判定 + 假阳性拦截（实跑 122 字命中 18 项） | `P0` | [README](skills/adlaw-compliance-precheck/README.md) |
| 4 | [转化结构模板](skills/conversion-structure-template/README.md) | 10 模块库搭详情页/A+ 骨架（模块数 6–10，首屏 ≤120 字） | `P1` | [README](skills/conversion-structure-template/README.md) |
| 5 | [A/B 文案变体](skills/ab-copy-variant/README.md) | 6 角度变体 + Jaccard 差异度 + 样本量公式（≥1900 曝光/组才下结论） | `P2` | [README](skills/ab-copy-variant/README.md) |

## 工作流清单（5 条）

| # | 工作流 | 一句话 | 触发 | README |
|---|--------|--------|------|--------|
| 1 | [关键词挖掘与标题组合](workflows/keyword-title-combo-flow/README.md) | 标题候选 → 广告法闸门，红线 0 才交付（回环 ≤2 次） | 人工 | [README](workflows/keyword-title-combo-flow/README.md) |
| 2 | [五点卖点生成](workflows/five-point-sellingpoint-flow/README.md) | FAB 翻译 → 双闸（质量 + 法规）→ 可用五点 | 人工 | [README](workflows/five-point-sellingpoint-flow/README.md) |
| 3 | [广告法合规预审](workflows/adlaw-compliance-flow/README.md) | 初检 + 复扫闭环，6 条量化验收（实跑红线 14→0） | 事件（文案定稿） | [README](workflows/adlaw-compliance-flow/README.md) |
| 4 | [详情页转化文案](workflows/detail-page-conversion-copy-flow/README.md) | 卖点校验→结构校验→终审，三技能串联出可排版文案稿 | 人工 | [README](workflows/detail-page-conversion-copy-flow/README.md) |
| 5 | [上架 CTR 追踪](workflows/listing-ctr-track-flow/README.md) | 6 节点 DAG：判健康→定位→A/B 判胜→合规拦截（实跑 B 组 +116%） | 定时（每周） | [README](workflows/listing-ctr-track-flow/README.md) |

---

## 知识库与连接器

| 目录 | 说明 |
|------|------|
| [`knowledge/`](knowledge/README.md) | RAG wiki 知识库：填入业务信息可显著提升输出质量 |
| [`connectors/`](connectors/README.md) | 连接器说明：数据从哪来、怎么合规地来 |

---

## 资产校验

```bash
pip install -r requirements.txt
pytest tests/ -v
```

校验技能完整性、提示词结构、契约一致性、工作流 DAG、技能级与工作流级 docs 完整性、知识库 wiki 与连接器结构。
**不需要任何 API Key。**

---

## 合规声明

- ✅ 所有输出为 **AI 辅助生成**，交付前须人工审核
- ✅ 提示词内置**违禁词禁止清单**，符合《广告法》要求
- ✅ 遵循《人工智能生成合成内容标识办法》
- ✅ 连接器只走**官方 API** 或**用户导出数据**
- ✅ 所有对外发布动作**保留人工确认环节**

---

## 许可

[Apache-2.0](LICENSE) — 可自由使用、修改、商用

---

*由 bangwozuo 业务库自动生成 · 2026-09-29*
