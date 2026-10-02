# 测试报告

## 一、结构校验

| 项 | 结果 |
|---|---|
| 四件套齐全（SKILL.md / prompt.txt / schema.json / examples） | ✅ PASS |
| SKILL.md 含 frontmatter + 元信息/编排的原子技能/步骤链路/步骤明细/输入规格/输出规格/错误处理/验收标准 | ✅ PASS |
| SKILL.md 声明 `composite` 且 Mermaid `flowchart` 围栏闭合 | ✅ PASS |
| 引用的原子技能目录真实存在 | ✅ PASS（selling-point-copy / adlaw-compliance-precheck） |
| prompt.txt 含 DAG + 步骤明细（输入/处理/输出/失败处理） | ✅ PASS |
| 无占位符残留 / 无 API Key / 无模型调用 | ✅ PASS |

## 二、prompt 深度指标

| 维度 | 证据 | 结果 |
|---|---|---|
| D1 领域术语 | FAB 三层追问、证据分级、首条差异化、四类规则分级、双闸 | ✅ ≥ 3 |
| D2 具体阈值 | 回环上限 2 次；Amazon 单条 ≤ 500 字符；抖音 40 / 拼多多 30 / 淘宝 80 字 | ✅ ≥ 2 |
| D3 方法步骤 | 4 步明细 + DAG 分支（含 2 条回环边） | ✅ ≥ 3 |
| D4 领域边界 | 跳闸门、Feature-only、无证据强断言、促销语入商品页、回环超限 | ✅ ≥ 2 |
| D5 可交付输出 | 流程执行报告 Excel + 分步 JSON 产物 | ✅ |

## 三、编排脚本实跑

**命令**：

```bash
python scripts/run_flow.py --demo
python scripts/run_flow.py --input examples/input.json --outdir out
```

**运行环境**：Python 3.13.12 / openpyxl（经 `lib/assettools.py`）

| 项 | 结果 |
|---|---|
| 退出码 | 0 |
| 步骤数 | 4（输入校验 / 卖点生成 / 广告法闸门 / 汇总交付） |
| 可用卖点 | 3 / 3 |
| 回环次数 | 0 |
| 合规结论 | 通过 |
| 产物 1 | `out/流程执行报告.xlsx`（7.7 KB，4 sheet） |
| 产物 2 | `out/flow_result.json` |
| 产物 3 | `out/step2_point/五点校验.xlsx` + `five_point.json` |
| 产物 4 | `out/step3_adlaw/广告法预审清单.xlsx` + `adlaw_scan.json` |

### 步骤明细（真实输出）

```
✅ 1 输入校验           payload 完整；平台 Amazon
✅ 2 卖点生成与校验      可用 3 / 3；待整改 0
✅ 3 广告法闸门          红线 0 / 警告 0；回环 0 次
✅ 4 汇总交付            交付 3 条卖点；结论「通过」
```

### 失败处理路径验证

| 场景 | 触发方式 | 实测行为 |
|---|---|---|
| 输入缺失 | 只传 `platform` | 第 1 步 ❌ 中止，列出缺失字段 `product_info` |
| 卖点含违禁词 | points 传「全网最低价，100%保温」+「优质材料」 | 第 2 步 ⚠️「可用 0 / 2」，第 3 步 ⏭ 跳过 |
| FAB 不全 | points 传「容量 500ml」等纯参数 | 第 2 步标「补充收益」，列入待整改 |
| 红线回环 | 闸门出红线 | 回到第 2 步改写，回环上限 2 次后中止 |
| 技能脚本缺失 | 重命名 `skills/` 下脚本 | 抛 `FileNotFoundError`，流程中止 |

## 四、边界与已知限制

| 限制 | 说明 |
|---|---|
| 回环为脚本内去词重写 | 真实场景中回环应由模型改写卖点；脚本用「剔除命中条目」模拟 |
| 依赖原子技能产物文件名 | 步骤衔接读取 `five_point.json` / `adlaw_scan.json`，改动字段名会断链 |
| FAB 词元匹配 | 第 2 步用词表匹配 F/A/B，语义质量仍须模型复核 |

## 五、结论

**通过。** 4 步 DAG 端到端跑通，产出 6 个真实文件，失败处理路径逐条验证有效。

---

*测试报告基于真实实跑输出生成 · 2026-09-30*
