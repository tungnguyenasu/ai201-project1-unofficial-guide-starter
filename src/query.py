import os
from typing import Dict, List, Any

from dotenv import load_dotenv
from groq import Groq

from vector_store import query_vector_store

load_dotenv()

MODEL_NAME = "llama-3.3-70b-versatile"

def format_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved chunks into numbered context blocks.
    """
    context_blocks = []

    for i, chunk in enumerate(chunks, start=1):
        metadata = chunk["metadata"]

        source_file = metadata.get("source_file", "Unknown file")
        source_url = metadata.get("source_url", "Unknown URL")
        course = metadata.get("course", "Unknown course")

        block = f"""
[Source {i}]
Course: {course}
Source file: {source_file}
Source URL: {source_url}
Text:
{chunk["text"]}
""".strip()

        context_blocks.append(block)

    return "\n\n---\n\n".join(context_blocks)

def build_prompt(question: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Builds a grounded prompt for the LLM.
    """
    context = format_context(chunks)

    return f"""
You are answering questions for an unofficial ASU Computer Science course guide.

Use ONLY the provided retrieved context to answer the user's question.
Do not use outside knowledge.
Do not guess.
If the context does not contain enough information to answer, say:
"I do not have enough information from the provided student sources to answer that."

When you answer, cite the source file or course name used.
Keep the answer concise but useful.

Retrieved context:
{context}

User question:
{question}

Answer:
""".strip()

def get_sources(chunks: List[Dict[str, Any]]) -> List[str]:
    """
    Creates a clean list of retrieved sources.
    """
    sources = []

    for chunk in chunks:
        metadata = chunk["metadata"]
        course = metadata.get("course", "Unknown course")
        source_file = metadata.get("source_file", "Unknown file")
        source_url = metadata.get("source_url", "Unknown URL")
        distance = chunk.get("distance", None)

        if distance is not None:
            source = f"{course} | {source_file} | distance={distance:.4f} | {source_url}"
        else:
            source = f"{course} | {source_file} | {source_url}"

        sources.append(source)

    return sources

def ask(question: str, top_k: int = 5) -> Dict[str, Any]:
    """
    End-to-end RAG function:
    1. retrieve chunks
    2. send grounded context to Groq
    3. return answer + sources
    """
    if not question.strip():
        return {
            "answer": "Please enter a question.",
            "sources": [],
            "retrieved_chunks": [],
        }

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Missing GROQ_API_KEY. Add it to your .env file.")

    retrieved_chunks = query_vector_store(question, top_k=top_k)

    # Optional safety check: if the best result is very weak, refuse before calling LLM.
    best_distance = retrieved_chunks[0]["distance"] if retrieved_chunks else 999

    if best_distance > 0.70:
        return {
            "answer": "I do not have enough information from the provided student sources to answer that.",
            "sources": get_sources(retrieved_chunks),
            "retrieved_chunks": retrieved_chunks,
        }

    prompt = build_prompt(question, retrieved_chunks)

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a grounded RAG assistant. "
                    "You must answer only from the retrieved context. "
                    "If the answer is not supported by the context, refuse."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=600,
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "sources": get_sources(retrieved_chunks),
        "retrieved_chunks": retrieved_chunks,
    }

if __name__ == "__main__":
    test_questions = [
        "What makes CSE 310 difficult?",
        "How should students prepare for CSE 340?",
        "Which dorm has the best food?",
    ]

    for question in test_questions:
        print("\n" + "=" * 80)
        print(f"QUESTION: {question}")
        print("=" * 80)

        result = ask(question)

        print("\nANSWER:")
        print(result["answer"])

        print("\nSOURCES:")
        for source in result["sources"]:
            print(f"- {source}")
