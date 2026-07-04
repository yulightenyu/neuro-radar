#!/usr/bin/env python3
"""Neuro Radar — 阿尔茨海默病前沿资讯
 - PubMed E-utilities 五路检索，无需 key
 - DeepSeek 生成中文摘要（专业/口语）+ 自动证据分级
环境变量：DEEPSEEK_API_KEY
"""
import json, datetime, time, traceback, re, os
import urllib.request, urllib.parse

CFG = json.load(open("config.json", encoding="utf-8"))
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = {"User-Agent": "neuro-radar/1.0 (research aggregator)"}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def esearch(term, retmax):
    q = urllib.parse.urlencode({
        "db": "pubmed", "term": term, "retmax": retmax,
        "sort": "date", "retmode": "json",
    })
    d = json.loads(_get(EUTILS + "/esearch.fcgi?" + q))
    return d["esearchresult"]["idlist"]


def efetch(pmids):
    if not pmids:
        return []
    q = urllib.parse.urlencode({
        "db": "pubmed", "id": ",".join(pmids),
        "retmode": "xml", "rettype": "abstract",
    })
    xml = _get(EUTILS + "/efetch.fcgi?" + q).decode("utf-8", "ignore")
    out = []
    for blk in re.findall(r"<PubmedArticle>.*?</PubmedArticle>", xml, re.S):
        def tag(name):
            m = re.search(r"<%s[^>]*>(.*?)</%s>" % (name, name), blk, re.S)
            return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
        pmid = tag("PMID")
        import html as _html; title = _html.unescape(" ".join(tag("ArticleTitle").split()))
        abst = " ".join(re.sub(r"<[^>]+>", " ",
                       " ".join(re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", blk, re.S))).split())
        journal = tag("Title") or tag("ISOAbbreviation")
        year = tag("Year")
        month = tag("Month")
        if not title:
            continue
        out.append({
            "pmid": pmid, "title": title, "abstract": abst[:1200],
            "journal": journal[:40], "year": year, "month": month,
            "link": "https://pubmed.ncbi.nlm.nih.gov/%s/" % pmid,
        })
    return out


def _ds_call(prompt, max_tokens=120, temperature=0.3):
    if not DS_KEY:
        return ""
    body = json.dumps({
        "model": CFG["deepseek"]["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature, "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(
        CFG["deepseek"]["base_url"], data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + DS_KEY})
    try:
        r = urllib.request.urlopen(req, timeout=40)
        d = json.loads(r.read())
        return " ".join(d["choices"][0]["message"]["content"].split())
    except Exception:
        traceback.print_exc()
        return ""


GRADES = {"META", "RCT", "COHORT", "CASE", "ANIMAL", "INVITRO", "REVIEW", "OTHER"}

def deepseek_grade(title, abstract):
    if not DS_KEY:
        return ""
    prompt = (
        "判断下面这篇阿尔茨海默病论文属于哪种研究类型，只能从以下标签里选一个，"
        "直接输出这个英文标签，不要任何其它字：\n"
        "META（荟萃分析/系统综述）、RCT（随机对照试验）、COHORT（队列/前瞻观察）、"
        "CASE（病例报告/横断面）、ANIMAL（动物实验）、INVITRO（细胞/体外）、"
        "REVIEW（普通综述/叙述性）、OTHER（其它或无法判断）。\n\n"
        "标题：%s\n摘要：%s" % (title, abstract[:600])
    )
    out = _ds_call(prompt, max_tokens=8, temperature=0).upper()
    for g in GRADES:
        if g in out:
            return g
    return "OTHER"


def deepseek_summary(title, abstract, style="pro"):
    if not DS_KEY:
        return ""
    if style == "plain":
        prompt = (
            "你是科普作者，要把一篇阿尔茨海默病的综述讲给完全没有医学背景的普通人听。"
            "请用一句大白话中文（25-50字）说清这篇综述在讲什么、对外行有什么用，"
            "避免专业术语，必须出现的术语用最简单的方式带过。"
            "只输出这句话，不要前缀、引号或解释。\n\n"
            "标题：%s\n摘要：%s" % (title, abstract[:800])
        )
    else:
        prompt = (
            "你是神经科学领域的医学编辑。下面是一篇阿尔茨海默病相关论文的标题和摘要，"
            "请用一句话中文（20-45字）点破它的核心发现或结论，让专业读者扫一眼就能判断要不要深入读。"
            "只输出这句话，不要任何前缀、引号或解释。\n\n"
            "标题：%s\n摘要：%s" % (title, abstract[:800])
        )
    return _ds_call(prompt, max_tokens=120)[:80]


def main():
    result = {}
    stats = {}
    for feed in CFG["feeds"]:
        items = []
        try:
            pmids = esearch(feed["term"], CFG["retmax"])
            time.sleep(0.4)
            items = efetch(pmids)
            time.sleep(0.4)
        except Exception:
            traceback.print_exc()
        st = feed.get("style", "pro")
        for it in items:
            it["zh"] = deepseek_summary(it["title"], it["abstract"], st)
            it["evidence"] = deepseek_grade(it["title"], it["abstract"])
            it.pop("abstract", None)
            time.sleep(0.2)
        result[feed["id"]] = items
        stats[feed["id"]] = len(items)
    data = {
        "updated": datetime.datetime.utcnow().isoformat() + "Z",
        "feeds": CFG["feeds"],
        "items": result,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("done | " + " ".join("%s=%d" % (k, v) for k, v in stats.items()) +
          " | deepseek=%s" % ("on" if DS_KEY else "OFF"))


if __name__ == "__main__":
    main()
