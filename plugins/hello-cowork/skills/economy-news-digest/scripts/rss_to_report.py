#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
경제뉴스 RSS -> CSV + 기업별 호재/악재 보고서 자동화 파서
- 입력: ./feeds/*.xml  (web_fetch로 받아 저장한 RSS XML들)
- 출력:
    out/news_YYYYMMDD.csv       (기사 원본 정리)
    out/analysis_YYYYMMDD.csv   (기업별 호재/악재 집계)
    out/report_YYYYMMDD.md      (마크다운 보고서)

주의: 이 스크립트는 네트워크에 직접 접속하지 않는다.
RSS 수집은 web_fetch가 담당하고, 이 스크립트는 저장된 XML만 파싱한다.
"""
import os, re, csv, glob, html, datetime
import xml.etree.ElementTree as ET

# 작업 폴더: 인자 > 환경변수 NEWS_DIR > 스크립트 위치 순으로 결정 (스킬 이식성)
import sys
BASE = (sys.argv[1] if len(sys.argv) > 1 else
        os.environ.get("NEWS_DIR") or
        os.path.dirname(os.path.abspath(__file__)))
FEED_DIR = os.path.join(BASE, "feeds")
OUT_DIR = os.path.join(BASE, "out")
os.makedirs(OUT_DIR, exist_ok=True)

TODAY = datetime.date.today().strftime("%Y%m%d")

# 파일명(소스 식별) -> 표시용 매체명
SOURCE_NAMES = {
    "hankyung_economy": "한국경제(경제)",
    "edaily_all": "이데일리(종합)",
    "edaily_stock": "이데일리(주식/펀드)",
}

# ---- 호재/악재 사전 (가중치) ----
POS = {
    "흑자전환":3, "흑자 전환":3, "사상 최대":3, "최대 실적":3, "역대급 실적":3,
    "신고가":3, "사상 최고":3, "상한가":3, "최단기":2,
    "수주":2, "공급계약":2, "납품 계약":2, "납품계약":2, "공급 계약":2, "계약 체결":2,
    "수출":2, "흑자":2, "호실적":2, "실적 개선":2, "수익성 개선":2, "호조":2,
    "자사주 소각":2, "자기주식 소각":2, "자사주 매입":2, "주주환원":2, "배당 확대":2, "배당확대":2,
    "투자 유치":2, "전략 투자":2, "전략적 투자":2, "유상증자":1,
    "협약":1, "MOU":1, "파트너십":1, "협력":1, "재계약":1, "맞손":1, "협업":1,
    "인수":1, "확보":1, "확대":1, "출시":1, "신제품":1, "승인":1, "허가":1, "선임":1,
    "급등":2, "돌파":1, "쾌거":2, "수상":1, "1위":1,
}
NEG = {
    "급락":3, "폭락":3, "적자":3, "영업손실":3, "순손실":3, "어닝쇼크":3,
    "반대매매":3, "구속영장":3, "구속":2, "횡령":3, "배임":3, "분식":3,
    "상장폐지":3, "거래정지":3, "부도":3, "디폴트":3, "감자":3,
    "압수수색":2, "소송":2, "고소":2, "고발":2, "제재":2, "과징금":2, "징계":2,
    "리콜":2, "결함":2, "철수":2, "사업 종료":2, "패소":2, "반려":2, "손배소":2,
    "실적 부진":2, "부진":1, "하락":1, "하향":2, "급감":2, "순매도":1, "매도":1,
    "주식병합":1, "병합":1, "감액":2, "손실":2, "위기":2, "악재":2, "리스크":1,
    "사망":2, "사고":1, "논란":1, "의혹":1, "송치":2, "처벌":2, "실형":2,
}

# ---- 주요 기업 사전 (티커 없는 기사 매칭용) ----
KNOWN = [
    "삼성전자","SK하이닉스","LG전자","LG화학","현대차","현대자동차","기아","네이버","카카오",
    "하이브","HYBE","셀트리온","포스코","KB금융","신한","하나금융","우리은행","국민은행",
    "농심","오뚜기","롯데칠성","롯데백화점","롯데마트","롯데","남양유업","풀무원","하이트진로",
    "미래에셋증권","삼성증권","NH투자증권","고려아연","영풍","펄어비스","현대홈쇼핑","홈플러스",
    "티웨이항공","파라타항공","유진그룹","한화","삼성웰스토리","YG플러스","하림","MBK","엔에스홈쇼핑",
    "애플","구글","퀄컴","브로드컴","마벨","ASML","혼다","벤츠","지피클럽","코스콤","인텔리빅스",
    "테크윙","테고사이언스","유바이오로직스","비아트론","에이팩트","옵티코어","스피어","태성",
]

EMOJI = {"호재": "🟢", "악재": "🔴", "중립": "⚪"}
VERDICT_EMOJI = {"호재 우위": "🟢", "악재 우위": "🔴", "혼조/중립": "⚪"}

TICKER_RE = re.compile(r"([가-힣A-Za-z0-9·\.]{2,20}?)\((\d{6})\)")

def clean(t):
    if t is None: return ""
    return html.unescape(re.sub(r"\s+", " ", t)).strip()

def source_key(path):
    name = os.path.splitext(os.path.basename(path))[0]
    return name

def parse_feed(path):
    items = []
    try:
        tree = ET.parse(path)
    except Exception as e:
        print(f"[warn] {path} 파싱 실패: {e}")
        return items
    root = tree.getroot()
    skey = source_key(path)
    src = SOURCE_NAMES.get(skey, skey)
    for it in root.iter("item"):
        title = clean(it.findtext("title"))
        link = clean(it.findtext("link"))
        desc = clean(it.findtext("description"))
        pub = clean(it.findtext("pubDate"))
        author = clean(it.findtext("author"))
        cat = clean(it.findtext("category"))
        if not title:
            continue
        items.append({
            "source": src, "title": title, "link": link,
            "desc": desc, "pubDate": pub, "author": author, "category": cat,
        })
    return items

def extract_companies(text):
    """티커 패턴 + 사전 매칭으로 기업명 추출"""
    found = {}
    for m in TICKER_RE.finditer(text):
        name = m.group(1).strip(" ·.")
        # 너무 일반적인 접두 제거
        name = re.sub(r"^(주|㈜)\s*", "", name)
        if len(name) >= 2:
            found[name] = m.group(2)
    for k in KNOWN:
        if k in text and k not in found:
            found[k] = ""
    return found  # {기업명: 티커 or ""}

def score_text(text):
    pos_hits, neg_hits = [], []
    pscore = nscore = 0
    for kw, w in POS.items():
        if kw in text:
            pos_hits.append(kw); pscore += w
    for kw, w in NEG.items():
        if kw in text:
            neg_hits.append(kw); nscore += w
    if pscore > nscore and pscore > 0:
        label = "호재"
    elif nscore > pscore and nscore > 0:
        label = "악재"
    else:
        label = "중립"
    return label, pscore, nscore, pos_hits, neg_hits

def main():
    feeds = sorted(glob.glob(os.path.join(FEED_DIR, "*.xml")))
    all_items = []
    for f in feeds:
        all_items.extend(parse_feed(f))
    print(f"수집 기사 수: {len(all_items)}  (피드 {len(feeds)}종)")

    # 1) 기사 원본 CSV
    news_csv = os.path.join(OUT_DIR, f"news_{TODAY}.csv")
    news_rows = []
    with open(news_csv, "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.writer(fp)
        w.writerow(["출처","발행일시","제목","관련기업","판정","호재/악재","근거키워드","링크"])
        for a in all_items:
            text = a["title"] + " " + a["desc"]
            comps = extract_companies(text)
            label, ps, ns, ph, nh = score_text(text)
            comp_str = ", ".join(
                (f"{c}({t})" if t else c) for c, t in comps.items()
            )
            evid = ", ".join((ph if label=="호재" else nh if label=="악재" else (ph+nh)))
            w.writerow([a["source"], a["pubDate"], a["title"], comp_str,
                        EMOJI[label], label, evid, a["link"]])
            news_rows.append({**a, "label": label, "comps": comp_str, "evid": evid})

    # 2) 기업별 집계
    agg = {}  # 기업 -> dict
    for a in all_items:
        text = a["title"] + " " + a["desc"]
        comps = extract_companies(text)
        if not comps:
            continue
        label, ps, ns, ph, nh = score_text(text)
        for c, t in comps.items():
            d = agg.setdefault(c, {"ticker": t, "호재":0,"악재":0,"중립":0,
                                   "articles":[], "pos_kw":set(), "neg_kw":set()})
            if t and not d["ticker"]:
                d["ticker"] = t
            d[label] += 1
            d["pos_kw"].update(ph); d["neg_kw"].update(nh)
            d["articles"].append((label, a["title"], a["source"], a["link"]))

    def net(d):
        return d["호재"] - d["악재"]

    rows = sorted(agg.items(), key=lambda kv: (net(kv[1]), kv[1]["호재"]+kv[1]["악재"]), reverse=True)

    ana_csv = os.path.join(OUT_DIR, f"analysis_{TODAY}.csv")
    with open(ana_csv, "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.writer(fp)
        w.writerow(["판정","기업","티커","종합판정","호재건수","악재건수","중립건수","핵심근거","대표기사","대표기사링크"])
        for c, d in rows:
            n = net(d)
            verdict = "호재 우위" if n>0 else "악재 우위" if n<0 else "혼조/중립"
            ev = ", ".join(sorted(d["pos_kw"])[:4] + sorted(d["neg_kw"])[:4]) or "-"
            rep = d["articles"][0][1] if d["articles"] else ""
            rep_link = d["articles"][0][3] if d["articles"] else ""
            w.writerow([VERDICT_EMOJI[verdict], c, d["ticker"], verdict,
                        d["호재"], d["악재"], d["중립"], ev, rep, rep_link])

    # 3) 마크다운 보고서 자동 생성 (이모지 + 링크 포함 baseline)
    md = build_report(all_items, news_rows, rows, agg)
    rep_md = os.path.join(OUT_DIR, f"report_{TODAY}.md")
    with open(rep_md, "w", encoding="utf-8") as fp:
        fp.write(md)

    print(f"저장: {news_csv}")
    print(f"저장: {ana_csv}")
    print(f"저장: {rep_md}")
    print(f"분석 기업 수: {len(agg)}")
    return news_csv, ana_csv, rep_md, len(all_items), len(agg)


def build_report(all_items, news_rows, rows, agg):
    def net(d): return d["호재"] - d["악재"]
    pos = [(c,d) for c,d in rows if net(d) > 0]
    neg = [(c,d) for c,d in rows if net(d) < 0]
    neu = [(c,d) for c,d in rows if net(d) == 0]
    sources = sorted({a["source"] for a in all_items})
    ymd = datetime.date.today().strftime("%Y-%m-%d")

    L = []
    L.append(f"# 경제뉴스 호재/악재 데일리 리포트\n")
    L.append(f"**생성일:** {ymd}  ")
    L.append(f"**소스:** {' · '.join(sources)}  ")
    L.append(f"**수집 기사:** {len(all_items)}건 · **분석 기업:** {len(agg)}개 "
             f"(🟢 호재 우위 {len(pos)} · 🔴 악재 우위 {len(neg)} · ⚪ 중립 {len(neu)})\n")
    L.append("> 범례: 🟢 호재 · 🔴 악재 · ⚪ 중립 — 키워드 사전 기반 1차 분류이며 투자 자문이 아니다.\n")

    # --- 요약 + 핵심 인사이트 (통계 기반 자동 생성) ---
    from collections import Counter
    pos_kw = Counter()
    for c, d in pos:
        pos_kw.update(d["pos_kw"])
    top_theme = pos_kw.most_common(1)[0][0] if pos_kw else "-"
    market_flags = [a for a in all_items if any(k in a["title"] for k in ("코스피","코스닥","외국인","순매도"))]
    L.append("## 요약\n")
    L.append(f"수집 기사 {len(all_items)}건에서 기업 {len(agg)}개를 분류한 결과 "
             f"🟢 호재 우위 {len(pos)}개, 🔴 악재 우위 {len(neg)}개, ⚪ 중립 {len(neu)}개로 집계됐다. "
             f"가장 많이 등장한 호재 신호는 '{top_theme}'이며, "
             f"시장 지표(코스피·수급) 관련 기사는 {len(market_flags)}건 감지됐다. "
             "개별 종목 호재와 시장 전반 흐름을 구분해 볼 필요가 있다.\n")
    L.append("## 핵심 인사이트\n")
    L.append(f"- 🟢 호재 신호 최다 테마는 '{top_theme}' 계열이다. 호재 우위 기업 {len(pos)}곳 중 다수가 공급계약·수주·실적 개선에서 비롯됐다.")
    L.append(f"- 🔴 악재 우위 기업은 {len(neg)}곳으로, 급락·소송·주식병합 등 성격이 서로 다르므로 개별 확인이 필요하다.")
    if market_flags:
        L.append(f"- ⚠️ 시장 지표 기사 {len(market_flags)}건 감지 — 지수·수급 환경은 개별 호재와 별개로 점검할 것.")
    L.append("- 주식병합·상장 주관사 매칭 등 일부 항목은 키워드 분류의 한계가 있어 수기 검토가 권장된다.\n")

    L.append("## 🟢 호재 우위 기업\n")
    L.append("| 판정 | 기업 | 티커 | 호재/악재 | 핵심근거 | 대표기사 |")
    L.append("|---|---|---|---|---|---|")
    for c, d in pos:
        a = d["articles"][0]
        ev = ", ".join(sorted(d["pos_kw"])[:3]) or "-"
        L.append(f"| 🟢 | {c} | {d['ticker'] or '-'} | {d['호재']}/{d['악재']} | {ev} | [{a[1][:40]}]({a[3]}) |")

    L.append("\n## 🔴 악재 우위 기업\n")
    L.append("| 판정 | 기업 | 티커 | 호재/악재 | 핵심근거 | 대표기사 |")
    L.append("|---|---|---|---|---|---|")
    for c, d in neg:
        a = d["articles"][0]
        ev = ", ".join(sorted(d["neg_kw"])[:3]) or "-"
        L.append(f"| 🔴 | {c} | {d['ticker'] or '-'} | {d['호재']}/{d['악재']} | {ev} | [{a[1][:40]}]({a[3]}) |")

    L.append("\n## ⚪ 중립/혼조 기업\n")
    L.append("| 판정 | 기업 | 티커 | 대표기사 |")
    L.append("|---|---|---|---|")
    for c, d in neu:
        a = d["articles"][0]
        L.append(f"| ⚪ | {c} | {d['ticker'] or '-'} | [{a[1][:40]}]({a[3]}) |")

    # --- 📈 티커별 주가 동향 (korean-stock-search 연동) ---
    tickers = {}
    for c, d in rows:
        if d["ticker"]:
            tickers[d["ticker"]] = c
    prices = {}
    pjson = os.path.join(BASE, "prices.json")
    if os.path.exists(pjson):
        import json
        try:
            prices = json.load(open(pjson, encoding="utf-8"))
        except Exception:
            prices = {}
    meta = prices.get("_meta", {}) if prices else {}
    bas = meta.get("bas_dd", "")
    L.append("\n## 📈 티커별 주가 동향\n")
    if bas:
        L.append(f"*기준일: {bas} · 출처: {meta.get('source','KRX')} (일별 종가, 실시간 아님)*\n")
    if tickers:
        L.append("| 뉴스판정 | 종목 | 티커 | 종가(원) | 전일대비 | 등락률 | 추세 |")
        L.append("|---|---|---|---|---|---|---|")
        for tk, name in tickers.items():
            verdict_e = "🟢" if any(net(d) > 0 for c, d in rows if d["ticker"] == tk) else \
                        "🔴" if any(net(d) < 0 for c, d in rows if d["ticker"] == tk) else "⚪"
            p = prices.get(tk, {})
            close = p.get("close", "—")
            diff = p.get("diff", "—")
            rate = p.get("rate", "—")
            trend = p.get("trend", "—")
            L.append(f"| {verdict_e} | {name} | {tk} | {close} | {diff} | {rate} | {trend} |")
        if not [k for k in prices if k != "_meta"]:
            L.append("\n> ⓘ 주가 데이터 미연동 상태. `korean-stock-search`(moai-finance)로 위 티커를 조회해 "
                     "`prices.json`을 채우면 표가 자동 완성된다.")
        else:
            # 뉴스 판정 vs 주가 방향 괴리 탐지
            div = []
            for tk, name in tickers.items():
                p = prices.get(tk, {})
                rate = p.get("rate", "")
                up = rate.startswith("+")
                down = rate.startswith("-")
                v = "🟢" if any(net(d) > 0 for c, d in rows if d["ticker"] == tk) else \
                    "🔴" if any(net(d) < 0 for c, d in rows if d["ticker"] == tk) else "⚪"
                if v == "🔴" and up:
                    div.append(f"{name}(뉴스 악재 · 주가 {rate})")
                elif v == "🟢" and down:
                    div.append(f"{name}(뉴스 호재 · 주가 {rate})")
            L.append("\n> 🟢/🔴/⚪ = 뉴스 호재/악재 판정. 뉴스 판정과 당일 주가 방향은 다를 수 있다.")
            if div:
                L.append(f">\n> ⚠️ **판정-주가 괴리:** {', '.join(div)} — 뉴스 톤과 시장 반응이 엇갈린 사례다.")
    else:
        L.append("티커가 식별된 종목이 없다.")

    L.append("\n## 전체 기사 (판정 · 링크)\n")
    for a in news_rows:
        e = EMOJI[a["label"]]
        comp = f" — {a['comps']}" if a["comps"] else ""
        L.append(f"- {e} [{a['title']}]({a['link']}){comp}  *({a['source']})*")

    L.append("\n---\n*본 리포트는 투자 자문이 아니며 공개 기사 기반 정보 정리 목적이다.*")
    return "\n".join(L)

if __name__ == "__main__":
    main()
