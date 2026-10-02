# -*- coding: utf-8 -*-
"""五点卖点生成 —— 工作流编排脚本（T3）。

串联两个原子技能：
  2 selling-point-copy         （FAB 翻译 + 五项校验）
  3 adlaw-compliance-precheck  （合规闸门：红线 > 0 则回环改写，最多 2 次）

用法：
  python run_flow.py --input input.json --outdir out
  python run_flow.py --demo

产物：
  out/流程执行报告.xlsx   步骤明细 / 最终交付 / 待整改 / 汇总
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

SKILL_SCRIPTS = {
    "selling-point-copy": "five_point_build.py",
    "adlaw-compliance-precheck": "adlaw_scan.py",
}
MAX_LOOP = 2

DEMO = {
    "platform": "Amazon",
    "category": "通用",
    "product_info": {
        "品名": "304 不锈钢真空保温杯 500ml",
        "材质": "304 不锈钢内胆 + 316 不锈钢外壳",
        "规格": "500ml / 杯高 21cm",
        "认证": "GB 4806.9 食品接触用不锈钢",
    },
    "evidence": ["GB 4806.9 检测报告号 SZ2026-1188", "自测：500ml 热水 12h 后 ≥ 55℃（样本 3 次）"],
    "points": [
        "304不锈钢内胆耐腐蚀，泡茶泡咖啡不串味，杯身冲洗即净",
        "316不锈钢外壳搭配真空层，保温更持久，实测500ml热水12小时后水温≥55℃（样本3次），通勤路上随时喝到温水",
        "杯盖硅胶密封圈设计，倒置不漏水，通勤包内放心放",
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


def run_flow(payload, outdir):
    at.ensure_outdir(outdir)
    steps = []

    missing = [k for k in ("platform", "product_info") if not payload.get(k)]
    if missing:
        steps.append({"步骤": "1 输入校验", "原子技能": "—", "状态": "❌ 中止",
                      "关键结果": "缺字段: " + "、".join(missing)})
        _write(outdir, steps, {}, [], {"结论": "输入不完整，流程中止"})
        return {"steps": steps, "aborted": True, "missing": missing}

    steps.append({"步骤": "1 输入校验", "原子技能": "—", "状态": "✅",
                  "关键结果": f'payload 完整；平台 {payload.get("platform")}'})

    # 第 2 步
    try:
        sp = load_skill("selling-point-copy", SKILL_SCRIPTS["selling-point-copy"])
        sp.run(payload, os.path.join(outdir, "step2_point"))
        detail = json.load(open(os.path.join(outdir, "step2_point", "five_point.json"), encoding="utf-8"))
        usable = [r["卖点"] for r in detail["point_checks"] if r["结论"] == "可用"]
        pending = [{"卖点": r["卖点"], "问题": r["结论"]} for r in detail["point_checks"]
                   if r["结论"] != "可用"]
        steps.append({"步骤": "2 卖点生成与校验", "原子技能": "selling-point-copy",
                      "状态": "✅" if usable else "⚠️ 无可用卖点",
                      "关键结果": f'可用 {len(usable)} / {len(detail["point_checks"])}；待整改 {len(pending)}'})
    except Exception as e:  # noqa: BLE001
        steps.append({"步骤": "2 卖点生成与校验", "原子技能": "selling-point-copy",
                      "状态": "❌ 失败", "关键结果": f"{type(e).__name__}: {e}"})
        _write(outdir, steps, {}, [], {"结论": "第 2 步失败，流程中止"})
        return {"steps": steps, "aborted": True}

    if not usable:
        steps.append({"步骤": "3 广告法闸门", "原子技能": "adlaw-compliance-precheck",
                      "状态": "⏭ 跳过", "关键结果": "第 2 步无可用卖点，闸门无输入"})
        _write(outdir, steps, {"可用卖点": []}, pending, {"结论": "无可用卖点，需补证据后重跑"})
        return {"steps": steps, "aborted": False, "usable": 0}

    # 第 3 步（含回环）
    adlaw = load_skill("adlaw-compliance-precheck", SKILL_SCRIPTS["adlaw-compliance-precheck"])
    loop, text, verdict, scan = 0, "；".join(usable), "", None
    while True:
        rep = adlaw.run({"text": text, "platform": payload.get("platform", "通用"),
                         "category": payload.get("category", "")},
                        os.path.join(outdir, "step3_adlaw"))
        scan = json.load(open(os.path.join(outdir, "step3_adlaw", "adlaw_scan.json"), encoding="utf-8"))
        verdict, red = scan["summary"]["总体结论"], scan["summary"]["红线"]
        if red == 0 or loop >= MAX_LOOP:
            break
        loop += 1
        text = "；".join(t for t in usable if not any(
            h["违规词/表述"] in t for h in scan["violations"])) or text

    steps.append({"步骤": "3 广告法闸门", "原子技能": "adlaw-compliance-precheck",
                  "状态": "✅" if verdict == "通过" else f"⚠️ {verdict}",
                  "关键结果": f"红线 {scan['summary']['红线']} / 警告 {scan['summary']['警告']}；回环 {loop} 次"})
    steps.append({"步骤": "4 汇总交付", "原子技能": "—",
                  "状态": "✅" if verdict == "通过" else "⚠️ 需整改",
                  "关键结果": f"交付 {len(usable)} 条卖点；结论「{verdict}」"})

    deliverable = {"可用卖点": usable, "合规结论": verdict, "回环次数": loop, "产物": rep["files"]}
    _write(outdir, steps, deliverable, pending,
           {"结论": verdict, "可用卖点数": len(usable), "待整改数": len(pending)})
    return {"steps": steps, "aborted": False, "usable": len(usable), "verdict": verdict}


def _write(outdir, steps, deliverable, pending, summary):
    rows = steps
    pts = deliverable.get("可用卖点", []) if isinstance(deliverable, dict) else []
    at.write_excel(
        os.path.join(outdir, "流程执行报告.xlsx"),
        {"步骤明细": rows,
         "最终交付": [{"#": i + 1, "可用卖点": t} for i, t in enumerate(pts)] or [{"#": "—", "可用卖点": "—"}],
         "待整改": pending or [{"卖点": "—", "问题": "—"}],
         "汇总": [{"项": k, "内容": str(v)} for k, v in summary.items()]},
        highlights={"步骤明细": {"状态": "contains:❌"}},
        widths={"步骤明细": {"关键结果": 50}, "最终交付": {"可用卖点": 50}},
    )
    at.write_json({"steps": steps, "deliverable": deliverable, "pending": pending,
                   "summary": summary, "generated_at": at.stamp()},
                  os.path.join(outdir, "flow_result.json"))


def main():
    ap = argparse.ArgumentParser(description="五点卖点生成 —— 工作流编排")
    ap.add_argument("--input")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    payload = DEMO if a.demo else (at.read_json(a.input) if a.input else None)
    if payload is None:
        ap.error("需要 --input / --demo 之一")

    r = run_flow(payload, a.outdir)
    for s in r["steps"]:
        print(f'{s["状态"]:>8}  {s["步骤"]}  —  {s["关键结果"]}')
    print("产物:", os.path.join(a.outdir, "流程执行报告.xlsx"), "|",
          os.path.join(a.outdir, "flow_result.json"))
    at.emit(r)


if __name__ == "__main__":
    main()
