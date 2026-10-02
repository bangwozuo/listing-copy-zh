# 卖点文案

> 原子技能 ｜ 属于「Listing 文案师」 ｜ 电商小卖家 客群 ｜ ID `de_ecom_07_sk02`

用 **FAB 三层追问**把商品参数翻译成用户收益，排成可上架的**五点描述 / 卖点清单**。

![流程示意](docs/assets/overview.svg)

---

## 这是什么

一份可直接粘贴到任意 AI 工具的提示词，外加一个**离线可跑的校验脚本**
（字符数 / FAB 三要素 / 首条差异化 / 证据数字 / 违禁词）。

| 特性 | 说明 |
|------|------|
| 零 API Key | 不需要任何密钥 |
| 零部署 | 无需服务端；脚本用本机 Python 直接跑 |
| 平台无关 | Coze / WorkBuddy / Dify / Claude / ChatGPT 均可 |
| 用户自备算力 | 模型来自你自己的订阅 |

## 快速开始

**方式一 · 纯提示词**

```text
1. 打开 skills/selling-point-copy/prompt.txt
2. 全文复制，粘贴到你的 AI 工具
3. 按输入规格提供 product_info + platform
```

**方式二 · 带脚本（产出 Excel 校验单）**

```bash
python scripts/five_point_build.py --input examples/input.json --outdir out
```

产物：`out/五点校验.xlsx`、`out/five_point.json`

## 能力要点

| 平台 | 单条卖点上限 | 口径 |
|---|---|---|
| Amazon（Bullet Points） | 500 字符 | 硬 |
| 抖音商品卡 | 40 字 | 建议 |
| 拼多多 | 30 字 | 建议 |
| 淘宝 / 天猫 | 80 字 | 建议 |

FAB = Feature（属性）→ Advantage（优势）→ Benefit（收益），每条至少追问 3 层；
第 1 条放最大差异化卖点。

## 文件地图

```text
├── README.md                ← 本文件
├── SKILL.md                 ← 资产定义（元信息 / 契约 / 边界）
├── prompt.txt               ← 提示词本体（核心交付物）
├── schema.json              ← 输入输出契约（机器可读）
├── scripts/                 ← 离线校验脚本（产出 Excel）
├── examples/                ← 示例输入与实跑输出
└── docs/                    ← 10 项配套文档
```

## 面向谁 / 解决什么

- **用户群体**：淘宝 / 抖店 / 拼多多 / 小红书 / Amazon 店铺小卖家
- **解决痛点**：卖点写成参数罗列、没有收益、上架被驳回
- **衡量指标**：详情页转化率、加购率、退货率（表述不符导致的退货）

详见 [使用示例](docs/04-examples.md) 与 [测试报告](docs/09-test-report.md)。

## 合规

- 本资产输出为 **AI 辅助生成内容**，发布前必须经人工审核
- 无证据不写强表述；涉及功效须保留证据出处
- 请按所在平台要求完成 **AI 生成内容标识**

---

*本资产遵循 [bangwozuo 数字员工资产规范](https://github.com/bangwozuo/digital-employee-spec) v3.0*
