from backend.sales_assistant.service import get_sales_assistant

assistant = get_sales_assistant()
assistant.reset("ux-1-0")
reply = assistant.reply("В Тибет возите?", "ux-1-0")
print(f"tibet={reply.kind}, items={len(reply.items)}")
