# NVatar SDK Architecture

> Behavior Pattern Registry + Franchise Memory + God Mode
>
> 설계일: 2026-04-13
> 상태: 설계 완료, 구현 미착수

---

## 1. 설계 철학

### 핵심 원칙: 자아 보존 (Identity Preservation)

NVatar의 아바타는 **자아를 가진 존재**다. 외부 서비스(eKYSS 영어학습, 코드 비서 등)와 연동될 때:

- **성격(traits)과 기억(core memory)은 일상 대화에서만 진화**한다
- 프랜차이즈 활동은 아바타의 **화제 풀을 넓히지만**, 성격을 바꾸지 않는다
- 사람이 직장에서 일한다고 성격이 바뀌진 않지만, 집에 와서 "오늘 이런 일 있었어"는 말할 수 있는 것과 같다

### 3가지 분리 원칙

```
1. 자아 ≠ 행동    → 성격은 코어, 행동은 Pattern별로 다름
2. 기억 ≠ 데이터  → 인격 형성 기억 vs 도메인 작업 데이터
3. 판단 ≠ 실행    → God Mode가 판단, Avatar가 실행
```

---

## 2. 전체 아키텍처

```
┌─ NVatar God Mode (Outer Harness) ──────────────────────────────────────┐
│                                                                         │
│  Gemma as 분석 도구 (캐릭터 프롬프트 없음, 순수 판단)                   │
│                                                                         │
│  ┌─ context_router ──┐  "이 메시지 뭐야?"        → T1~T10 분류        │
│  ┌─ mbti_analyzer ───┐  "성격 어떻게 변해?"      → 4D spectrum delta   │
│  ┌─ user_profiler ───┐  "이 사용자는 어떤 사람?" → 행동 패턴 분석      │
│                                                                         │
│  판단 결과로 제어:                                                      │
│  ├─ Pattern 라우팅 (어떤 행동 패턴을 활성화?)                           │
│  ├─ 메모리 라우팅 (Core vs Franchise 어디에 저장?)                      │
│  └─ 프롬프트 조립 (어떤 컨텍스트를 Gemma에 주입?)                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         ↓ 제어                              ↓ 제어
┌─ Avatar Core (Inner) ──────────┐  ┌─ Behavior Pattern Registry ────────┐
│                                 │  │                                     │
│  성격 (8 traits + pending)     │  │  ┌─ CodeAssistPattern ──┐          │
│  감정 (9 dimensions)           │  │  │  relay 모드           │          │
│  기억 (L1→L2→L3)              │  │  │  Gemma 우회           │          │
│  MBTI (4D continuous 0-100)    │  │  └────────────────────────┘          │
│  Gemma + 캐릭터 프롬프트       │  │  ┌─ LanguageTutorPattern ┐          │
│                                 │  │  │  assisted 모드        │          │
│  일상 대화에서만 진화           │  │  │  외부 AI + Gemma 래핑  │          │
│                                 │  │  └────────────────────────┘          │
│                                 │  │  ┌─ NormalChatPattern ──┐          │
│                                 │  │  │  pure chat 모드       │          │
│                                 │  │  │  Gemma 풀 응답        │          │
│                                 │  │  └────────────────────────┘          │
│                                 │  │  ┌─ (future patterns) ──┐          │
│                                 │  │  │  TherapistPattern     │          │
│                                 │  │  │  CustomerServicePattern│          │
│                                 │  │  └────────────────────────┘          │
└─────────────────────────────────┘  └─────────────────────────────────────┘
```

---

## 3. 메모리 3트랙

### 3.1 Core Memory (인격 트랙)

기존 L1→L2→L3 시스템 그대로. **일상 대화(pure chat)에서만 기록**.

```
L1: 최근 대화 원문 (최대 100건, uncompacted)
L2: 의미 이벤트 요약 (compaction 시 생성, relevance_score)
L3: 장기 키워드 (L2 10개+ 축적 후 전환)

→ 성격 진화에 반영 (trait delta, MBTI shift)
→ 감정 추적에 반영
→ "아바타의 자아"를 형성
```

**DB**: `nv_messages`, `nv_memory_l2`, `nv_memory_l3` (기존)

### 3.2 User Profile (사용자 이해 트랙)

God Mode의 `user_profiler`가 관장. 기존 `user_mbti`의 확장.

```
기존:
  - user_mbti_label, user_mbti_confidence (nv_avatars)

확장:
  - 행동 패턴: 근면성, 꾸준함, 학습 속도
  - 성향: 칭찬에 반응, 도전 선호, 안정 선호
  - 프랜차이즈별 축적 데이터에서 추출
  - 모든 Pattern이 읽기 가능
```

**목적**: "이 사람은 어떤 사람인가"를 아바타가 이해하기 위함.
사용자의 행동 패턴은 아바타 성격을 바꾸지 않지만, 아바타가 사용자에게
**어떻게 접근할지** 결정하는 데 사용된다.

