# -*- coding: utf-8 -*-
"""A/B 文案变体 —— 差异度（Jaccard）与实验有效性校验器。

职责边界：本脚本做**可计算部分**（字符集相似度、字数、样本量公式、CTR 择优判定、
违禁词）。**变体撰写与角度选择**由模型按 prompt.txt 完成。

用法：
  python variant_matrix.py --input input.json --outdir out
  python variant_matrix.py --demo

产物：
  out/AB变体矩阵.xlsx   变体组 / 差异度矩阵 / 实验设计 / 汇总
  out/variant_matrix.json  机器可读结果
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

PLATFORM_LIMITS = {
    "淘宝": ("字符", 60), "天猫": ("字符", 60), "拼多多": ("字符", 60),
    "抖音": ("字", 30), "小红书": ("字", 20), "Amazon": ("字符", 200), "通用": ("字符", 60),
}

J_SAME, J_CLOSE = 0.6, 0.3          # 同质化 / 偏相似 阈值
COEF = 16.0                          # 两比例检验近似系数

BANNED = [
    (r"最(好|佳|优|强|低|便宜|先进|流行|受欢迎|高档|高级|顶级|优质)", "绝对化·最高级"),
    (r"(第一|TOP\s*1|冠军|之王|领导者)", "绝对化·排名"),
    (r"(唯一|独家|首创|首个|首款)", "绝对化·唯一性"),
    (r"(国家级|世界级|顶级|极致|极品)", "绝对化·级别"),
    (r"(100\s*%|百分百|彻底|根治|永不|绝对)", "绝对化·功效断言"),
    (r"(二维码|微信号|加微信|扫码|私信领)", "站外导流"),
    (r"(仅此一天|最后一天|清仓价|全网最低)", "虚假促销"),
]

DEMO = {
    "brief": "测试标题中的保温卖点表达，目标人群为办公室白领",
    "platform": "淘宝",
    "selling_point": "12 小时保温",
    "p_bar": 0.05,
    "delta": 0.02,
    "variants": [
        {"角度": "理性功能", "文案": "304不锈钢+真空层，12小时保温"},
        {"角度": "场景代入", "文案": "早上灌的热水，开完下午的会还是温的"},
        {"角度": "疑问钩子", "文案": "你的保温杯，撑得住一个工作日吗？"},
        {"角度": "情感共鸣", "文案": "忙到忘了喝水的人，更需要一杯温的"},
    ],
    "metrics": {
        "A": {"曝光": 2400, "点击": 132},
        "B": {"曝光": 2450, "点击": 176},
        "C": {"曝光": 2380, "点击": 121},
        "D": {"曝光": 2420, "点击": 139},
    },
}


# ---------------------------------------------------------------- 计算

def grams(text):
    t = re.sub(r"\s+", "", str(text))
    if len(t) < 2:
        return {t} if t else set()
    return {t[i:i + 2] for i in range(len(t) - 1)}


def jaccard(a, b):
    A, B = grams(a), grams(b)
    if not A and not B:
        return 1.0
    return round(len(A & B) / len(A | B), 2)


def scan_banned(text):
    hits = []
    for pat, rule in BANNED:
        for m in re.finditer(pat, str(text)):
            hits.append({"片段": m.group(0), "规则": rule})
    return hits


def min_sample(p_bar, delta):
    if not delta or delta <= 0:
        return None
    return int(round(COEF * p_bar * (1 - p_bar) / (delta ** 2)))


# ---------------------------------------------------------------- 主流程

def run(payload, outdir):
    variants = payload.get("variants") or []
    if len(variants) < 2:
        raise ValueError("缺少 variants：A/B 至少需要 2 个变体。")

    platform = payload.get("platform", "通用")
    unit, limit = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS["通用"])
    keys = [chr(ord("A") + i) for i in range(len(variants))]

    # 变体组校验
    rows, banned_all = [], []
    angles = []
    for k, v in zip(keys, variants):
        text = v.get("文案", "")
        n = len(text.replace(" ", "")) if unit == "字" else len(text)
        ang = v.get("角度", "")
        angles.append(ang)
        b = scan_banned(text)
        if b:
            banned_all.append({"变体": k, "命中": b})
        rows.append({
            "变体": k, "角度": ang, "文案": text, "字数": n,
            "上限": limit, "口径": unit,
            "字数合规": "✅" if n <= limit else "🔴 超限",
            "无违禁词": "✅" if not b else "🔴",
        })

    dup_angle = len(angles) != len(set(angles))

    # 差异度矩阵
    matrix, same_pairs, close_pairs = [], [], []
    for i, k in enumerate(keys):
        row = {"变体": k}
        for j, k2 in enumerate(keys):
            if i == j:
                row[k2] = 1.0
                continue
            J = jaccard(variants[i].get("文案", ""), variants[j].get("文案", ""))
            row[k2] = J
            if i < j:
                if J >= J_SAME:
                    same_pairs.append(f"{k}-{k2}(J={J})")
                elif J >= J_CLOSE:
                    close_pairs.append(f"{k}-{k2}(J={J})")
        matrix.append(row)

    # 实验设计
    p_bar = payload.get("p_bar", 0.05)
    delta = payload.get("delta", 0.02)
    n_min = min_sample(p_bar, delta)
    metrics = payload.get("metrics") or {}
    ctrs, better = {}, None
    for k in keys:
        m = metrics.get(k)
        if m and m.get("曝光"):
            ctr = m["点击"] / m["曝光"] * 100
            ctrs[k] = {"曝光": m["曝光"], "点击": m["点击"], "CTR": round(ctr, 2)}
    verdict = "未提供 CTR 数据，仅输出实验设计"
    if ctrs and n_min:
        under = [k for k, v in ctrs.items() if v["曝光"] < n_min]
        spread = max(v["曝光"] for v in ctrs.values()) / max(1, min(v["曝光"] for v in ctrs.values()))
        if under:
            verdict = f"⚠️ 样本不足（{ '、'.join(under) } < {n_min}），只报值不下结论"
        elif spread > 3:
            verdict = "⚠️ 曝光分布不均（>3:1），先排查渠道再判优"
        else:
            top = max(ctrs.items(), key=lambda kv: kv[1]["CTR"])
            low = min(ctrs.items(), key=lambda kv: kv[1]["CTR"])
            diff = round(top[1]["CTR"] - low[1]["CTR"], 2)
            if diff > delta * 100:
                better = top[0]
                verdict = f"✅ 样本充足，{top[0]} 版 CTR 高 {diff}pp，建议采用 {top[0]}"
            else:
                verdict = f"⚪ 样本充足但差值 {diff}pp ≤ 阈值 {round(delta*100,1)}pp，无显著差异，保持原版"

    checks = [
        {"检查项": "变体数 ≥ 2", "结果": "✅" if len(variants) >= 2 else "🔴", "说明": f"当前 {len(variants)} 个"},
        {"检查项": "角度互异（无重复角度）", "结果": "✅" if not dup_angle else "🔴",
         "说明": "无重复" if not dup_angle else "存在重复角度，违反角度互异"},
        {"检查项": "两两 Jaccard < 0.6（无同质化）", "结果": "✅" if not same_pairs else "🔴",
         "说明": "全部达标" if not same_pairs else "同质化对：" + "、".join(same_pairs)},
        {"检查项": "字数全部合规", "结果": "✅" if all(r["字数合规"] == "✅" for r in rows) else "🔴",
         "说明": f"上限 {limit} {unit}"},
        {"检查项": "无绝对化/导流/虚假促销", "结果": "✅" if not banned_all else "🔴",
         "说明": f"{len(banned_all)} 个变体命中" if banned_all else "无命中"},
    ]

    summary = {
        "目标平台": platform, "变体数": len(variants), "被改写卖点": payload.get("selling_point", "（未指定）"),
        "每组最小曝光": n_min, "经验点击率 p̄": f"{round(p_bar*100,1)}%", "期望提升 Δ": f"{round(delta*100,1)}pp",
        "实验结论": verdict,
    }

    at.ensure_outdir(outdir)
    exp_rows = [{"项": k, "值": str(v)} for k, v in summary.items()]
    if ctrs:
        exp_rows += [{"项": f"变体 {k} CTR", "值": f'{v["CTR"]}%（{v["点击"]}/{v["曝光"]}）'}
                     for k, v in ctrs.items()]

    xlsx = at.write_excel(
        os.path.join(outdir, "AB变体矩阵.xlsx"),
        {"变体组": rows, "差异度矩阵": matrix, "实验设计": exp_rows, "校验": checks},
        highlights={"变体组": {"字数合规": "contains:🔴", "无违禁词": "contains:🔴"},
                    "校验": {"结果": "contains:🔴"}},
        widths={"变体组": {"文案": 44}, "差异度矩阵": {"变体": 8}},
    )
    js = at.write_json(
        {"summary": summary, "variants": rows, "similarity_matrix": matrix, "checks": checks,
         "same_pairs": same_pairs, "banned_detail": banned_all,
         "generated_at": at.stamp(),
         "note": "相似度/字数/样本量为脚本计算；变体撰写与角度选择须由模型按 prompt.txt 完成"},
        os.path.join(outdir, "variant_matrix.json"),
    )
    return {"files": [xlsx, js], "summary": summary, "variants": len(variants),
            "same_pairs": same_pairs, "verdict": verdict}


def main():
    ap = argparse.ArgumentParser(description="A/B 文案变体 —— 差异度与实验校验")
    ap.add_argument("--input")
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
    print(f"变体 {r['variants']} 个，同质化对 {len(r['same_pairs'])} —— {r['verdict']}")
    for f in r["files"]:
        print(" 产物:", f)
    at.emit(r)


if __name__ == "__main__":
    main()
