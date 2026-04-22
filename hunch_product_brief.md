# Hunch Product Brief

## Overview

**Hunch**는 사용자의 기록과 대화를 바탕으로, 이상과 현실 사이의 긴장을 함께 해석하고 더 건강하고 현실적인 선택을 돕는 자기 성찰 대화 서비스다.

기존 AI가 정보 검색과 일반적인 답변 생성에 강하다면, Hunch는 한 사람의 **맥락, 반복 패턴, 가치관, 변화 흐름**을 장기적으로 이해하고 이를 기반으로 더 개인화된 대화를 제공하는 데 집중한다.

핵심 방향은 단순한 “나를 흉내 내는 AI”가 아니라, **대화를 통해 사용자를 더 잘 이해하고, 고민을 구조화하고, 다음 선택을 돕는 reflective AI**를 만드는 것이다.

---

## Problem

사용자는 다음과 같은 문제를 자주 겪는다.

- 내가 진짜 원하는 것이 무엇인지 명확하지 않다
- 이상과 현실 사이에서 어떤 선택이 맞는지 판단하기 어렵다
- 비슷한 고민을 반복하지만, 왜 반복되는지 스스로 잘 보이지 않는다
- 감정, 불안, 비교심, 자기비난 때문에 판단이 흐려질 때가 많다

기존 챗봇은 매 대화를 일회적으로 처리하는 경우가 많아, **사용자의 장기 맥락과 변화**를 충분히 반영하지 못한다.

---

## Product Goal

Hunch의 목표는 아래 3가지를 동시에 만족하는 것이다.

1. **Understand me**  
   대화를 할수록 사용자의 성향, 가치, 갈등 축, 변화 흐름을 더 잘 이해한다.

2. **Structure my thoughts**  
   사용자의 고민을 이상, 현실, 감정, 동기, 선택지의 형태로 구조화한다.

3. **Guide me forward**  
   비관이나 자기비난을 강화하지 않으면서, 더 건강하고 현실적인 다음 선택을 돕는다.

---

## Core Value Proposition

- 사용자를 장기적으로 이해하는 대화 경험
- 이상 / 현실 / 가치 / 패턴을 함께 해석하는 자기 성찰 지원
- 반복 고민과 감정 패턴에 대한 인사이트 제공
- 무조건적인 위로가 아닌, 현실을 인정하는 희망적 리프레이밍
- 사용자가 자신의 삶을 더 주체적으로 이해하고 선택하도록 돕는 개인화 경험

---

## Core Features (Top 5)

### 1. Self Model
사용자의 메모, 글, 대화 기록에서 장기적인 특징을 추출해 **지속적으로 갱신되는 사용자 모델**을 만든다.

예시:
- 핵심 소망
- 현실 제약
- 반복 갈등 축
- 선호/비선호
- 감정 패턴
- 중요 가치
- 최근 변화

**기대 효과:**  
대화를 할수록 “나를 점점 더 이해하고 있다”는 느낌을 제공한다.

---

### 2. Reflection Chat
사용자의 고민을 단순히 답해주는 것이 아니라, 아래 구조로 재정리하며 대화를 이끈다.

- 내가 바라는 것
- 현재 현실
- 숨은 감정 / 동기
- 왜곡된 해석 가능성
- 지금 가능한 선택

**기대 효과:**  
막연한 고민을 구조화해 생각을 더 선명하게 만든다.

---

### 3. Pattern Detection
누적된 대화와 기록을 바탕으로 사용자의 반복 패턴을 찾아낸다.

예시:
- 비슷한 고민의 반복
- 특정 상황에서의 회피
- 비교심이 강해지는 트리거
- 피곤할 때 더 비관적으로 해석하는 경향
- 최근 긍정적으로 바뀌는 흐름

**기대 효과:**  
사용자가 스스로 보지 못했던 반복 구조를 인식하게 돕는다.

---

### 4. Guided Reframing
부정적 해석을 그대로 강화하지 않고, 현실을 부정하지 않으면서도 더 건강한 관점으로 재구성한다.

예시:
- 자기비난 → 패턴 이해
- 극단적 결론 → 작은 실험 제안
- 비교 기반 조급함 → 자기 속도 재정렬
- 막연한 불안 → 구체적 선택지 정리

**기대 효과:**  
대화 이후 사용자가 더 정리되고, 다음 행동으로 이어질 가능성을 높인다.

---

### 5. Values Layer
사용자가 중요하게 여기는 가치관을 반영해 답변의 방향을 조정한다.

예시:
- 기본 성찰 모드
- 관계 중심 모드
- 성장 중심 모드
- 신앙/영성 기반 모드

