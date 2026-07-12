from backend.sales_assistant.service import SalesAssistant

def main() -> None:
    a=SalesAssistant(); r=a.reply('Хочу консультацию буддолога','smoke')
    assert r.topic == 'psychologist' and r.answer
    r2=a.reply('Сколько стоит?','smoke')
    assert r2.needs_manager
    print('SMOKE PASSED')
if __name__ == '__main__': main()