**노출 정책**: 사용자 프로파일은 **직접 노출하지 않는다**.
- 아바타가 "너는 근면한 사람이야"라고 명시적으로 말하지 않음
- 프롬프트에 주입되어 아바타의 **행동에 간접 반영**될 뿐
- 사용자가 자신의 프로파일을 알고 싶다면 → 서비스 차원의 별도 기능으로 제공
  (예: "아바타가 분석한 나의 프로필" 페이지, 시점/형태 미정)
- 기존 사용자 MBTI 추론도 동일 정책: confidence 3+에서도 **명시적 언급 없이 스타일만 조정**

**분석 방식**: mbti_analyzer의 blind 분석 패턴을 재활용.
```
기존 mbti_analyzer:
  대화 메시지 → Gemma blind 분석 → 4D MBTI delta → 가중 적용

user_profiler 확장:
  프랜차이즈 이벤트 → Gemma blind 분석 → 행동 특성 추출 → 가중 적용

  입력 예: "지난 2주 eKYSS: 학습 10회, 평균 82점, 3일 연속 후 1일 빈 패턴,
           어려운 문법에서 점수 하락 후 복습 요청"
  출력 예: { "diligence": 0.75, "resilience": 0.8,
            "challenge_preference": "moderate" }
```

**실행 시점**: compaction과 동기화 — 코어 메모리 compaction이 돌 때
프랜차이즈 메모리도 함께 스캔하여 user_profile 업데이트.
추가 Gemma 호출 1회로 처리 가능 (토큰 비용 최소).

**DB**: `nv_user_profile` (신규, 구조화된 JSON or 컬럼)

### 3.3 Franchise Memory (도메인 트랙)

Pattern별 독립 메모리 공간. 성격 진화에 **절대 반영 안 됨**.

Core L2의 검증된 패턴을 차용:
- **status 필드**: `success|failed|pending|ongoing` (L2와 동일)
- **relevance_score**: 시간 경과��� 감쇠 (단, Core보다 느린 속도)
- **entry_type별 decay 정책**: event/commitment은 감쇠, state는 감쇠 없음

```
구조:
  - pattern_name: "ekyss" | "code-assist" | "therapy" | ...
  - avatar_id: 소유 아바타
  - entry_type: "event" | "state" | "commitment"
  - status: "success" | "failed" | "pending" | "ongoing"  ← L2 차용
  - relevance_score: 1~100 (entry_type별 decay 정책)
  - data: 구조화된 JSON
  - created_at: 타임스탬프

예시:
  { pattern: "ekyss", type: "event", status: "success",
    relevance: 80,
    data: { lesson: 3, topic: "past-tense", score: 80 } }
  { pattern: "ekyss", type: "commitment", status: "ongoing",
    relevance: 100,
    data: { schedule: "daily", time: "20:00", duration: 30 } }
  { pattern: "ekyss", type: "state", status: "ongoing",
    relevance: null,  ← state는 decay 없음
    data: { current_level: "intermediate", next_lesson: 4 } }
  { pattern: "code-assist", type: "event", status: "success",
    relevance: 60,
    data: { task: "README 업데이트", summary: "완료" } }
```

**Relevance Decay 정책 (Core L2와 차등):**

| 트랙 | decay 속도 | 이유 |
|------|-----------|------|
| Core L2 | -2/day | 일상 기억은 빨리 흐려짐 |
| Franchise event | -1/day | 도메인 학습 기록은 더 오래 유지 |
| Franchise commitment | -0.5/day | 약속은 천천히 잊혀짐 |
| Franchise state | decay 없음 | "현재 레벨"은 시간과 무관한 상태값 |

**재언급 시 복원**: Core L2와 동일하게 relevance → 80으로 복원.

**Proactive 스케줄러 연동**: `status: "pending"` 이벤트를 스캔하여 리마인더 생성.
`commitment` + `ongoing` 이벤트의 이행 여부를 추적하여 "약속 이행률" 산출.

**DB**: `nv_franchise_memory` (신규)

### 3.4 프랜차이즈 메모리 소비 경로

| 소비자 | 시점 | 사용법 |
|--------|------|--------|
| **Pattern 자체** | 해당 모드 활성 시 | "어제 lesson-3 했으니 4 하자" |
| **Proactive 스케줄러** | 30분 배치 스캔 | "학습 시간인데 할 거야?" |
| **prompt_builder** | pure chat 시 | 화제 풀 확장 (optional 주입) |
| **Monologue 루틴** | 30~60초 간격 | 토픽 샘플링에 포함 |

---

## 4. BehaviorPattern 인터페이스

### 4.1 기본 인터페이스

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class GemmaMode(Enum):
    RELAY = "relay"           # Gemma 완전 우회, 외부 AI만
    ASSISTED = "assisted"     # 외부 AI + Gemma 캐릭터 래핑
    PURE_CHAT = "pure_chat"   # Gemma 풀 응답

class MemoryPolicy(Enum):
    SKIP = "skip"                     # 코어 메모리에 저장 안 함
    CORE_ONLY = "core_only"           # 코어 메모리만 저장
    FRANCHISE_ONLY = "franchise_only" # 프랜차이즈 메모리만 저장
    BOTH = "both"                     # 코어 + 프랜차이즈 모두 저장

