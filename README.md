# Hunch

Hunch는 사용자의 메모와 대화 맥락을 바탕으로, 이상과 현실 사이의 긴장을 구조화해 더 건강하고 현실적인 다음 선택을 돕는 자기 성찰 대화 서비스입니다.

## 왜 만드는가
- 사람은 비슷한 고민을 반복하지만, 반복 패턴과 감정 트리거를 스스로 보기 어렵습니다.
- 일반 챗봇은 대화를 일회성으로 처리해 장기 맥락 반영이 약한 경우가 많습니다.
- Hunch는 장기 맥락을 기억하고, 고민을 구조화하며, 실행 가능한 다음 행동까지 연결하는 데 집중합니다.

## Hunch v0 범위
- 입력: 사용자 메모/짧은 글/대화 기록
- 출력: 이상 vs 현실 고민을 구조화한 답변
- 핵심 목표:
  - "나를 좀 이해하네"라는 개인화 체감
  - 자기비난/비관을 강화하지 않는 건강한 리프레이밍
  - 24~72시간 내 실행 가능한 작은 다음 행동 제안

## 현재 저장소 구성
- `hunch_product_brief.md`: 제품 브리프 원문
- `v0_use_case.md`: v0 단일 문제 정의 및 실패 유형
- `user_model_schema.md`: Self Model v0 스키마/업데이트 규칙
- `response_contract.md`: 답변 포맷 계약
- `eval_rubric_v0.md`: 초기 평가 루브릭
- `eval_dataset_v0.jsonl`: 골든 테스트셋 20문항
- `eval_dataset_v0_ko.jsonl`: 한국어 골든 테스트셋 20문항
- `generate_answer.py`: v0 구조화 답변 생성기
- `run_eval.py`: v0 평가 하네스
- `ai_journal/`: AI 작업 기록(프롬프트/플랜/실행 로그)

## 평가 실행
```bash
python3 run_eval.py --dataset eval_dataset_v0.jsonl --output-dir eval_runs
python3 run_eval.py --dataset eval_dataset_v0_ko.jsonl --output-dir eval_runs_ko
```

## 개발 원칙 (v0)
- 제품 구현과 평가 하네스를 분리하지 않고 함께 개발합니다.
- 기능 확장보다 "응답 품질 루프"를 먼저 검증합니다.
- 매 작업은 `ai_journal`에 기록하고 git에 함께 커밋합니다.
