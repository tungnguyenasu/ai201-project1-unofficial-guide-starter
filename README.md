# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This project collects student-generated commentary about ASU Computer Science courses (course difficulty, workload, project expectations, professor helpfulness, and preparation advice) and exposes that information through a small RAG system. This knowledge is valuable because official course pages and syllabi rarely convey real student experiences — how much time assignments take, what exam formats look like, or which instructors provide effective support. As a CS student, I rely on informal advice when planning my schedule and preparing for courses, so aggregating and citing these sources makes that information easier to consult.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | r/ASU thread about CSE 110 | Reddit thread / raw text | data/raw/cse110_reviews.txt — https://www.reddit.com/r/ASU/comments/1cly644/cse_110/ |
| 2 | r/ASU thread comparing CSE 205 professors | Reddit thread / raw text | data/raw/cse205_reviews.txt — https://www.reddit.com/r/ASU/comments/qdk2wz/cse_205_feng_vs_navabi/ |
| 3 | r/ASU threads on CSE 230 | Reddit thread / raw text | data/raw/cse230_reviews.txt — https://www.reddit.com/r/ASU/comments/1apat4w/cse_230_makes_me_regret_coming_to_asu/ |
| 4 | r/ASU discussion about CSE 240 | Reddit thread / raw text | data/raw/cse240_reviews.txt — https://www.reddit.com/r/ASU/comments/1ixpih7/review_of_different_cs_professors/ |
| 5 | r/ASU threads on CSE 310 | Reddit thread / raw text | data/raw/cse310_reviews.txt — https://www.reddit.com/r/ASU/comments/e9q52j/anyone_nervous_about_taking_xue_for_cse_310/ |
| 6 | r/ASU preparation thread for CSE 340/355 | Reddit thread / raw text | data/raw/cse340_reviews.txt — https://www.reddit.com/r/ASU/comments/w89geu/how_to_prepare_for_cse_355_and_cse_340_what/ |
| 7 | r/ASU thread on preparing for CSE 355 | Reddit thread / raw text | data/raw/cse355_reviews.txt — https://www.reddit.com/r/ASU/comments/13yvlki/how_do_i_prepare_for_cse_355/ |
| 8 | r/ASU threads about CSE 360 workload | Reddit thread / raw text | data/raw/cse360_reviews.txt — https://www.reddit.com/r/ASU/comments/13c4dfj/cse_360_or_cse_365_with_cse_310_and_cse_230/ |
| 9 | r/ASU threads about CSE 365 | Reddit thread / raw text | data/raw/cse365_reviews.txt — https://www.reddit.com/r/ASU/comments/gdsrbw/cse_365_doable_during_summer/ |
| 10 | r/ASU discussion about CSE 412 | Reddit thread / raw text | data/raw/cse412_reviews.txt — https://www.reddit.com/r/ASU/comments/asyu8n/cse_412_database_management_with_dr_nakamura/ |

---

## Chunking Strategy

**Chunk size:**

This dataset contains short Reddit-style posts and summaries. During development I inspected sample documents and chose to produce one self-contained chunk per document because most raw files were already short and cohesive. Chunk size therefore varies by document (roughly 200–1,500 characters), but each chunk is human-readable and contains the course name, the core student opinion, and any supporting detail.

**Overlap:**

No overlap. Because each source file was small and I produced a single chunk per file, overlap was unnecessary and would have duplicated content across records.

**Why these choices fit your documents:**

The raw documents are short Reddit threads or thread excerpts. Fixed-length character splits produced poor fragments (half-sentences or mixed courses). Generating a single chunk per file preserves context and keeps retrieval results readable and citable.

**Final chunk count:**

10 chunks (one per file in `data/raw/`).

---

## Embedding Model

**Model used:**

`all-MiniLM-L6-v2` (sentence-transformers)

**Production tradeoff reflection:**

`all-MiniLM-L6-v2` is a small, fast, local model with good semantic performance for short documents and student-language text. It allowed offline embedding in the project environment without API costs. If deploying for real users and budget permitted, I'd evaluate larger models or API-based embeddings with better semantic resolution (e.g., OpenAI or other encoder models) to reduce confusions between semantically similar course descriptions. Tradeoffs: larger models increase cost and latency but often improve retrieval accuracy; API-hosted models avoid local GPU requirements but raise privacy and expense concerns.

---

## Grounded Generation

**System prompt grounding instruction:**

The system enforces grounding at three levels:

- Retrieval filtering: the top-k=5 chunks are returned by `query_vector_store()` and passed to the LLM.
- Pre-call refusal: if the best retrieved distance is > 0.70 the system returns a refusal string without calling the LLM: "I do not have enough information from the provided student sources to answer that." This prevents low-quality prompts from being sent.
- LLM instruction: the prompt instructs the model to use ONLY the retrieved context and to refuse when the context is insufficient. The exact user prompt built by `src/query.py::build_prompt()` is:

```
You are answering questions for an unofficial ASU Computer Science course guide.

Use ONLY the provided retrieved context to answer the user's question.
Do not use outside knowledge.
Do not guess.
If the context does not contain enough information to answer, say:
"I do not have enough information from the provided student sources to answer that."

When you answer, cite the source file or course name used.
Keep the answer concise but useful.

Retrieved context:
<formatted context blocks>

User question:
<question>

Answer:
```

An additional low-temperature call (`temperature=0.1`) is used to reduce creative or hallucinatory completions.

