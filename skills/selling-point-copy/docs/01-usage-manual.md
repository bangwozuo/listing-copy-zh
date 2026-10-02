# 卖点文案 · 安装使用手册

> 本资产有两条使用路径：**纯提示词**（最快）与**带脚本**（产出 Excel 校验单）。
> 全程 **不需要 API Key**。

---

## 一、前置条件

| 项 | 要求 |
|----|------|
| AI 工具 | 任一支持自定义提示词/角色设定的工具（Coze / WorkBuddy / Dify / Claude / ChatGPT / 通义 / Kimi） |
| 算力 | 你自己的账号订阅，本资产不代付任何模型费用 |
| 数据 | 按「输入准备」提供的商品参数与证据 |
| 脚本路径（可选） | Python 3.10+，依赖 `openpyxl`（经共享库 `lib/assettools.py`；缺失时会打印修复命令） |
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
python scripts/five_point_build.py --demo
python scripts/five_point_build.py --input examples/input.json --outdir out
```

---

## 三、输入准备

| 输入项 | 必填 | 说明 |
|--------|------|------|
| `product_info` | ✅ | 品名、材质、规格、参数、已证实卖点、适用人群 |
| `platform` | ✅ | Amazon / 淘宝 / 天猫 / 抖音 / 拼多多 / 小红书 |
| `points` | ⬜ | 已有卖点；提供则只校验与改写 |
| `evidence` | ⬜ | 检测报告号、专利号、实测数据与样本量 |

> 完整字段定义见同目录 `schema.json`。

---

## 四、使用方法

```text
1. 把 prompt.txt 全文作为系统提示词
2. 按「输入准备」把数据发给 AI → 得到五点描述 + FAB 拆解 + 校验表
3. 需要精确长度/FAB/违禁词证据时，跑 scripts/five_point_build.py
4. 人工审核后使用
```

---

## 五、看懂脚本产物

| 文件 | 内容 |
|---|---|
| `out/五点校验.xlsx` | Sheet1 五点校验（红线格标红）/ Sheet2 违规明细 / Sheet3 汇总 |
| `out/five_point.json` | 机器可读结果；含 `banned_detail` 逐条违禁命中 |

---

## 六、常见问题

| 问题 | 处理 |
|------|------|
| 卖点写成参数罗列 | 按 prompt 的 FAB 三层追问，逐层落到收益 |
| 一条卖点被判「FAB 不全」 | 缺 A（优势）或 B（收益），补一句「所以……你能……」 |
| 脚本报缺依赖 | `python -m pip install openpyxl` |
| 无证据想写强表述 | 不允许；按保守表述改写并标注口径 |

---

## 七、版本

| 项 | 值 |
|----|-----|
| 资产版本 | v0.3.0（深度改造：加脚本 + FAB 量化） |
| 规范版本 | bangwozuo 资产规范 v3.0 |
| 资产形态 | 纯提示词 + 可选离线校验脚本（零密钥） |

---

*面向：淘宝 / 抖店 / 拼多多 / 小红书 / Amazon 店铺小卖家*
