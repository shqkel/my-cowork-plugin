# hello-cowork

마켓플레이스 구조가 제대로 동작하는지 확인하기 위한 가장 작은 예시 플러그인이다.

## 구성

```
hello-cowork/
├── .claude-plugin/
│   └── plugin.json          # 플러그인 매니페스트 (이름·버전·설명)
├── skills/
│   ├── greeting/
│   │   └── SKILL.md         # "안녕", "인사해줘" 등에 반응하는 인사 스킬
│   └── economy-news-digest/
│       ├── SKILL.md         # 경제뉴스 호재/악재 데일리 다이제스트 스킬
│       └── scripts/
│           └── rss_to_report.py
└── README.md
```

## 포함 스킬

- `greeting` — "안녕", "플러그인 테스트"에 반응해 인사하고 마켓플레이스 동작을 확인한다.
- `economy-news-digest` — 경제뉴스 RSS를 호재/악재/중립으로 분류해 CSV·마크다운 보고서를 생성한다. ("오늘 경제뉴스 호재 악재 분석해줘" 등)

## 이 플러그인을 복제해 새 플러그인 만들기

1. `plugins/hello-cowork` 폴더를 통째로 복사해 `plugins/<새-플러그인-이름>` 으로 만든다.
2. `.claude-plugin/plugin.json` 의 `name`·`description` 을 새 이름에 맞게 바꾼다.
3. `skills/` 아래에 필요한 스킬을 추가하거나 수정한다.
4. 저장소 최상위 `.claude-plugin/marketplace.json` 의 `plugins` 배열에 새 플러그인을 등록한다.
