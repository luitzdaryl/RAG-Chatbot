<template>
  <div class="app">
    <header class="header">
      <div class="header-inner">
        <div class="logo">
          <span class="logo-bracket">[</span>
          RAG
          <span class="logo-bracket">]</span>
        </div>
        <div class="status">
          <span class="status-dot" :class="{ active: isConnected }"></span>
          {{ isConnected ? 'CONNECTED' : 'OFFLINE' }}
        </div>
      </div>
    </header>

    <main class="chat-area" ref="chatContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">⬡</div>
        <p>Knowledge base is loaded.<br />Ask me anything.</p>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="message"
        :class="msg.role"
      >
        <div class="message-meta">
          <span class="role-tag">{{ msg.role === 'user' ? 'YOU' : 'RAG' }}</span>
          <span class="timestamp">{{ msg.time }}</span>
        </div>

        <div class="bubble">
          {{ msg.content }}
          <span v-if="msg.streaming" class="cursor">▍</span>
        </div>

        <div v-if="msg.sources && msg.sources.length" class="sources">
          <button class="sources-toggle" @click="msg.showSources = !msg.showSources">
            {{ msg.showSources ? '▲' : '▼' }} {{ msg.sources.length }} source{{ msg.sources.length > 1 ? 's' : '' }}
          </button>
          <div v-if="msg.showSources" class="sources-list">
            <div v-for="(src, j) in msg.sources" :key="j" class="source-item">
              <span class="source-score">{{ (src.similarity * 100).toFixed(0) }}%</span>
              <span class="source-text">{{ src.text }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="isLoading" class="message assistant">
        <div class="message-meta">
          <span class="role-tag">RAG</span>
        </div>
        <div class="bubble typing">
          <span></span><span></span><span></span>
        </div>
      </div>
    </main>

    <footer class="input-bar">
      <div class="input-inner">
        <textarea
          v-model="userInput"
          @keydown.enter.exact.prevent="sendMessage"
          placeholder="Ask the knowledge base..."
          :disabled="isLoading || isStreaming"
          rows="1"
          ref="inputRef"
        ></textarea>
        <button
          @click="sendMessage"
          :disabled="isLoading || isStreaming || !userInput.trim()"
          class="send-btn"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
      <p class="hint">Enter to send · Shift+Enter for new line</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'

const API_URL = 'http://localhost:8000'

const messages = ref([])
const userInput = ref('')
const isLoading = ref(false)    // shows typing dots before first token arrives
const isStreaming = ref(false)  // true while tokens are arriving
const isConnected = ref(false)
const chatContainer = ref(null)
const inputRef = ref(null)

// Check if backend is alive
onMounted(async () => {
  try {
    const res = await fetch(`${API_URL}/`)
    if (res.ok) isConnected.value = true
  } catch {
    isConnected.value = false
  }
  inputRef.value?.focus()
})

function getTime() {
  return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

async function sendMessage() {
  const text = userInput.value.trim()
  if (!text || isLoading.value || isStreaming.value) return

  // Add user message
  messages.value.push({ role: 'user', content: text, time: getTime() })
  userInput.value = ''
  isLoading.value = true
  await scrollToBottom()

  try {
    const res = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    })

    if (!res.ok) throw new Error(`Server error: ${res.status}`)

    const reader = res.body.getReader()
    const decoder = new TextDecoder()

    // Push an empty assistant message we'll stream tokens into
    messages.value.push({
      role: 'assistant',
      content: '',
      sources: [],
      showSources: false,
      streaming: true,
      time: getTime()
    })

    // Hide typing dots — tokens are about to arrive
    isLoading.value = false
    isStreaming.value = true

    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Each line is one JSON chunk from the server
      const lines = buffer.split('\n')
      buffer = lines.pop() // keep any incomplete line for next iteration

      for (const line of lines) {
        if (!line.trim()) continue
        try {
          const parsed = JSON.parse(line)

          if (parsed.type === 'sources') {
            messages.value.at(-1).sources = parsed.data
          } else if (parsed.type === 'token') {
            messages.value.at(-1).content += parsed.data
            await scrollToBottom()
          }
        } catch {
          // Incomplete JSON — skip and wait for more data
        }
      }
    }

    isConnected.value = true
  } catch (err) {
    // Remove empty assistant bubble if streaming never started
    if (messages.value.at(-1)?.content === '') {
      messages.value.pop()
    }
    messages.value.push({
      role: 'assistant',
      content: `⚠ Could not reach the backend. Is your server running at ${API_URL}?`,
      time: getTime()
    })
    isConnected.value = false
  } finally {
    // Hide the blinking cursor
    if (messages.value.at(-1)) {
      messages.value.at(-1).streaming = false
    }
    isLoading.value = false
    isStreaming.value = false
    await scrollToBottom()
    inputRef.value?.focus()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0d0f0e;
  --surface: #141614;
  --border: #232623;
  --border-bright: #2f332f;
  --text: #c8cfc8;
  --text-dim: #5a635a;
  --accent: #4ade80;
  --accent-dim: #1a3326;
  --user-bg: #161c16;
  --font-mono: 'IBM Plex Mono', monospace;
  --font-sans: 'IBM Plex Sans', sans-serif;
}

