# 关键词挖掘与标题组合 · 安装使用手册

> 两条路径：**纯提示词编排**（最快）与**端到端脚本**（产出流程执行报告）。
> 全程 **不需要 API Key**。

---

## 一、前置条件

| 项 | 要求 |
|----|------|
| AI 工具 | 任一支持自定义提示词/角色设定的工具（Coze / WorkBuddy / Dify / Claude / ChatGPT / 通义 / Kimi） |
| 算力 | 你自己的账号订阅，本资产不代付任何模型费用 |
| 数据 | `platform` + `product_info`（商品信息） |
| 脚本路径（可选） | Python 3.10+，依赖 `openpyxl`（经共享库 `lib/assettools.py`；缺失时会打印修复命令） |
| 同仓依赖 | `skills/keyword-combination/`、`skills/adlaw-compliance-precheck/` 必须存在 |

---

## 二、安装

### 方式一 · 导入提示词

| 平台 | 导入方式 |
|------|---------|
| **Coze / 扣子** | 新建 Bot → 人设与回复逻辑 → 粘贴 `prompt.txt` |
| **WorkBuddy** | 新建 Skill → 指令区填入 `prompt.txt` |
| **Dify** | 新建 Workflow → 按 DAG 添加节点，各节点填入对应原子技能的 `prompt.txt` |
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
| `platform` | ✅ | 淘宝 / 天猫 / 抖音 / 拼多多 / 小红书 / Amazon |
| `product_info` | ✅ | 品名、材质、规格、卖点、场景 |
| `core_word` | ⬜ | 核心词；缺省取 `keywords` 中「核心词」层级 |
| `keywords` | ⬜ | 关键词及层级 |
| `candidate_titles` | ⬜ | 待校验的标题候选 |

> 完整字段定义见同目录 `schema.json`。

---

## 四、使用方法

```text
1. 把 prompt.txt 全文作为系统提示词（或按 DAG 在平台上串两个原子技能）
2. 提供 platform + product_info
3. 模型按 4 步执行；闸门出红线时回环重写（≤2 次）
4. 需要端到端产物时跑 scripts/run_flow.py
5. 人工审核后使用
```

---

## 五、看懂脚本产物

| 文件 | 内容 |
|---|---|
| `out/流程执行报告.xlsx` | 步骤明细 / 最终交付 / 汇总 |
| `out/flow_result.json` | 机器可读流程结果（含 `aborted` 标记） |
| `out/step2_keyword/` | 第 2 步原子技能产物（Excel + JSON） |
| `out/step3_adlaw/` | 第 3 步合规扫描产物（Excel + JSON） |

---

## 六、常见问题

| 问题 | 处理 |
|------|------|
| 流程中止并报缺字段 | 补齐 `platform` / `product_info` 后重跑 |
| 反复回环 | 素材本身含违禁表述，先改素材再重跑 |
| 报 FileNotFoundError | 检查同仓 `skills/` 下原子技能是否齐全 |
| 脚本报缺依赖 | `python -m pip install openpyxl` |

---

## 七、版本

| 项 | 值 |
|----|-----|
| 资产版本 | v0.3.0（深度改造：真 DAG + 闸门 + 编排脚本） |
| 规范版本 | bangwozuo 资产规范 v3.0 |
| 资产形态 | 纯提示词 + 可选离线编排脚本（零密钥） |

---

*面向：淘宝 / 抖店 / 拼多多 / 小红书店铺小卖家*
