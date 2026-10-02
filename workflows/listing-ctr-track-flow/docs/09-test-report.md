# 测试报告

## 一、结构校验

| 项 | 结果 |
|---|---|
| 资产四件套（SKILL.md / prompt.txt / schema.json / examples） | ✅ PASS |
| SKILL.md 段落齐全（元信息 / 能力描述 / 输入规格 / 输出规格 / 使用步骤 / 边界 / 调用示例 / 所属工作流 / 合规声明 + frontmatter + ID 行） | ✅ PASS |
| prompt.txt 长度 | ✅ PASS — **3,921 字**（T3 门槛 1,200 字） |
| DAG 节点 = 本仓真实技能 slug（keyword-combination / selling-point-copy / ab-copy-variant / adlaw-compliance-precheck / conversion-structure-template 均存在于 `../../skills/`） | ✅ PASS |
| schema.json 含 `scripts` 声明与 `artifacts`；skill_refs 与各原子技能 ID 一致 | ✅ PASS |
| examples/input.json 无占位符（真实曝光/点击 + A/B 分组数据） | ✅ PASS |

## 二、脚本实跑验证（verify_deep V5/V6 口径）

**环境**：Windows 11 · Python 3（`C:\Users\nsxzy\.workbuddy\binaries\python\envs\default\Scripts\python.exe`）

| 命令 | 退出码 | 产物 |
|---|---|---|
| `python scripts/run_flow.py --demo` | 0 | out/CTR跟踪表.xlsx（10.1 KB）、out/ctr_trend.png（41.8 KB）、out/ctr_flow.json（4.2 KB） |
| `python scripts/run_flow.py --input examples/input.json --outdir out` | 0 | 同上三件产物 |

依赖走 `lib/assettools.py` 的 `need()`：缺依赖打印修复命令并退出码 2，不静默失败。

## 三、数值正确性核对（脚本输出 vs 人工核算）

**输入**：`examples/input.json`（7 天明细 + A/B 各 3 天）

| 指标 | 公式 | 输入数据 | 脚本输出 | 人工核算 | 一致 |
|---|---|---|---|---|---|
| 整体 CTR | Σ点击 ÷ Σ曝光 | 281 ÷ 30,335 | 0.93% | 0.9263% | ✅ |
| 09-24 日 CTR | 点击 ÷ 曝光 | 45 ÷ 4,230 | 1.06% | 1.0638% | ✅ |
| A 组 CTR | Σ点击 ÷ Σ曝光 | 37 ÷ 3,485 | 1.06% | 1.0617% | ✅ |
| B 组 CTR | Σ点击 ÷ 曝光 | 88 ÷ 3,845 | 2.29% | 2.2887% | ✅ |
| B 相对 A | B ÷ A − 1 | 2.2887 ÷ 1.0617 − 1 | +116% | +115.6% | ✅ |
| 趋势斜率 | 最小二乘（7 天日 CTR） | — | -0.03 pct/天 | 缓慢阴跌方向一致 | ✅ |
| 连续 <1% 天数 | 连续 True 游程 | 09-25 ~ 09-30 | 6 天 | 6 天 | ✅ |

## 四、量化验收标准逐条验证（prompt 中的硬数字在脚本中生效）

| 验收标准 | 脚本行为 | 实跑证据 |
|---|---|---|
| CTR 基准 2%~5% | `BAND_DEFAULT=(0.02,0.05)`；抖音/拼多多 `(0.01,0.03)` 且 summary 显式注明 | 判定输出「主图/标题问题」✅ |
| CTR < 1% 判主图/标题问题并给改法 | `best_run >= 3` 触发 `s3_diagnose()`，改法给到具体动作 | 输出标题+主图双定位与改法 ✅ |
| A/B 至少 3 天样本 | `days < 3 → 测试中（还需 N 天）` | 逻辑内建 ✅ |
| 单组曝光 ≥ 1000 再下结论 | `imp < 1000 → 曝光不足不下结论`；单日 < 1000 只记录 | 逻辑内建 ✅ |
| 胜出线 +20% / 噪声线 +10% | `WIN_UPLIFT=0.20 / NOISE_UPLIFT=0.10` | +116% 判胜出 ✅ |
| 曝光差 > 30% 不可比 | `IMP_DIFF_MAX=0.30` | 逻辑内建（demo 10.3% 可比）✅ |
| 红线词拦截上架 | 胜出变体词表扫描，「销量第一」命中 🔴 | 合规拦截=是 ✅ |

## 五、深度五维自检（DEEP_STANDARD 第二节）

| 维度 | 证据 | 结果 |
|---|---|---|
| D1 领域术语 | CTR / 核心词前置 / 牛皮癣 / Jaccard 同质化 / 信息流健康带 / 曝光分配 / 游程判定 | ✅ ≥ 3 命中 |
| D2 具体阈值 | 2%~5%、1% 问题线、3 天、1000 曝光、+20%/+10%、30% 不可比、13 字符前置、首屏 120 字 | ✅ ≥ 2 处 |
| D3 方法/算法 | 六步 DAG；`s2_ctr()` 游程判定；`s4_abtest()` 五分支判胜树；`s3_diagnose()` 证据规则 | ✅ ≥ 3 步 |
| D4 真实边界 | 小曝光噪声 ±50%、A/B 日间波动 ±10%、曝光差不代表人群差异、多变量同改无法归因 | ✅ ≥ 2 条领域专属 |
| D5 输出可交付 | Excel 五 sheet（条件格式标红）+ PNG 趋势图（健康带+A/B 曲线）+ JSON | ✅ 真实文件 |

## 六、边界与依赖

- 脚本依赖：openpyxl / matplotlib（经 `assettools.need()` 检查）
- 无模型调用、无 API Key、不访问网络
- 合规词表为 `adlaw-compliance-precheck` 的简化同源版；语境判断与改法文案由模型按 prompt.txt 补充
- 变体生成（6 角度、Jaccard 剔重）由 `ab-copy-variant` 技能完成，本脚本做判胜与拦截

## 七、结论

本工作流四件套 + 编排脚本齐全，prompt 达标（3,921 字，DAG 节点全部为本仓真实 slug）；
`run_flow.py` 在 `--demo` 与 `--input` 两模式下实跑通过（退出码 0），产出 Excel + PNG + JSON 三类真实文件；
7 项数值脚本输出与人工核算逐项一致；
7 条量化验收标准全部内建于代码（基准带、问题线、样本纪律、胜出/噪声线、不可比、红线拦截）。

---

*测试报告基于 2026-09-30 的真实实跑结果。*
