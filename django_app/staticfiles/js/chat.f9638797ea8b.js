/**
 * AgriBot Premium Chat Widget
 * Matches AgriPredict's glassmorphism + Space Grotesk aesthetic
 * Posts to: /api/chat/
 */

(function () {
  "use strict";

  const CHAT_URL = "/api/chat/";
  const MAX_HISTORY = 10;

  let history = [];
  let isTyping = false;
  let isOpen = false;
  let currentLang = (typeof USER_LANG !== "undefined" && USER_LANG === "gu") ? "gu" : "en";

  const toggleBtn  = document.getElementById("chatToggle");
  const chatPanel  = document.getElementById("chatPanel");
  const messagesEl = document.getElementById("chatMessages");
  const inputEl    = document.getElementById("chatInput");
  const sendBtn    = document.getElementById("chatSend");
  const closeBtn   = document.getElementById("chatClose");
  const langBtn    = document.getElementById("chatLang");
  const chipsEl    = document.getElementById("chatChips");

  if (!toggleBtn || !messagesEl || !inputEl || !sendBtn) return;

  const STRINGS = {
    en: {
      placeholder: "Ask about merit, colleges, scholarships…",
      welcome: "👋 Hi! I'm <strong>AgriBot</strong> — your Gujarat agriculture admissions guide. Ask me anything about merit scores, college cutoffs, scholarships, or the admission process.",
      error: "Sorry, couldn't reach AgriBot. Please try again.",
    },
    gu: {
      placeholder: "Merit, college, scholarship વિશે પૂછો…",
      welcome: "👋 નમસ્તે! હું <strong>AgriBot</strong> છું. Merit, college cutoffs, scholarships — કંઈ પણ પૂછો.",
      error: "AgriBot સુધી પહોંચી શક્યા નહીં. ફરી પ્રયત્ન કરો.",
    },
  };

  // ── Open / Close ──────────────────────────────────────────────────────────
  toggleBtn.addEventListener("click", () => {
    isOpen ? closePanel() : openPanel();
  });

  if (closeBtn) closeBtn.addEventListener("click", closePanel);

  function openPanel() {
    isOpen = true;
    chatPanel.style.display = "flex";
    requestAnimationFrame(() => chatPanel.classList.add("agb-open"));
    toggleBtn.innerHTML = `<i class="bi bi-x-lg"></i>`;
    inputEl.focus();
    scrollToBottom();
  }

  function closePanel() {
    isOpen = false;
    chatPanel.classList.remove("agb-open");
    setTimeout(() => { chatPanel.style.display = "none"; }, 300);
    toggleBtn.innerHTML = `<i class="bi bi-robot"></i><span class="agb-toggle-label">AgriBot</span>`;
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function getCookie(name) {
    const val = `; ${document.cookie}`;
    const parts = val.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  function scrollToBottom() {
    requestAnimationFrame(() => { messagesEl.scrollTop = messagesEl.scrollHeight; });
  }

  function appendMessage(role, html) {
    const wrapper = document.createElement("div");
    wrapper.className = `agb-msg agb-msg--${role}`;

    if (role === "assistant") {
      const avatar = document.createElement("div");
      avatar.className = "agb-avatar-sm";
      avatar.textContent = "🤖";
      wrapper.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = "agb-bubble";
    bubble.innerHTML = html;
    wrapper.appendChild(bubble);

    messagesEl.appendChild(wrapper);
    requestAnimationFrame(() => wrapper.classList.add("agb-msg--in"));
    scrollToBottom();
    return wrapper;
  }

  function showTyping() {
    if (isTyping) return;
    isTyping = true;
    const el = appendMessage("assistant", `<span class="agb-dot"></span><span class="agb-dot"></span><span class="agb-dot"></span>`);
    el.id = "agbTyping";
  }

  function hideTyping() {
    isTyping = false;
    const el = document.getElementById("agbTyping");
    if (el) el.remove();
  }

  function escapeHtml(s) {
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  function formatAnswer(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`(.*?)`/g, "<code>$1</code>")
      .replace(/\n\n/g, "</p><p>")
      .replace(/\n/g, "<br>")
      .replace(/✓/g, '<span style="color:var(--primary)">✓</span>')
      .replace(/^/, "<p>").replace(/$/, "</p>");
  }

  // ── Language toggle ───────────────────────────────────────────────────────
  if (langBtn) {
    langBtn.addEventListener("click", () => {
      currentLang = currentLang === "en" ? "gu" : "en";
      langBtn.textContent = currentLang === "en" ? "ગુ" : "EN";
      inputEl.placeholder = STRINGS[currentLang].placeholder;
    });
  }

  // ── Chips ─────────────────────────────────────────────────────────────────
  if (chipsEl) {
    chipsEl.addEventListener("click", (e) => {
      const chip = e.target.closest(".agb-chip");
      if (!chip) return;
      inputEl.value = chip.dataset.q;
      chipsEl.style.display = "none";
      sendMessage();
    });
  }

  // ── Auto-resize textarea ──────────────────────────────────────────────────
  inputEl.addEventListener("input", () => {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 100) + "px";
  });

  // ── Send ──────────────────────────────────────────────────────────────────
  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isTyping) return;

    inputEl.value = "";
    inputEl.style.height = "auto";
    inputEl.disabled = true;
    sendBtn.disabled = true;
    if (chipsEl) chipsEl.style.display = "none";

    appendMessage("user", escapeHtml(text));
    showTyping();

    const payload = { message: text, language: currentLang, history: history.slice(-MAX_HISTORY) };

    const widget = document.getElementById("chatWidget");
    if (widget) {
      if (widget.dataset.merit)           payload.user_merit       = parseFloat(widget.dataset.merit);
      if (widget.dataset.category)        payload.user_category    = widget.dataset.category;
      if (widget.dataset.studentCategory) payload.student_category = widget.dataset.studentCategory;
    }

    try {
      const res = await fetch(CHAT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      hideTyping();
      appendMessage("assistant", formatAnswer(data.answer || STRINGS[currentLang].error));
      history.push({ role: "user", content: text });
      history.push({ role: "assistant", content: data.answer || "" });
      if (history.length > MAX_HISTORY * 2) history = history.slice(-MAX_HISTORY * 2);
    } catch (err) {
      hideTyping();
      appendMessage("assistant", `<span style="color:#ef4444">${STRINGS[currentLang].error}</span>`);
      console.error("AgriBot:", err);
    } finally {
      inputEl.disabled = false;
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  sendBtn.addEventListener("click", sendMessage);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  // ── Welcome ───────────────────────────────────────────────────────────────
  appendMessage("assistant", STRINGS[currentLang].welcome);

})();