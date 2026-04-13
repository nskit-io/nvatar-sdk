"""
NVatar SDK — Minimal BehaviorPattern Example

The simplest possible pattern: echoes user input with avatar personality.
Use this as a starting point for your own pattern.

Usage:
  1. Copy this file to your NVatar server: app/sdk/patterns/
  2. Register in chat.py: registry.register(EchoPattern())
  3. Send a message containing "에코 테스트" to trigger it
"""
import asyncio
from app.sdk.pattern import (
    BehaviorPattern, GemmaMode, MemoryPolicy, PatternContext, PatternResult,
)
from app.service import gemma_service, prompt_builder


class EchoPattern(BehaviorPattern):
    """Minimal pattern — wraps user input in avatar's character voice."""

    @property
    def name(self) -> str:
        return "echo"

    @property
    def gemma_mode(self) -> GemmaMode:
        return GemmaMode.ASSISTED  # External logic + Gemma wrapping

    @property
    def memory_policy(self) -> MemoryPolicy:
        return MemoryPolicy.BOTH  # Save to core + franchise

    async def should_activate(self, ctx: PatternContext) -> bool:
        # Activate when user says "에코 테스트"
        return "에코 테스트" in ctx.user_text

    async def handle(self, ctx: PatternContext) -> PatternResult:
        # --- Your domain logic here ---
        # In a real pattern, this would call your external API
        domain_result = f"Echo: {ctx.user_text}"

        # --- Gemma wraps result in character voice ---
        extra_context = (
            f"[에코 테스트 모드. 사용자의 메시지를 따라하되, "
            f"캐릭터답게 재미있는 한마디를 덧붙여. 원문: '{ctx.user_text}']"
        )
        messages = prompt_builder.build_messages(
            ctx.avatar_id, ctx.user_text, extra_context=extra_context
        )
        await ctx.websocket.send_json({"type": "typing"})
        response = await asyncio.to_thread(
            gemma_service.chat_collect, messages, 128, False
        )
        if not response:
            response = f"따라하기~ {ctx.user_text} 😊"

        return PatternResult(
            response_text=response,
            franchise_events=[{
                "type": "event",
                "status": "success",
                "data": {"action": "echo", "original": ctx.user_text[:100]},
            }],
        )

    def get_franchise_context(self, avatar_id: int) -> str | None:
        # Optional: provide context for normal chat
        return None


# --- Registration (add to chat.py) ---
#
# from app.sdk.patterns.simple_pattern import EchoPattern
# registry.register(EchoPattern())
