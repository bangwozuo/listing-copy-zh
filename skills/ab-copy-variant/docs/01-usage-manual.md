# A/B 文案变体 · 安装使用手册

> 本资产有两条使用路径：**纯提示词**（最快）与**带脚本**（差异度与样本量计算 + 产出 Excel）。
> 全程 **不需要 API Key**。

---

## 一、前置条件

| 项 | 要求 |
|----|------|
| AI 工具 | 任一支持自定义提示词/角色设定的工具（Coze / WorkBuddy / Dify / Claude / ChatGPT / 通义 / Kimi） |
| 算力 | 你自己的账号订阅，本资产不代付任何模型费用 |
| 数据 | 实验需求 + 被改写的单一卖点；有 CTR 数据则更佳 |
| 脚本路径（可选） | Python 3.10+，依赖 `openpyxl`（经共享库 `lib/assettools.py`；缺失时会打印缺失命令） |
| 知识库 | 可选，强烈建议（见仓库 `knowledge/`） |

---

## 二、安装

### 方式一 · 导入提示词

| 平台 | 导入方式 |
|------|---------|
| **Coze / 扣子** | 新建 Bot → 人设与回复逻辑 → 粘贴 `prompt.txt` |
| **WorkBuddy** | 新建 Skill → 指令区填入 `prompt.txt` |
| **Dify** | 新建应用 → 提示词编排 → 粘贴 `prompt.txt` |
| **Claude** | 新建 Project → Instructions → 粘贴 `prompt.txt` |
| **ChatGPT** | 新建 GPT → Instructions → 粘贴 `prompt.txt` |
| **通义 / 文心 / Kimi** | 直接粘贴到系统提示词 / 角色设定 |

> **要点**：`prompt.txt` 是完整提示词，**整份粘贴**，不要只取片段。

### 方式二 · 运行校验脚本

```bash
python scripts/variant_matrix.py --demo
python scripts/variant_matrix.py --input examples/input.json --outdir out
```

---

## 三、输入准备

| 输入项 | 必填 | 说明 |
|--------|------|------|
| `brief` | ✅ | 实验需求：测什么、目标平台、目标人群 |
| `selling_point` | ⬜ | 被改写的卖点原文（单一卖点，变体只改它） |
| `variants` | ⬜ | 已有变体（提供则只做差异度与合规校验） |
| `metrics` | ⬜ | 各变体曝光量与点击量，用于显著性判定与择优 |
| `platform` | ⬜ | 淘宝 / 天猫 / 抖音 / 拼多多 / 小红书 / Amazon |

> 完整字段定义见同目录 `schema.json`。

---

## 四、使用方法

```text
1. 把 prompt.txt 全文作为系统提示词
2. 明确单一变量（只改哪个卖点的表达），冻结其余变量
3. 从 6 个角度选 2–6 个写变体；跑 scripts/variant_matrix.py 算差异度与样本量
4. 样本充足才下择优结论；上线前人工确认
```

---

## 五、看懂脚本产物

| 文件 | 内容 |
|---|---|
| `out/AB变体矩阵.xlsx` | Sheet1 变体组 / Sheet2 差异度矩阵 / Sheet3 实验设计 / Sheet4 校验 |
| `out/variant_matrix.json` | 机器可读结果；含 `same_pairs` / `verdict` / `checks` |

---

## 六、常见问题

| 问题 | 处理 |
|------|------|
| 变体被判同质化 | J ≥ 0.6 说明只是换词，换角度重写 |
| 实验结果不可信 | 检查是否同时改了价格/主图；曝光是否 ≥ 最小样本量 |
| 曝光不足 | 延长投放周期或提高投放预算，不要提前看结论 |
| 脚本报缺依赖 | `python -m pip install openpyxl` |

---

## 七、版本

| 项 | 值 |
|----|-----|
| 资产版本 | v0.3.0（深度改造：角度库 + Jaccard + 样本量公式） |
| 规范版本 | bangwozuo 资产规范 v3.0 |
| 资产形态 | 纯提示词 + 可选离线校验脚本（零密钥） |

---

*面向：淘宝 / 抖店 / 拼多多 / 小红书 / Amazon 店铺小卖家*
