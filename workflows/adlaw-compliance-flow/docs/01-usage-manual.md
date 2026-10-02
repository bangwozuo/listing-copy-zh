# 广告法合规预审 · 安装使用手册

> 两条路径：**纯提示词编排**（最快）与**端到端脚本**（两遍扫描，产出流程执行报告）。
> 全程 **不需要 API Key**。

---

## 一、前置条件

| 项 | 要求 |
|----|------|
| AI 工具 | 任一支持自定义提示词/角色设定的工具（Coze / WorkBuddy / Dify / Claude / ChatGPT / 通义 / Kimi） |
| 算力 | 你自己的账号订阅，本资产不代付任何模型费用 |
| 数据 | `text`（待检文案）；有整改稿请附 `revised_text` |
| 脚本路径（可选） | Python 3.10+，依赖 `openpyxl`（经共享库 `lib/assettools.py`；缺失时会打印修复命令） |
| 同仓依赖 | `skills/adlaw-compliance-precheck/` 必须存在 |

---

## 二、安装

### 方式一 · 导入提示词

| 平台 | 导入方式 |
|------|---------|
| **Coze / 扣子** | 新建 Bot → 人设与回复逻辑 → 粘贴 `prompt.txt` |
| **WorkBuddy** | 新建 Skill → 指令区填入 `prompt.txt` |
| **Dify** | 新建 Workflow → 按 DAG 添加两个节点（初检 / 复扫），各填入原子技能 `prompt.txt` |
| **Claude** | 新建 Project → Instructions → 粘贴 `prompt.txt` |
| **ChatGPT** | 新建 GPT → Instructions → 粘贴 `prompt.txt` |
| **通义 / 文心 / Kimi** | 直接粘贴到系统提示词 / 角色设定 |

### 方式二 · 运行编排脚本

```bash
python scripts/run_flow.py --demo
python scripts/run_flow.py --input examples/input.json --outdir out
```

---

## 三、输入准备

| 输入项 | 必填 | 说明 |
|--------|------|------|
| `text` | ✅ | 待检文案：标题 + 副标题 + 卖点 + 详情页 + 图上文字 |
| `platform` | ⬜ | 淘宝 / 天猫 / 抖音 / 拼多多 / 小红书 / 通用 |
| `category` | ⬜ | 化妆品 / 食品 / 保健品 / 医疗器械 / 母婴 / 教育 / 金融 |
| `revised_text` | ⬜ | 整改后的文案（提供则触发复扫） |
| `rules` | ⬜ | 用户自定义词表或平台补充规则 |

> 完整字段定义见同目录 `schema.json`。

---

## 四、使用方法

```text
1. 把 prompt.txt 全文作为系统提示词（或按 DAG 在平台上串初检 → 复扫两节点）
2. 传 text → 得到初检违规清单与替换写法
3. 按清单改完文案，把整改稿作为 revised_text 再传 → 得到复扫结论
4. 复扫仍有红线则继续改（复扫上限 2 次）
5. 人工审核后使用
```

---

## 五、看懂脚本产物

| 文件 | 内容 |
|---|---|
| `out/流程执行报告.xlsx` | 步骤明细 / 违规清单 / 整改对比 / 整体建议 / 汇总 |
| `out/flow_result.json` | 机器可读结果（含整改前后全文） |
| `out/step2_first/` | 初检产物（Excel + JSON） |
| `out/step3_review/` | 复扫产物（Excel + JSON） |

---

## 六、常见问题

| 问题 | 处理 |
|------|------|
| 初检红线很多 | 先删绝对化用语与站外导流（这两类处罚概率最高） |
| 复扫还有残留 | 按复扫清单继续改；连续 2 次仍有红线建议换卖点方向 |
| 没整改稿 | 流程如实交付「待整改」，不会假称「通过」 |
| 脚本报缺依赖 | `python -m pip install openpyxl` |

---

## 七、版本

| 项 | 值 |
|----|-----|
| 资产版本 | v0.3.0（深度改造：两遍扫描闭环 + 编排脚本） |
| 规范版本 | bangwozuo 资产规范 v3.0 |
| 资产形态 | 纯提示词 + 可选离线编排脚本（零密钥） |

---

*面向：淘宝 / 抖店 / 拼多多 / 小红书店铺小卖家*