@dataclass
class PatternContext:
    """Pattern에 전달되는 실행 컨텍스트"""
    avatar_id: int
    user_text: str
    websocket: WebSocket
    conv_types: list[str]           # context_router 분류 결과
    core_services: CoreServices     # avatar, memory, emotion, gemma, prompt_builder
    franchise_memory: FranchiseMemoryService
    user_profile: UserProfileService

class BehaviorPattern(ABC):
    """모든 행동 패턴의 기본 인터페이스"""

    @property
    @abstractmethod
    def name(self) -> str:
        """패턴 이름 (e.g., "code-assist", "ekyss", "normal-chat")"""

    @property
    @abstractmethod
    def gemma_mode(self) -> GemmaMode:
        """이 패턴의 Gemma 개입 수준"""

    @property
    @abstractmethod
    def memory_policy(self) -> MemoryPolicy:
        """이 패턴의 기억 저장 정책"""

    @abstractmethod
    async def should_activate(self, ctx: PatternContext) -> bool:
        """이 메시지를 이 패턴이 처리해야 하는가?

        God Mode(context_router)의 분류 결과와 현재 상태를 보고 판단.
        True를 반환하면 이 패턴이 메시지를 가져감.
        """

    @abstractmethod
    async def handle(self, ctx: PatternContext) -> PatternResult:
        """메시지 처리 실행.

        Returns:
            PatternResult: 응답 텍스트 + 프랜차이즈 메모리 이벤트 + 메타데이터
        """

    def get_franchise_context(self, ctx: PatternContext) -> str | None:
        """prompt_builder에 주입할 프랜차이즈 컨텍스트 (optional).

        pure chat 시점에 이 Pattern의 프랜차이즈 메모리에서
        관련 정보를 요약해 반환. 아바타가 일상 대화에서
        자연스럽게 언급할 수 있도록.
        """
        return None

    def get_proactive_triggers(self, ctx: PatternContext) -> list[dict] | None:
        """Proactive 스케줄러에 등록할 트리거 목록 (optional).

        Returns:
            [{ "type": "schedule_remind", "condition": "...", "message_hint": "..." }]
        """
        return None

@dataclass
class PatternResult:
    """Pattern 실행 결과"""
    response_text: str | None        # 아바타 응답 (relay 모드면 None 가능)
    franchise_events: list[dict]     # 프랜차이즈 메모리에 저장할 이벤트
    user_profile_updates: dict | None  # 사용자 프로파일 업데이트
    relay_results: list[dict] | None   # relay 모드의 원본 결과 (UI 패널용)
    suppress_core_memory: bool = False # True면 코어 메모리 저장 억제
```

### 4.2 Pattern Registry

```python
class PatternRegistry:
    """행동 패턴 등록소. chat.py의 if/else 체인을 대체."""

    def __init__(self):
        self._patterns: list[BehaviorPattern] = []
        self._active_pattern: dict[int, BehaviorPattern] = {}  # avatar_id → 현재 활성 패턴

    def register(self, pattern: BehaviorPattern):
        """패턴 등록 (순서 = 우선순위)"""
        self._patterns.append(pattern)

    async def route(self, ctx: PatternContext) -> BehaviorPattern:
        """메시지를 처리할 패턴 결정.

        1. 현재 활성 패턴이 있으면 우선 확인
        2. 없으면 등록 순서대로 should_activate 호출
        3. 아무도 안 가져가면 NormalChatPattern (fallback)
        """
        # 활성 패턴 우선
        active = self._active_pattern.get(ctx.avatar_id)
        if active and await active.should_activate(ctx):
            return active

        # 순서대로 탐색
        for pattern in self._patterns:
            if await pattern.should_activate(ctx):
                return pattern

        # fallback
        return self._default_pattern

    def set_active(self, avatar_id: int, pattern: BehaviorPattern | None):
        """명시적 모드 전환 (e.g., 코드 비서모드 온)"""
        if pattern:
            self._active_pattern[avatar_id] = pattern
        else:
            self._active_pattern.pop(avatar_id, None)
```

---

## 5. Gemma 개입 모드 3종

### 5.1 Relay 모드 (Gemma 우회)

```
사용자 메시지 → 외부 AI (Claude Code 등) → 결과 직접 반환
                                          ↓
                               프랜차이즈 메모리에만 기록
                               코어 메모리 저장 안 함
                               성격 진화 없음

예: Code Assist — "README 업데이트해줘" → Claude Code 실행 → 결과 표시
```

**특징**:
- Gemma 호출 없음 (토큰 절약, 지연 없음)
- 아바타는 결과를 "전달"만 함 (character wrap 선택적)
- 대화 기록이 코어에 쌓이지 않아 성격 오염 방지

### 5.2 Assisted 모드 (외부 AI + Gemma 래핑)

```
사용자 메시지 → 외부 AI (학습 엔진 등) → 도메인 결과
                                          ↓
                               Gemma가 캐릭터로서 래핑
                               "잘했어~ 다음은 현재완료 해볼까?"
                                          ↓
                               코어 메모리: 대화 자체 기록 (L1)
                               프랜차이즈 메모리: 도메인 데이터 기록
                               성격 진화: 대화에서만 (도메인 데이터는 무시)

