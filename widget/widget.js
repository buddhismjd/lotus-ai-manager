(() => {
  "use strict";

  const config = {
    apiUrl: window.AI_BODHI_API_URL || "/api/sales/chat",
    sessionUrl: window.AI_BODHI_SESSION_URL || "/api/sales/session",
    resetUrl: window.AI_BODHI_RESET_URL || "/api/sales/reset",
    healthUrl: window.AI_BODHI_HEALTH_URL || "/widget/health",
    requestTimeoutMs: Number(window.AI_BODHI_REQUEST_TIMEOUT_MS || 20000),
    storageKey: "ai-bodhi-session-id",
    tokenStorageKey: "ai-bodhi-session-token",
  };

  const root = document.getElementById("ai-bodhi-widget");
  if (!root || root.dataset.initialized === "true") return;
  root.dataset.initialized = "true";

  const byId = (id) => document.getElementById(id);
  const toggle = byId("ai-bodhi-toggle");
  const badge = byId("ai-bodhi-badge");
  const panel = byId("ai-bodhi-panel");
  const closeButton = byId("ai-bodhi-close");
  const resetButton = byId("ai-bodhi-reset");
  const messages = byId("ai-bodhi-messages");
  const typing = byId("ai-bodhi-typing");
  const form = byId("ai-bodhi-form");
  const input = byId("ai-bodhi-input");
  const sendButton = byId("ai-bodhi-send");
  if (![toggle, panel, closeButton, messages, typing, form, input, sendButton].every(Boolean)) return;

  const createSessionId = () => `web-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  let sessionId;
  try {
    sessionId = window.localStorage.getItem(config.storageKey) || createSessionId();
    window.localStorage.setItem(config.storageKey, sessionId);
  } catch (_) { sessionId = createSessionId(); }

  let sessionToken = null;
  try { sessionToken = window.localStorage.getItem(config.tokenStorageKey); } catch (_) { sessionToken = null; }

  const saveSessionToken = (token) => {
    sessionToken = token || null;
    try {
      if (sessionToken) window.localStorage.setItem(config.tokenStorageKey, sessionToken);
      else window.localStorage.removeItem(config.tokenStorageKey);
    } catch (_) { /* private browsing can reject storage */ }
  };

  let loading = false;
  let unread = 0;
  let lastFailedMessage = "";

  const setBadge = (count) => {
    unread = Math.max(0, count);
    if (!badge) return;
    badge.hidden = unread === 0;
    badge.textContent = unread > 9 ? "9+" : String(unread);
  };

  const setOpen = (isOpen) => {
    panel.hidden = !isOpen;
    toggle.setAttribute("aria-expanded", String(isOpen));
    if (isOpen) { setBadge(0); window.setTimeout(() => input.focus(), 40); }
  };

  const setLoading = (isLoading) => {
    loading = isLoading;
    typing.hidden = !isLoading;
    input.disabled = isLoading;
    sendButton.disabled = isLoading;
    if (resetButton) resetButton.disabled = isLoading;
    if (isLoading) messages.scrollTop = messages.scrollHeight;
  };

  const resizeInput = () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 112)}px`;
  };

  const appendMessage = (text, type) => {
    const message = document.createElement("div");
    message.className = `ai-bodhi__message ai-bodhi__message--${type}`;
    message.textContent = text;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
    if (type === "assistant" && panel.hidden) setBadge(unread + 1);
  };

  const removeQuickActions = () => root.querySelector("[data-bodhi-quick-actions]")?.remove();

  const appendSuggestions = (suggestions) => {
    if (!Array.isArray(suggestions) || !suggestions.length) return;
    const box = document.createElement("div");
    box.className = "ai-bodhi__suggestions";
    suggestions.forEach((suggestion) => {
      if (!suggestion?.label) return;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "ai-bodhi__suggestion";
      button.textContent = suggestion.label;
      button.addEventListener("click", () => {
        box.remove();
        if (suggestion.url) window.open(suggestion.url, "_blank", "noopener,noreferrer");
        else if (suggestion.message) sendMessage(suggestion.message);
      });
      box.appendChild(button);
    });
    if (box.childElementCount) messages.appendChild(box);
  };

  const appendRetry = (messageText) => {
    const box = document.createElement("div");
    box.className = "ai-bodhi__retry";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ai-bodhi__suggestion";
    button.textContent = "Повторить отправку";
    button.addEventListener("click", () => {
      box.remove();
      sendMessage(messageText);
    });
    box.appendChild(button);
    messages.appendChild(box);
  };

  const fetchJson = async (url, options = {}) => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), config.requestTimeoutMs);
    try {
      const response = await fetch(url, {...options, signal: controller.signal});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } finally {
      window.clearTimeout(timeoutId);
    }
  };

  const appendCollection = (items) => {
    if (!Array.isArray(items) || items.length === 0) return;
    const groups = new Map();
    items.forEach((item) => {
      const label = item.group || "Подходящие варианты";
      if (!groups.has(label)) groups.set(label, []);
      groups.get(label).push(item);
    });
    groups.forEach((groupItems, groupLabel) => {
      const section = document.createElement("section");
      section.className = "ai-bodhi__collection-section";
      const heading = document.createElement("div");
      heading.className = "ai-bodhi__collection-title";
      heading.textContent = groupLabel;
      section.appendChild(heading);
      const collection = document.createElement("div");
      collection.className = "ai-bodhi__collection";
      groupItems.forEach((item) => {
        const card = document.createElement("article");
        card.className = "ai-bodhi__card";
        if (item.image_url) {
          const image = document.createElement("img");
          image.className = "ai-bodhi__card-image";
          image.src = item.image_url;
          image.alt = item.title || "Карточка";
          image.loading = "lazy";
          image.referrerPolicy = "no-referrer-when-downgrade";
          image.addEventListener("error", () => image.remove());
          card.appendChild(image);
        }
        const body = document.createElement("div");
        body.className = "ai-bodhi__card-body";
        const title = document.createElement("div");
        title.className = "ai-bodhi__card-title";
        title.textContent = item.title || "Без названия";
        body.appendChild(title);
        [item.dates, item.duration, item.direction, item.price, item.size, item.material, item.availability].filter(Boolean).forEach((value) => {
          const meta = document.createElement("div");
          meta.className = "ai-bodhi__card-meta";
          meta.textContent = value;
          body.appendChild(meta);
        });
        if (item.url) {
          const link = document.createElement("a");
          link.className = "ai-bodhi__card-link";
          link.href = item.url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          const defaultLabel = item.item_type === "tour" ? "Открыть тур" : item.item_type === "service" ? "Открыть услугу" : "Открыть товар";
          link.textContent = item.button_label || defaultLabel;
          body.appendChild(link);
        }
        card.appendChild(body);
        collection.appendChild(card);
      });
      section.appendChild(collection);
      messages.appendChild(section);
    });
    messages.scrollTop = messages.scrollHeight;
  };

  const sendMessage = async (text) => {
    const cleanText = String(text || "").trim();
    if (!cleanText || loading) return;
    removeQuickActions();
    appendMessage(cleanText, "user");
    setLoading(true);
    try {
      const payload = await fetchJson(config.apiUrl, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: cleanText, session_id: sessionId, session_token: sessionToken}),
      });
      if (payload.session_token) saveSessionToken(payload.session_token);
      appendMessage(payload.answer || "Сейчас не удалось подготовить ответ.", "assistant");
      appendCollection(payload.items || []);
      appendSuggestions(payload.suggestions || []);
    } catch (error) {
      console.error("AI Bodhi widget error:", error);
      lastFailedMessage = cleanText;
      const timeout = error?.name === "AbortError";
      appendMessage(timeout ? "Ответ занял слишком много времени. Попробуйте отправить сообщение ещё раз." : "Не удалось связаться с помощником. Проверьте соединение и попробуйте ещё раз.", "error");
      appendRetry(lastFailedMessage);
    } finally {
      setLoading(false);
      input.focus();
    }
  };

  const restoreConversation = async () => {
    try {
      const payload = await fetchJson(`${config.sessionUrl}/${encodeURIComponent(sessionId)}`, {
        headers: sessionToken ? {"X-Session-Token": sessionToken} : {},
      });
      if (!Array.isArray(payload.messages) || payload.messages.length === 0) return;
      messages.replaceChildren();
      payload.messages.forEach((message) => {
        if (!message?.content) return;
        appendMessage(message.content, message.role === "user" ? "user" : "assistant");
      });
    } catch (error) { console.warn("AI Bodhi session restore skipped:", error); }
  };

  const resetConversation = async () => {
    if (loading || !window.confirm("Начать новый диалог? Текущая переписка будет закрыта.")) return;
    setLoading(true);
    try {
      await fetch(config.resetUrl, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({session_id: sessionId, session_token: sessionToken})});
    } catch (error) { console.warn("AI Bodhi reset request failed:", error); }
    try {
      sessionId = createSessionId();
      window.localStorage.setItem(config.storageKey, sessionId);
      saveSessionToken(null);
    } catch (_) { sessionId = createSessionId(); saveSessionToken(null); }
    messages.innerHTML = '<div class="ai-bodhi__message ai-bodhi__message--assistant ai-bodhi__welcome"><span class="ai-bodhi__welcome-title">Новый диалог начат</span>Чем я могу помочь?</div>';
    setLoading(false);
    input.focus();
  };

  const checkBackend = async () => {
    try { await fetchJson(config.healthUrl); }
    catch (error) { console.warn("AI Bodhi backend health check failed:", error); }
  };

  checkBackend();
  restoreConversation();
  root.querySelectorAll("[data-message]").forEach((button) => button.addEventListener("click", () => sendMessage(button.dataset.message)));
  toggle.addEventListener("click", () => setOpen(panel.hidden));
  closeButton.addEventListener("click", () => setOpen(false));
  resetButton?.addEventListener("click", resetConversation);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    resizeInput();
    await sendMessage(text);
  });
  input.addEventListener("input", resizeInput);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); }
    if (event.key === "Escape") setOpen(false);
  });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !panel.hidden) setOpen(false); });
})();
