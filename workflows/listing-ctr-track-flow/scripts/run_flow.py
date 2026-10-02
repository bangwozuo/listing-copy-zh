# -*- coding: utf-8 -*-
"""
上架 CTR 追踪 —— 端到端编排脚本。

流程 DAG（与 prompt.txt 同源）：
  每日曝光/点击 → S1 数据校验(脚本) → S2 CTR 计算与判定(脚本)
               → S3 问题定位(keyword-combination + selling-point-copy 口径)
               → S4 A/B 变体判胜(ab-copy-variant) → S5 合规预审(adlaw-compliance-precheck 词表)
               → S6 落位建议(conversion-structure-template 口径) → 跟踪表产物

量化基准（硬数字）：
  CTR 健康带 2%~5%（抖音/拼多多信息流下移为 1%~3%）；< 1% 连续 ≥ 3 天判主图/标题问题；
  单日曝光 < 1000 只记录不判定；A/B 每组 ≥ 3 天且总曝光 ≥ 1000 才下结论；
  胜出 = B 相对 A 提升 ≥ 20%；提升 < 10% 判噪声；两组曝光差 > 30% 不可比。

用法：
  python run_flow.py --input examples/input.json --outdir out
  python run_flow.py --demo

产物：
  out/CTR跟踪表.xlsx   日明细 / AB对比 / 合规扫描 / 问题诊断 / 汇总
  out/ctr_trend.png    CTR 趋势 + 健康基准带
  out/ctr_flow.json    机器可读结果
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
WF_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(WF_DIR))
sys.path.insert(0, os.path.join(REPO, "lib"))

try:
    import assettools as at
except ImportError:  # pragma: no cover
    print("[错误] 未找到 lib/assettools.py。请确认工作流位于 <repo>/workflows/<slug>/scripts/ 下，"
          "且 <repo>/lib/assettools.py 存在。", file=sys.stderr)
    sys.exit(2)

# ---------------------------------------------------------------- 基准

BAND_DEFAULT = (0.02, 0.05)          # CTR 健康带（搜索场景）
BAND_PLATFORM = {"抖音": (0.01, 0.03), "拼多多": (0.01, 0.03)}   # 信息流场景下移
MIN_DAY_IMP = 1000                    # 单日曝光低于此只记录
MIN_GROUP_IMP = 1000                  # 单组总曝光低于此不下结论
MIN_AB_DAYS = 3                       # A/B 每组最少天数
WIN_UPLIFT = 0.20                     # 胜出线
NOISE_UPLIFT = 0.10                   # 噪声线
IMP_DIFF_MAX = 0.30                   # 两组曝光差超此不可比
PROBLEM_DAYS = 3                      # CTR<1% 连续天数坐实主图/标题问题
TITLE_LIMIT = {"淘宝": "30 汉字", "天猫": "30 汉字", "拼多多": "60 字符",
               "抖音": "40 字", "Amazon": "200 字符"}

# 合规词表（与 adlaw-compliance-precheck 口径一致，简化版；语境判断由模型补）
COMPLIANCE_WORDS = [
    (r"第一|销量第一|TOP\s*1|冠军|最低价|最便宜|最好|最佳", "R", "绝对化用语·排名/最高级",
     "《广告法》第九条", "删除排名表述，改为「店铺热销单品」并注明数据口径"),
    (r"唯一|独家|首创|首款|国家级|顶级|极品", "R", "绝对化用语·唯一性/级别",
     "《广告法》第九条", "删除；有专利可附专利号"),
    (r"100\s*%|百分百|根治|永不|无任何副作用", "R", "绝对化用语·功效断言",
     "《广告法》第九条", "改为有条件表述并附证据"),
    (r"神器|爆款|网红|秒杀", "W", "营销强化词", "平台可能判夸大宣传", "保留但加限定语"),
]

# 问题定位 → 改法（与 prompt.txt 定位规则同源）
TITLE_FIX = ("核心词前置到标题前 13 字符，按「核心词+属性词+场景词」重组，"
             "长度不超过平台硬上限（淘宝 30 汉字 / Amazon 200 字符）")
IMAGE_FIX = "首图只留产品+1 个差异点，文字面积 ≤ 20%（抖音口径），换场景图或白底图做 A/B"


DEMO = {
    "listing": {
        "name": "不锈钢厨房置物架",
        "platform": "淘宝",
        "scene": "搜索",
        "title": "不锈钢架子置物架储物 收纳架 厨房落地多层",
        "core_keywords": ["厨房置物架", "不锈钢", "落地"],
        "main_image_text": "首图含促销贴片文字与店铺水印，与竞品白底图高度相似",
    },
    "days": [
        {"date": "2026-09-24", "impressions": 4230, "clicks": 45},
        {"date": "2026-09-25", "impressions": 4102, "clicks": 41},
        {"date": "2026-09-26", "impressions": 4388, "clicks": 39},
        {"date": "2026-09-27", "impressions": 4510, "clicks": 38},
        {"date": "2026-09-28", "impressions": 4402, "clicks": 41},
        {"date": "2026-09-29", "impressions": 4288, "clicks": 37},
        {"date": "2026-09-30", "impressions": 4415, "clicks": 40},
    ],
    "ab_test": {
        "groups": [
            {"name": "A 原版标题+原主图", "copy": "不锈钢架子置物架储物 收纳架 厨房落地多层",
             "daily": [
                 {"date": "2026-09-26", "impressions": 1180, "clicks": 13},
                 {"date": "2026-09-27", "impressions": 1215, "clicks": 12},
                 {"date": "2026-09-28", "impressions": 1090, "clicks": 12},
             ]},
            {"name": "B 核心词前置+场景首图", "copy": "【销量第一】厨房置物架收纳神器，304 不锈钢落地多层，实测承重 40kg",
             "daily": [
                 {"date": "2026-09-26", "impressions": 1290, "clicks": 31},
                 {"date": "2026-09-27", "impressions": 1310, "clicks": 29},
                 {"date": "2026-09-28", "impressions": 1245, "clicks": 28},
             ]},
        ]
    },
    "notes": "09-26 起主图与标题同时换版，前后各 3 天对照组；曝光分配差异 10.3%",
}


# ---------------------------------------------------------------- S1-S2 计算

def s1_validate(days):
    """数据校验：缺字段/负数 → 剔除并记入缺失清单。"""
    ok, issues = [], []
    for d in days:
        date = d.get("date")
        imp, clk = d.get("impressions"), d.get("clicks")
        if not date or imp is None or clk is None:
            issues.append(f"{date or '（缺日期）'}：字段缺失，剔除")
            continue
        if imp < 0 or clk < 0:
            issues.append(f"{date}：曝光/点击为负数，剔除")
            continue
        if imp == 0:
            issues.append(f"{date}：曝光为 0，无法计算 CTR，剔除")
            continue
        ok.append({"date": date, "impressions": int(imp), "clicks": int(clk)})
    return ok, issues


def band_of(platform):
    return BAND_PLATFORM.get(platform, BAND_DEFAULT)


def s2_ctr(days, platform):
    """日 CTR、整体 CTR、趋势斜率、达标判定。曝光 < MIN_DAY_IMP 的天只记录。"""
    band = band_of(platform)
    lo, hi = band[0] * 100, band[1] * 100
    rows = []
    valid = []
    for d in days:
        ctr = d["clicks"] / d["impressions"] * 100
        enough = d["impressions"] >= MIN_DAY_IMP
        if enough:
            valid.append(ctr)
        rows.append({
            "日期": d["date"], "曝光": d["impressions"], "点击": d["clicks"],
            "CTR": f"{ctr:.2f}%",
            "曝光达标": "是" if enough else f"否（< {MIN_DAY_IMP}，只记录）",
        })
    overall = sum(d["clicks"] for d in days) / max(sum(d["impressions"] for d in days), 1) * 100
    slope = at.trend_slope(valid) if len(valid) >= 3 else None
    # 连续 < 1% 坐实主图/标题问题（只在曝光达标的天上判）
    flags = [c < 1.0 for c in valid]
    best_run, runs = at.consecutive_runs(flags)
    return rows, valid, overall, slope, best_run, runs, band


def judge_overall(overall, band, best_run, n_valid):
    lo, hi = band[0] * 100, band[1] * 100
    if n_valid < 3:
        return "数据不足（曝光达标天 < 3），只记录不下结论"
    if overall >= lo and overall <= hi:
        return f"健康（{lo:.0f}%~{hi:.0f}% 带内）"
    if overall >= 1.0:
        return f"需关注（低于 {lo:.0f}% 健康下限，未到 1% 问题线）"
    if best_run >= PROBLEM_DAYS:
        return f"主图/标题问题（CTR < 1% 连续 {best_run} 天，≥ {PROBLEM_DAYS} 天坐实）"
    return "需关注（CTR < 1% 但连续天数不足，继续观察）"


# ---------------------------------------------------------------- S3 问题定位

def s3_diagnose(listing, overall, best_run):
    """CTR < 1% 时的证据式定位；证据不足列待排查。"""
    title = str(listing.get("title", ""))
    kws = listing.get("core_keywords") or []
    image_text = str(listing.get("main_image_text", ""))
    rows = []
    # 标题证据（keyword-combination 口径）
    ev = []
    for k in kws:
        if k not in title:
            ev.append(f"核心词「{k}」未出现在标题")
        elif title.find(k) > 12:
            ev.append(f"核心词「{k}」位置在第 {title.find(k) + 1} 字符（> 13 字符，未前置）")
    if not kws and title:
        ev.append("未提供核心词清单，无法做覆盖校验（待补 keywords）")
    if ev:
        rows.append({"定位": "标题问题", "证据": "；".join(ev), "改法": TITLE_FIX})
    # 主图证据
    ev2 = []
    for w, name in (("贴片", "促销贴片文字"), ("水印", "水印"), ("二维码", "二维码"),
                    ("边框", "文字边框")):
        if w in image_text:
            ev2.append(f"主图含{name}（牛皮癣风险）")
    if "相似" in image_text or "同质" in image_text:
        ev2.append("主图与竞品同质化（无差异点）")
    if ev2:
        rows.append({"定位": "主图问题", "证据": "；".join(ev2), "改法": IMAGE_FIX})
    if not rows:
        if overall < 1.0 or best_run >= PROBLEM_DAYS:
            rows.append({"定位": "待排查（证据不足）",
                         "证据": "CTR 低于问题线，但未提供标题/主图描述，无法定位",
                         "改法": f"先补 core_keywords 与 main_image_description；"
                                 f"标题按「{TITLE_FIX[:20]}…」方向自查，主图对照 IMAGE_FIX 自查"})
    return rows


# ---------------------------------------------------------------- S4 A/B 判胜

def s4_abtest(ab):
    groups = (ab or {}).get("groups", [])
    stats = []
    for g in groups:
        daily, issues = s1_validate(g.get("daily", []))
        n = len(daily)
        imp = sum(d["impressions"] for d in daily)
        clk = sum(d["clicks"] for d in daily)
        ctr = clk / imp * 100 if imp else None
        stats.append({"group": g, "name": g.get("name", f"组{len(stats) + 1}"),
                      "days": n, "imp": imp, "clk": clk, "ctr": ctr, "daily": daily})
    rows = []
    base = stats[0] if stats else None
    for i, s in enumerate(stats):
        if s["days"] < MIN_AB_DAYS:
            verdict = f"测试中（{s['days']}/{MIN_AB_DAYS} 天，还需 {MIN_AB_DAYS - s['days']} 天）"
        elif s["imp"] < MIN_GROUP_IMP:
            verdict = f"曝光不足（总曝光 {s['imp']:,} < {MIN_GROUP_IMP:,}），不下结论"
        elif i == 0:
            verdict = "对照组（A）"
        else:
            if base["imp"] and abs(s["imp"] - base["imp"]) / base["imp"] > IMP_DIFF_MAX:
                verdict = "与 A 不可比（曝光差 > 30%，先修流量分配）"
            else:
                up = s["ctr"] / base["ctr"] - 1 if (s["ctr"] and base["ctr"]) else None
                if up is None:
                    verdict = "数据不足"
                elif up >= WIN_UPLIFT:
                    verdict = f"胜出（+{up:.0%} ≥ {WIN_UPLIFT:.0%}，样本达标）"
                elif up < NOISE_UPLIFT:
                    verdict = f"噪声（+{up:.0%} < {NOISE_UPLIFT:.0%}，不换文案）"
                else:
                    verdict = f"不确定（+{up:.0%}，延长测试，不中途换文案）"
        rows.append({"组别": s["name"], "天数": s["days"], "总曝光": s["imp"],
                     "CTR": f"{s['ctr']:.2f}%" if s["ctr"] is not None else "—",
                     "判定": verdict, "_uplift": None})
    # 相对 A 列
    if base and base["ctr"]:
        for r, s in zip(rows, stats):
            if s is not base and s["ctr"]:
                r["相对A"] = f"{s['ctr'] / base['ctr'] - 1:+.0%}"
            else:
                r["相对A"] = "—"
    else:
        for r in rows:
            r["相对A"] = "—"
    for r in rows:
        r.pop("_uplift", None)
    winner = None
    for r, s in zip(rows, stats):
        if "胜出" in r["判定"]:
            winner = s
    return rows, winner, stats


# ---------------------------------------------------------------- S5 合规

def s5_compliance(groups, stats, winner):
    """对各组文案跑词表扫描（语境判断由模型按 adlaw-compliance-precheck 补）。"""
    import re
    rows = []
    targets = [(winner["name"], winner["group"].get("copy", ""))] if winner else []
    if not targets:
        targets = [(s["name"], s["group"].get("copy", "")) for s in stats]
    for name, copy in targets:
        if not copy:
            rows.append({"组别": name, "级别": "—", "原文片段": "（未提供文案）",
                         "命中规则": "—", "改法": "补充文案后重扫"})
            continue
        hit = False
        for pat, lvl, rule, basis, fix in COMPLIANCE_WORDS:
            for m in re.finditer(pat, copy):
                rows.append({"组别": name, "级别": "🔴 红线" if lvl == "R" else "🟡 警告",
                             "原文片段": m.group(0), "命中规则": f"{rule}（{basis}）", "改法": fix})
                hit = True
        if not hit:
            rows.append({"组别": name, "级别": "✅ 通过", "原文片段": "—",
                         "命中规则": "词表无命中", "改法": "模型按 prompt 做语境复核后可上架"})
    return rows


# ---------------------------------------------------------------- 主流程

def build(payload, outdir):
    listing = payload.get("listing", {}) or {}
    platform = listing.get("platform", "通用")
    scene = listing.get("scene", "搜索")
    name = listing.get("name", "未命名商品")

    # S1
    days, issues = s1_validate(payload.get("days", []))
    # S2
    ctr_rows, valid_ctrs, overall, slope, best_run, runs, band = s2_ctr(days, platform)
    verdict = judge_overall(overall, band, best_run, len(valid_ctrs))
    problem = ("主图/标题问题" in verdict) or ("待排查" in "") and False
    problem = verdict.startswith("主图/标题问题")
    # S3
    diag_rows = s3_diagnose(listing, overall, best_run) if problem else \
        [{"定位": "无需定位（CTR 在健康带或观察带内）", "证据": f"整体 CTR {overall:.2f}%", "改法": "维持，继续按日监控"}]
    # S4
    ab_rows, winner, stats = s4_abtest(payload.get("ab_test"))
    # S5
    comp_rows = s5_compliance(payload.get("ab_test"), stats, winner)
    blocked = any(r["级别"].startswith("🔴") for r in comp_rows)

    summary = {
        "商品": name, "平台": platform, "场景": scene,
        "记录天数": len(days), "有效判定天": len(valid_ctrs),
        "剔除问题天": issues or "无",
        "整体CTR": f"{overall:.2f}%", "健康带": f"{band[0]:.0%}~{band[1]:.0%}" + ("（信息流下移）" if platform in BAND_PLATFORM else "（搜索基准）"),
        "趋势斜率": f"{slope:+.2f} pct/天" if slope is not None else "有效天不足，未算趋势",
        "判定": verdict,
        "AB胜出组": winner["name"] if winner else "无（测试中/未判出）",
        "合规拦截": "是（胜出变体含红线词，须改写后重测）" if blocked else "否",
        "落位建议": ("首屏文字 ≤ 120 字；胜出文案上主图区与标题位，详情页首模块做卖点图文，"
                     "对比表只对比本店 SKU（conversion-structure-template 口径）"),
        "基准": {"CTR健康带": "2%~5%（信息流 1%~3%）", "问题线": "CTR<1% 连续 ≥ 3 天",
                 "A/B样本": "每组 ≥ 3 天 且 总曝光 ≥ 1000",
                 "胜出线": "+20%", "噪声线": "+10%", "不可比": "曝光差 > 30%"},
        "编排说明": ("S1 校验 → S2 CTR 判定(脚本) → S3 定位(keyword-combination/selling-point-copy 口径) "
                     "→ S4 判胜(ab-copy-variant) → S5 合规(adlaw-compliance-precheck 词表) → "
                     "S6 落位(conversion-structure-template 口径)；数值以脚本输出为准，不要自己算"),
    }

    at.ensure_outdir(outdir)

    chart = None
    if valid_ctrs:
        valid_days = [r["日期"] for r in ctr_rows if r["曝光达标"] == "是"]
        nan = float("nan")
        series = {"当日 CTR": valid_ctrs,
                  f"健康下限 {band[0]:.0%}": [band[0] * 100] * len(valid_days),
                  f"健康上限 {band[1]:.0%}": [band[1] * 100] * len(valid_days)}
        # 叠加 A/B 各组日 CTR（按日期对齐，未测试的日期断开）
        for s in stats:
            m = {d["date"]: d["clicks"] / d["impressions"] * 100 for d in s["daily"]}
            if m:
                series[s["name"]] = [m.get(d, nan) for d in valid_days]
        chart = at.line_chart(
            os.path.join(outdir, "ctr_trend.png"),
            [d[-5:] for d in valid_days], series,
            title=f"{name} CTR 趋势（{platform}·{scene}）", ylabel="CTR (%)")

    xlsx = at.write_excel(
        os.path.join(outdir, "CTR跟踪表.xlsx"),
        {
            "日明细": ctr_rows or [{"日期": "（无合格数据）"}],
            "AB对比": ab_rows or [{"组别": "（未提供 A/B 数据）"}],
            "合规扫描": comp_rows or [{"组别": "（未提供文案）"}],
            "问题诊断": diag_rows,
            "汇总": [{"项": k, "内容": str(v)} for k, v in summary.items()],
        },
        highlights={"AB对比": {"判定": "contains:胜出"},
                    "合规扫描": {"级别": "contains:红线"},
                    "日明细": {"曝光达标": "contains:否"}},
        widths={"合规扫描": {"改法": 42}, "问题诊断": {"证据": 40, "改法": 44},
                "AB对比": {"判定": 34}},
    )

    js = at.write_json(
        {"summary": summary, "daily": ctr_rows, "abtest": ab_rows,
         "compliance": comp_rows, "diagnosis": diag_rows,
         "generated_at": at.stamp(),
         "note": "脚本计算与判定结果；改法文案与语境合规判断由模型按 prompt.txt 补充"},
        os.path.join(outdir, "ctr_flow.json"))
    files = [f for f in (xlsx, chart, js) if f]

    conclusion = (f"整体 CTR {overall:.2f}%（基准 {band[0]:.0%}~{band[1]:.0%}）→ {verdict}；"
                  f"A/B 判定：{ab_rows[1]['判定'] if len(ab_rows) > 1 else '未提供对照组'}"
                  + ("；胜出变体含红线词须先改写" if blocked else ""))
    return {"files": files, "summary": summary, "conclusion": conclusion,
            "daily_rows": ctr_rows, "ab_rows": ab_rows, "diag_rows": diag_rows,
            "comp_rows": comp_rows}


def main():
    ap = argparse.ArgumentParser(description="上架 CTR 追踪工作流")
    ap.add_argument("--input", help="输入 JSON（listing/days/ab_test）")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    if a.demo:
        payload = DEMO
    elif a.input:
        payload = at.read_json(a.input)
    else:
        ap.error("需要 --input / --demo 之一")

    r = build(payload, a.outdir)
    print(r["conclusion"])
    for f in r["files"]:
        print(" 产物:", f)
    at.emit(r)


if __name__ == "__main__":
    main()
