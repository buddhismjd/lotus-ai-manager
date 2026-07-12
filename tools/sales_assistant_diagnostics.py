from backend.sales_assistant.service import SalesAssistant

def main() -> None:
    assistant=SalesAssistant()
    probes=("Есть тур на Кайлас?","Есть ваджра?","Хочу консультацию буддолога","Как связаться?")
    print("AI BODHI SALES ASSISTANT DIAGNOSTICS")
    for i,q in enumerate(probes,1):
        r=assistant.reply(q,f"diag-{i}")
        print(f"{i}. topic={r.topic} kind={r.kind} manager={r.needs_manager}")
if __name__ == '__main__': main()
