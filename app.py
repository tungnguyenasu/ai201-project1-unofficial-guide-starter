import sys
from pathlib import Path

import gradio as gr

# Allow app.py to import files from src/
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))

from query import ask

def handle_query(question: str):
    """
    Handles one user question from the Gradio interface.
    """
    try:
        result = ask(question)

        answer = result["answer"]

        sources = "\n".join(
            f"• {source}" for source in result["sources"]
        )

        retrieved_chunks = "\n\n".join(
            f"Rank {chunk['rank']} | "
            f"Distance: {chunk['distance']:.4f} | "
            f"Course: {chunk['metadata'].get('course')}\n"
            f"Source: {chunk['metadata'].get('source_file')}\n"
            f"{chunk['text']}"
            for chunk in result["retrieved_chunks"]
        )

        return answer, sources, retrieved_chunks

    except Exception as exc:
        return f"Error: {exc}", "", ""

with gr.Blocks(title="ASU CS Unofficial Guide") as demo:
    gr.Markdown("# ASU CS Unofficial Guide")
    gr.Markdown(
        "Ask a question about ASU Computer Science courses based on collected student-generated sources."
    )

    question = gr.Textbox(
        label="Your question",
        placeholder="Example: What makes CSE 310 difficult?",
        lines=2,
    )

    ask_button = gr.Button("Ask")

    answer = gr.Textbox(
        label="Grounded answer",
        lines=8,
    )

    sources = gr.Textbox(
        label="Retrieved sources",
        lines=6,
    )

    retrieved_chunks = gr.Textbox(
        label="Retrieved chunks for debugging/evaluation",
        lines=12,
    )

    ask_button.click(
        handle_query,
        inputs=question,
        outputs=[answer, sources, retrieved_chunks],
    )

    question.submit(
        handle_query,
        inputs=question,
        outputs=[answer, sources, retrieved_chunks],
    )

if __name__ == "__main__":
    demo.launch()
