(() => {
  "use strict";

  const config = {
    apiUrl:
      window.AI_BODHI_API_URL ||
      "http://127.0.0.1:8000/api/bodhi/chat",
  };

  const root = document.getElementById("ai-bodhi-widget");
  if (!root) return;

  const toggle = document.getElementById("ai-bodhi-toggle");
  const panel = document.getElementById("ai-bodhi-panel");
  const closeButton = document.getElementById("ai-bodhi-close");
  const messages = document.getElementById("ai-bodhi-messages");
  const typing = document.getElementById("ai-bodhi-typing");
  const form = document.getElementById("ai-bodhi-form");
  const input = document.getElementById("ai-bodhi-input");
  const sendButton = document.getElementById("ai-bodhi-send");

  const setOpen = (isOpen) => {
    panel.hidden = !isOpen;
    toggle.setAttribute("aria-expanded", String(isOpen));

    if (isOpen) {
      input.focus();
    }
  };

  const setLoading = (isLoading) => {
    typing.hidden = !isLoading;
    input.disabled = isLoading;
    sendButton.disabled = isLoading;

    if (isLoading) {
      messages.scrollTop = messages.scrollHeight;
    }
  };

  const appendMessage = (text, type) => {
    const message = document.createElement("div");
    message.className =
      `ai-bodhi__message ai-bodhi__message--${type}`;
    message.textContent = text;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
  };

  const sendMessage = async (text) => {
    appendMessage(text, "user");
    setLoading(true);

    try {
      const response = await fetch(config.apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = await response.json();
      appendMessage(
        payload.answer || "Сейчас я не смог подготовить ответ.",
        "assistant",
      );
    } catch (error) {
      console.error("AI Bodhi widget error:", error);
      appendMessage(
        "Не удалось связаться с AI Бодхи. "
          + "Пожалуйста, попробуйте ещё раз немного позже.",
        "error",
      );
    } finally {
      setLoading(false);
      input.focus();
    }
  };

  toggle.addEventListener("click", () => {
    setOpen(panel.hidden);
  });

  closeButton.addEventListener("click", () => {
    setOpen(false);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    await sendMessage(text);
  });

  input.addEventListener("keydown", (event) => {
    if (
      event.key === "Enter"
      && !event.shiftKey
    ) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
})();
