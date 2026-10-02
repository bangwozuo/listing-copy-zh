# 测试报告

## 一、结构校验

| 项 | 结果 |
|---|---|
| 四件套齐全（SKILL.md / prompt.txt / schema.json / examples） | ✅ PASS |
| SKILL.md 含 frontmatter + 元信息/编排的原子技能/步骤链路/步骤明细/输入规格/输出规格/错误处理/验收标准 | ✅ PASS |
| SKILL.md 声明 `composite` 且 Mermaid `flowchart` 围栏闭合 | ✅ PASS |
| 引用的原子技能目录真实存在 | ✅ PASS（keyword-combination / adlaw-compliance-precheck） |
| prompt.txt 含 DAG + 步骤明细（输入/处理/输出/失败处理） | ✅ PASS |
| 无占位符残留 / 无 API Key / 无模型调用 | ✅ PASS |

## 二、prompt 深度指标

| 维度 | 证据 | 结果 |
|---|---|---|
| D1 领域术语 | 质量闸门、回环、核心词前置、五项校验、四类规则分级 | ✅ ≥ 3 |
| D2 具体阈值 | 回环上限 2 次；平台字数（60/30/20/200）；核心词位次 ≤ 10 | ✅ ≥ 2 |
| D3 方法步骤 | 4 步明细 + DAG 分支（含 2 条回环边） | ✅ ≥ 3 |
| D4 领域边界 | 跳闸门、回环超限、编造 KD、字段名改动导致下游断裂 | ✅ ≥ 2 |
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
| 步骤数 | 4（输入校验 / 标题组合 / 广告法闸门 / 汇总交付） |
| 可用标题数 | 3 |
| 回环次数 | 0 |
| 合规结论 | 通过 |
| 产物 1 | `out/流程执行报告.xlsx`（6.8 KB，3 sheet） |
| 产物 2 | `out/flow_result.json`（1.3 KB） |
| 产物 3 | `out/step2_keyword/标题关键词校验.xlsx` + `keyword_check.json` |
| 产物 4 | `out/step3_adlaw/广告法预审清单.xlsx` + `adlaw_scan.json` |

### 步骤明细（真实输出）

```
✅ 1 输入校验           payload 完整；平台 淘宝
✅ 2 标题组合与校验      可用 3 个；推荐「保温杯 304不锈钢 500ml 办公室便携带茶隔」
✅ 3 广告法闸门          红线 0 / 警告 0；回环 0 次
✅ 4 汇总交付            交付 3 个标题；结论「通过」
```

### 失败处理路径验证

| 场景 | 触发方式 | 实测行为 |
|---|---|---|
| 输入缺失 | 只传 `platform` | 第 1 步 ❌ 中止，列出缺失字段 `product_info` |
| 全候选不合格 | 候选全含违禁词 | 第 2 步 ⚠️，第 3 步 ⏭ 跳过，交付「需修改素材」 |
| 红线回环 | 闸门出红线 | 回到第 2 步重写，回环上限 2 次后中止 |
| 技能脚本缺失 | 重命名 `skills/` 下脚本 | 抛 `FileNotFoundError`，流程中止 |

## 四、边界与已知限制

| 限制 | 说明 |
|---|---|
| 回环为脚本内去词重写 | 真实场景中回环应由模型重写候选；脚本用「剔除命中候选」模拟回环 |
| 依赖原子技能产物文件名 | 步骤衔接读取 `keyword_check.json` / `adlaw_scan.json`，改动字段名会断链 |
| 平台规则时效 | 字数上限与审核规则以官方最新公示为准 |

## 五、结论

**通过。** 4 步 DAG 端到端跑通，产出 6 个真实文件（2 个汇总 + 4 个分步），
失败处理路径逐条验证有效。

---

*测试报告基于真实实跑输出生成 · 2026-09-30*
