# -*- coding: utf-8 -*-
"""广告法合规预审 —— 工作流编排脚本（T3）。

两遍扫描：
  2 adlaw-compliance-precheck 初检（text）
  3 adlaw-compliance-precheck 复扫（revised_text，可选）

用法：
  python run_flow.py --input input.json --outdir out
  python run_flow.py --demo

产物：
  out/流程执行报告.xlsx   步骤明细 / 违规清单 / 整改对比 / 汇总
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

SKILL = ("adlaw-compliance-precheck", "adlaw_scan.py")
MAX_REVIEW = 2

DEMO = {
    "platform": "淘宝",
    "category": "化妆品",
    "text": "【全网最低价】医美级精华液，100%彻底淡化痘印，效果最好的抗敏修复神器！国家级实验室研发，独家配方，销量第一。好评返现 5 元，加微信 xxx 领试用装，扫码进群。比 XX 大牌好用，专利配方，纯天然无添加，本品适用于各类肌肤，无任何副作用。",
    "revised_text": "2026 年新款精华液，限时优惠价 ¥99。配方含神经酰胺与透明质酸，主打舒缓保湿。实测反馈良好（样本 30 人）。专利配方（ZL2026xxxxxxx）。",
}


def load_skill(slug, filename):
    path = os.path.join(REPO, "skills", slug, "scripts", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"原子技能脚本不存在: {path}")
    spec = importlib.util.spec_from_file_location(f"skill_{slug.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _scan(adlaw, text, payload, outdir):
    adlaw.run({"text": text, "platform": payload.get("platform", "通用"),
               "category": payload.get("category", ""), "rules": payload.get("rules")}, outdir)
    return json.load(open(os.path.join(outdir, "adlaw_scan.json"), encoding="utf-8"))


def run_flow(payload, outdir):
    at.ensure_outdir(outdir)
    steps = []

    if not payload.get("text"):
        steps.append({"步骤": "1 输入校验", "原子技能": "—", "状态": "❌ 中止",
                      "关键结果": "缺字段: text"})
        _write(outdir, steps, {}, [], [], {"结论": "输入不完整，流程中止"})
        return {"steps": steps, "aborted": True}

    steps.append({"步骤": "1 输入校验", "原子技能": "—", "状态": "✅",
                  "关键结果": f'payload 完整；平台 {payload.get("platform", "通用")}'})
    adlaw = load_skill(*SKILL)

    # 第 2 步 初检
    try:
        first = _scan(adlaw, payload["text"], payload, os.path.join(outdir, "step2_first"))
    except Exception as e:  # noqa: BLE001
        steps.append({"步骤": "2 初检扫描", "原子技能": SKILL[0], "状态": "❌ 失败",
                      "关键结果": f"{type(e).__name__}: {e}"})
        _write(outdir, steps, {}, [], [], {"结论": "初检失败，流程中止"})
        return {"steps": steps, "aborted": True}

    s = first["summary"]
    steps.append({"步骤": "2 初检扫描", "原子技能": SKILL[0],
                  "状态": "✅ 通过" if s["红线"] == 0 else f'⚠️ {s["总体结论"]}',
                  "关键结果": f'红线 {s["红线"]} / 警告 {s["警告"]} / 提示 {s["提示"]}'})

    review, review_summary, loop = None, None, 0
    revised = payload.get("revised_text")

    if s["红线"] == 0:
        steps.append({"步骤": "3 整改复扫", "原子技能": SKILL[0], "状态": "⏭ 跳过",
                      "关键结果": "初检红线为 0，无需整改复扫"})
    elif not revised:
        steps.append({"步骤": "3 整改复扫", "原子技能": SKILL[0], "状态": "⏭ 跳过",
                      "关键结果": "未提供 revised_text，仅输出整改清单"})
    else:
        while True:
            review = _scan(adlaw, revised, payload, os.path.join(outdir, "step3_review"))
            review_summary = review["summary"]
            if review_summary["红线"] == 0 or loop >= MAX_REVIEW:
                break
            loop += 1
            revised = "".join(
                ch for ch in revised
                if ch not in "".join(h["违规词/表述"][0] for h in review["violations"])) or revised
        steps.append({"步骤": "3 整改复扫", "原子技能": SKILL[0],
                      "状态": "✅ 整改后通过" if review_summary["红线"] == 0 else "⚠️ 仍有残留",
                      "关键结果": f'红线 {review_summary["红线"]} / 警告 {review_summary["警告"]}；复扫 {loop + 1} 次'})

    final = "通过" if (review_summary and review_summary["红线"] == 0) else (
        "通过" if (s["红线"] == 0) else "待整改")
    steps.append({"步骤": "4 汇总交付", "原子技能": "—",
                  "状态": "✅" if final == "通过" else "⚠️ 待整改",
                  "关键结果": f'交付结论「{final}」'})

    deliverable = {"初检结论": s["总体结论"], "初检红线": s["红线"],
                   "复扫结论": (review_summary["总体结论"] if review_summary else "未复扫"),
                   "最终结论": final, "整改前": payload["text"],
                   "整改后": revised or "（未提供）"}
    _write(outdir, steps, deliverable,
           first["violations"], first.get("suggestions", []),
           {"结论": final, "初检红线": s["红线"],
            "复扫红线": (review_summary["红线"] if review_summary else "—")})
    return {"steps": steps, "aborted": False, "verdict": final}


def _write(outdir, steps, deliverable, violations, suggestions, summary):
    at.write_excel(
        os.path.join(outdir, "流程执行报告.xlsx"),
        {
            "步骤明细": steps,
            "违规清单": violations or [{"级别": "（无）"}],
            "整改对比": [{"项": k, "内容": str(v)} for k, v in (deliverable or {}).items()] or [{"项": "—", "内容": "—"}],
            "整体建议": [{"#": i + 1, "建议": t} for i, t in enumerate(suggestions or [])] or [{"#": "—", "建议": "—"}],
            "汇总": [{"项": k, "内容": str(v)} for k, v in summary.items()],
        },
        highlights={"步骤明细": {"状态": "contains:❌"}, "违规清单": {"级别": "contains:红线"}},
        widths={"步骤明细": {"关键结果": 44}, "违规清单": {"修改建议": 40}},
    )
    at.write_json({"steps": steps, "deliverable": deliverable, "violations": violations,
                   "suggestions": suggestions, "summary": summary, "generated_at": at.stamp()},
                  os.path.join(outdir, "flow_result.json"))


def main():
    ap = argparse.ArgumentParser(description="广告法合规预审 —— 工作流编排（两遍扫描）")
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
