---
name: selling-point-copy
description: 电商卖点提炼与五点描述（Amazon Bullet Points）生成。用 FAB 三层追问（Feature 物理属性 → Advantage 优势 → Benefit 用户收益）把参数翻译成用户收益，按平台字数硬上限（Amazon 单条 ≤500 字符、抖音商品卡 ≤40 字、拼多多 ≤30 字）排版，并对每条跑长度、FAB 三要素、首条差异化、证据数字、违禁词五项校验，产出 Excel 校验单。当用户需要写五点描述、提炼卖点、把参数翻译成人话、卖点合规自检时使用。
---

# 卖点文案

把商品参数通过 **FAB 三层追问**翻译成用户收益，排成可上架的**五点描述 / 卖点清单**。

不做的事：不写标题、不写促销方案、不判断商品质量。

## 元信息

| 字段 | 值 |
|------|-----|
| ID | `de_ecom_07_sk02` |
| 类型 | **`atomic`（原子技能）** |
| 所属员工 | Listing 文案师 |
| 能力族 | 文案生成 · 卖点提炼 |
| 复杂度 | `S` |
| 阶段 | `P0` |
| 复用度 | ★★★★☆（①⑤共用） |
| 资产形态 | 纯提示词 + 可选 Python 脚本（离线、无 API Key） |

## 能力描述

1. **FAB 三层追问** —— Feature（属性）→ Advantage（优势）→ Benefit（收益），
   每条卖点至少追问 3 层，答不出收益的不算卖点。
2. **平台长度约束** —— Amazon 单条 ≤ 500 字符（硬）；抖音 ≤ 40 字、拼多多 ≤ 30 字、
   淘宝/天猫 ≤ 80 字（建议值，以后台为准）。
3. **首条差异化法则** —— 第 1 条放最大差异化卖点，且须含可辨识特征（材质/数字/认证）。
4. **证据分级** —— 有报告号/样本量的才敢写强表述；无证据一律改保守表述。

## 输入规格

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `product_info` | object | ✅ | 品名、材质、规格、参数、已证实卖点、适用人群 |
| `platform` | string | ✅ | Amazon / 淘宝 / 天猫 / 抖音 / 拼多多 / 小红书 |
| `points` | array | ⬜ | 已有卖点；提供则只做校验与改写 |
| `evidence` | array | ⬜ | 检测报告号、专利号、实测数据、样本量 |

## 输出规格

- `points`：五点描述（含证据），每条标字符数与上限
- `fab_table`：FAB 拆解表（Feature / Advantage / Benefit 三列）
- `checks`：五项校验（长度 / FAB 三要素 / 首条差异化 / 有数字或证据 / 无违禁词）

## 使用步骤

### 方式一：纯提示词（最快）

1. 打开任意 AI 工具（Coze / WorkBuddy / Dify / Claude / ChatGPT）
2. 把 `prompt.txt` **全文**粘贴为系统提示词
3. 提供 `product_info` + `platform`（可选 `evidence`、`points`）
4. 得到五点描述 + FAB 拆解表 + 校验表

### 方式二：带脚本（长度与 FAB 三要素精确校验 + 产出 Excel）

```bash
python3 <SKILL_DIR>/scripts/five_point_build.py --input input.json --outdir out
python3 <SKILL_DIR>/scripts/five_point_build.py --demo      # 无输入也能看效果
```

产物：

| 文件 | 内容 |
|---|---|
| `out/五点校验.xlsx` | 五点校验 / 违规明细 / 汇总 |
| `out/five_point.json` | 机器可读结果 |

**分工**：脚本做**长度、FAB 词元、证据数字、违禁词的机械检查**；模型做**语义翻译与收益撰文**。

## 边界（不做的事）

- ❌ 不写没有证据的绝对化表述（最好/第一/100%/永久/绝对）
- ❌ 不把 Feature 当卖点交付（「采用 304 不锈钢」这类无收益句）
- ❌ 不编造检测报告号、专利号、样本量、销量
- ❌ 卖点里不写促销语、价格、竞品名、联系方式

## 调用示例

**输入**（`examples/input.json`）：Amazon 保温杯，5 条卖点含 1 条 Feature-only、1 条违禁。

**输出**（脚本实跑）：5 条中 3 条可用；第 4 条被判「无信息量形容词（优质）」，
第 5 条命中 7 处（最低 / 100% / 永久 / 加微信 / 领券 / 比某品牌 / 全网最低）。

## 所属工作流

- `five-point-sellingpoint-flow`（五点卖点生成）

## 合规声明

- 本技能输出为 **AI 辅助生成内容**，发布前必须人工确认
- 涉及功效的表述须保留证据出处，无法提供的按保守表述改写
- 平台字数与 style guide 以官方最新公示为准

---

*本技能遵循 [bangwozuo 数字员工资产规范](https://github.com/bangwozuo/digital-employee-spec) v3.0*
