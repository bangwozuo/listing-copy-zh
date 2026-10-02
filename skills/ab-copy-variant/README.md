# A/B 文案变体

> 原子技能 ｜ 属于「Listing 文案师」 ｜ 电商小卖家 客群 ｜ ID `de_ecom_07_sk05`

把**同一个卖点**从不同角度改写成**不同质**、**单一变量**、**可做显著性检验**的变体，
并给出 CTR 数据下的择优建议。

![流程示意](docs/assets/overview.svg)

---

## 这是什么

一份可直接粘贴到任意 AI 工具的提示词，外加一个**离线可跑的校验脚本**
（Jaccard 差异度 / 字数 / 最小样本量 / CTR 择优 / 违禁词）。

| 特性 | 说明 |
|------|------|
| 零 API Key | 不需要任何密钥 |
| 零部署 | 无需服务端；脚本用本机 Python 直接跑 |
| 平台无关 | Coze / WorkBuddy / Dify / Claude / ChatGPT 均可 |
| 用户自备算力 | 模型来自你自己的订阅 |

## 快速开始

**方式一 · 纯提示词**

```text
1. 打开 skills/ab-copy-variant/prompt.txt
2. 全文复制，粘贴到你的 AI 工具
3. 提供 brief + selling_point（可选 metrics）
```

**方式二 · 带脚本（产出 Excel 变体矩阵）**

```bash
python scripts/variant_matrix.py --input examples/input.json --outdir out
```

产物：`out/AB变体矩阵.xlsx`、`out/variant_matrix.json`

## 能力要点

| 项 | 口径 |
|---|---|
| 角度库 | 理性功能 / 数据实证 / 场景代入 / 情感共鸣 / 疑问钩子 / 对比反差 |
| 差异度 | Jaccard `J = |A∩B| / |A∪B|`；J ≥ 0.6 判同质化 |
| 每组最小曝光 | `n ≈ 16·p̄(1-p̄)/Δ²`（两比例检验近似） |
| 单一变量 | 只改卖点表达，价格/主图/时段/类目全部冻结 |

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
- **解决痛点**：标题迭代凭感觉、变体其实是同义换词、样本不足就下结论
- **衡量指标**：点击率（CTR）、实验可归因率

详见 [使用示例](docs/04-examples.md) 与 [测试报告](docs/09-test-report.md)。

## 合规

- 本资产输出为 **AI 辅助生成内容**，上线实验前必须经人工审核
- 实验不得针对同一用户展示不同价格；不采集任何用户数据
- 请按所在平台要求完成 **AI 生成内容标识**

---

*本资产遵循 [bangwozuo 数字员工资产规范](https://github.com/bangwozuo/digital-employee-spec) v3.0*
