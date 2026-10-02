# 广告法合规预审 · 安装使用手册

> 本资产有两条使用路径：**纯提示词**（最快）与**带脚本**（产出 Excel 违规清单）。
> 全程 **不需要 API Key**。

---

## 一、前置条件

| 项 | 要求 |
|----|------|
| AI 工具 | 任一支持自定义提示词/角色设定的工具（Coze / WorkBuddy / Dify / Claude / ChatGPT / 通义 / Kimi） |
| 算力 | 你自己的账号订阅，本资产不代付任何模型费用 |
| 数据 | 待检文案（标题 + 卖点 + 详情页 + 图上文字） |
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

### 方式二 · 运行扫描脚本

```bash
python scripts/adlaw_scan.py --demo
python scripts/adlaw_scan.py --input examples/input.json --outdir out
python scripts/adlaw_scan.py --text "全网最低价" --platform 淘宝 --category 化妆品
```

---

## 三、输入准备

| 输入项 | 必填 | 说明 |
|--------|------|------|
| `text` | ✅ | 待检文案：标题 + 副标题 + 卖点 + 详情页 + 图上文字 |
| `platform` | ⬜ | 淘宝 / 天猫 / 抖音 / 拼多多 / 小红书 / 通用 |
| `category` | ⬜ | 化妆品 / 食品 / 保健品 / 医疗器械 / 母婴 / 教育 / 金融 |
| `rules` | ⬜ | 用户自定义词表或平台补充规则 |

> 完整字段定义见同目录 `schema.json`。

---

## 四、使用方法

```text
1. 把 prompt.txt 全文作为系统提示词
2. 按「输入准备」把数据发给 AI → 得到分级违规清单 + 替换写法
3. 需要词表精确证据时，跑 scripts/adlaw_scan.py
4. 复核后整改；对外发布保留人工确认
```

---

## 五、看懂脚本产物

| 文件 | 内容 |
|---|---|
| `out/广告法预审清单.xlsx` | Sheet1 违规清单（红线行标红）/ Sheet2 需补材料 / Sheet3 整体建议 / Sheet4 汇总 |
| `out/adlaw_scan.json` | 机器可读结果；含 `violations` / `need_material` / `suggestions` |

---

## 六、常见问题

| 问题 | 处理 |
|------|------|
| 输出太泛 | 挂载知识库，填入你的类目与平台规则 |
| 结果与平台判定不一致 | 平台规则每月可能更新，以官方公示为准 |
| 脚本报缺依赖 | `python -m pip install openpyxl` |
| 想扫图上文字 | 先 OCR 得到文字，再作为 `text` 一部分传入 |

---

## 七、版本

| 项 | 值 |
|----|-----|
| 资产版本 | v0.3.0（深度改造：四类规则 + 脚本 + 假阳性拦截） |
| 规范版本 | bangwozuo 资产规范 v3.0 |
| 资产形态 | 纯提示词 + 可选离线扫描脚本（零密钥） |

---

*面向：淘宝 / 抖店 / 拼多多 / 小红书店铺小卖家*