**How source attribution is surfaced in the response:**

The system returns a `sources` list (course, source file, distance, and URL) derived from retrieved chunk metadata. The LLM answer is also prompted to cite source file or course names; the Gradio UI and test scripts display the retrieved chunks and the `sources` list for human verification.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say is difficult about CSE 310? | Mention algorithm topics, runtime analysis/Big‑O, projects, C++ and the jump in difficulty | Answer cites the CSE 310 chunk: jump in difficulty, runtime analysis topics (Big O, heaps, graphs, red‑black trees), and study advice (start projects early, attend recitation) | Relevant (top result is `cse310_reviews.txt`) | Accurate |
| 2 | How should students prepare for CSE 340? | Start projects early, ask TAs, manage time carefully | Answer cites `cse340_reviews.txt`: start projects on day one and ask TAs for help during the project | Relevant (top result is `cse340_reviews.txt`) | Accurate |
| 3 | Why do students say CSE 355 is challenging? | Theory-style content (automata, Turing machines, proofs), need for office hours and outside resources | Answer cites `cse355_reviews.txt`: mentions automata, proof-style thinking, and recommendations (office hours, textbooks) | Relevant (top result is `cse355_reviews.txt`) | Accurate |
| 4 | What do students say about the workload in CSE 360? | Group project can be time-consuming; quizzes and homework vary; professor-dependent workload | Answer: notes group project can take a long time, but top retrieved chunk was `cse365_reviews.txt` and `cse360_reviews.txt` was ranked second; some mixing of nearby-course content occurred | Partially relevant (top result was `cse365_reviews.txt`, second was `cse360_reviews.txt`) | Partially accurate |
| 5 | Which classes should a student avoid taking together with too many other hard classes? | Point to time-consuming/difficult courses such as CSE 340, CSE 355, CSE 365, or CSE 310 depending on evidence | Answer: recommends avoiding `CSE 340` and `CSE 365` (sources include CSE 340, CSE 310, CSE 412, CSE 360, CSE 365) — reasonable but omits CSE 355 which also appears in the corpus | Partially relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** What do students say about the workload in CSE 360?

**What the system returned:**

The system correctly reported that the group project can take a long time, but the top retrieved chunk was `cse365_reviews.txt` (CSE 365) instead of `cse360_reviews.txt`. The answer therefore mixed content from related courses.

**Root cause (tied to a specific pipeline stage):**

This is a retrieval-stage failure. The `all-MiniLM-L6-v2` embeddings placed `cse365` and `cse360` content close in vector space because both discuss project workload, causing `cse365_reviews.txt` to rank higher. Contributing factors: (a) very small corpus (10 documents) so per-document signals dominate; (b) coarse chunking (one chunk per file) which reduces the number of distinct context pieces available for fine-grained ranking; (c) no metadata-based reranking to prefer exact course matches when present in the query.

**What you would change to fix it:**

1. Expand the corpus with more course-specific posts to strengthen per-course signals.
2. Use paragraph-aware chunking (or sentence-level splits for longer sources) so that course-specific sentences are separate retrieval targets.
3. Add a simple metadata reranker that boosts chunks whose `course` metadata exactly matches a detected course number in the question.
4. Evaluate a stronger embedding model or a hybrid lexical+semantic retriever.

---

## Spec Reflection

**One way the spec helped you during implementation:**

The `planning.md` document forced a clear, testable architecture: ingest → clean → chunk → embed → store → retrieve → generate → UI. That checklist made it straightforward to implement milestones incrementally, verify each stage (I inspected sample chunks before embedding), and design the evaluation (the five test questions in the plan were used verbatim). The chunking and retrieval strategy sections were especially helpful when deciding how to format metadata and what to return to the LLM.

**One way your implementation diverged from the spec, and why:**

I diverged from the original chunking plan: instead of producing ~800-character chunks with 150-character overlap, I generated one cleaned chunk per source file. The divergence was intentional: the raw files were short Reddit excerpts and fixed-size splitting produced fragmented, unreadable pieces. Producing a single chunk per file preserved readability and simpler metadata attribution. I documented this change in the Chunking Strategy section.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The `Documents` and `Chunking Strategy` sections from `planning.md` and a prompt asking for a Python ingestion + chunking script that reads `data/raw/*.txt`, removes headers, and outputs `data/processed/chunks.jsonl` with metadata fields (`source_file`, `source_url`, `course`).
- *What it produced:* An initial `ingest.py` implementation with a fixed-character chunking approach and some cleaning heuristics.
- *What I changed or overrode:* I replaced the fixed-character chunking with paragraph-aware logic and ultimately simplified to one chunk per document because the dataset files were short. I also tightened the cleaning function to remove Reddit-style metadata lines and extra boilerplate.

**Instance 2**

- *What I gave the AI:* A description of the desired grounded prompt, including the requirement that the model only use retrieved context and must refuse when evidence is lacking. I asked for a user/system prompt and a small Gradio UI layout.
- *What it produced:* A draft prompt and UI code (`app.py`) that showed the question input and an answer area.
- *What I changed or overrode:* I added a pre-call distance check (`best_distance > 0.70`) to refuse low-quality retrievals without calling the LLM, lowered `temperature` to 0.1, and adjusted the prompt wording to require explicit citation of source files or course names. I also refined the UI to display retrieved chunks for debugging.
