from __future__ import annotations

from .service import PersonaOrchestrator


def run_cli() -> None:
    orchestrator = PersonaOrchestrator()
    print("Personas loaded:")
    for name in orchestrator.segment_names:
        print(f"- {name}")
    print("")
    print("Digite uma pergunta de negócio. Use 'sair' para encerrar.")
    while True:
        question = input("\nPergunta: ").strip()
        if not question:
            continue
        if question.lower() in {"sair", "exit", "quit"}:
            print("Encerrado.")
            break
        responses = orchestrator.ask(question)
        print("")
        for segment_name, answer in responses.items():
            print(f"[{segment_name}]")
            print(answer)
            print("")

