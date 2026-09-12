const API_BASE = window.VOICE_AGENT_API || "http://localhost:8000";
const messages = document.getElementById("messages");
const input = document.getElementById("message");
const statusEl = document.getElementById("status");
const sendButton = document.getElementById("send");
const micButton = document.getElementById("mic");
const clearButton = document.getElementById("clear");
const sessionId = crypto.randomUUID ? crypto.randomUUID() : `session-${Date.now()}`;

let socket = null;
let recorder = null;
let chunks = [];
let recording = false;

function addMessage(role, text) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = text;
  messages.appendChild(item);
  messages.scrollTop = messages.scrollHeight;
}

function connect() {
  const url = API_BASE.replace(/^http/, "ws") + `/ws/voice?session_id=${encodeURIComponent(sessionId)}`;
  socket = new WebSocket(url);

  socket.addEventListener("open", () => {
    statusEl.textContent = "Online";
    statusEl.className = "status online";
  });

  socket.addEventListener("message", async (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "assistant") {
      addMessage("user", message.transcript || "Voice message");
      addMessage("assistant", message.data.reply);
      if (message.audio_url) {
        const audio = new Audio(API_BASE + message.audio_url);
        audio.play().catch(() => {});
      }
    }
  });

  socket.addEventListener("close", () => {
    statusEl.textContent = "Offline";
    statusEl.className = "status";
    setTimeout(connect, 1500);
  });
}

function sendText() {
  const text = input.value.trim();
  if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;
  addMessage("user", text);
  socket.send(JSON.stringify({ type: "text", text, language: "auto" }));
  input.value = "";
}

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    document.getElementById("voiceHelp").textContent = "This browser does not support microphone recording. Use the text box or a modern browser over HTTPS/localhost.";
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  chunks = [];
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (event) => {
    if (event.data.size) chunks.push(event.data);
  };
  recorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop());
    const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
    const bytes = new Uint8Array(await blob.arrayBuffer());
    let binary = "";
    for (let i = 0; i < bytes.length; i += 0x8000) {
      binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    }
    if (socket?.readyState === WebSocket.OPEN) {
      const extension = blob.type.includes("ogg") ? ".ogg" : ".webm";
      socket.send(JSON.stringify({
        type: "audio_base64",
        data: btoa(binary),
        extension,
        language: "auto",
      }));
    }
    chunks = [];
  };
  recorder.start();
  recording = true;
  micButton.textContent = "⏹ Stop & Send";
}

function stopRecording() {
  if (recorder && recorder.state !== "inactive") {
    recorder.stop();
  }
  recording = false;
  micButton.textContent = "🎙️ Voice";
}

sendButton.addEventListener("click", sendText);
clearButton.addEventListener("click", () => {
  messages.innerHTML = "";
  input.value = "";
});
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendText();
  }
});
micButton.addEventListener("click", () => {
  if (recording) stopRecording();
  else startRecording().catch(() => {
    document.getElementById("voiceHelp").textContent = "Microphone permission was not granted or is unavailable.";
  });
});

connect();
addMessage("assistant", "Namaskaram! I’m your AI admissions counsellor. Which course or admission detail can I help you with?");