예: eKYSS — 학습 결과 80점 → Gemma가 "오~ 잘했어!" → 캐릭터 대화 기록
```

**특징**:
- 외부 AI가 도메인 처리, Gemma가 캐릭터 표현
- 대화 자체는 코어에 기록 (아바타가 "오늘 영어 했었지" 기억 가능)
- 도메인 데이터(점수, 진도)는 프랜차이즈 트랙에만

### 5.3 Pure Chat 모드 (Gemma 풀 응답)

```
사용자 메시지 → context_router → Gemma (캐릭터 프롬프트 풀 적용)
                                   ↓
                        prompt_builder:
                          시스템 프롬프트 (성격, MBTI, 감정)
                        + 코어 메모리 (L2, L3)
                        + 사용자 프로파일
                        + 프랜차이즈 최근 활동 (optional)
                        + 최근 대화
                                   ↓
                        코어 메모리 기록 (L1)
                        성격 진화 반영

예: 일상 대화 — "오늘 뭐했어?" → "나? 그냥~ 아 맞다 너 어제 영어 잘했던데~"
```

**특징**:
- 기존 NVatar의 기본 동작
- 프랜차이즈 메모리를 prompt에 선택적 주입 → 화제 풀 확장
- 이 모드에서만 성격이 진화함

---

## 6. God Mode 상세

### 6.1 개요

God Mode는 **아바타 위의 메타 레이어**. 아바타 캐릭터 프롬프트 없이 Gemma를 순수 분석 도구로 사용.

```
God Mode 구성:
├── context_router      (기존) 메시지 타입 분류 T1~T10
├── mbti_analyzer       (기존) 4D 성격 스펙트럼 분석
├── user_profiler       (신규) 사용자 행동 패턴 분석
└── proactive_scheduler (기존, 확장) 프랜차이즈 리마인더 추가
```

### 6.2 User Profiler (신규)

기존 `mbti_analyzer`의 사용자 MBTI 추론을 확장.

```python
class UserProfiler:
    """사용자 행동 패턴 분석기 (God Mode)"""

    def analyze_franchise_activity(self, avatar_id: int) -> dict:
        """프랜차이즈 메모리에서 사용자 행동 패턴 추출.

        Compaction 시점 또는 배치로 실행 (실시간 아님).

        분석 대상:
          - 학습 빈도/꾸준함 (commitment 이행률)
          - 성취도 추이 (점수 변화)
          - 참여 패턴 (시간대, 간격)
          - 약속 이행 여부

        Returns:
          { "diligence": 0.8, "growth_rate": "steady",
            "preferred_time": "20:00", "commitment_rate": 0.7 }
        """

    def get_profile_summary(self, avatar_id: int) -> str:
        """prompt_builder에 주입할 사용자 프로파일 요약.

        Returns:
          "이 사용자는 꾸준한 학습자 (주 5회), 칭찬에 잘 반응하며,
           저녁 8시에 주로 활동한다."
        """
```

### 6.3 Proactive Scheduler 확장

기존 4종 + 프랜차이즈 리마인더 추가.

```python
# 기존
PROACTIVE_TYPES = [
    "morning",           # 8~9시, 6시간+ 부재
    "absence",           # threshold_hours 초과
    "emotion_followup",  # slumps 75+
]

# 신규
PROACTIVE_TYPES += [
    "franchise_remind",  # 프랜차이즈 메모리 기반
]

async def _check_franchise_remind(self, avatar_id: int):
    """프랜차이즈 메모리 스캔 → 리마인더 생성.

    조건 예시:
      - commitment "daily 20:00" 인데 오늘 기록 없음 → "영어 할 시간~"
      - 마지막 학습 3일 전 → "요즘 바빠? 영어 좀 쉬고 있어?"
      - lesson 완료 직후 → "오늘 잘했어~ 내일도 해볼까?"

    Gemma 캐릭터 프롬프트로 래핑하여 자연스러운 말투로 전달.
    """
```

---

## 7. Pattern 구현 예시

### 7.1 CodeAssistPattern (기존 코드 추출)

```python
class CodeAssistPattern(BehaviorPattern):
    """Claude Code Channel 연동 — 코드 작업 relay"""

    name = "code-assist"
    gemma_mode = GemmaMode.RELAY
    memory_policy = MemoryPolicy.FRANCHISE_ONLY

    async def should_activate(self, ctx: PatternContext) -> bool:
        # 코드 비서모드 ON 상태 + 채널 활성
        return (
            channel_service.is_code_assist(ctx.avatar_id)
            and channel_service.is_channel_active()
        )

    async def handle(self, ctx: PatternContext) -> PatternResult:
        # 의견 요청이면 Gemma로 라우팅
        if channel_service.is_opinion_request(ctx.avatar_id, ctx.user_text):
            return await self._handle_opinion(ctx)

        # Claude Code로 relay
        result = await channel_service.send_to_channel(
            ctx.avatar_id, ctx.user_text,
            on_progress=lambda t: _send_bubbles(ctx.websocket, t)
        )

        return PatternResult(
            response_text=result.get("text"),
            franchise_events=[{
                "type": "event",
                "data": {
                    "task": ctx.user_text[:200],
                    "status": result.get("status"),
                    "summary": result.get("text", "")[:500]
                }
            }],
            relay_results=[result],
            suppress_core_memory=True
        )

    def get_franchise_context(self, ctx: PatternContext) -> str | None:
        recent = ctx.franchise_memory.get_recent(ctx.avatar_id, "code-assist", limit=3)
        if not recent:
            return None
        summaries = [f"- {r['data']['task']}: {r['data']['status']}" for r in recent]
        return f"최근 코드 작업:\n" + "\n".join(summaries)
