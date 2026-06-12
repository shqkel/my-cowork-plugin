# my-cowork-plugin

Cowork 플러그인을 모아 배포하는 **마켓플레이스** 저장소다.
하나의 마켓플레이스 안에 여러 플러그인을 담을 수 있고, 각 플러그인은 스킬·MCP 서버·에이전트 등으로 Claude의 기능을 확장한다.

## 폴더 구조

```
my-cowork-plugin/
├── .claude-plugin/
│   └── marketplace.json        # 마켓플레이스 매니페스트 (플러그인 목록)
├── plugins/
│   └── hello-cowork/           # 플러그인 1개 (예시)
│       ├── .claude-plugin/
│       │   └── plugin.json     # 플러그인 매니페스트
│       ├── skills/
│       │   └── greeting/
│       │       └── SKILL.md    # 스킬 1개
│       └── README.md
├── README.md
└── .gitignore
```

핵심 규칙은 두 가지다. 마켓플레이스 매니페스트(`marketplace.json`)는 반드시 저장소 최상위 `.claude-plugin/` 안에 있어야 하고,
각 플러그인은 자기 폴더 안에 별도의 `.claude-plugin/plugin.json` 을 가진다.

## marketplace.json

마켓플레이스의 이름, 소유자, 그리고 담고 있는 플러그인 목록을 정의한다.
새 플러그인을 만들면 이 파일의 `plugins` 배열에 한 항목을 추가하면 된다.

```json
{
  "name": "my-cowork-plugin",
  "owner": { "name": "동현", "email": "shqkel1863@gmail.com" },
  "metadata": { "description": "동현의 Cowork 플러그인 마켓플레이스", "version": "0.1.0" },
  "plugins": [
    {
      "name": "hello-cowork",
      "source": "./plugins/hello-cowork",
      "description": "마켓플레이스 구조 검증용 예시 플러그인"
    }
  ]
}
```

- `name` — 마켓플레이스 식별자 (kebab-case)
- `owner` — 소유자 정보
- `plugins[].source` — 플러그인 폴더의 상대 경로
- `plugins[].name` — 플러그인 이름 (해당 플러그인의 `plugin.json` 의 `name` 과 일치)

## 새 플러그인 추가하기

1. `plugins/hello-cowork` 폴더를 복사해 `plugins/<새-플러그인-이름>` 으로 만든다.
2. 새 폴더의 `.claude-plugin/plugin.json` 에서 `name`·`description` 을 수정한다.
3. `skills/<스킬-이름>/SKILL.md` 를 작성한다. SKILL.md 앞머리(frontmatter)에는 `name` 과,
   언제 이 스킬을 써야 하는지 알려 주는 `description`(트리거 문구 포함)을 넣는다.
4. 최상위 `.claude-plugin/marketplace.json` 의 `plugins` 배열에 새 플러그인을 등록한다.

## 설치해서 써 보기

이 저장소를 GitHub에 올린 뒤, Cowork 또는 Claude Code에서 마켓플레이스로 등록한다.

```bash
/plugin marketplace add <GitHub-사용자명>/my-cowork-plugin
/plugin install hello-cowork@my-cowork-plugin
```

## 진행 메모

- 초기 저장소 세팅 완료 (README, .gitignore)
- 마켓플레이스 구조 추가 (marketplace.json + 예시 플러그인 hello-cowork)
- hello-cowork에 economy-news-digest 스킬 추가 (경제뉴스 호재/악재 데일리 다이제스트)
