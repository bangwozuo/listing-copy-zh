# -*- coding: utf-8 -*-
"""广告法合规预审 —— 四类规则分级扫描器。

职责边界：本脚本做**词表精确扫描与产物生成**（机器的强项，不漏不猜）。
语境判断、误报排除、替换写法撰写由模型按 prompt.txt 完成（模型的强项）。

用法：
  python adlaw_scan.py --input input.json --outdir out
  python adlaw_scan.py --demo
  python adlaw_scan.py --text "全网最低价" --platform 淘宝 --category 化妆品

产物：
  out/广告法预审清单.xlsx   违规清单 / 需补材料 / 汇总
  out/adlaw_scan.json       机器可读结果（供智能体读取）
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


# ---------------------------------------------------------------- 词表
# 每条：(正则, 级别, 规则名, 依据, 建议改法)   级别 R=红线 W=警告 I=提示

ABSOLUTE = [
    (r"最(好|佳|优|强|低|便宜|先进|流行|受欢迎|高档|高级|顶级|优质|低)",
     "R", "绝对化·最高级", "《广告法》第九条", "改用具体描述，如「2026 年新款」「店铺热销」"),
    (r"(第一|TOP\s*1|top\s*1|No\.?\s*1|冠军|之王|领导者|领导品牌|销量冠军|排名第\s*一)",
     "R", "绝对化·排名", "《广告法》第九条", "删除排名表述，或改「店铺热销单品」并注明数据来源与口径"),
    (r"(唯一|独家|首创|首个|首款|绝无仅有|空前绝后|前所未有)",
     "R", "绝对化·唯一性", "《广告法》第九条", "删除；有专利可改「已获专利 ZL…」（附专利号）"),
    (r"(国家级|世界级|全球级|顶级|极品|极佳|绝佳|终极|极致|巅峰|至尊)",
     "R", "绝对化·级别", "《广告法》第九条", "删除级别词，改用可验证的客观参数"),
    (r"(100\s*%|百分百|彻底|根治|根除|永不|毫无|绝对安全|无任何副作用)",
     "R", "绝对化·功效断言", "《广告法》第九条", "改有条件表述，如「实测反馈良好（样本 30 人）」"),
]

CATEGORY_WORDS = {
    "化妆品": [
        (r"(治疗|疗效|消炎|杀菌|抗敏|药妆|医学级|医美级|药用|处方|修复痘印|祛斑|美白针)",
         "R", "化妆品·医疗宣称", "《化妆品监督管理条例》第 22 条",
         "删除医疗类表述，改「护理」「舒缓」等非医疗用词"),
    ],
    "食品": [
        (r"(降血压|降血糖|降血脂|抗癌|排毒|壮阳|治疗|防癌|补血|养颜)",
         "R", "食品·疾病治疗宣称", "《食品安全法》第 73 条", "删除功效宣称，仅描述口味、原料、工艺"),
    ],
    "保健品": [
        (r"(治愈|替代药物|无副作用|疗效)", "R", "保健品·疗效宣称",
         "不得宣称疾病预防治疗功能", "删除；注册保健食品可标「本品不能代替药物」"),
    ],
    "医疗器械": [
        (r"(根治|痊愈|包治|无风险)", "R", "医疗器械·疗效断言", "需附注册证号",
         "删除；改为「适用于…（详见注册证适用范围）」"),
    ],
    "母婴": [
        (r"(最安全|绝对安全)", "R", "母婴·安全断言", "《广告法》第九条", "改「通过 XX 标准检测」并附报告"),
        (r"(无添加|零添加)", "I", "母婴·无添加宣称", "需检测报告支撑", "补充第三方检测报告编号"),
        (r"(防过敏|抗过敏)", "I", "母婴·防过敏宣称", "需检测报告支撑", "补充皮肤测试报告编号"),
    ],
    "教育": [
        (r"(保过|包过|包就业|100\s*%?\s*提分|名师)", "R", "教育·效果保证", "《广告法》第 24 条",
         "删除保证性表述；持证教师可标「教师资质：XX」"),
    ],
    "金融": [
        (r"(保本|稳赚|零风险|保收益|日入过万|稳赚不赔)", "R", "金融·收益保证", "《广告法》第 25 条",
         "删除收益承诺，加「投资有风险，入市需谨慎」"),
    ],
}

UNFAIR = [
    (r"(好评返现|晒图返|好评送|五星返现|返\s*\d+\s*元)", "R", "诱导评价", "《反不正当竞争法》第八条",
     "删除返现话术；用真实售后回访替代"),
    (r"(比\s*[^，。！]{1,8}(好|强|便宜)|碾压|吊打|秒杀同款|智商税|比同行)",
     "R", "贬低竞品", "《反不正当竞争法》第十一条", "删除对比竞品的贬低表述，改为客观参数对比"),
    (r"(平替\s*[^，。]{1,10}|同款\s*[A-Za-z]{2,})", "W", "未授权品牌词", "《商标法》/平台规则",
     "删除他人品牌名；如已获授权须附授权书"),
    (r"(专利产品|专利配方|已申请专利)(?![^，。]{0,12}ZL)", "W", "专利虚标", "《广告法》第十二条",
     "补专利号「ZL…」，无号则删除专利表述"),
    (r"(仅此一天|最后一天|限时抢购|清仓价|全网最低|历史最低价)", "W", "虚假促销", 
     "《禁止价格欺诈行为的规定》", "确认活动真实并注明起止时间"),
    (r"(纯天然|无添加|零添加)(?![^，。]{0,12}(报告|检测))", "I", "无添加宣称", "需检测报告支撑",
     "补充第三方检测报告编号"),
]

PLATFORM_RULES = {
    "淘宝": [(r"(二维码|微信号|加微信|VX|vx|扫码|加群|私信领)", "R", "淘宝·站外导流",
              "淘宝内容规范：禁站外导流", "删除导流信息，避免扣分")],
    "天猫": [(r"(二维码|微信号|加微信|微信|扫码)", "R", "天猫·站外导流", "天猫内容规范", "删除导流信息")],
    "抖音": [(r"(二维码|微信号|加微信|扫码)", "R", "抖音·站外导流", "抖音电商规则", "删除导流信息")],
    "小红书": [(r"(二维码|微信号|加微信|私信领|点赞领|加群)", "R", "小红书·导流",
                "小红书社区规范：禁导流", "改「评论区留言交流」，不发联系方式")],
    "拼多多": [(r"(二维码|微信号|加微信|扫码)", "R", "拼多多·站外导流", "拼多多规则", "删除导流信息")],
    "通用": [(r"(二维码|微信号|加微信|扫码|私信领)", "R", "通用·站外导流", "各平台通用规范", "删除导流信息")],
}

DEMO = {
    "platform": "淘宝",
    "category": "化妆品",
    "text": ("【全网最低价】医美级精华液，100%彻底淡化痘印，效果最好的抗敏修复神器！"
             "国家级实验室研发，独家配方，销量第一。好评返现 5 元，加微信 xxx 领试用装，扫码进群。"
             "比 XX 大牌好用，专利配方，纯天然无添加，本品适用于各类肌肤，无任何副作用。"),
}


# ---------------------------------------------------------------- 扫描

def scan(text, platform, category, extra_rules=None):
    rules = list(ABSOLUTE) + CATEGORY_WORDS.get(category, []) + UNFAIR
    rules += PLATFORM_RULES.get(platform, PLATFORM_RULES["通用"])
    if extra_rules:
        rules += [(re.escape(w), "W", "用户自定义词表", "用户指定", "按用户规则复核") for w in extra_rules]

    hits, seen = [], set()
    for pattern, level, rule, basis, fix in rules:
        for m in re.finditer(pattern, text):
            key = (m.span(), rule)
            if key in seen:
                continue
            seen.add(key)
            hits.append({
                "级别": {"R": "🔴 红线", "W": "🟡 警告", "I": "🔵 提示"}[level],
                "_lvl": level,
                "违规词/表述": m.group(0),
                "原文片段": _snippet(text, m.start(), m.end()),
                "位置": f"第 {m.start() + 1} 字符",
                "命中规则": rule,
                "依据": basis,
                "修改建议": fix,
            })
    order = {"R": 0, "W": 1, "I": 2}
    hits.sort(key=lambda h: (order[h["_lvl"]], h["位置"]))
    return hits


def _snippet(text, s, e, pad=6):
    a, b = max(0, s - pad), min(len(text), e + pad)
    return ("…" if a > 0 else "") + text[a:b] + ("…" if b < len(text) else "")


def summarize(hits, n_chars, platform):
    n = {"R": 0, "W": 0, "I": 0}
    for h in hits:
        n[h["_lvl"]] += 1
    verdict = "不建议上架" if n["R"] else ("修改后上架" if n["W"] else "通过")
    return {
        "受检平台": platform,
        "受检文本量": f"{n_chars} 字",
        "红线": n["R"],
        "警告": n["W"],
        "提示": n["I"],
        "总体结论": verdict,
    }


# ---------------------------------------------------------------- 主流程

def run(payload, outdir):
    text = payload.get("text", "")
    if not text:
        raise ValueError("缺少 text：请提供待检文案。")
    platform = payload.get("platform", "通用")
    category = payload.get("category", "")
    hits = scan(text, platform, category, payload.get("rules"))
    summary = summarize(hits, len(text), platform)

    rows = [{k: v for k, v in h.items() if not k.startswith("_")} for h in hits]
    need = [{"表述": h["违规词/表述"], "需提供的材料": h["修改建议"]}
            for h in hits if h["_lvl"] == "I"]
    suggestions = _suggestions(hits)

    at.ensure_outdir(outdir)
    xlsx = at.write_excel(
        os.path.join(outdir, "广告法预审清单.xlsx"),
        {
            "违规清单": rows or [{"级别": "（无）", "违规词/表述": "", "命中规则": "", "依据": "",
                                 "修改建议": ""}],
            "需补材料": need or [{"表述": "—", "需提供的材料": "—"}],
            "整体建议": [{"#": i + 1, "建议": s} for i, s in enumerate(suggestions)],
            "汇总": [{"项": k, "内容": str(v)} for k, v in summary.items()],
        },
        highlights={"违规清单": {"级别": "contains:红线"}},
        widths={"违规清单": {"原文片段": 26, "命中规则": 20, "依据": 26, "修改建议": 40}},
    )
    js = at.write_json(
        {
            "summary": summary,
            "violations": rows,
            "need_material": need,
            "suggestions": suggestions,
            "generated_at": at.stamp(),
            "note": "词表机器扫描结果；语境判断与误报排除须由模型按 prompt.txt 复核",
        },
        os.path.join(outdir, "adlaw_scan.json"),
    )
    return {"files": [xlsx, js], "summary": summary, "hit_count": len(hits)}


def _suggestions(hits):
    rules = {h["命中规则"] for h in hits}
    out = []
    if any("绝对化" in r for r in rules):
        out.append("删除全部绝对化用语，改用具体描述或注明数据来源与口径（《广告法》第九条）。")
    if any("医疗宣称" in r for r in rules):
        out.append("化妆品/食品类删除医疗与功效宣称，只描述原料、工艺、使用感受。")
    if any("导流" in r for r in rules):
        out.append("删除微信号/二维码/扫码等站外导流信息，避免平台扣分。")
    if any(r in ("诱导评价",) for r in rules):
        out.append("删除好评返现/晒图返现话术；售后回访走平台内渠道。")
    if any(r in ("贬低竞品", "未授权品牌词") for r in rules):
        out.append("删除与竞品的贬低性对比及未授权品牌词，改为客观参数对比。")
    if any(r in ("专利虚标", "无添加宣称") for r in rules):
        out.append("补齐专利号/检测报告编号，无法提供的删除对应表述。")
    if not out:
        out.append("未发现需整改项；上架前仍建议对照平台官方最新规范二次确认。")
    return out


def main():
    ap = argparse.ArgumentParser(description="广告法合规预审 —— 四类规则分级扫描")
    ap.add_argument("--input", help="输入 JSON（text/platform/category/rules）")
    ap.add_argument("--text", help="直接传文本")
    ap.add_argument("--platform", default="通用")
    ap.add_argument("--category", default="")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    if a.demo:
        payload = DEMO
    elif a.input:
        payload = at.read_json(a.input)
    elif a.text:
        payload = {"text": a.text, "platform": a.platform, "category": a.category}
    else:
        ap.error("需要 --input / --text / --demo 之一")

    r = run(payload, a.outdir)
    print(f"命中 {r['hit_count']} 项 —— 判定：{r['summary']['总体结论']}")
    for f in r["files"]:
        print(" 产物:", f)
    at.emit(r)


if __name__ == "__main__":
    main()