html, body { height: 100%; background: var(--bg); color: var(--text); }

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 780px;
  margin: 0 auto;
  font-family: var(--font-sans);
}

/* HEADER */
.header {
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  height: 52px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  background: var(--surface);
}
.header-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.logo {
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--accent);
}
.logo-bracket { color: var(--text-dim); }
.status {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.15em;
  color: var(--text-dim);
  display: flex;
  align-items: center;
  gap: 7px;
}
.status-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--text-dim);
  transition: background 0.4s;
}
.status-dot.active { background: var(--accent); box-shadow: 0 0 6px var(--accent); }

/* CHAT AREA */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 28px 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

.empty-state {
  margin: auto;
  text-align: center;
  color: var(--text-dim);
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.8;
}
.empty-icon {
  font-size: 36px;
  margin-bottom: 12px;
  color: var(--border-bright);
}

/* MESSAGE */
.message { display: flex; flex-direction: column; gap: 6px; max-width: 90%; }
.message.user { align-self: flex-end; align-items: flex-end; }
.message.assistant { align-self: flex-start; align-items: flex-start; }

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
}
.role-tag { color: var(--text-dim); }
.timestamp { color: var(--border-bright); }

.bubble {
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}
.message.user .bubble {
  background: var(--user-bg);
  border: 1px solid var(--border-bright);
  color: var(--text);
  border-bottom-right-radius: 1px;
}
.message.assistant .bubble {
  background: var(--accent-dim);
  border: 1px solid #235238;
  color: #b6f5cc;
  border-bottom-left-radius: 1px;
}

/* Blinking cursor shown while streaming */
.cursor {
  display: inline-block;
  color: var(--accent);
  animation: blink-cursor 0.7s steps(1) infinite;
}
@keyframes blink-cursor {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* TYPING INDICATOR (before first token) */
.bubble.typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 14px 18px;
}
.bubble.typing span {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: blink 1.2s infinite;
}
.bubble.typing span:nth-child(2) { animation-delay: 0.2s; }
.bubble.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink {
  0%, 80%, 100% { opacity: 0.2; transform: scale(0.9); }
  40% { opacity: 1; transform: scale(1.1); }
}

/* SOURCES */
.sources { margin-top: 4px; }
.sources-toggle {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-dim);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  padding: 4px 10px;
  border-radius: 3px;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}
.sources-toggle:hover { border-color: var(--accent); color: var(--accent); }
.sources-list { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.source-item {
  display: flex;
  gap: 10px;
  font-size: 12px;
  line-height: 1.5;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 3px;
  padding: 8px 10px;
}
.source-score {
  font-family: var(--font-mono);
  color: var(--accent);
  font-size: 11px;
  white-space: nowrap;
  padding-top: 1px;
}
.source-text { color: var(--text-dim); }

/* INPUT BAR */
.input-bar {
  border-top: 1px solid var(--border);
  padding: 16px 24px 12px;
  background: var(--surface);
  flex-shrink: 0;
}
.input-inner {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: var(--bg);
  border: 1px solid var(--border-bright);
  border-radius: 4px;
  padding: 10px 12px;
  transition: border-color 0.2s;
}
.input-inner:focus-within { border-color: var(--accent); }

textarea {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  max-height: 120px;
  overflow-y: auto;
}
textarea::placeholder { color: var(--text-dim); }
textarea:disabled { opacity: 0.4; }

.send-btn {
  background: var(--accent);
  border: none;
  border-radius: 3px;
  width: 34px; height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 0.2s, transform 0.1s;
  color: #0d0f0e;
}
.send-btn:hover:not(:disabled) { opacity: 0.85; }
.send-btn:active:not(:disabled) { transform: scale(0.94); }
.send-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.send-btn svg { width: 16px; height: 16px; }

.hint {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 7px;
  letter-spacing: 0.08em;
}
</style>