```

### 7.2 LanguageTutorPattern (eKYSS 예시)

```python
class LanguageTutorPattern(BehaviorPattern):
    """eKYSS 영어 학습 — 외부 학습 엔진 + Gemma 캐릭터 래핑"""

    name = "ekyss"
    gemma_mode = GemmaMode.ASSISTED
    memory_policy = MemoryPolicy.BOTH  # 대화는 코어, 학습 데이터는 프랜차이즈

    async def should_activate(self, ctx: PatternContext) -> bool:
        # eKYSS SDK 세션이 활성화된 상태
        return ekyss_service.is_session_active(ctx.avatar_id)

    async def handle(self, ctx: PatternContext) -> PatternResult:
        # 1. 외부 학습 엔진에 전달
        lesson_result = await ekyss_service.process(ctx.user_text)

        # 2. Gemma가 캐릭터로서 래핑
        extra_context = (
            f"[영어 수업 중. 학습 엔진 결과: {lesson_result['feedback']}. "
            f"점수: {lesson_result['score']}점. "
            f"캐릭터답게 반응해줘. 결과를 자연스럽게 전달하되 강의하지 마.]"
        )
        messages = ctx.core_services.prompt_builder.build_messages(
            ctx.avatar_id, ctx.user_text, extra_context=extra_context
        )
        response = await ctx.core_services.gemma.chat_collect(messages, 256, False)

        return PatternResult(
            response_text=response,
            franchise_events=[{
                "type": "event",
                "data": {
                    "lesson": lesson_result["lesson_id"],
                    "topic": lesson_result["topic"],
                    "score": lesson_result["score"],
                }
            }],
            user_profile_updates={
                "last_study": datetime.now().isoformat(),
                "total_lessons": "+1",
            }
        )

    def get_franchise_context(self, ctx: PatternContext) -> str | None:
        state = ctx.franchise_memory.get_latest_state(ctx.avatar_id, "ekyss")
        if not state:
            return None
        return (
            f"사용자는 eKYSS에서 영어 학습 중. "
            f"현재 레벨: {state.get('current_level', '?')}. "
            f"마지막 수업: {state.get('last_topic', '?')} ({state.get('last_score', '?')}점). "
            f"이 정보를 자연스럽게 대화에 녹여도 좋지만 강요하지 마."
        )

    def get_proactive_triggers(self, ctx: PatternContext) -> list[dict] | None:
        return [
            {
                "type": "schedule_remind",
                "condition": "commitment 'daily' 미이행",
                "message_hint": "오늘 영어 공부 할 시간이야~"
            },
            {
                "type": "absence_remind",
                "condition": "3일 이상 미학습",
                "message_hint": "요즘 바빠? 영어 좀 쉬고 있는 거야?"
            }
        ]
```

### 7.3 NormalChatPattern (기존 일상 대화)

```python
class NormalChatPattern(BehaviorPattern):
    """기본 일상 대화 — 기존 chat.py 로직 추출"""

    name = "normal-chat"
    gemma_mode = GemmaMode.PURE_CHAT
    memory_policy = MemoryPolicy.CORE_ONLY

    async def should_activate(self, ctx: PatternContext) -> bool:
        return True  # fallback — 항상 활성화 가능

    async def handle(self, ctx: PatternContext) -> PatternResult:
        # 기존 _handle_normal/thinking/csw_conversation 로직
        needs_external = context_router.needs_csw(ctx.conv_types)
        needs_thinking = context_router.thinking_needed(ctx.conv_types)

        if needs_external:
            return await self._handle_csw(ctx)
        elif needs_thinking:
            return await self._handle_thinking(ctx)
        else:
            return await self._handle_normal(ctx)

    async def _handle_normal(self, ctx: PatternContext) -> PatternResult:
        # 프랜차이즈 컨텍스트 수집 (다른 Pattern들에서)
        franchise_ctx = self._collect_franchise_contexts(ctx)

        extra = None
        if franchise_ctx:
            extra = f"[참고 — 사용자의 최근 활동]\n{franchise_ctx}"

        messages = ctx.core_services.prompt_builder.build_messages(
            ctx.avatar_id, ctx.user_text, extra_context=extra
        )
        response = await ctx.core_services.gemma.chat_collect(messages, 256, False)

        return PatternResult(
            response_text=response,
            franchise_events=[],
        )
