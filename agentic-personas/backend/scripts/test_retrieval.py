from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.retriever import retrieve_context


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona-id", type=int, required=True)
    parser.add_argument("--question", required=True)
    args = parser.parse_args()

    results = retrieve_context(args.question, args.persona_id)
    for item in results:
        print(f"doc_id={item.doc_id}")
        print(f"persona_id={item.persona_id}")
        print(f"doc_type={item.doc_type}")
        print(f"confidence={item.confidence}")
        print(f"source_file={item.source_file}")
        print(f"score={item.score}")
        print(item.content[:400].replace("\n", " "))
        print("")


if __name__ == "__main__":
    main()

