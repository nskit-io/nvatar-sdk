"""
NVatar SDK — Language Tutor Pattern (Assisted Mode)

Full example of an ASSISTED mode pattern:
- External API handles lesson logic (quiz, scoring, curriculum)
- Gemma wraps results in avatar's personality
- Franchise memory tracks learning progress
- Proactive reminders for daily commitment
- Daily chat references learning history

This is the reference implementation for the eKYSS integration model.

Usage:
  1. Implement your TutorService (replace the stub below)
  2. Copy to app/sdk/patterns/
  3. Register in chat.py
"""
import asyncio
from app.sdk.pattern import (
    BehaviorPattern, GemmaMode, MemoryPolicy, PatternContext, PatternResult,
)
from app.service import gemma_service, prompt_builder
from app.sdk import franchise_memory


# ---------------------------------------------------------------------------
# Stub: Replace with your actual tutoring service
# ---------------------------------------------------------------------------

class TutorService:
    """Stub for external tutoring API. Replace with your implementation."""

    _sessions: dict[int, bool] = {}

    @classmethod
    def start_session(cls, avatar_id: int):
        cls._sessions[avatar_id] = True

    @classmethod
    def end_session(cls, avatar_id: int):
        cls._sessions.pop(avatar_id, None)

    @classmethod
    def is_active(cls, avatar_id: int) -> bool:
        return cls._sessions.get(avatar_id, False)

    @classmethod
    async def process_answer(cls, avatar_id: int, user_text: str) -> dict:
        """Process user's answer. Replace with your API call.

        Returns:
            {
                "lesson_id": 9,
                "topic": "Passive Voice",
                "question": "The cake ___ (eat) by the children.",
                "user_answer": user_text,
                "correct_answer": "was eaten",
                "is_correct": True,
                "score": 85,
                "feedback": "Great job! You got the passive voice right.",
                "next_hint": "Try the next exercise on reported speech."
            }
        """
        # --- Stub implementation ---
        return {
            "lesson_id": 9,
            "topic": "Reported Speech",
            "score": 85,
            "is_correct": True,
            "feedback": f"Good answer: '{user_text}'",
            "next_hint": "Let's try another one!",
        }


tutor = TutorService()


# ---------------------------------------------------------------------------
# Pattern Implementation
# ---------------------------------------------------------------------------

class LanguageTutorPattern(BehaviorPattern):
    """Language tutoring — external AI + Gemma character wrapping."""

    def __init__(self):
        super().__init__()
        self._save_franchise_memory = True  # Learning history is valuable

    @property
    def name(self) -> str:
        return "language-tutor"

    @property
    def gemma_mode(self) -> GemmaMode:
        return GemmaMode.ASSISTED

    @property
    def memory_policy(self) -> MemoryPolicy:
        return MemoryPolicy.BOTH  # Conversation → core, lesson data → franchise

    async def should_activate(self, ctx: PatternContext) -> bool:
        return tutor.is_active(ctx.avatar_id)

    async def handle(self, ctx: PatternContext) -> PatternResult:
        # 1. External API processes the answer
        result = await tutor.process_answer(ctx.avatar_id, ctx.user_text)

        # 2. Build context for Gemma character wrapping
        if result["is_correct"]:
            mood = "기뻐하며 칭찬해"
        else:
            mood = "아쉬워하면서도 격려해"

        extra_context = (
            f"[영어 수업 중. 학습 엔진 결과: {result['feedback']}. "
            f"점수: {result['score']}점. "
            f"{mood}. 캐릭터답게 자연스럽게 반응하고, "
            f"다음 힌트도 살짝 알려줘: {result.get('next_hint', '')}. "
            f"강의하지 말고 친구처럼.]"
        )

        # 3. Gemma generates character response
        messages = prompt_builder.build_messages(
            ctx.avatar_id, ctx.user_text, extra_context=extra_context
        )
        await ctx.websocket.send_json({"type": "typing"})
        response = await asyncio.to_thread(
            gemma_service.chat_collect, messages, 256, False
        )
        if not response:
            response = "오~ 잘했어! 다음 문제 가볼까? 💪"

        # 4. Return with franchise events
        return PatternResult(
            response_text=response,
            franchise_events=[{
                "type": "event",
                "status": "success",
                "data": {
                    "lesson": result["lesson_id"],
                    "topic": result["topic"],
                    "score": result["score"],
                    "is_correct": result["is_correct"],
                },
            }],
            user_profile_updates={
                "last_study": "now",
                "total_answers": "+1",
            },
        )

    def get_franchise_context(self, avatar_id: int) -> str | None:
        """Provide learning context for daily conversations."""
        state = franchise_memory.get_latest_state(avatar_id, self.name)
        events = franchise_memory.get_recent(avatar_id, self.name, limit=3, entry_type="event")

        if not events and not state:
            return None

        parts = []
        if state:
            parts.append(
                f"사용자는 영어 학습 중. "
                f"레벨: {state.get('current_level', '?')}. "
                f"완료: {state.get('total_lessons', '?')}개 레슨."
            )
        if events:
            recent = [f"{e['data'].get('topic','?')} ({e['data'].get('score','?')}점)" for e in events[:3]]
            parts.append(f"최근 학습: {', '.join(recent)}")

        return "\n".join(parts) if parts else None

    def get_proactive_triggers(self, ctx: PatternContext) -> list[dict]:
        """Register daily commitment reminders."""
        return [
            {
                "type": "schedule_remind",
                "condition": "commitment 'daily' missed",
                "message_hint": "오늘 영어 공부 할 시간이야~",
            },
            {
                "type": "absence_remind",
                "condition": "3+ days without study",
                "message_hint": "요즘 바빠? 영어 좀 쉬고 있는 거야?",
            },
        ]


# --- Registration (add to chat.py) ---
#
# from app.sdk.patterns.language_tutor_pattern import LanguageTutorPattern
# registry.register(LanguageTutorPattern())
#
# --- Session management (call from your API) ---
#
# TutorService.start_session(avatar_id)   # When user enters lesson
# TutorService.end_session(avatar_id)     # When user leaves lesson
