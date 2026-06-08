from pathlib import Path
import json
import re
import html
from typing import List, Dict

RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "chunks.jsonl"

TARGET_CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
MIN_CHUNK_SIZE = 120

def extract_source_url(text: str) -> str:
    """
    Finds the first Source URL line in a raw document.
    """
    for line in text.splitlines():
        if line.lower().startswith("source url"):
            return line.split(":", 1)[1].strip()
    return "Unknown source"

def extract_course_from_filename(path: Path) -> str:
    """
    Example: cse310_reviews.txt -> CSE 310
    """
    match = re.search(r"(cse)(\d+)", path.stem, re.IGNORECASE)
    if match:
        return f"{match.group(1).upper()} {match.group(2)}"
    return "Unknown course"

def clean_text(text: str) -> str:
    """
    Cleans copied Reddit / student discussion text.
    Keeps only the actual student-generated content.
    """
    text = html.unescape(text)
    text = text.lstrip("\ufeff")
    text = text.replace("```", "")
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove everything after Notes for RAG because that is not source evidence
    text = re.split(r"\n\s*Notes for RAG\s*:", text, flags=re.IGNORECASE)[0]

    lines = []
    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        lower = line.lower()

        # Remove metadata/header lines from embedded content
        if lower.startswith("title:"):
            continue
        if lower.startswith("source url"):
            continue
        if lower.startswith("source type"):
            continue
        if lower.startswith("student-generated text"):
            continue

        lines.append(line)

    cleaned = "\n\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    return cleaned.strip()

def split_long_text_with_overlap(text: str, target_size: int, overlap: int) -> List[str]:
    """
    Splits long text by sentence-ish boundaries with overlap.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 > target_size and len(current) >= MIN_CHUNK_SIZE:
            chunks.append(current.strip())

            # Create overlap from the end of previous chunk
            overlap_text = current[-overlap:] if current else ""
            current = f"{overlap_text} {sentence}".strip()
        else:
            current = f"{current} {sentence}".strip() if current else sentence

    if len(current.strip()) >= MIN_CHUNK_SIZE:
        chunks.append(current.strip())

    return chunks

def chunk_document(text: str) -> List[str]:
    """
    Paragraph-aware chunking.
    For short documents, keep the whole document as one chunk.
    For longer documents, split by paragraphs without cutting words.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= TARGET_CHUNK_SIZE:
            current = f"{current}\n\n{paragraph}".strip() if current else paragraph
        else:
            if len(current.strip()) >= MIN_CHUNK_SIZE:
                chunks.append(current.strip())

            current = paragraph

    if len(current.strip()) >= MIN_CHUNK_SIZE:
        chunks.append(current.strip())

    return chunks

def load_and_chunk_documents() -> List[Dict]:
    """
    Loads every .txt file from data/raw and returns structured chunks.
    """
    all_chunks = []

    raw_files = sorted(RAW_DIR.glob("*.txt"))

    if not raw_files:
        raise FileNotFoundError(
            "No .txt files found in data/raw. Add your source files before running ingestion."
        )

    for file_path in raw_files:
        raw_text = file_path.read_text(encoding="utf-8")
        source_url = extract_source_url(raw_text)
        course = extract_course_from_filename(file_path)

        cleaned = clean_text(raw_text)
        chunks = chunk_document(cleaned)

        for index, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "id": f"{file_path.stem}_chunk_{index}",
                    "text": chunk,
                    "metadata": {
                        "source_file": str(file_path),
                        "source_url": source_url,
                        "course": course,
                        "chunk_index": index,
                    },
                }
            )

    return all_chunks

def save_chunks(chunks: List[Dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

def print_sample_chunks(chunks: List[Dict], sample_count: int = 5) -> None:
    print("\n==============================")
    print(f"Total chunks created: {len(chunks)}")
    print("==============================\n")

    for chunk in chunks[:sample_count]:
        print("-------- SAMPLE CHUNK --------")
        print(f"ID: {chunk['id']}")
        print(f"Course: {chunk['metadata']['course']}")
        print(f"Source file: {chunk['metadata']['source_file']}")
        print(f"Source URL: {chunk['metadata']['source_url']}")
        print()
        print(chunk["text"])
        print("------------------------------\n")

def main():
    chunks = load_and_chunk_documents()
    save_chunks(chunks)
    print_sample_chunks(chunks)

    print(f"Saved chunks to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
