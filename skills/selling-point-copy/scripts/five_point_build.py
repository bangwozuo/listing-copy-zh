# -*- coding: utf-8 -*-
"""卖点文案 —— 五点描述（Bullet Points）结构与长度校验器。

职责边界：本脚本做**可计算的机械检查**（字符数、FAB 三要素词元、首条差异化、证据数字、
违禁词命中）。**真正的 FAB 翻译与收益撰文**由模型按 prompt.txt 完成。

用法：
  python five_point_build.py --input input.json --outdir out
  python five_point_build.py --demo

产物：
  out/五点校验.xlsx    五点校验 / 违规明细 / 汇总
  out/five_point.json  机器可读结果
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(SKILL_DIR))
sys.path.insert(0, os.path.join(REPO, "lib"))

try:
    import assettools as at
except ImportError:  # pragma: no cover
    print("[错误] 未找到 lib/assettools.py：请确认技能位于 <repo>/skills/<slug>/scripts/ 下。",
          file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------- 领域常量

# 平台 → (单条上限, 口径)。Amazon 为硬上限，中文平台为建议值。
POINT_LIMITS = {
    "Amazon": (500, "硬"),
    "淘宝": (80, "建议"),
    "天猫": (80, "建议"),
    "抖音": (40, "建议"),
    "拼多多": (30, "建议"),
    "小红书": (100, "建议"),
    "通用": (80, "建议"),
}

FEATURE_MARKERS = ["采用", "材质", "内胆", "外壳", "不锈钢", "钛", "陶瓷", "玻璃", "硅胶",
                   "棉", "规格", "容量", "ml", "mL", "尺寸", "工艺", "涂层", "认证", "专利", "层"]
ADVANTAGE_MARKERS = ["耐", "防", "抗", "不易", "轻", "薄", "强", "稳定", "持久", "密封",
                     "保温", "提升", "减少", "降低", "避免", "延长", "锁"]
BENEFIT_MARKERS = ["你可以", "让你", "无需", "不用", "省", "省心", "放心", "安心", "轻松",
                   "方便", "不怕", "随时", "搞定", "省事", "不用担心", "即净", "好打理"]

EVIDENCE = [r"\d", r"报告", r"检测", r"专利", r"样本", r"认证", r"GB\s*\d", r"ZL"]

# 违禁：绝对化用语 + 无信息量空话 + 促销/价格/竞品
BANNED = [
    (r"最(好|佳|优|强|低|便宜|先进|流行|受欢迎|高档|高级|顶级|优质|低)", "绝对化·最高级"),
    (r"(第一|TOP\s*1|No\.?\s*1|冠军|之王|领导者)", "绝对化·排名"),
    (r"(唯一|独家|首创|首个|首款)", "绝对化·唯一性"),
    (r"(国家级|世界级|全球级|顶级|极品|极佳|绝佳|终极|极致|巅峰|至尊)", "绝对化·级别"),
    (r"(100\s*%|百分百|彻底|根治|永久|永不|绝对|毫无|无任何副作用)", "绝对化·功效断言"),
    (r"(优质|高端|精致|尊贵|匠心|奢华)", "无信息量形容词"),
    (r"(全网最低|限时抢购|仅此一天|最后一天|清仓价|加微信|扫码|领券|优惠券)", "促销/导流"),
    (r"(比\s*[^，。]{1,8}\s*品牌|比同行|碾压|吊打)", "贬低竞品"),
    (r"(¥|￥|\d+\s*元)", "价格信息"),
]

DEMO = {
    "platform": "Amazon",
    "product_info": {
        "品名": "304 不锈钢真空保温杯 500ml",
        "材质": "304 不锈钢内胆 + 316 不锈钢外壳",
        "规格": "500ml / 杯高 21cm",
        "认证": "GB 4806.9 食品接触用不锈钢",
        "场景": ["办公室", "通勤", "车载"],
    },
    "evidence": ["GB 4806.9 检测报告号 SZ2026-1188", "自测：500ml 热水 12h 后 ≥ 55℃（样本 3 次）"],
    "points": [
        "304不锈钢内胆耐腐蚀，泡茶泡咖啡不串味，杯身冲洗即净",
        "316不锈钢外壳搭配真空层，保温更持久，实测500ml热水12小时后水温≥55℃（样本3次），通勤路上随时喝到温水",
        "杯盖硅胶密封圈设计，倒置不漏水，通勤包内放心放",
        "采用优质材料",
        "全网最低价，100%保温，永久不漏，比某品牌好，加微信领券"
    ],
}


# ---------------------------------------------------------------- 计算

def scan_banned(text: str):
    hits = []
    for pat, rule in BANNED:
        for m in re.finditer(pat, text):
            hits.append({"片段": m.group(0), "规则": rule})
    return hits


def has_any(text: str, markers) -> bool:
    return any(m in text for m in markers)


def has_evidence(text: str) -> bool:
    return any(re.search(p, text) for p in EVIDENCE)


def check_point(payload, idx: int, text: str):
    platform = payload.get("platform", "通用")
    limit, kind = POINT_LIMITS.get(platform, POINT_LIMITS["通用"])
    n = len(text)

    f = has_any(text, FEATURE_MARKERS)
    a = has_any(text, ADVANTAGE_MARKERS)
    b = has_any(text, BENEFIT_MARKERS)
    ev = has_evidence(text)
    banned = scan_banned(text)

    ok_len = n <= limit
    ok_fab = f and a and b
    ok_ev = ev
    ok_ban = not banned

    if not ok_ban:
        verdict = "需修改"
    elif not ok_len:
        verdict = "需修改"
    elif not ok_fab:
        verdict = "补充收益（FAB 不全）"
    else:
        verdict = "可用"

    return {
        "序号": idx,
        "卖点": text,
        "字符数": n,
        "上限": limit,
        "口径": kind,
        "F(属性)": "✅" if f else "—",
        "A(优势)": "✅" if a else "—",
        "B(收益)": "✅" if b else "—",
        "有数字/证据": "✅" if ev else "—",
        "长度合规": "✅" if ok_len else "🔴 超限",
        "无违禁词": "✅" if ok_ban else "🔴 违禁",
        "结论": verdict,
        "_banned": banned,
    }


def first_point_diff(payload, rows):
    """首条差异化：首条须含数字/材质/认证等可辨识特征。"""
    if not rows:
        return "—"
    t = rows[0]["卖点"]
    return "✅" if has_any(t, FEATURE_MARKERS) and has_evidence(t) else "🟡 首条建议放最大差异化"


# ---------------------------------------------------------------- 主流程

def run(payload, outdir):
    points = payload.get("points") or []
    if not points:
        raise ValueError("缺少 points：请提供待校验/改写的卖点条目。")

    rows = [check_point(payload, i + 1, t) for i, t in enumerate(points)]
    d = first_point_diff(payload, rows)

    bad = [r for r in rows if r["结论"] != "可用"]
    summary = {
        "目标平台": payload.get("platform", "通用"),
        "单条上限": f'{POINT_LIMITS.get(payload.get("platform", "通用"), POINT_LIMITS["通用"])[0]} '
                    f'{POINT_LIMITS.get(payload.get("platform", "通用"), POINT_LIMITS["通用"])[1]}上限',
        "条数": len(rows),
        "可用数": len(rows) - len(bad),
        "需改数": len(bad),
        "首条差异化": d,
        "最长字符数": max(r["字符数"] for r in rows),
    }

    at.ensure_outdir(outdir)
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    bad_rows = [{"序号": r["序号"], "卖点": r["卖点"], "问题": r["结论"],
                 "命中": "；".join(f'{h["片段"]}({h["规则"]})' for h in r["_banned"]) or "—"}
                for r in rows if r["_banned"] or r["结论"] != "可用"]

    xlsx = at.write_excel(
        os.path.join(outdir, "五点校验.xlsx"),
        {
            "五点校验": clean,
            "违规明细": bad_rows or [{"序号": "—", "卖点": "—", "问题": "—", "命中": "—"}],
            "汇总": [{"项": k, "内容": str(v)} for k, v in summary.items()],
        },
        highlights={"五点校验": {"长度合规": "contains:🔴", "无违禁词": "contains:🔴"}},
        widths={"五点校验": {"卖点": 46, "结论": 18}},
    )
    js = at.write_json(
        {
            "summary": summary,
            "point_checks": clean,
            "banned_detail": [{"序号": r["序号"], "命中": r["_banned"]} for r in rows if r["_banned"]],
            "generated_at": at.stamp(),
            "note": "长度/FAB 词元/证据数字/违禁词为脚本机械检查；FAB 语义质量须由模型复核",
        },
        os.path.join(outdir, "five_point.json"),
    )
    return {"files": [xlsx, js], "summary": summary, "total": len(rows), "usable": len(rows) - len(bad)}


def main():
    ap = argparse.ArgumentParser(description="卖点文案 —— 五点描述校验")
    ap.add_argument("--input")
    ap.add_argument("--platform", default="Amazon")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    if a.demo:
        payload = DEMO
    elif a.input:
        payload = at.read_json(a.input)
    else:
        ap.error("需要 --input / --demo 之一")

    r = run(payload, a.outdir)
    print(f"校验 {r['total']} 条卖点，可用 {r['usable']} 条 —— 首条差异化：{r['summary']['首条差异化']}")
    for f in r["files"]:
        print(" 产物:", f)
    at.emit(r)


if __name__ == "__main__":
    main()
