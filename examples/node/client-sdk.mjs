/**
 * NVatar SDK — Node.js Client Example
 *
 * Connect to NVatar from your Node.js/Bun service.
 * Uses native fetch + WebSocket for zero dependencies.
 *
 * Usage:
 *   node client-sdk.mjs
 *   # or
 *   bun run client-sdk.mjs
 *
 * Requirements:
 *   Node.js 18+ (native fetch + WebSocket)
 *   or Bun (any version)
 */

const NVATAR_URL = process.env.NVATAR_URL || 'http://localhost:54444';
const WS_URL = NVATAR_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// ---------------------------------------------------------------------------
// NVatar Client
// ---------------------------------------------------------------------------

class NVatarClient {
  constructor(baseUrl = NVATAR_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.wsUrl = this.baseUrl.replace('https://', 'wss://').replace('http://', 'ws://');
  }

  // --- Avatar ---

  async getAvatar(avatarId) {
    const res = await fetch(`${this.baseUrl}/api/v1/avatars/${avatarId}`);
    if (!res.ok) throw new Error(`getAvatar failed: ${res.status}`);
    return res.json();
  }

  async createAvatar({ userId, name, persona, mbti, tone = '친근한', language = 'ko' }) {
    const res = await fetch(`${this.baseUrl}/api/v1/avatars`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId, name, persona, mbti, tone,
        speech_level: 'polite', language,
      }),
    });
    if (!res.ok) throw new Error(`createAvatar failed: ${res.status}`);
    return res.json();
  }

  // --- SDK Session ---

  async sdkConnect(avatarId, { saveFranchiseMemory = true } = {}) {
    const res = await fetch(`${this.baseUrl}/api/v1/sdk/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        avatar_id: avatarId,
        save_franchise_memory: saveFranchiseMemory,
      }),
    });
    if (!res.ok) throw new Error(`sdkConnect failed: ${res.status}`);
    return res.json();
  }

  async sdkDisconnect(avatarId) {
    const res = await fetch(`${this.baseUrl}/api/v1/sdk/disconnect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ avatar_id: avatarId }),
    });
    if (!res.ok) throw new Error(`sdkDisconnect failed: ${res.status}`);
    return res.json();
  }

  // --- Chat via WebSocket ---

  async chat(avatarId, messages, { onResponse, timeout = 15000 } = {}) {
    const ws = new WebSocket(`${this.wsUrl}/ws/chat/${avatarId}`);

    return new Promise((resolve, reject) => {
      const responses = [];

      ws.onmessage = (event) => {
        let data;
        try { data = JSON.parse(event.data); } catch { return; }
        const text = data.text || data.message || '';
        if (text && onResponse) {
          onResponse(data.type, text);
        }
        if (text) responses.push({ type: data.type, text });
      };

      ws.onopen = async () => {
        // Wait for initial messages (first meeting, proactive)
        await sleep(3000);

        for (const msg of messages) {
          ws.send(JSON.stringify({ type: 'message', text: msg }));
          await sleep(timeout);  // Wait for response
        }

        ws.close();
        resolve(responses);
      };

      ws.onerror = (err) => reject(err);
    });
  }
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ---------------------------------------------------------------------------
// Example
// ---------------------------------------------------------------------------

async function main() {
  const client = new NVatarClient();

  // 1. Get avatar info
  const avatar = await client.getAvatar(155);
  const avatarData = avatar.response || avatar;
  console.log(`Avatar: ${avatarData.name || 'unknown'}`);

  // 2. Connect SDK
  const session = await client.sdkConnect(155, { saveFranchiseMemory: true });
  console.log('SDK connected:', session.ok);

  // 3. Chat
  const responses = await client.chat(155, [
    '안녕! 오늘 기분 어때?',
    '요즘 뭐 하고 지내?',
  ], {
    onResponse: (type, text) => {
      console.log(`  [${type}] ${text.slice(0, 100)}`);
    },
    timeout: 12000,
  });

  console.log(`\nTotal responses: ${responses.length}`);

  // 4. Disconnect
  await client.sdkDisconnect(155);
  console.log('Done!');
}

main().catch(console.error);
