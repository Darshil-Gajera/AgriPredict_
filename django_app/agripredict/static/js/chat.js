// chat.js — AgriBot floating chat widget

const chatToggle   = document.getElementById("chatToggle");
const chatBox      = document.getElementById("chatBox");
const chatClose    = document.getElementById("chatClose");
const chatInput    = document.getElementById("chatInput");
const chatSend     = document.getElementById("chatSend");
const chatMessages = document.getElementById("chatMessages");
const chatLang     = document.getElementById("chatLang");

if (!chatToggle) {
  // Widget not present on this page
} else {

  let history = [];  // [{role, content}, ...]
  let isOpen = false;

  chatToggle.addEventListener("click", () => {
    isOpen = !isOpen;
    chatBox.classList.toggle("d-none", !isOpen);
    if (isOpen) chatInput.focus();
  });

  chatClose.addEventListener("click", () => {
    isOpen = false;
    chatBox.classList.add("d-none");
  });

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  chatSend.addEventListener("click", sendMessage);

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage("user", text);
    history.push({ role: "user", content: text });
    chatInput.value = "";
    chatSend.disabled = true;

    const typingId = appendTyping();

    try {
      const payload = {
        message: text,
        history: history.slice(-20),
        language: chatLang ? chatLang.value : "en",
        merit_context: window._meritContext || null,
      };

      const res = await fetch("/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      removeTyping(typingId);

      const answer = data.answer || data.error || "Sorry, I couldn't get an answer.";
      appendMessage("bot", answer, data.sources || []);
      history.push({ role: "assistant", content: answer });

    } catch (err) {
      removeTyping(typingId);
      appendMessage("bot", "Network error. Please try again.");
    } finally {
      chatSend.disabled = false;
      chatInput.focus();
    }
  }

  function appendMessage(role, text, sources = []) {
    const div = document.createElement("div");
    div.className = `chat-msg ${role}`;

    let sourceHtml = "";
    if (sources.length) {
      sourceHtml = `<div class="chat-sources mt-1">
        <small class="text-muted">Sources: ${sources.slice(0, 3).join(", ")}</small>
      </div>`;
    }

    div.innerHTML = `<div class="bubble">${escapeHtml(text)}${sourceHtml}</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendTyping() {
    const id = "typing_" + Date.now();
    const div = document.createElement("div");
    div.className = "chat-msg bot";
    div.id = id;
    div.innerHTML = `<div class="bubble chat-typing"><span></span><span></span><span></span></div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
  }

  function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br>");
  }

  // Reuse getCookie from main.js (loaded first)
  function getCookie(name) {
    const v = `; ${document.cookie}`;
    const parts = v.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }

} // end if chatToggle
