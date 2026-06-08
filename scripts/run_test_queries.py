import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
sys.path.append(str(SRC_DIR))

from query import ask

questions = [
    "What makes CSE 310 difficult?",
    "How should students prepare for CSE 340?",
    "Why do students say CSE 355 is challenging?",
    "What do students say about the workload in CSE 360?",
    "Which classes should a student avoid taking together with too many other hard classes?",
]

for q in questions:
    print("=" * 80)
    print(f"QUESTION: {q}")
    print("=" * 80)
    try:
        res = ask(q)
        print("ANSWER:\n")
        print(res.get("answer"))
        print("\nSOURCES:")
        for s in res.get("sources", []):
            print(f"- {s}")
        print("\nRETRIEVED CHUNKS:")
        for c in res.get("retrieved_chunks", []):
            print(f"Rank {c['rank']} | distance={c['distance']:.4f} | file={c['metadata'].get('source_file')}")
            print(c['text'][:300].replace('\n',' ') + ('...' if len(c['text'])>300 else ''))
            print()
    except Exception as e:
        print(f"Error running ask(): {e}")

print("Test queries finished.")
