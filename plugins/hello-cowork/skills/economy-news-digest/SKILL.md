---
name: economy-news-digest
description: |
  경제뉴스 RSS를 받아 CSV로 정리하고, 기사에 등장하는 기업별 호재/악재/중립을 근거와 함께
  분류해 마크다운 보고서(이모지·기사 링크 포함)를 생성하는 스킬이다. moai-finance:korean-stock-search가
  설치돼 있으면 기사에 나온 티커의 KRX 일별 시세(종가·등락률)도 표로 첨부한다.

  다음 상황에서 반드시 사용한다:
  - "경제뉴스 정리해줘", "오늘 경제뉴스 호재 악재 분석해줘"
  - "뉴스 RSS 받아서 CSV로 만들어줘", "기업별 호재 악재 보고서 만들어줘"
  - "경제뉴스 데일리 리포트", "증시 뉴스 요약 + 주가 동향"
  - "이 종목들 뉴스에 호재야 악재야", "뉴스 기반 종목 브리핑"
  - RSS/뉴스 + (호재 | 악재 | CSV | 보고서 | 주가 | 티커) 키워드 조합 시
user-invocable: true
version: 1.0.0
---

# 경제뉴스 호재/악재 데일리 다이제스트

경제뉴스 RSS를 수집해 ① 기사 원본 CSV, ② 기업별 호재/악재 집계 CSV, ③ 이모지·링크가 포함된
마크다운 보고서를 생성한다. 선택적으로 KRX 일별 시세를 티커별로 붙인다.

## 산출물
- `out/news_YYYYMMDD.csv` — 기사별 출처·발행일·제목·관련기업·판정(🟢/🔴/⚪)·근거키워드·링크
- `out/analysis_YYYYMMDD.csv` — 기업별 호재/악재/중립 집계·핵심근거·대표기사 링크
- `out/report_YYYYMMDD.md` — 요약 1문단 + 핵심 인사이트 + 호재/악재/중립 표 + 📈 티커별 주가 동향 + 전체 기사 링크

## 사용 방법 (Claude가 수행하는 절차)

작업 폴더(예: 사용자가 고른 폴더)를 `WORK` 라고 하자. 스크립트는 `scripts/rss_to_report.py` 에 있다.

### 1) RSS 수집 — 반드시 web_fetch로만
아래 피드를 web_fetch로 받아 `WORK/feeds/<소스키>.xml` 로 저장한다. (python/curl 직접 다운로드 금지)

| 소스키 | 매체 | URL |
|---|---|---|
| hankyung_economy | 한국경제(경제) | https://www.hankyung.com/feed/economy |
| edaily_stock | 이데일리(주식/펀드) | https://rss.edaily.co.kr/stock_news.xml |
| edaily_all | 이데일리(종합) | https://rss.edaily.co.kr/edaily_news.xml |

받은 XML 본문을 그대로 저장한다. 연합뉴스·매일경제·네이버 RSS는 web_fetch 차단 대상이므로 시도하지 않는다.
다른 경제 피드를 추가하려면 `WORK/feeds/<이름>.xml` 로 저장하면 자동 인식된다.
(소스 표시명은 `scripts/rss_to_report.py` 의 `SOURCE_NAMES` 에 등록하면 보고서에 예쁘게 나온다.)

### 2) 파싱·보고서 생성
```bash
python3 scripts/rss_to_report.py "WORK"
```
(인자로 작업 폴더를 넘긴다. 생략 시 환경변수 NEWS_DIR, 둘 다 없으면 스크립트 위치를 사용.)
→ `out/` 에 CSV 2종과 report MD가 생성된다. 보고서엔 🟢 호재 / 🔴 악재 / ⚪ 중립 이모지와 기사 링크가 자동 포함된다.

### 3) (선택) 티커별 주가 동향 — moai-finance:korean-stock-search 필요
`out/analysis_YYYYMMDD.csv` 의 '티커' 열에 있는 6자리 종목코드를 모두 조회한다.
korean-stock-search 의 trade-info 엔드포인트를 web_fetch로 호출한다 (market은 KOSPI→실패 시 KOSDAQ 재시도):
```
https://k-skill-proxy.nomadamas.org/v1/korean-stock/trade-info?market=KOSPI&code=005930&bas_dd=YYYYMMDD
```
각 종목의 close_price / change_price / fluctuation_rate 를 받아 `WORK/prices.json` 을 아래 형식으로 저장한다:
```json
{
  "_meta": {"bas_dd": "2026-06-11", "source": "KRX 공식(k-skill-proxy)"},
  "005930": {"close": "299,000", "diff": "-3,500", "rate": "-1.16%", "trend": "🔻"}
}
```
trend 아이콘: 상승 🔺 / 하락 🔻 / 보합·거래없음 ⏸️. 그런 다음 2)의 스크립트를 다시 실행하면
보고서의 '📈 티커별 주가 동향' 표가 자동으로 채워지고, 뉴스 판정과 주가 방향이 엇갈린 종목도 표시된다.
korean-stock-search 가 없으면 이 단계를 건너뛰고 표는 '미연동' 상태로 둔다.

### 4) 오분류 보정
`out/analysis_YYYYMMDD.csv` 를 검토해 키워드 사전이 놓친 항목을 보정한다. 자주 나오는 케이스:
- 띄어쓰기 변형: '자사주 216만주 소각' → 호재 (사전은 '자사주 소각' 연속 매칭만 잡음)
- 반어/문맥, 상장 주관사가 발행사 기사에 과대 매칭되는 경우
필요 시 report MD를 직접 수정한다.

### 5) 공유
report MD, analysis CSV, news CSV 를 present_files로 공유하고, 🟢 호재 우위 / 🔴 악재 우위 기업 수와
그날의 가장 큰 테마 한 줄을 요약해 알린다.

## 매일 자동화
schedule 스킬로 위 절차를 매일 아침 실행하도록 등록할 수 있다. (cron 예: `0 7 * * *`)

## 분류 사전 커스터마이즈
`scripts/rss_to_report.py` 의 `POS`(호재)·`NEG`(악재) 딕셔너리와 `KNOWN`(주요 기업명) 리스트를 편집해
업종·관심사에 맞게 조정한다. 가중치(숫자)가 높을수록 강한 신호다.

## 주의
- RSS 수집·주가 조회는 반드시 web_fetch로만 한다 (정책상 curl/python 직접 다운로드 금지).
- 투자 자문이 아니라 공개 기사·KRX 공식 시세 기반 정보 정리 목적이다.
- 정치적 입장 표명·개인정보 처리는 하지 않는다.
