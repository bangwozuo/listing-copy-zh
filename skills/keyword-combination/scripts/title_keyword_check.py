# -*- coding: utf-8 -*-
"""关键词组合 —— 标题字数 / 位置 / 密度 / 违规词精确校验器。

职责边界：本脚本做**确定性计算**（字符数、核心词位置、词元重复、违禁词命中），
这是机器不会算错的强项。**词分层、语义相关性、KD 判断**由模型按 prompt.txt 完成。

用法：
  python title_keyword_check.py --input input.json --outdir out
  python title_keyword_check.py --demo
  python title_keyword_check.py --text "保温杯 304不锈钢 500ml" --platform 淘宝 --core-word 保温杯

产物：
  out/标题关键词校验.xlsx   标题校验 / 关键词布局 / 汇总
  out/keyword_check.json    机器可读结果（供智能体读取）
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

# 平台 → (计数单位, 上限)
PLATFORM_LIMITS = {
    "淘宝": ("字符", 60),
    "天猫": ("字符", 60),
    "抖音": ("字", 30),
    "拼多多": ("字符", 60),
    "小红书": ("字", 20),
    "Amazon": ("字符", 200),
    "通用": ("字符", 60),
}

# 核心词起始位次超过此值即判「核心词未前置」
CORE_HEAD_POS = 10

# 同义词归并：同一词元的多个写法，重复出现即词元内耗
SYNONYM_GROUPS = [
    ("便携", "轻便", "轻盈"),
    ("保温", "保暖", "恒温"),
    ("不漏", "防漏", "密封"),
]

# 《广告法》第九条绝对化用语（标题高频子集）
BANNED = [
    (r"最(好|佳|优|强|低|便宜|先进|流行|受欢迎|高档|高级|顶级|优质)", "绝对化·最高级"),
    (r"(第一|TOP\s*1|No\.?\s*1|冠军|之王|领导者|领导品牌)", "绝对化·排名"),
    (r"(唯一|独家|首创|首个|首款|绝无仅有|空前绝后|前所未有)", "绝对化·唯一性"),
    (r"(国家级|世界级|全球级|顶级|极品|极佳|绝佳|终极|极致|巅峰|至尊)", "绝对化·级别"),
    (r"(100\s*%|百分百|彻底|根治|根除|永不|毫无|绝对安全|无任何副作用)", "绝对化·功效断言"),
]

DEMO = {
    "platform": "淘宝",
    "core_word": "保温杯",
    "product_info": {
        "品名": "304 不锈钢真空保温杯",
        "材质": "304 不锈钢内胆 + 316 不锈钢外壳",
        "规格": "500ml / 杯高 21cm",
        "卖点": ["12 小时保温", "带茶隔", "杯盖密封不漏"],
        "场景": ["办公室", "通勤", "车载"],
    },
    "keywords": [
        {"词": "保温杯", "层级": "核心词"},
        {"词": "带茶隔保温杯", "层级": "长尾词"},
        {"词": "大容量女款", "层级": "长尾词"},
        {"词": "办公室水杯", "层级": "场景词"},
        {"词": "车载焖烧杯", "层级": "蓝海词"},
    ],
    "candidate_titles": [
        "保温杯 304不锈钢 500ml 办公室便携带茶隔",
        "带茶隔保温杯 大容量女款 500ml 304不锈钢 通勤车载",
        "2026新款保温杯大容量办公室学生便携水杯不漏水焖烧杯",
        "全网最低价保温杯 100%保温 销量第一 独家304不锈钢",
    ],
    "category_words_to_avoid": ["手机壳", "数据线", "充电宝"],
}


# ---------------------------------------------------------------- 计算

def char_count(text: str, unit: str) -> int:
    """字符=含空格全长度；字=不含空格的可见字符数。"""
    if unit == "字":
        return len(text.replace(" ", ""))
    return len(text)


def core_head_position(title: str, core_word: str) -> int:
    """核心词起始位次（1 基）。找不到返回 -1。"""
    if not core_word:
        return -1
    i = title.find(core_word)
    return i + 1 if i >= 0 else -1


def count_occurrences(title: str, word: str) -> int:
    return title.count(word) if word else 0


def synonym_conflicts(title: str):
    """返回标题内命中的同义词组（同组出现 ≥2 个不同写法即冲突）。"""
    hits = []
    for group in SYNONYM_GROUPS:
        found = [w for w in group if w in title]
        if len(found) >= 2:
            hits.append("、".join(found))
    return hits


def scan_banned(title: str):
    hits = []
    for pat, rule in BANNED:
        for m in re.finditer(pat, title):
            hits.append({"片段": m.group(0), "规则": rule})
    return hits


def check_title(payload, title: str):
    platform = payload.get("platform", "通用")
    unit, limit = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS["通用"])
    core = payload.get("core_word") or ""
    kws = payload.get("keywords", [])
    avoid = payload.get("category_words_to_avoid", [])

    n = char_count(title, unit)
    pos = core_head_position(title, core)
    over = [w for w in avoid if w in title]
    banned = scan_banned(title)
    syn = synonym_conflicts(title)

    reps = {k["词"]: count_occurrences(title, k["词"]) for k in kws
            if isinstance(k, dict) and k.get("词")}

    ok_len = n <= limit
    ok_head = 10 >= pos >= 1
    ok_dup = all(v <= 1 for v in reps.values()) and not syn
    ok_rel = not over
    ok_ban = not banned
    verdict = "可用" if all([ok_len, ok_head, ok_dup, ok_rel, ok_ban]) else "需修改"

    return {
        "标题": title,
        "字数": n,
        "上限": limit,
        "单位": unit,
        "占上限": f"{round(n / limit * 100)}%",
        "核心词": core or "（未指定）",
        "核心词位置": pos if pos > 0 else "未命中",
        "字数合规": "✅" if ok_len else "🔴 超限",
        "核心词前置": "✅" if ok_head else ("🟡 未前置" if pos > 0 else "🔴 未命中"),
        "无重复词": "✅" if ok_dup else "🟡 词元内耗",
        "无无关词": "✅" if ok_rel else "🔴 蹭流量词",
        "无违禁词": "✅" if ok_ban else "🔴 违禁词",
        "结论": verdict,
        "_banned": banned,
        "_over": over,
        "_rep": {k: v for k, v in reps.items() if v > 1},
    }


def keyword_layout(payload):
    core = payload.get("core_word") or ""
    rows = []
    for k in payload.get("keywords", []):
        if not isinstance(k, dict):
            continue
        word, layer = k.get("词", ""), k.get("层级", "长尾词")
        if layer == "核心词" or word == core:
            kd, pos, cnt = "必争", "标题前 10 字符 + 五点首条", 1
        elif layer == "蓝海词":
            kd, pos, cnt = "≤ 0.2", "详情页小标题 + 卖点尾部（不进标题）", 1
        elif layer == "场景词":
            kd, pos, cnt = "≤ 0.5", "标题中段 + 详情页场景段", 1
        else:
            kd, pos, cnt = "≤ 0.5", "标题中后段 + 五点描述", 1
        rows.append({"关键词": word, "层级": layer, "KD 区间": kd,
                     "建议位置": pos, "建议出现次数": cnt})
    return rows


# ---------------------------------------------------------------- 主流程

def run(payload, outdir):
    titles = payload.get("candidate_titles") or payload.get("titles") or []
    if not titles:
        raise ValueError("缺少 candidate_titles：请提供 3 个左右待校验标题。")

    checks = [check_title(payload, t) for t in titles]
    layout = keyword_layout(payload)

    usable = [c for c in checks if c["结论"] == "可用"]
    best = usable[0] if usable else None
    summary = {
        "目标平台": payload.get("platform", "通用"),
        "字数上限": f'{PLATFORM_LIMITS.get(payload.get("platform", "通用"), PLATFORM_LIMITS["通用"])[1]}'
                    f'{PLATFORM_LIMITS.get(payload.get("platform", "通用"), PLATFORM_LIMITS["通用"])[0]}',
        "候选数": len(checks),
        "可用数": len(usable),
        "推荐标题": best["标题"] if best else "（无——全部候选需修改）",
        "推荐字数": best["字数"] if best else "—",
        "核心词": payload.get("core_word", "（未指定）"),
    }

    at.ensure_outdir(outdir)
    xlsx_rows = [{k: v for k, v in c.items() if not k.startswith("_")} for c in checks]
    xlsx = at.write_excel(
        os.path.join(outdir, "标题关键词校验.xlsx"),
        {
            "标题校验": xlsx_rows,
            "关键词布局": layout or [{"关键词": "（无）"}],
            "汇总": [{"项": k, "内容": str(v)} for k, v in summary.items()],
        },
        highlights={"标题校验": {"字数合规": "contains:🔴",
                                "核心词前置": "contains:🔴",
                                "无无关词": "contains:🔴",
                                "无违禁词": "contains:🔴"}},
        widths={"标题校验": {"标题": 46, "结论": 10}},
    )
    js = at.write_json(
        {
            "summary": summary,
            "title_checks": xlsx_rows,
            "keyword_layout": layout,
            "banned_detail": [{"标题": c["标题"], "命中": c["_banned"]} for c in checks if c["_banned"]],
            "generated_at": at.stamp(),
            "note": "字数/位置/重复/违禁词为脚本精确计算；词分层与 KD 须由模型按 prompt.txt 复核",
        },
        os.path.join(outdir, "keyword_check.json"),
    )
    return {"files": [xlsx, js], "summary": summary, "checks": len(checks), "usable": len(usable)}


def main():
    ap = argparse.ArgumentParser(description="关键词组合 —— 标题与关键词校验")
    ap.add_argument("--input", help="输入 JSON")
    ap.add_argument("--text", help="直接传标题（配合 --platform/--core-word）")
    ap.add_argument("--platform", default="通用")
    ap.add_argument("--core-word", default="")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    if a.demo:
        payload = DEMO
    elif a.input:
        payload = at.read_json(a.input)
    elif a.text:
        payload = {"platform": a.platform, "core_word": a.core_word, "candidate_titles": [a.text]}
    else:
        ap.error("需要 --input / --text / --demo 之一")

    r = run(payload, a.outdir)
    print(f"校验 {r['checks']} 个候选，可用 {r['usable']} 个 —— 推荐：{r['summary']['推荐标题']}")
    for f in r["files"]:
        print(" 产物:", f)
    at.emit(r)


if __name__ == "__main__":
    main()
