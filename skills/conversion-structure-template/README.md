# 转化结构模板

> 原子技能 ｜ 属于「Listing 文案师」 ｜ 电商小卖家 客群 ｜ ID `de_ecom_07_sk04`

把卖点搭成**模块化**的详情页 / A+ 页面骨架，标注每个模块的功能定位、字数与素材要求。

![流程示意](docs/assets/overview.svg)

---

## 这是什么

一份可直接粘贴到任意 AI 工具的提示词，外加一个**离线可跑的结构校验脚本**
（模块数 / A+ 必备模块 / 首屏字数 / 对比表红线 / 模块文案违禁词）。

| 特性 | 说明 |
|------|------|
| 零 API Key | 不需要任何密钥 |
| 零部署 | 无需服务端；脚本用本机 Python 直接跑 |
| 平台无关 | Coze / WorkBuddy / Dify / Claude / ChatGPT 均可 |
| 用户自备算力 | 模型来自你自己的订阅 |

## 快速开始

**方式一 · 纯提示词**

```text
1. 打开 skills/conversion-structure-template/prompt.txt
2. 全文复制，粘贴到你的 AI 工具
3. 提供 brief（品类 / 卖点 / 人群 / 品牌 / 本店 SKU）
```

**方式二 · 带脚本（产出 Excel 结构单）**

```bash
python scripts/detail_page_outline.py --input examples/input.json --outdir out
```

产物：`out/详情页结构.xlsx`、`out/detail_page.json`

## 模块库与硬约束

| 约束 | 数值 |
|---|---|
| 模块数 | 6–10 个 |
| 首屏（前 3 模块）字数 | ≤ 120 字 |
| A+ 必备模块 | 品牌故事 / 对比表 / 场景图 |
| 对比表 | 只对比本店 SKU，禁写竞品名与贬低话术 |

## 文件地图

```text
├── README.md                ← 本文件
├── SKILL.md                 ← 资产定义（元信息 / 契约 / 边界）
├── prompt.txt               ← 提示词本体（核心交付物）
├── schema.json              ← 输入输出契约（机器可读）
├── scripts/                 ← 离线结构校验脚本（产出 Excel）
├── examples/                ← 示例输入与实跑输出
└── docs/                    ← 10 项配套文档
```

## 面向谁 / 解决什么

- **用户群体**：淘宝 / 抖店 / 拼多多 / 小红书 / Amazon 店铺小卖家
- **解决痛点**：详情页没结构、美工不知道排什么、对比表踩竞品红线
- **衡量指标**：详情页停留时长、转化率、因「描述不符」的退货率

详见 [使用示例](docs/04-examples.md) 与 [测试报告](docs/09-test-report.md)。

## 合规

- 本资产输出为 **AI 辅助生成内容**，排版定稿前必须经人工审核
- 对比表与参数表须与实物一致；不得贬低竞品
- 请按所在平台要求完成 **AI 生成内容标识**

---

*本资产遵循 [bangwozuo 数字员工资产规范](https://github.com/bangwozuo/digital-employee-spec) v3.0*
