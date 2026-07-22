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
          card.appendChild(image);
        }

        const body = document.createElement("div");
        body.className = "ai-bodhi__card-body";

        const title = document.createElement("div");
        title.className = "ai-bodhi__card-title";
        title.textContent = item.title || "Без названия";
        body.appendChild(title);

        if (item.description) {
          const description = document.createElement("div");
          description.className = "ai-bodhi__card-description";
          description.textContent = item.description;
          body.appendChild(description);
        }

        [item.price, item.size, item.material, item.availability]
          .filter(Boolean)
          .forEach((value) => {
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
          link.textContent = item.button_label || (item.item_type === "tour" ? "Открыть тур" : "Открыть товар");
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
      appendCollection(payload.items || []);
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
