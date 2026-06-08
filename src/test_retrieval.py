from vector_store import query_vector_store

TEST_QUERIES = [
    "What makes CSE 310 difficult?",
    "How should students prepare for CSE 340?",
    "Why do students say CSE 355 is challenging?",
    "What is the workload like in CSE 360?",
    "Which classes should I avoid taking with too many other hard classes?",
]


def print_results(query: str, top_k: int = 5) -> None:
    print("\n" + "=" * 90)
    print(f"QUERY: {query}")
    print("=" * 90)

    results = query_vector_store(query, top_k=top_k)

    for result in results:
        metadata = result["metadata"]

        print(f"\nRank: {result['rank']}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Course: {metadata.get('course')}")
        print(f"Source file: {metadata.get('source_file')}")
        print(f"Source URL: {metadata.get('source_url')}")
        print("\nChunk:")
        print(result["text"])
        print("-" * 90)


def main():
    for query in TEST_QUERIES:
        print_results(query, top_k=5)


if __name__ == "__main__":
    main()