```

---

## 8. 리팩토링 대상 매핑

### chat.py 현재 → Pattern 전환

| 현재 위치 (chat.py) | 라인 | → Pattern |
|---------------------|------|-----------|
| monologue 분기 | 131-134 | MonologuePattern (또는 Proactive 통합) |
| mode toggle 감지 | 144-147 | Registry.set_active() 인프라 |
| code assist ON + relay | 150-171 | CodeAssistPattern |
| code assist + opinion | 152-162 | CodeAssistPattern._handle_opinion() |
| SDK + code kw 인터셉트 | 174-179 | CodeAssistPattern.should_activate() 확장 |
| lookup confirm | 182-186 | LookupPattern (CSW 분리) |
| T5/T6 → CSW | 211-213 | NormalChatPattern._handle_csw() |
| T4 → thinking | 215-217 | NormalChatPattern._handle_thinking() |
| 나머지 → normal | 219-227 | NormalChatPattern._handle_normal() |

### channel_service.py → CodeAssistPattern 내부로

| 현재 함수 | → 위치 |
|-----------|--------|
| is_code_assist() | CodeAssistPattern.should_activate() |
| is_code_request() | CodeAssistPattern.should_activate() |
| is_opinion_request() | CodeAssistPattern._is_opinion() |
| check_mode_toggle() | Registry 인프라 (패턴 활성화/비활성화) |
| send_to_channel() | CodeAssistPattern.handle() 내부 |
| receive_callback() | CodeAssistPattern 내부 이벤트 |
| store_code_result() | FranchiseMemoryService |
| get_recent_results() | FranchiseMemoryService.get_recent() |

---

## 9. 새 WebSocket 핸들러 (리팩토링 후)

```python
# chat.py — 리팩토링 후 핵심 루프
async def websocket_chat(websocket: WebSocket, avatar_id: int):
    await websocket.accept()

    while True:
        data = json.loads(await websocket.receive_text())

        if data.get("type") == "monologue_request":
            await monologue_pattern.handle(...)
            continue

        if data.get("type") != "message" or not data.get("text"):
            await websocket.send_json({"type": "error", ...})
            continue

        user_text = data["text"].strip()

        # ── God Mode: 분류 ──
        conv_types = context_router.classify(user_text, ...)

        # ── 컨텍스트 조립 ──
        ctx = PatternContext(
            avatar_id=avatar_id,
            user_text=user_text,
            websocket=websocket,
            conv_types=conv_types,
            core_services=core_services,
            franchise_memory=franchise_memory_service,
            user_profile=user_profile_service,
        )

        # ── 모드 토글 체크 ──
        toggle = registry.check_mode_toggle(ctx)
        if toggle:
            continue

        # ── Pattern 라우팅 ──
        pattern = await registry.route(ctx)
        result = await pattern.handle(ctx)

        # ── 공통 후처리 ──
        # 응답 전송
        if result.response_text:
            await _send_bubbles(websocket, result.response_text, avatar_id=avatar_id)

        # 코어 메모리 저장 (정책에 따라)
        if pattern.memory_policy in (MemoryPolicy.CORE_ONLY, MemoryPolicy.BOTH):
            if not result.suppress_core_memory:
                memory_service.add_message(avatar_id, "user", user_text)
                if result.response_text:
                    memory_service.add_message(avatar_id, "assistant", result.response_text)

        # 프랜차이즈 메모리 저장
        if pattern.memory_policy in (MemoryPolicy.FRANCHISE_ONLY, MemoryPolicy.BOTH):
            for event in result.franchise_events:
                franchise_memory_service.add_event(
                    avatar_id, pattern.name, event["type"], event["data"]
                )

        # 사용자 프로파일 업데이트
        if result.user_profile_updates:
            user_profile_service.update(avatar_id, result.user_profile_updates)

        # 감정/성격 업데이트 (pure chat에서만)
        if pattern.gemma_mode == GemmaMode.PURE_CHAT:
            emotions = emotion_service.update_from_text(avatar_id, user_text)
            trait_deltas = persona_evolution_service.analyze_trait_delta(user_text)
            if trait_deltas:
                persona_evolution_service.apply_pending_delta(avatar_id, trait_deltas)
            await websocket.send_json({"type": "emotion_update", "emotions": emotions})
