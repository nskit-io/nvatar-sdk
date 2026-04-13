"""
NVatar SDK — Python Client Example

Connect to NVatar from your own service.
This is for EXTERNAL integration — when your app calls NVatar APIs
rather than running code inside the NVatar server.

Use cases:
  - Mobile app connecting to NVatar avatar
  - Web service triggering avatar conversations
  - Backend service managing avatar sessions

Requirements:
  pip install httpx websockets
"""
import asyncio
import json
import httpx
import websockets


NVATAR_URL = "https://nvatar.nskit.io"  # or localhost:54444


class NVatarClient:
    """Simple client for NVatar SDK APIs."""

    def __init__(self, base_url: str = NVATAR_URL):
        self.base_url = base_url.rstrip("/")
        self.ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://")

    # --- Avatar Management ---

    async def create_avatar(self, user_id: str, name: str, persona: str, **kwargs) -> dict:
        """Create a new avatar."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/v1/avatars", json={
                "user_id": user_id,
                "name": name,
                "persona": persona,
                "mbti": kwargs.get("mbti"),
                "tone": kwargs.get("tone", "친근한"),
                "speech_level": kwargs.get("speech_level", "polite"),
                "language": kwargs.get("language", "ko"),
            })
            resp.raise_for_status()
            return resp.json()

    async def get_avatar(self, avatar_id: int) -> dict:
        """Get avatar details."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/api/v1/avatars/{avatar_id}")
            resp.raise_for_status()
            return resp.json()

    # --- SDK Session ---

    async def sdk_connect(self, avatar_id: int, save_franchise_memory: bool = True) -> dict:
        """Initialize SDK session for an avatar."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/v1/sdk/connect", json={
                "avatar_id": avatar_id,
                "save_franchise_memory": save_franchise_memory,
            })
            resp.raise_for_status()
            return resp.json()

    async def sdk_disconnect(self, avatar_id: int) -> dict:
        """End SDK session."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/v1/sdk/disconnect", json={
                "avatar_id": avatar_id,
            })
            resp.raise_for_status()
            return resp.json()

    # --- Chat via WebSocket ---

    async def chat(self, avatar_id: int, messages: list[str], on_response=None):
        """Send messages and receive responses via WebSocket.

        Args:
            avatar_id: Avatar to chat with
            messages: List of user messages to send
            on_response: Callback for each response (type, text)
        """
        uri = f"{self.ws_url}/ws/chat/{avatar_id}"

        async with websockets.connect(uri) as ws:
            # Receive initial messages (first meeting, proactive)
            await self._drain(ws, on_response, timeout=3)

            for msg in messages:
                await ws.send(json.dumps({"type": "message", "text": msg}))
                await self._drain(ws, on_response, timeout=15)

    async def _drain(self, ws, callback, timeout: float = 5):
        """Drain WebSocket messages until timeout."""
        import time
        start = time.time()
        while time.time() - start < timeout:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                msg_type = data.get("type", "")
                text = data.get("text", data.get("message", ""))
                if callback and text:
                    callback(msg_type, text)
            except asyncio.TimeoutError:
                continue


# ---------------------------------------------------------------------------
# Example Usage
# ---------------------------------------------------------------------------

async def main():
    client = NVatarClient("http://localhost:54444")

    # 1. Get avatar
    avatar = await client.get_avatar(155)
    avatar_data = avatar.get("response", avatar)
    print(f"Avatar: {avatar_data.get('name', 'unknown')}")

    # 2. Connect SDK session
    session = await client.sdk_connect(155, save_franchise_memory=True)
    print(f"SDK connected: {session}")

    # 3. Chat
    def on_msg(msg_type, text):
        print(f"  [{msg_type}] {text[:100]}")

    await client.chat(155, [
        "안녕! 오늘 기분 어때?",
        "요즘 영어 공부 하고 있는데 잘 되고 있는 거 같아?",
    ], on_response=on_msg)

    # 4. Disconnect
    await client.sdk_disconnect(155)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
