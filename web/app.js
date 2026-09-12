const API_BASE = window.VOICE_AGENT_API || "http://localhost:8000";
const messages = document.getElementById("messages");
const input = document.getElementById("message");
const statusEl = document.getElementById("status");
const sendButton = document.getElementById("send");
const micButton = document.getElementById("mic");
const clearButton = document.getElementById("clear");
const sessionId = crypto.randomUUID ? crypto.randomUUID() : `session-${Date.now()}`;

let socket = null;
let recognition = null;
let listening = false;

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

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "assistant") {
      addMessage("assistant", message.data.reply);
      speak(message.data.reply, message.data.language);
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

function speak(text, language) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const lang = language === "te" ? "te-IN" : language === "hi" ? "hi-IN" : "en-IN";
  utterance.lang = lang;
  utterance.rate = 0.98;
  window.speechSynthesis.speak(utterance);
}

function setupRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    micButton.disabled = true;
    document.getElementById("voiceHelp").textContent = "Browser voice recognition is unavailable here. Use typing or a browser that supports SpeechRecognition.";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-IN";

  recognition.onstart = () => {
    listening = true;
    micButton.textContent = "⏹ Stop";
  };
  recognition.onend = () => {
    listening = false;
    micButton.textContent = "🎙️ Voice";
  };
  recognition.onerror = () => {
    listening = false;
    micButton.textContent = "🎙️ Voice";
  };
  recognition.onresult = (event) => {
    input.value = event.results[0][0].transcript;
    sendText();
  };
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
  if (!recognition) return;
  if (listening) recognition.stop();
  else recognition.start();
});

connect();
setupRecognition();
addMessage("assistant", "Namaskaram! I’m your AI admissions counsellor. Which course or admission detail can I help you with?");
