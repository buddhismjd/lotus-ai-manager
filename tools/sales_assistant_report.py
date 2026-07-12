from backend.sales_assistant.service import SalesAssistant

def main() -> None:
    a=SalesAssistant(); queries=['тур в Непал','ваджра','консультация психолога-буддолога','контакты']
    print('AI BODHI MVP SALES ASSISTANT REPORT')
    for q in queries:
        r=a.reply(q,q)
        print(f'- {q}: topic={r.topic}, kind={r.kind}, manager={r.needs_manager}')
if __name__ == '__main__': main()
