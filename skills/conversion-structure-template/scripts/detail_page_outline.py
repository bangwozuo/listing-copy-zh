# -*- coding: utf-8 -*-
"""转化结构模板 —— 详情页 / A+ 页面模块结构与合规校验器。

职责边界：本脚本做**结构规则校验**（模块数区间、A+ 必备模块、首屏字数、对比表红线、
模块文案违禁词）与产物生成。**模块创意与文案撰写**由模型按 prompt.txt 完成。

用法：
  python detail_page_outline.py --input input.json --outdir out
  python detail_page_outline.py --demo

产物：
  out/详情页结构.xlsx   模块结构 / 对比表 / 校验 / 汇总
  out/detail_page.json  机器可读结果
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

MODULE_MIN, MODULE_MAX = 6, 10
FIRST_SCREEN_LIMIT = 120           # 前 3 屏字数上限
DEFAULT_FIRST_SCREEN_N = 3

# A+ 页面必备模块
APLUS_REQUIRED = ["品牌故事", "对比表", "场景图"]

BANNED_TEXT = [
    (r"最(好|佳|优|强|低|便宜|先进|流行|受欢迎|高档|高级|顶级|优质)", "绝对化·最高级"),
    (r"(第一|TOP\s*1|冠军|之王|领导者)", "绝对化·排名"),
    (r"(唯一|独家|首创|首个|首款)", "绝对化·唯一性"),
    (r"(国家级|世界级|顶级|极品|极致)", "绝对化·级别"),
    (r"(100\s*%|百分百|彻底|根治|永不|绝对)", "绝对化·功效断言"),
    (r"(二维码|微信号|加微信|扫码|私信领)", "站外导流"),
]

# 对比表红线：竞品/贬低
TABLE_REDLINE = [
    (r"(竞品|同行|其他品牌|别家)", "提及竞品（平台可能判影射）", "W"),
    (r"(比\s*[^，。|]{1,8}(好|强|便宜)|碾压|吊打|智商税|秒杀同款)", "贬低竞品", "R"),
]

DEMO = {
    "platform": "Amazon",
    "brief": {
        "品类": "304 不锈钢真空保温杯",
        "品牌": "MUGGO",
        "核心卖点": ["12 小时保温", "带茶隔", "杯盖密封倒置不漏", "316 外壳"],
        "目标人群": ["办公室白领", "通勤族"],
        "本店 SKU": ["500ml 保温款", "350ml 迷你款", "700ml 焖烧款"]
    },
    "modules": [
        {"模块": "主图区", "功能定位": "首屏抓眼", "建议字数": 12, "素材状态": "✅", "文案": "MUGGO 保温杯 12 小时保温"},
        {"模块": "痛点共鸣", "功能定位": "建立共鸣", "建议字数": 48, "素材状态": "🟡", "文案": "早上的热水，到了下午就凉了？办公室一杯热茶常喝常凉。"},
        {"模块": "卖点图文", "功能定位": "差异化卖点", "建议字数": 52, "素材状态": "🟡", "文案": "304 不锈钢内胆 + 真空层，实测 500ml 热水 12 小时后 ≥55℃。"},
        {"模块": "场景图", "功能定位": "场景代入", "建议字数": 18, "素材状态": "🟡", "文案": "通勤、办公、车载，随时一杯温水。"},
        {"模块": "品牌故事", "功能定位": "建立信任", "建议字数": 110, "素材状态": "🟡", "文案": "MUGGO 专注饮水器具，坚持食品级用料与出厂逐只测漏。"},
        {"模块": "对比表", "功能定位": "店内导购", "建议字数": 0, "素材状态": "✅", "文案": "—"},
        {"模块": "规格表", "功能定位": "参数如实", "建议字数": 0, "素材状态": "✅", "文案": "—"},
        {"模块": "售后承诺", "功能定位": "降风险", "建议字数": 30, "素材状态": "✅", "文案": "杯盖密封件质保 12 个月，质量问题免费补寄。"}
    ],
    "sku_table": [
        {"参数": "容量", "本店 500ml 保温款": "500ml", "本店 350ml 迷你款": "350ml", "本店 700ml 焖烧款": "700ml"},
        {"参数": "保温时长", "本店 500ml 保温款": "12h", "本店 350ml 迷你款": "8h", "本店 700ml 焖烧款": "12h"},
        {"参数": "内胆材质", "本店 500ml 保温款": "304 不锈钢", "本店 350ml 迷你款": "304 不锈钢", "本店 700ml 焖烧款": "316 不锈钢"},
        {"参数": "带茶隔", "本店 500ml 保温款": "是", "本店 350ml 迷你款": "否", "本店 700ml 焖烧款": "是"},
    ],
}


# ---------------------------------------------------------------- 校验

def scan_banned(text):
    hits = []
    for pat, rule in BANNED_TEXT:
        for m in re.finditer(pat, str(text)):
            hits.append({"片段": m.group(0), "规则": rule})
    return hits


def check_modules(modules):
    names = [m.get("模块", "") for m in modules]
    n = len(modules)
    issues = []
    checks = []

    checks.append({"检查项": "模块数在 6–10", "结果": "✅" if MODULE_MIN <= n <= MODULE_MAX else "🔴",
                   "说明": f"当前 {n} 个"})

    missing_required = [r for r in APLUS_REQUIRED if not any(r in x for x in names)]
    checks.append({"检查项": "A+ 必备模块齐全", "结果": "✅" if not missing_required else "🔴",
                   "说明": "缺：" + "、".join(missing_required) if missing_required else "品牌故事/对比表/场景图 均有"})

    first_n = modules[:DEFAULT_FIRST_SCREEN_N]
    first_chars = sum(int(m.get("建议字数", 0) or 0) for m in first_n)
    checks.append({"检查项": f"首屏（前 {DEFAULT_FIRST_SCREEN_N} 模块）字数 ≤ {FIRST_SCREEN_LIMIT}",
                   "结果": "✅" if first_chars <= FIRST_SCREEN_LIMIT else "🟡",
                   "说明": f"当前 {first_chars} 字"})

    banned = []
    for m in modules:
        for h in scan_banned(m.get("文案", "")):
            banned.append({"模块": m.get("模块", ""), **h})
    checks.append({"检查项": "模块文案无绝对化/导流", "结果": "✅" if not banned else "🔴",
                   "说明": f"{len(banned)} 处" if banned else "无命中"})

    if missing_required:
        issues.append("缺 A+ 必备模块：" + "、".join(missing_required))
    if not (MODULE_MIN <= n <= MODULE_MAX):
        issues.append(f"模块数 {n} 超出 6–10 区间")
    if first_chars > FIRST_SCREEN_LIMIT:
        issues.append(f"首屏字数 {first_chars} 超 {FIRST_SCREEN_LIMIT}")
    if banned:
        issues.append("模块文案含违禁词，须先过广告法预审")

    return checks, issues, banned


def check_table(sku_table):
    if not sku_table:
        return [{"检查项": "对比表无竞品/贬低", "结果": "🔵", "说明": "未提供对比表"}], []
    text = " ".join(str(v) for row in sku_table for v in row.values())
    hits = []
    for pat, rule, lv in TABLE_REDLINE:
        for m in re.finditer(pat, text):
            hits.append({"片段": m.group(0), "规则": rule, "级别": lv})
    ok = not any(h["级别"] == "R" for h in hits)
    res = {"检查项": "对比表无竞品/贬低",
           "结果": "✅" if ok and not hits else ("🟡" if ok else "🔴"),
           "说明": "无命中" if not hits else "；".join(f'{h["片段"]}({h["规则"]})' for h in hits)}
    return [res], hits


# ---------------------------------------------------------------- 主流程

def run(payload, outdir):
    modules = payload.get("modules") or []
    if not modules:
        raise ValueError("缺少 modules：请提供详情页模块结构（可由模型按 prompt.txt 生成）。")
    sku_table = payload.get("sku_table") or []

    mod_checks, issues, banned = check_modules(modules)
    tab_checks, tab_hits = check_table(sku_table)
    checks = mod_checks + tab_checks

    rows = []
    for i, m in enumerate(modules, 1):
        rows.append({
            "#": i,
            "模块": m.get("模块", ""),
            "功能定位": m.get("功能定位", ""),
            "建议字数": m.get("建议字数", 0),
            "素材状态": m.get("素材状态", ""),
            "文案": m.get("文案", ""),
        })

    summary = {
        "目标平台": payload.get("platform", "通用"),
        "模块数": len(modules),
        "A+ 必备模块": "齐全" if not [r for r in APLUS_REQUIRED
                                     if not any(r in m.get("模块", "") for m in modules)] else "缺失",
        "校验通过项": sum(1 for c in checks if c["结果"] == "✅"),
        "校验总项": len(checks),
        "待整改": len(issues),
    }

    at.ensure_outdir(outdir)
    xlsx = at.write_excel(
        os.path.join(outdir, "详情页结构.xlsx"),
        {
            "模块结构": rows,
            "对比表": sku_table or [{"参数": "（未提供）"}],
            "校验": checks,
            "汇总": [{"项": k, "内容": str(v)} for k, v in summary.items()],
        },
        highlights={"校验": {"结果": "contains:🔴"}},
        widths={"模块结构": {"文案": 46, "功能定位": 14}, "校验": {"说明": 40}},
    )
    js = at.write_json(
        {
            "summary": summary,
            "modules": rows,
            "structure_map": sku_table,
            "checks": checks,
            "issues": issues,
            "banned_in_copy": banned,
            "table_redline_hits": tab_hits,
            "generated_at": at.stamp(),
            "note": "模块数/必备模块/首屏字数/对比表红线为脚本规则校验；模块创意须由模型按 prompt.txt 产出",
        },
        os.path.join(outdir, "detail_page.json"),
    )
    return {"files": [xlsx, js], "summary": summary, "issues": issues}


def main():
    ap = argparse.ArgumentParser(description="转化结构模板 —— 详情页/A+ 结构校验")
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
    print(f"模块数 {r['summary']['模块数']}，校验通过 {r['summary']['校验通过项']}/{r['summary']['校验总项']}，待整改 {r['summary']['待整改']}")
    for f in r["files"]:
        print(" 产物:", f)
    at.emit(r)


if __name__ == "__main__":
    main()
