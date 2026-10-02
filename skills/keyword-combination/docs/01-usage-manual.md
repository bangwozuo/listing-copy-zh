# 关键词组合 · 安装使用手册

> 本资产有两条使用路径：**纯提示词**（最快）与**带脚本**（产出 Excel 校验单）。
> 全程 **不需要 API Key**。

---

## 一、前置条件

| 项 | 要求 |
|----|------|
| AI 工具 | 任一支持自定义提示词/角色设定的工具（Coze / WorkBuddy / Dify / Claude / ChatGPT / 通义 / Kimi） |
| 算力 | 你自己的账号订阅，本资产不代付任何模型费用 |
| 数据 | 按「输入准备」提供的商品与关键词数据 |
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
# 无输入也能看效果
python scripts/title_keyword_check.py --demo

# 用真实数据
python scripts/title_keyword_check.py --input examples/input.json --outdir out

# 单条快速校验
python scripts/title_keyword_check.py --text "保温杯 304不锈钢 500ml" --platform 淘宝 --core-word 保温杯
```

---

## 三、输入准备

| 输入项 | 必填 | 说明 |
|--------|------|------|
| `product_info` | ✅ | 品名、材质、规格、卖点、适用人群/场景 |
| `platform` | ✅ | 淘宝 / 天猫 / 抖音 / 拼多多 / 小红书 / Amazon |
| `keywords` | ⬜ | 已知关键词及层级（核心词/长尾词/蓝海词/场景词） |
| `candidate_titles` | ⬜ | 已有标题；提供则只校验不生成 |

> 完整字段定义见同目录 `schema.json`。

---

## 四、使用方法

```text
1. 把 prompt.txt 全文作为系统提示词
2. 按「输入准备」把数据发给 AI → 得到标题候选 + 关键词布局 + 五项校验
3. 需要精确字数/违禁词证据时，跑 scripts/title_keyword_check.py
4. 人工审核后使用（对外发布保留人工确认）
```

---

## 五、看懂脚本产物

| 文件 | 内容 |
|---|---|
| `out/标题关键词校验.xlsx` | Sheet1 标题校验（红线格标红）/ Sheet2 关键词布局 / Sheet3 汇总 |
| `out/keyword_check.json` | 机器可读结果；含 `banned_detail` 逐条违禁命中 |

---

## 六、常见问题

| 问题 | 处理 |
|------|------|
| 输出太泛 | 挂载知识库，填入真实类目词表 |
| 标题被平台截断 | 跑脚本核对字数上限（抖音 30 字 / 小红书 20 字易踩） |
| 脚本报缺依赖 | 按提示执行 `python -m pip install openpyxl` |
| 无 KD 数据 | 脚本输出 `pending_data`，从平台后台补真实 KD 后再定词序 |

---

## 七、版本

| 项 | 值 |
|----|-----|
| 资产版本 | v0.3.0（深度改造：加脚本 + 量化阈值） |
| 规范版本 | bangwozuo 资产规范 v3.0 |
| 资产形态 | 纯提示词 + 可选离线校验脚本（零密钥） |

---

*面向：淘宝 / 抖店 / 拼多多 / 小红书店铺小卖家*