**기대 효과:**  
답변이 더 개인적이고 일관된 기준 위에서 느껴지도록 만든다.

---

## MVP Scope

### Input Sources
- 사용자 메모
- 사용자가 직접 쓴 글
- Hunch 내 대화 기록

### MVP Capabilities
- 이상 vs 현실 분별 대화
- 반복 고민 패턴 인식
- 희망 중심 리프레이밍
- 가치관 프레임 반영
- 대화 기반 사용자 모델 업데이트

### Out of Scope (initial)
- 모든 외부 소셜 데이터 자동 수집
- 지나치게 민감한 데이터 자동 해석
- 강한 결론형 인생 결정 조언
- 사용자 편향을 무비판적으로 강화하는 응답

---

## System Architecture (Diagram-Level)

```text
[User Inputs]
  - Notes
  - Writings
  - Chat History
        |
        v
[Ingestion Layer]
  - parsing
  - chunking
  - metadata tagging
  - sensitivity / timestamp labeling
        |
        +----------------------+
        |                      |
        v                      v
[Document Store]         [Vector Store]
  - raw text             - embeddings
  - source metadata      - semantic retrieval
  - chunks
        |
        v
[Self Model Builder]
  - profile extraction
  - pattern aggregation
  - confidence scoring
  - change tracking
        |
        v
[User Model Store]
  - desires
  - constraints
  - values
  - recurring conflicts
  - emotional patterns
  - growth signals
        |
        +------------------------------+
        |                              |
        v                              v
[Conversation Orchestrator]      [Safety / Tone Layer]
  - query classification         - negativity control
  - retrieval planning           - anti-self-blame rules
  - prompt composition           - overconfidence checks
  - response assembly            - value imposition guardrails
        |                              |
        +--------------+---------------+
                       |
                       v
               [LLM Response Engine]
                       |
                       v
                 [User Response]

After each conversation
        |
        v
[Memory Update Pipeline]
  - extract new facts
  - update recurring patterns
  - detect growth/change
  - revise user model if needed
```

---

## Architecture Notes

### 1. Dual memory approach
Hunch는 단순한 대화 로그 저장이 아니라, 최소한 아래 두 층을 분리해야 한다.

- **Retrieval memory**: 원문 기록과 대화 내용을 검색하기 위한 저장층
- **Self memory**: 사용자의 장기적 성향과 패턴을 구조화한 모델

이 분리가 있어야 “최근 감정”과 “장기 성향”을 혼동하지 않을 수 있다.

### 2. User model is the core
이 제품의 핵심은 일반적인 RAG가 아니라, **지속적으로 갱신되는 user model**이다.  
답변은 원문 검색 결과만으로 생성하는 것이 아니라, user model과 원문 근거를 함께 참조해야 한다.

### 3. Safety should be structural
부정성 억제는 프롬프트 한 줄로 해결되지 않는다.  
아래와 같은 구조적 계층이 필요하다.

- 자기비난 강화 방지
- 절망적 결론 유도 방지
- 과도한 단정 억제
- 특정 가치관 강요 방지

### 4. Memory update is a product feature
Hunch는 “잘 답하는 것”만큼이나 “잘 배워가는 것”이 중요하다.  
매 대화 이후 무엇을 장기 기억으로 승격할지, 무엇은 일시적 감정으로 남길지 구분하는 로직이 필요하다.

---

## Suggested Tech Direction

### Application Layer
- Mobile-first or web-first conversational UI
- Chat view + insight / profile view 분리

### Backend
- API server
- user/session management
- ingestion pipeline
- async worker for extraction and memory updates

### AI Layer
- embedding model
- response generation model
- structured extraction pipeline for self model
- safety / sentiment / risk scoring modules

### Data Layer
- relational DB for users, sessions, metadata, structured profile
- vector DB for semantic retrieval
- document store for raw notes and writings

---

## Success Metrics

### User Experience
- 사용자가 “나를 좀 안다”고 느끼는 비율
- 대화를 더 깊게 이어가는 비율
- 답변 후 더 정리되었다고 느끼는 비율
- 반복 사용률 / 재방문율

### Product Quality
- 사용자 모델 업데이트 정확도
- 패턴 탐지 유용도
- 리프레이밍 이후 대화 지속률
- 부정적/과도하게 단정적인 응답 비율 감소

---

## One-Line Summary

**Hunch는 사용자의 기록과 대화를 통해 그 사람의 이상, 현실, 가치, 반복 패턴을 이해하고, 장기적으로 더 건강하고 현실적인 선택을 돕는 자기 성찰 대화 엔진이다.**
