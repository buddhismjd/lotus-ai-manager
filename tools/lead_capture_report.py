from backend.sales_assistant.dialogue import NextActionType
from backend.sales_assistant.state import DialogueStage

def main() -> None:
    print("AI BODHI SDM-3 — LEAD CAPTURE REPORT")
    print(f"Dialogue stages: {len(DialogueStage)}")
    print(f"Next actions: {len(NextActionType)}")
    print("Persistence: SQLite leads table")
    print("Required fields: name, contact method, contact value")

if __name__ == "__main__":
    main()
