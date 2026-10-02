# -*- coding: utf-8 -*-
"""详情页转化文案 —— 工作流编排脚本（T3）。

串联本仓三个真实原子技能：
  2 selling-point-copy            五点卖点校验（FAB / 字数 / 证据 / 违禁词）
  3 conversion-structure-template 详情页结构校验（模块数 / A+ 必备 / 首屏字数 / 对比表红线）
  4 adlaw-compliance-precheck     广告法终审（四类规则分级扫描）

用法：
  python run_flow.py --input input.json --outdir out
  python run_flow.py --demo

产物：
  out/流程执行报告.xlsx   步骤明细 / 五点校验 / 模块结构 / 违规清单 / 汇总
  out/flow_result.json    机器可读结果
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FLOW_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(FLOW_DIR))
sys.path.insert(0, os.path.join(REPO, "lib"))

try:
    import assettools as at
except ImportError:  # pragma: no cover
    print("[错误] 未找到 lib/assettools.py：请确认工作流位于 <repo>/workflows/<slug>/scripts/ 下。",
          file=sys.stderr)
    sys.exit(2)

SKILL_SELLING = ("selling-point-copy", "five_point_build.py")
SKILL_OUTLINE = ("conversion-structure-template", "detail_page_outline.py")
SKILL_ADLAW = ("adlaw-compliance-precheck", "adlaw_scan.py")

REQUIRED = ["points", "modules", "text"]

DEMO = {
    "platform": "Amazon",
    "category": "",
    "product_info": {
        "品名": "304 不锈钢真空保温杯 500ml",
        "材质": "304 不锈钢内胆 + 316 不锈钢外壳",
        "规格": "500ml / 杯高 21cm",
        "认证": "GB 4806.9 食品接触用不锈钢",
        "场景": ["办公室", "通勤", "车载"],
    },
    "evidence": ["GB 4806.9 检测报告号 SZ2026-1188", "自测：500ml 热水 12h 后 ≥ 55℃（样本 3 次）"],
    "text": ("MUGGO 保温杯 12 小时保温。"
             "早上的热水，到了下午就凉了？办公室一杯热茶常喝常凉。"
             "304 不锈钢内胆 + 真空层，实测 500ml 热水 12 小时后 ≥55℃。"
             "通勤、办公、车载，随时一杯温水。"
             "MUGGO 专注饮水器具，坚持食品级用料与出厂逐只测漏。"
             "杯盖密封件质保 12 个月，质量问题免费补寄。"
             "304不锈钢内胆耐腐蚀，泡茶泡咖啡不串味，杯身冲洗即净；"
             "316不锈钢外壳搭配真空层，保温更持久，实测500ml热水12小时后水温≥55℃（样本3次）；"
             "杯盖硅胶密封圈设计，倒置不漏水，通勤包内放心放；"
             "杯口尺寸 5.5cm，密封杯盖防尘防漏，夏天加冰随时喝，清洗也方便；"
             "700ml 大容量焖烧款锁温 6 小时，带粥带汤出门随时吃上热饭。"),
    "points": [
        "304不锈钢内胆耐腐蚀，泡茶泡咖啡不串味，杯身冲洗即净",
        "316不锈钢外壳搭配真空层，保温更持久，实测500ml热水12小时后水温≥55℃（样本3次），通勤路上随时喝到温水",
        "杯盖硅胶密封圈设计，倒置不漏水，通勤包内放心放",
        "杯口尺寸 5.5cm，密封杯盖防尘防漏，夏天加冰随时喝，清洗也方便",
        "700ml 大容量焖烧款锁温 6 小时，带粥带汤出门随时吃上热饭",
    ],
    "brief": {
        "品类": "304 不锈钢真空保温杯",
        "品牌": "MUGGO",
        "核心卖点": ["12 小时保温", "带茶隔", "杯盖密封倒置不漏", "316 外壳"],
        "目标人群": ["办公室白领", "通勤族"],
        "本店 SKU": ["500ml 保温款", "350ml 迷你款", "700ml 焖烧款"],
    },
    "modules": [
        {"模块": "主图区", "功能定位": "首屏抓眼", "建议字数": 12, "素材状态": "✅", "文案": "MUGGO 保温杯 12 小时保温"},
        {"模块": "痛点共鸣", "功能定位": "建立共鸣", "建议字数": 48, "素材状态": "🟡", "文案": "早上的热水，到了下午就凉了？办公室一杯热茶常喝常凉。"},
        {"模块": "卖点图文", "功能定位": "差异化卖点", "建议字数": 52, "素材状态": "🟡", "文案": "304 不锈钢内胆 + 真空层，实测 500ml 热水 12 小时后 ≥55℃。"},
        {"模块": "场景图", "功能定位": "场景代入", "建议字数": 18, "素材状态": "🟡", "文案": "通勤、办公、车载，随时一杯温水。"},
        {"模块": "品牌故事", "功能定位": "建立信任", "建议字数": 110, "素材状态": "🟡", "文案": "MUGGO 专注饮水器具，坚持食品级用料与出厂逐只测漏。"},
        {"模块": "对比表", "功能定位": "店内导购", "建议字数": 0, "素材状态": "✅", "文案": "—"},
        {"模块": "规格表", "功能定位": "参数如实", "建议字数": 0, "素材状态": "✅", "文案": "—"},
        {"模块": "售后承诺", "功能定位": "降风险", "建议字数": 30, "素材状态": "✅", "文案": "杯盖密封件质保 12 个月，质量问题免费补寄。"},
    ],
    "sku_table": [
        {"参数": "容量", "本店 500ml 保温款": "500ml", "本店 350ml 迷你款": "350ml", "本店 700ml 焖烧款": "700ml"},
        {"参数": "保温时长", "本店 500ml 保温款": "12h", "本店 350ml 迷你款": "8h", "本店 700ml 焖烧款": "12h"},
        {"参数": "内胆材质", "本店 500ml 保温款": "304 不锈钢", "本店 350ml 迷你款": "304 不锈钢", "本店 700ml 焖烧款": "316 不锈钢"},
        {"参数": "带茶隔", "本店 500ml 保温款": "是", "本店 350ml 迷你款": "否", "本店 700ml 焖烧款": "是"},
    ],
}


def load_skill(slug, filename):
    path = os.path.join(REPO, "skills", slug, "scripts", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"原子技能脚本不存在: {path}")
    spec = importlib.util.spec_from_file_location(f"skill_{slug.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _step(steps, no, name, skill, status, key):
    steps.append({"步骤": f"{no} {name}", "原子技能": skill, "状态": status, "关键结果": key})


def run_flow(payload, outdir):
    at.ensure_outdir(outdir)
    steps = []
    missing = [k for k in REQUIRED if not payload.get(k)]
    if missing:
        _step(steps, 1, "输入校验", "—", "❌ 中止", "缺字段: " + "、".join(missing))
        _write(outdir, steps, {}, [], [], {"结论": "输入不完整，流程中止"})
        return {"steps": steps, "aborted": True}

    _step(steps, 1, "输入校验", "—", "✅",
          f'payload 完整；平台 {payload.get("platform", "通用")}，卖点 {len(payload["points"])} 条，'
          f'模块 {len(payload["modules"])} 个')

    selling = load_skill(*SKILL_SELLING)
    outline = load_skill(*SKILL_OUTLINE)
    adlaw = load_skill(*SKILL_ADLAW)

    # 第 2 步 五点卖点校验
    s2_dir = os.path.join(outdir, "step2_selling")
    try:
        r2 = selling.run({"platform": payload.get("platform", "通用"),
                          "product_info": payload.get("product_info", {}),
                          "evidence": payload.get("evidence", []),
                          "points": payload["points"]}, s2_dir)
    except Exception as e:  # noqa: BLE001
        _step(steps, 2, "五点卖点校验", SKILL_SELLING[0], "❌ 失败", f"{type(e).__name__}: {e}")
        _write(outdir, steps, {}, [], [], {"结论": "五点校验失败，流程中止"})
        return {"steps": steps, "aborted": True}
    sum2 = r2["summary"]
    ok2 = sum2["可用数"] == sum2["条数"]
    _step(steps, 2, "五点卖点校验", SKILL_SELLING[0],
          "✅" if ok2 else "⚠️ 有不合格条目",
          f'可用 {sum2["可用数"]}/{sum2["条数"]}；需改 {sum2["需改数"]}；首条差异化 {sum2["首条差异化"]}')

    # 第 3 步 结构校验
    s3_dir = os.path.join(outdir, "step3_outline")
    try:
        r3 = outline.run({"platform": payload.get("platform", "通用"),
                          "brief": payload.get("brief", {}),
                          "modules": payload["modules"],
                          "sku_table": payload.get("sku_table", [])}, s3_dir)
    except Exception as e:  # noqa: BLE001
        _step(steps, 3, "结构校验", SKILL_OUTLINE[0], "❌ 失败", f"{type(e).__name__}: {e}")
        _write(outdir, steps, {}, [], [], {"结论": "结构校验失败，流程中止"})
        return {"steps": steps, "aborted": True}
    sum3 = r3["summary"]
    ok3 = sum3["待整改"] == 0
    _step(steps, 3, "结构校验", SKILL_OUTLINE[0],
          "✅" if ok3 else "⚠️ 结构待整改",
          f'模块 {sum3["模块数"]} 个；校验通过 {sum3["校验通过项"]}/{sum3["校验总项"]}；'
          f'A+ 必备 {sum3["A+ 必备模块"]}' + (f'；issues: {"; ".join(r3["issues"])}' if r3["issues"] else ""))

    # 第 4 步 广告法终审
    s4_dir = os.path.join(outdir, "step4_adlaw")
    try:
        r4 = adlaw.run({"text": payload["text"],
                        "platform": payload.get("platform", "通用"),
                        "category": payload.get("category", "")}, s4_dir)
    except Exception as e:  # noqa: BLE001
        _step(steps, 4, "广告法终审", SKILL_ADLAW[0], "❌ 失败", f"{type(e).__name__}: {e}")
        _write(outdir, steps, {}, [], [], {"结论": "广告法终审失败，流程中止"})
        return {"steps": steps, "aborted": True}
    sum4 = r4["summary"]
    ok4 = sum4["红线"] == 0
    _step(steps, 4, "广告法终审", SKILL_ADLAW[0],
          "✅" if ok4 else "⚠️ 有红线",
          f'红线 {sum4["红线"]} / 警告 {sum4["警告"]} / 提示 {sum4["提示"]} → {sum4["总体结论"]}')

    # 第 5 步 汇总交付（以最严项为准）
    if not (ok2 and ok3 and ok4):
        final = "待整改"
    elif sum4["警告"] > 2:
        final = "待整改"
    else:
        final = "通过"
    _step(steps, 5, "汇总交付", "—", "✅" if final == "通过" else "⚠️ 待整改",
          f'交付结论「{final}」')

    deliverable = {"五点可用": f'{sum2["可用数"]}/{sum2["条数"]}',
                   "结构待整改": sum3["待整改"],
                   "广告法红线": sum4["红线"],
                   "最终结论": final}
    fix_rows = []
    for r in json.load(open(os.path.join(s2_dir, "five_point.json"), encoding="utf-8"))["point_checks"]:
        if r["结论"] != "可用":
            fix_rows.append({"来源步骤": "2 五点卖点校验", "问题": f'条目{r["序号"]}：{r["结论"]}',
                             "改法": "按 FAB 补收益层并删除违禁词后重跑"})
    d3 = json.load(open(os.path.join(s3_dir, "detail_page.json"), encoding="utf-8"))
    for i, issue in enumerate(d3["issues"], 1):
        fix_rows.append({"来源步骤": "3 结构校验", "问题": issue, "改法": "按 issue 调整模块结构后重跑"})
    d4 = json.load(open(os.path.join(s4_dir, "adlaw_scan.json"), encoding="utf-8"))
    for v in d4["violations"]:
        if v["级别"].startswith("🔴"):
            fix_rows.append({"来源步骤": "4 广告法终审", "问题": f'{v["违规词/表述"]}（{v["命中规则"]}）',
                             "改法": v["修改建议"]})

    _write(outdir, steps, deliverable, d4["violations"], fix_rows,
           {"结论": final, "五点可用": deliverable["五点可用"],
            "结构待整改": sum3["待整改"], "红线": sum4["红线"], "警告": sum4["警告"]})
    return {"steps": steps, "aborted": False, "verdict": final}


def _write(outdir, steps, deliverable, violations, fixes, summary):
    at.write_excel(
        os.path.join(outdir, "流程执行报告.xlsx"),
        {
            "步骤明细": steps,
            "整改清单": fixes or [{"来源步骤": "—", "问题": "—", "改法": "—"}],
            "违规清单": violations or [{"级别": "（无）", "违规词/表述": "", "命中规则": "", "修改建议": ""}],
            "汇总": [{"项": k, "内容": str(v)} for k, v in summary.items()],
        },
        highlights={"步骤明细": {"状态": "contains:❌"}, "违规清单": {"级别": "contains:红线"}},
        widths={"步骤明细": {"关键结果": 46}, "整改清单": {"问题": 34, "改法": 40}},
    )
    at.write_json({"steps": steps, "deliverable": deliverable, "fixes": fixes,
                   "summary": summary, "generated_at": at.stamp()},
                  os.path.join(outdir, "flow_result.json"))


def main():
    ap = argparse.ArgumentParser(description="详情页转化文案 —— 三技能编排（卖点→结构→广告法）")
    ap.add_argument("--input")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    payload = DEMO if a.demo else (at.read_json(a.input) if a.input else None)
    if payload is None:
        ap.error("需要 --input / --demo 之一")

    r = run_flow(payload, a.outdir)
    for s in r["steps"]:
        print(f'{s["状态"]:>10}  {s["步骤"]}  —  {s["关键结果"]}')
    print("产物:", os.path.join(a.outdir, "流程执行报告.xlsx"), "|",
          os.path.join(a.outdir, "flow_result.json"))
    at.emit(r)


if __name__ == "__main__":
    main()
