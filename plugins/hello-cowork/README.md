# hello-cowork

마켓플레이스 구조가 제대로 동작하는지 확인하기 위한 가장 작은 예시 플러그인이다.

## 구성

```
hello-cowork/
├── .claude-plugin/
│   └── plugin.json          # 플러그인 매니페스트 (이름·버전·설명)
├── skills/
│   └── greeting/
│       └── SKILL.md         # "안녕", "인사해줘" 등에 반응하는 인사 스킬
└── README.md
```

## 동작

이 플러그인을 설치한 뒤 Claude에게 "안녕" 또는 "플러그인 테스트"라고 말하면,
`greeting` 스킬이 호출되어 인사와 함께 마켓플레이스가 정상 동작 중임을 알려 준다.

## 이 플러그인을 복제해 새 플러그인 만들기

1. `plugins/hello-cowork` 폴더를 통째로 복사해 `plugins/<새-플러그인-이름>` 으로 만든다.
2. `.claude-plugin/plugin.json` 의 `name`·`description` 을 새 이름에 맞게 바꾼다.
3. `skills/` 아래에 필요한 스킬을 추가하거나 수정한다.
4. 저장소 최상위 `.claude-plugin/marketplace.json` 의 `plugins` 배열에 새 플러그인을 등록한다.
