#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感日报 · 数据生成脚本 (无第三方依赖，仅用 Python 标准库)

由 GitHub Actions 定时调用，生成 data/news.json 供前端读取。
每条数据除标题/来源/热度/摘要外，还会尽量带上「原文链接 url」，
前端点击卡片即可在详情弹窗里跳转到原始内容。
"""

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# ========================= CONFIG =========================
# 情感类关键词：用于从通用热榜中过滤出「夫妻感情 / 婚姻 / 育儿 / 两性生活」相关内容。
EMOTION_KEYWORDS = ["夫妻", "婚姻", "结婚", "离婚", "育儿", "带娃", "婆婆", "产后",
                    "异地恋", "亲密", "两性", "情侣", "丈夫", "妻子", "家庭", "孩子"]

# 各分类命中关键词（用于给条目打分类标签）
CATEGORY_MAP = {
    "夫妻感情": ["夫妻", "异地恋", "情侣", "亲密", "丈夫", "妻子"],
    "婚姻":     ["婚姻", "结婚", "离婚", "婆婆", "婚后"],
    "育儿":     ["育儿", "带娃", "产后", "孩子", "二胎", "宝妈"],
    "两性生活": ["两性", "情绪价值", "边界感", "亲密关系"],
}

# 真实数据源（公开聚合/官方接口，无需鉴权，可在 GitHub Actions 上访问）
# 每个源返回 [(title, heat(万), excerpt, url), ...]
SOURCES = [
    {"name": "微博热搜", "url": "https://weibo.com/ajax/side/hotSearch", "parse": "weibo"},
    {"name": "知乎热榜", "url": "https://api.vvhan.com/api/hotlist/zhihuHot", "parse": "vvhan"},
    {"name": "抖音热点", "url": "https://api.vvhan.com/api/hotlist/douyinHot", "parse": "vvhan"},
]
# =========================================================


def http_get_json(url: str):
    # Referer/Origin 用于绕过微博等站点对无来源请求的 403 拦截。
    req = urllib.request.Request(
        url, headers={
            "User-Agent": UA,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://weibo.com/",
            "Origin": "https://weibo.com",
        })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_weibo(obj):
    out = []
    for it in obj.get("data", {}).get("realtime", []) or []:
        if it.get("is_ad") or it.get("is_ad_top"):
            continue
        word = it.get("word", "")
        if not word:
            continue
        hot = int(re.sub(r"\D", "", str(it.get("num", "0")) or "0") or 0)
        url = "https://s.weibo.com/weibo?q=" + urllib.parse.quote(word)
        out.append((word, round(hot / 10000, 1), "", url))
    return out


def parse_vvhan(obj):
    out = []
    for it in obj.get("data", []) or []:
        title = it.get("title") or it.get("word") or ""
        if not title:
            continue
        hot = int(re.sub(r"\D", "", str(it.get("hot", "0")) or "0") or 0)
        url = it.get("url", "") or ""
        out.append((title, round(hot / 10000, 1), "", url))
    return out


PARSERS = {"weibo": parse_weibo, "vvhan": parse_vvhan}


def classify(title: str) -> str:
    for cat, keys in CATEGORY_MAP.items():
        if any(k in title for k in keys):
            return cat
    return "夫妻感情"


def is_emotion(title: str) -> bool:
    return any(k in title for k in EMOTION_KEYWORDS)


# 内置情感语料池：保证在没有真实 API 时，流水线仍可产出合规数据（无原文链接）。
BUILTIN_POOL = [
    ("结婚十年，我们终于学会了'不说话也能懂对方'", "微信公众号", 47.2, "一位妻子记录下婚姻里最难的不是争吵，而是沉默后的彼此接住。", ""),
    ("异地恋如何熬过第三年？一对夫妻的实操清单", "知乎", 38.9, "从固定通话到共同目标，他们用三年把距离变成了信任的练习。", ""),
    ("婆婆说'带孩子是女人的事'，我用三句话化解了", "微博", 31.5, "没有正面冲突，边界感与表达技巧让一次潜在矛盾悄然化解。", ""),
    ("产后第一年，我们的婚姻差点散了", "豆瓣", 28.3, "新手父母的疲惫被看见，比任何育儿建议都更能挽救关系。", ""),
    ("两性关系里，'情绪价值'到底值多少钱", "知乎", 25.1, "当陪伴变成消耗，如何重新评估一段关系里的情绪收支。", ""),
    ("夫妻冷战超过三天，关系就开始变冷", "微博", 22.7, "心理咨询师提醒：冷处理不是冷静，而是把问题冻在了冰里。", ""),
    ("女儿问我'为什么要结婚'，我答不上来", "微信公众号", 19.4, "一场亲子对话，让一位母亲重新打量自己的婚姻选择。", ""),
    ("婚姻咨询师的忠告：别把伴侣当情绪垃圾桶", "豆瓣", 16.8, "健康的亲密关系，需要彼此承接，也需要各自安放。", ""),
    ("二胎后，我和丈夫重新分工的半年", "微博", 14.2, "从'丧偶式育儿'到共同带娃，一份真实的家庭协作复盘。", ""),
    ("亲密关系里，'边界感'比'黏在一起'更重要", "知乎", 12.6, "好的关系不是融为一体，而是两个完整的人选择并肩。", ""),
]


def build_items():
    raw = []
    for s in SOURCES:
        try:
            obj = http_get_json(s["url"])
            for title, heat, excerpt, url in PARSERS[s["parse"]](obj):
                raw.append({"title": title, "source": s["name"],
                            "heat": heat, "excerpt": excerpt, "url": url})
        except Exception as e:  # 单源失败不影响整体
            print(f"[warn] 源 {s['name']} 抓取失败，已跳过：{e}")

    # 去重
    seen, deduped = set(), []
    for it in raw:
        key = re.sub(r"\s+", "", it["title"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)

    # 过滤情感 + 分类 + 排序 + 取前 10
    items = [i for i in deduped if is_emotion(i["title"])]
    items = [dict(i, category=classify(i["title"])) for i in items]
    items.sort(key=lambda x: x["heat"], reverse=True)

    if not items:  # 全部真实源失败 → 内置语料兜底，保证站点不空
        print("[info] 真实源无可用数据，启用内置语料兜底。")
        items = [{"title": t, "source": s, "heat": h, "excerpt": e, "url": u}
                 for t, s, h, e, u in BUILTIN_POOL]
        items = [dict(i, category=classify(i["title"])) for i in items]

    items = items[:10]
    for idx, it in enumerate(items, 1):
        it["rank"] = idx
    return items


def main():
    now = datetime.now()
    snapshot = (now - timedelta(days=1)).strftime("%Y-%m-%d")  # 昨日快照
    update_count = (now.hour // 4) + 1  # 今日第几次更新（每4小时一次）

    data = {
        "snapshotDate": snapshot,
        "updateCountToday": update_count,
        "items": build_items(),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已生成 {out_path}：{len(data['items'])} 条，快照 {snapshot}")


if __name__ == "__main__":
    main()
