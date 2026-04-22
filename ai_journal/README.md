# AI Journal Guide

이 폴더는 AI Agent 작업 기록을 git에 남기기 위한 표준 기록 위치입니다.

## 원칙
- 모든 작업 세션은 `ai_journal/sessions/YYYY-MM-DD.md`에 기록합니다.
- 각 세션 로그에는 최소한 아래 3개 섹션이 있어야 합니다.
  - `## Prompt`
  - `## Plan`
  - `## Execution`
- 코드/문서 변경과 같은 커밋에 작업 기록도 함께 포함합니다.

## 빠른 시작
1. 새 기록 파일 만들기
   - `./scripts/new_agent_log.sh`
2. 훅 활성화(로컬 1회)
   - `./scripts/setup-hooks.sh`

## 훅 동작
- `.githooks/pre-commit` 훅은 당일 로그 파일(`ai_journal/sessions/YYYY-MM-DD.md`)과 필수 섹션 존재 여부를 검사합니다.
- 조건을 만족하지 않으면 커밋이 중단됩니다.

