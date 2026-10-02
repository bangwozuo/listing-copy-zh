# -*- coding: utf-8 -*-
"""关键词挖掘与标题组合 —— 工作流编排脚本（T3）。

串联两个原子技能：
  S1 keyword-combination        （标题组合 + 五项校验）
  S2 adlaw-compliance-precheck  （合规闸门：红线 > 0 则回环重写，最多 2 次）

用法：
  python run_flow.py --input input.json --outdir out
  python run_flow.py --demo

产物：
  out/流程执行报告.xlsx   步骤明细 / 最终交付 / 汇总
  out/flow_result.json    机器可读结果
"""
from __future__ import annotations

import argparse
import importlib.util
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
    "keyword-combination": "title_keyword_check.py",
    "adlaw-compliance-precheck": "adlaw_scan.py",
}
MAX_LOOP = 2

DEMO = {
    "platform": "淘宝",
    "core_word": "保温杯",
    "product_info": {
        "品名": "304 不锈钢真空保温杯", "材质": "304 内胆 + 316 外壳",
        "规格": "500ml / 杯高 21cm", "卖点": ["12 小时保温", "带茶隔", "杯盖密封不漏"],
        "场景": ["办公室", "通勤", "车载"],
    },
    "keywords": [
        {"词": "保温杯", "层级": "核心词"},
        {"词": "带茶隔保温杯", "层级": "长尾词"},
        {"词": "大容量女款", "层级": "长尾词"},
        {"词": "车载焖烧杯", "层级": "蓝海词"},
    ],
    "candidate_titles": [
        "保温杯 304不锈钢 500ml 办公室便携带茶隔",
        "带茶隔保温杯 大容量女款 500ml 304不锈钢 通勤车载",
        "2026新款保温杯大容量办公室学生便携水杯不漏水焖烧杯",
    ],
    "category_words_to_avoid": ["手机壳", "数据线"],
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
    steps, result = [], {}

    # ---- S0 输入校验
    missing = [k for k in ("platform", "product_info") if not payload.get(k)]
    if missing:
        steps.append({"步骤": "1 输入校验", "原子技能": "—", "状态": "❌ 中止",
                      "关键结果": "缺字段: " + "、".join(missing)})
        _write(outdir, steps, {}, {"结论": "输入不完整，流程中止", "缺失字段": missing})
        return {"steps": steps, "aborted": True, "missing": missing}

    steps.append({"步骤": "1 输入校验", "原子技能": "—", "状态": "✅",
                  "关键结果": f'payload 完整；平台 {payload.get("platform")}'})

    # ---- S1 标题组合与校验
    try:
        kw = load_skill("keyword-combination", SKILL_SCRIPTS["keyword-combination"])
        s1 = kw.run(payload, os.path.join(outdir, "step2_keyword"))
        import json as _json
        detail = _json.load(open(os.path.join(outdir, "step2_keyword", "keyword_check.json"),
                                 encoding="utf-8"))
        usable_titles = [c["标题"] for c in detail["title_checks"] if c["结论"] == "可用"]
        result["S1"] = {"可用数": len(usable_titles), "推荐": detail["summary"]["推荐标题"]}
        steps.append({"步骤": "2 标题组合与校验", "原子技能": "keyword-combination",
                      "状态": "✅" if usable_titles else "⚠️ 无可用候选",
                      "关键结果": f'可用 {len(usable_titles)} 个；推荐「{detail["summary"]["推荐标题"]}」'})
    except Exception as e:  # noqa: BLE001
        steps.append({"步骤": "2 标题组合与校验", "原子技能": "keyword-combination",
                      "状态": "❌ 失败", "关键结果": f"{type(e).__name__}: {e}"})
        _write(outdir, steps, {}, {"结论": "S1 失败，流程中止"})
        return {"steps": steps, "aborted": True}

    if not usable_titles:
        steps.append({"步骤": "3 广告法闸门", "原子技能": "adlaw-compliance-precheck",
                      "状态": "⏭ 跳过", "关键结果": "S1 无可用候选，闸门无输入"})
        _write(outdir, steps, {"可用标题": []}, {"结论": "无可用标题，需修改素材后重跑"})
        return {"steps": steps, "aborted": False, "usable": 0}

    # ---- S2 广告法闸门（含回环）
    adlaw = load_skill("adlaw-compliance-precheck", SKILL_SCRIPTS["adlaw-compliance-precheck"])
    loop, text, verdict = 0, "；".join(usable_titles), ""
    while True:
        rep = adlaw.run({"text": text, "platform": payload.get("platform", "通用")},
                        os.path.join(outdir, "step3_adlaw"))
        import json as _json
        scan = _json.load(open(os.path.join(outdir, "step3_adlaw", "adlaw_scan.json"), encoding="utf-8"))
        verdict = scan["summary"]["总体结论"]
        red = scan["summary"]["红线"]
        if red == 0 or loop >= MAX_LOOP:
            break
        loop += 1
        text = "；".join(t for t in usable_titles if not any(
            h["违规词/表述"] in t for h in scan["violations"])) or text

    steps.append({"步骤": "3 广告法闸门", "原子技能": "adlaw-compliance-precheck",
                  "状态": "✅" if verdict == "通过" else f"⚠️ {verdict}",
                  "关键结果": f"红线 {scan['summary']['红线']} / 警告 {scan['summary']['警告']}；回环 {loop} 次"})

    deliverable = {"可用标题": usable_titles, "合规结论": verdict,
                   "回环次数": loop, "产物": rep["files"]}
    steps.append({"步骤": "4 汇总交付", "原子技能": "—",
                  "状态": "✅" if verdict == "通过" else "⚠️ 需整改",
                  "关键结果": f"交付 {len(usable_titles)} 个可用标题；结论「{verdict}」"})
    _write(outdir, steps, deliverable, {"结论": verdict, "可用标题数": len(usable_titles)})
    return {"steps": steps, "aborted": False, "usable": len(usable_titles), "verdict": verdict}


def _write(outdir, steps, deliverable, summary):
    rows = [{"步骤": s["步骤"], "原子技能": s["原子技能"], "状态": s["状态"], "关键结果": s["关键结果"]}
            for s in steps]
    titles = deliverable.get("可用标题", []) if isinstance(deliverable, dict) else []
    at.write_excel(
        os.path.join(outdir, "流程执行报告.xlsx"),
        {"步骤明细": rows,
         "最终交付": [{"#": i + 1, "可用标题": t} for i, t in enumerate(titles)] or [{"#": "—", "可用标题": "—"}],
         "汇总": [{"项": k, "内容": str(v)} for k, v in summary.items()]},
        highlights={"步骤明细": {"状态": "contains:❌"}},
        widths={"步骤明细": {"关键结果": 50}},
    )
    at.write_json({"steps": steps, "deliverable": deliverable, "summary": summary,
                   "generated_at": at.stamp()}, os.path.join(outdir, "flow_result.json"))


def main():
    ap = argparse.ArgumentParser(description="关键词挖掘与标题组合 —— 工作流编排")
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