```

---

## 10. DB 스키마 (신규 테이블)

### nv_franchise_memory

```sql
CREATE TABLE nv_franchise_memory (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    avatar_id       INT NOT NULL,
    pattern_name    VARCHAR(50) NOT NULL,       -- "ekyss", "code-assist", ...
    entry_type      VARCHAR(20) NOT NULL,       -- "event", "state", "commitment"
    status          VARCHAR(20) DEFAULT 'success', -- success|failed|pending|ongoing (L2 차용)
    relevance_score INT DEFAULT 80,             -- 1~100, entry_type별 decay (state는 NULL)
    data            JSON NOT NULL,              -- 구조화된 도메인 데이터
    created_at      DATETIME DEFAULT NOW(),

    INDEX idx_avatar_pattern (avatar_id, pattern_name),
    INDEX idx_avatar_type (avatar_id, entry_type),
    INDEX idx_relevance (avatar_id, relevance_score),
    FOREIGN KEY (avatar_id) REFERENCES nv_avatars(id)
);
```

### nv_user_profile

```sql
CREATE TABLE nv_user_profile (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    avatar_id   INT NOT NULL UNIQUE,          -- 1:1 with avatar
    diligence   FLOAT DEFAULT 0.5,            -- 근면성 0~1
    growth_rate VARCHAR(20) DEFAULT 'unknown', -- steady, accelerating, declining
    preferred_time VARCHAR(10),                -- "20:00"
    commitment_rate FLOAT DEFAULT 0.0,         -- 약속 이행률 0~1
    traits_json JSON,                          -- 확장 가능한 추가 특성
    updated_at  DATETIME DEFAULT NOW() ON UPDATE NOW(),

    FOREIGN KEY (avatar_id) REFERENCES nv_avatars(id)
);
```

---

## 11. 구현 순서

> **결정 (2026-04-13)**: SDK 인프라 먼저. MBTI 발화 고도화는 코어 별도 진행.

### Phase 1: SDK 인프라 — 구조 전환 (동작 변경 없음)

기존 코드의 동작을 **1도 바꾸지 않고** 구조만 Pattern으로 전환.
모든 기존 기능이 그대로 동작해야 Phase 1 완료.

```
신규 파일:
  app/sdk/pattern.py          — BehaviorPattern ABC + GemmaMode + MemoryPolicy + PatternResult
  app/sdk/registry.py         — PatternRegistry (route, set_active, check_mode_toggle)
  app/sdk/patterns/normal.py  — NormalChatPattern (기존 _handle_normal/thinking/csw 추출)
  app/sdk/patterns/monologue.py — MonologuePattern (기존 _handle_monologue 추출)
  app/sdk/franchise_memory.py — FranchiseMemoryService (nv_franchise_memory CRUD)

수정 파일:
  app/api/chat.py             — if/else 체인 → registry.route() 전환
```

**검증**: 서버 기동 → 일상 대화 / CSW / thinking / monologue 모두 기존과 동일하게 동작

### Phase 2: Code Assist 추출 — 첫 번째 Pattern

```
신규 파일:
  app/sdk/patterns/code_assist.py — CodeAssistPattern (channel_service 로직 이전)

수정 파일:
  app/api/chat.py             — code assist 분기 제거 (Pattern이 대체)
  app/service/channel_service.py — Pattern 내부 메서드로 슬림화
```

**검증**: Code Assist 토글 ON/OFF → relay → opinion → channel disconnect 전부 동일

### Phase 3: 프랜차이즈 메모리 활용

```
DB: nv_franchise_memory 테이블 생성

수정 파일:
  app/service/prompt_builder.py — get_franchise_context() 주입 포인트
  app/service/proactive_scheduler.py — franchise_remind 타입 추가
  code_result_store.py → FranchiseMemoryService로 마이그레이션
```

**검증**: 일상 대화에서 프랜차이즈 활동 자연스럽게 언급 / Proactive 리마인더 작동

### Phase 4: User Profiler + DB

```
DB: nv_user_profile 테이블 생성

신규 파일:
  app/sdk/user_profiler.py    — blind 분석 (compaction 연동)

수정 파일:
  app/service/compactor.py    — user_profiler 호출 추가
  app/service/prompt_builder.py — user profile summary 주입
```

### Phase 5: eKYSS 파트너 연동 (첫 프랜차이즈)

```
신규 파일:
  app/sdk/patterns/language_tutor.py — LanguageTutorPattern

API:
  POST /api/v1/sdk/register   — 파트너 앱 등록
  POST /api/v1/sdk/session     — 세션 시작/종료
  GET  /api/v1/sdk/avatar/{id}/export — 캐릭터 데이터 내보내기
```

---

## 12. 기존 문서와의 관계

| 문서 | 관계 |
|------|------|
| `ARCHITECTURE.md` | 현재 시스템 구조 → 이 문서는 **확장 설계** |
| `MEMORY_SYSTEM.md` | Core Memory 설계 → Franchise Memory가 **별도 트랙으로 추가** |
| `MBTI_SPECTRUM_DESIGN.md` | God Mode의 mbti_analyzer 부분 → `user_profiler`가 확장 |
| `VISION_ROADMAP.md` | SDK 비전/프랜차이즈 모델 → 이 문서가 **구체적 구현 설계** |
| `CSW_INTEGRATION.md` | lookup_service → NormalChatPattern 내부로 편입 |

---

## 13. 기존 시스템과의 통합 포인트

SDK 아키텍처는 기존 NVatar 시스템의 검증된 패턴을 최대한 재활용한다.

### 13.1 Compaction 연동

현재 compaction은 100 메시지 축적 시 트리거되어 아래를 수행:
```
L1→L2 요약 → trait commit(decay) → MBTI blind 분석(20%) → 사용자 MBTI 추론
→ L2→L3 전환 체크 → L3 키워드 생성 → MBTI blind 분석(40%)
```

SDK 확장 후 compaction에 추가:
```
(기존 전체) + 프랜차이즈 메모리 relevance decay 일괄 적용
            + user_profiler blind 분석 (프랜차이즈 이벤트 기반)
            + Franchise commitment 이행률 산출
