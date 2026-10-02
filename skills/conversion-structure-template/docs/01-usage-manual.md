# 转化结构模板 · 安装使用手册

> 本资产有两条使用路径：**纯提示词**（最快）与**带脚本**（结构规则校验 + 产出 Excel）。
> 全程 **不需要 API Key**。

---

## 一、前置条件

| 项 | 要求 |
|----|------|
| AI 工具 | 任一支持自定义提示词/角色设定的工具（Coze / WorkBuddy / Dify / Claude / ChatGPT / 通义 / Kimi） |
| 算力 | 你自己的账号订阅，本资产不代付任何模型费用 |
| 数据 | 商品 brief（品类 / 卖点 / 人群 / 品牌 / 本店 SKU） |
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

### 方式二 · 运行结构校验脚本

```bash
python scripts/detail_page_outline.py --demo
python scripts/detail_page_outline.py --input examples/input.json --outdir out
```

---

## 三、输入准备

| 输入项 | 必填 | 说明 |
|--------|------|------|
| `brief` | ✅ | 品类、核心卖点、目标人群、品牌名、本店 SKU 列表 |
| `platform` | ⬜ | Amazon（A+）/ 淘宝 / 天猫 / 抖音 / 拼多多 / 小红书 |
| `selling_points` | ⬜ | 已有卖点清单（无则按 brief 归纳） |
| `competitor` | ⬜ | 竞品名，仅用于提示规避，不得写入成品 |

> 完整字段定义见同目录 `schema.json`。

---

## 四、使用方法

```text
1. 把 prompt.txt 全文作为系统提示词
2. 按「输入准备」把 brief 发给 AI → 得到模块结构 + 对比表设计 + 校验表
3. 需要结构规则校验时，跑 scripts/detail_page_outline.py
4. 美工按模块结构出图；定稿前人工确认
```

---

## 五、看懂脚本产物

| 文件 | 内容 |
|---|---|
| `out/详情页结构.xlsx` | Sheet1 模块结构 / Sheet2 对比表 / Sheet3 校验 / Sheet4 汇总 |
| `out/detail_page.json` | 机器可读结果；含 `issues` / `banned_in_copy` / `table_redline_hits` |

---

## 六、常见问题

| 问题 | 处理 |
|------|------|
| 详情页太啰嗦 | 模块数超 10 会被判「用户流失」，删掉弱模块 |
| 首屏没人看 | 首屏 ≤ 120 字，参数类内容后移到规格表 |
| 对比表被判违规 | 只对比本店 SKU，删除竞品名与「比 XX 好」类话术 |
| 脚本报缺依赖 | `python -m pip install openpyxl` |

---

## 七、版本

| 项 | 值 |
|----|-----|
| 资产版本 | v0.3.0（深度改造：模块库 + 脚本 + 对比表红线） |
| 规范版本 | bangwozuo 资产规范 v3.0 |
| 资产形态 | 纯提示词 + 可选离线校验脚本（零密钥） |

---

*面向：淘宝 / 抖店 / 拼多多 / 小红书 / Amazon 店铺小卖家*