```

**설계 원칙**: compaction은 이미 "무거운 배치 작업"의 자연스러운 시점.
추가 Gemma 호출을 여기에 묶으면 실시간 성능 영향 없음.

### 13.2 Blind 분석 패턴 재활용

mbti_analyzer의 blind 분석 (캐릭터 프롬프트 없는 Gemma 호출)은
God Mode의 핵심 패턴이며, 다음 3곳에서 동일한 구조를 사용:

| 분석기 | 입력 | 출력 | 실행 시점 |
|--------|------|------|-----------|
| context_router | 단일 메시지 | T1~T10 | 매 메시지 (실시간) |
| mbti_analyzer | compaction 대상 대화 | 4D MBTI delta | compaction 시 |
| user_profiler | 프랜차이즈 이벤트 누적 | 행동 특성 | compaction 시 |

모두 `Gemma(system="분석해줘", user=데이터, max_tokens=60~128)` 패턴.
**God Mode 공통 유틸**로 추출 가능.

### 13.3 L2 status → Proactive 연동

Core L2의 `status: "pending"` 이벤트는 이미 프롬프트에 "예정된 사건"으로 주입됨.
Franchise Memory도 동일한 status 필드를 사용하므로:

```
Proactive Scheduler 30분 스캔:
  1. Core L2 pending → "다음주 여행이라며? 준비 다 했어?" (기존)
  2. Franchise pending → "오늘 영어 수업 시간인데 할 거야?" (신규)
  3. Franchise commitment + 미이행 → "3일째 안 했네, 괜찮아?" (신규)
```

---

## 14. 미구현 항목 현황

SDK 설계와 관련된 기존 시스템의 미구현 항목 목록.
SDK 구현 전에 완료해야 할 것과 SDK와 병행 가능한 것을 구분.

### 코어 고도화 (SDK와 독립, 별도 진행)

SDK 인프라와 의존성 없음. 별개의 코어 품질 개선 작업으로 이후 진행.

| 항목 | 현재 상태 | 비고 |
|------|----------|------|
| **확률적 MBTI 발화 가이드** | 🔲 미구현 | prompt_builder._build_mbti_prompt 개선. 코어 품질 향상 |
| **사용자 MBTI → 프롬프트 반영** | 🔲 미구현 | confidence 기반 단계별 스타일 조정. user_profiler 확장의 기반이 되지만 SDK 없이도 독립 구현 가능 |

### SDK와 병행 가능

| 항목 | 현재 상태 | 연결 |
|------|----------|------|
| 사용자 MBTI 추론 DB 필드 | ✅ 설계 완료 | nv_avatars에 user_mbti_* 필드 추가 예정 |
| compactor L2→L3 + MBTI 40% | ✅ 구현 완료 | 그대로 유지 |
| 9차원 감정 (curiosity) | ✅ 구현 완료 | 그대로 유지 |
| 시뮬레이션 프레임워크 | ✅ simulate_chat.py | Pattern별 시뮬레이션으로 확장 가능 |

### SDK 구현 후 순차 진행

| 항목 | 연결 |
|------|------|
| Franchise Memory relevance decay 배치 | compaction 연동 후 |
| User Profiler blind 분석 | mbti_analyzer 패턴 복제 후 |
| Proactive franchise_remind | Pattern.get_proactive_triggers() 구현 후 |
| 사용자 프로파일 서비스 노출 | UI/UX 기획 필요 (시점 미정) |

---

## 15. 설계 원칙 요약

```
1. 자아 보존      아바타 성격은 일상 대화에서만 진화
2. 기억 분리      Core(인격) / User Profile(사용자 이해) / Franchise(도메인)
3. God Mode       캐릭터 없는 Gemma로 판단, 캐릭터 있는 Gemma로 실행
4. 검증된 재활용  L2 status, relevance decay, blind 분석 — 기존 패턴 차용
5. 암묵적 반영    사용자 프로파일은 행동에 녹이되, 직접 말하지 않음
6. Compaction 동기 무거운 분석은 compaction 시점에 묶어서 실시간 영향 제로
7. Pattern 독립   각 Pattern은 코어를 수정하지 않고 행동만 추가
8. 저장 자기결정  프랜차이즈 메모리 저장 여부는 Pattern이 결정 (민감 정보 보호)
```

---

> 이 문서는 NVatar를 단일 앱에서 **플랫폼 엔진**으로 전환하기 위한 핵심 설계.
> Code Assist를 첫 번째 BehaviorPattern으로 추출하고,
> eKYSS를 첫 번째 프랜차이즈 파트너로 연동하는 것이 목표.
>
> 기존 시스템(L2 status, blind 분석, compaction, proactive)의 검증된 패턴을
> 최대한 재활용하여 구현 리스크를 최소화한다.
