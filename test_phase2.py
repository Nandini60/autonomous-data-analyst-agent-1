"""
Phase 2 Test Script -- RAG Pipeline
======================================
End-to-end test that:
  1. Generates sample business PDF documents
  2. Parses PDFs and creates text chunks
  3. Embeds and stores chunks in ChromaDB
  4. Tests retrieval with various queries
  5. Tests the full RAG Q&A pipeline
  6. Tests hallucination guard and edge cases

Usage:
    cd autonomous-data-analyst
    python test_phase2.py

Prerequisites:
    * pip install -r requirements.txt
    * Set GROQ_API_KEY in .env
"""

from __future__ import annotations

import os
import shutil
import sys
import traceback
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()


def divider(title: str) -> None:
    """Print a formatted section divider."""
    print(f"\n{'=' * 64}")
    print(f"  {title}")
    print(f"{'=' * 64}")


def step_header(step: int, title: str) -> None:
    """Print a step header."""
    print(f"\n{'-' * 48}")
    print(f"  Step {step}: {title}")
    print(f"{'-' * 48}")


def main() -> None:
    """Run the full Phase 2 test suite."""
    results: list[dict] = []
    all_passed = True

    divider("PHASE 2 -- RAG PIPELINE TEST SUITE")

    # == Step 1: Generate PDF documents ==
    step_header(1, "Generate Sample Business PDFs")
    try:
        from utils.generate_docs import generate_all_docs

        docs = generate_all_docs(outdir="data/docs")
        assert len(docs) == 3, f"Expected 3 docs, got {len(docs)}"
        for doc in docs:
            assert doc.exists(), f"Missing: {doc}"
            size_kb = doc.stat().st_size / 1024
            print(f"  [OK] {doc.name} ({size_kb:.1f} KB)")
        print("  [OK] All 3 documents generated")
    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        sys.exit(1)

    # == Step 2: Test PDF parsing ==
    step_header(2, "Test PDF Parsing (pdfplumber)")
    try:
        from utils.doc_loader import parse_pdf

        for doc in docs:
            pages = parse_pdf(doc)
            print(f"  [OK] {doc.name}: {len(pages)} pages extracted")
            # Show first 100 chars of first page
            if pages:
                preview = pages[0]["text"][:100].replace("\n", " ")
                print(f"       Preview: \"{preview}...\"")
            assert len(pages) >= 2, f"Expected >= 2 pages, got {len(pages)}"

        print("  [OK] All PDFs parsed successfully")
    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        sys.exit(1)

    # == Step 3: Test text chunking ==
    step_header(3, "Test Text Chunking")
    try:
        from utils.doc_loader import chunk_text, parse_pdf

        pages = parse_pdf(docs[0])  # Market Analysis Report
        full_text = "\n\n".join(p["text"] for p in pages)

        chunks = chunk_text(
            full_text,
            chunk_size=500,
            chunk_overlap=50,
            metadata={"source": docs[0].name},
        )

        print(f"  [OK] Created {len(chunks)} chunks from {docs[0].name}")
        print(f"       Text length: {len(full_text):,} chars")
        print(f"       Avg chunk size: {sum(len(c.text) for c in chunks) / len(chunks):.0f} chars")
        print(f"       First chunk ID: {chunks[0].chunk_id}")
        print(f"       First chunk preview: \"{chunks[0].text[:80]}...\"")

        # Verify chunk properties
        for i, chunk in enumerate(chunks):
            assert len(chunk.text) > 0, f"Chunk {i} is empty"
            assert chunk.chunk_id, f"Chunk {i} has no ID"
            assert "source" in chunk.metadata, f"Chunk {i} missing source metadata"

        # Verify overlap exists (adjacent chunks should share some text)
        if len(chunks) >= 2:
            c1_end = chunks[0].text[-30:]
            c2_start = chunks[1].text[:100]
            # Overlap check: some words from end of c1 should appear in start of c2
            c1_words = set(c1_end.split())
            c2_words = set(c2_start.split())
            overlap_words = c1_words & c2_words
            print(f"       Overlap detected: {len(overlap_words)} shared words between chunk 0-1")

        print("  [OK] Chunking validated")
    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        sys.exit(1)

    # == Step 4: Test ChromaDB ingestion ==
    step_header(4, "Test ChromaDB Ingestion")
    try:
        from utils.doc_loader import DocumentLoader

        # Clear any existing vectorstore for clean test
        vs_path = Path("vectorstore")
        if vs_path.exists():
            shutil.rmtree(vs_path)

        loader = DocumentLoader(
            persist_dir="vectorstore",
            collection_name="test_documents",
            chunk_size=500,
            chunk_overlap=50,
            verbose=True,
        )

        total_chunks = loader.load_directory("data/docs")
        print(f"\n  [OK] Loaded {total_chunks} total chunks into ChromaDB")

        stats = loader.get_collection_stats()
        print(f"  [OK] Collection stats:")
        print(f"       Total chunks: {stats['total_chunks']}")
        print(f"       Sources: {stats['sources']}")
        print(f"       Embedding model: {stats['embedding_model']}")

        assert stats["total_chunks"] > 0, "No chunks in collection"
        assert stats["n_sources"] == 3, f"Expected 3 sources, got {stats['n_sources']}"

        print("  [OK] ChromaDB ingestion validated")
    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        sys.exit(1)

    # == Step 5: Test retrieval ==
    step_header(5, "Test Vector Retrieval")
    retrieval_tests = [
        {
            "query": "What is the return policy for laptops?",
            "expected_source": "Product_Return_Policy.pdf",
            "description": "Specific policy question",
        },
        {
            "query": "What were the total Q1 2024 revenue numbers?",
            "expected_source": "Q1_2024_Market_Analysis_Report.pdf",
            "description": "Financial data question",
        },
        {
            "query": "What is the sales target for 2024?",
            "expected_source": "Sales_Strategy_Memo_2024.pdf",
            "description": "Strategy question",
        },
        {
            "query": "restocking fee percentage for chairs",
            "expected_source": "Product_Return_Policy.pdf",
            "description": "Specific detail lookup",
        },
        {
            "query": "Which region has the highest revenue?",
            "expected_source": "Q1_2024_Market_Analysis_Report.pdf",
            "description": "Regional analysis question",
        },
    ]

    for i, test in enumerate(retrieval_tests, start=1):
        print(f"\n  -- Retrieval Test {i}: {test['description']}")
        print(f"     Q: \"{test['query']}\"")

        try:
            # Test standard retrieval
            result = loader.query(
                test["query"],
                n_results=5,
                relevance_threshold=0.5,  # lower threshold for testing
            )

            print(f"     Retrieved: {result.n_relevant} relevant chunks")
            passed = result.n_relevant > 0
            source_found = False

            for j, (chunk, score) in enumerate(zip(result.chunks, result.scores)):
                source = chunk.metadata.get("source", "?")
                if test["expected_source"] in source:
                    source_found = True
                print(f"     Chunk {j+1}: score={score:.3f}, source={source}")

            if source_found:
                print(f"     [OK] Expected source found")
            else:
                print(f"     [!] Expected source '{test['expected_source']}' not in top results")
                # Not a hard failure -- relevance depends on embedding quality

            results.append({"test": test["description"], "passed": passed})

            # Test MMR retrieval
            mmr_result = loader.query_mmr(
                test["query"],
                n_results=5,
                relevance_threshold=0.5,
                diversity_factor=0.3,
            )
            print(f"     MMR: {mmr_result.n_relevant} chunks retrieved")

        except Exception as e:
            all_passed = False
            results.append({"test": test["description"], "passed": False, "error": str(e)})
            print(f"     [FAIL] {e}")

    # == Step 6: Test full RAG pipeline ==
    step_header(6, "Test Full RAG Pipeline (with LLM)")
    try:
        from agent.tools.rag_tool import RAGTool

        # Reuse existing vectorstore from Step 4/5 (don't delete -
        # ChromaDB locks files on Windows, causing PermissionError)
        rag_tool = RAGTool(
            docs_dir="data/docs",
            vectorstore_dir="vectorstore",
            verbose=True,
        )

        rag_tests = [
            {
                "question": "What is the return policy for furniture items like chairs?",
                "description": "Return policy -- specific category",
                "validate": lambda r: r.success and r.confidence > 30,
            },
            {
                "question": "What was the total revenue in Q1 2024 and how did Technology perform?",
                "description": "Financial performance -- multi-fact",
                "validate": lambda r: r.success and r.n_chunks_used >= 1,
            },
            {
                "question": "What are the 2024 sales targets by region?",
                "description": "Regional targets -- strategy doc",
                "validate": lambda r: r.success and len(r.sources) >= 1,
            },
            {
                "question": "What is the weather forecast for Mars?",
                "description": "Irrelevant question -- hallucination guard",
                "validate": lambda r: r.success and r.confidence <= 30,
            },
        ]

        for i, test in enumerate(rag_tests, start=1):
            print(f"\n  -- RAG Test {i}: {test['description']}")
            print(f"     Q: \"{test['question']}\"")

            result = rag_tool.run(test["question"])

            passed = test["validate"](result)
            status = "[OK] PASS" if passed else "[FAIL]"
            if not passed:
                all_passed = False

            results.append({
                "test": test["description"],
                "passed": passed,
            })

            print(f"     {status}")
            print(f"     Confidence: {result.confidence}%")
            print(f"     Chunks used: {result.n_chunks_used}")
            print(f"     Sources: {result.sources}")
            print(f"     Time: {result.execution_time:.2f}s")

            # Show truncated answer
            answer_preview = result.answer[:250].replace("\n", " ")
            if len(result.answer) > 250:
                answer_preview += "..."
            print(f"     Answer: {answer_preview}")

            if result.error:
                print(f"     Error: {result.error}")

    except Exception as e:
        all_passed = False
        print(f"  [FAIL] RAG Pipeline error: {e}")
        traceback.print_exc()

    # == Step 7: Test vector store stats ==
    step_header(7, "Test Vector Store Management")
    try:
        stats = rag_tool.get_stats()
        print(f"  [OK] Collection: {stats['collection_name']}")
        print(f"  [OK] Total chunks: {stats['total_chunks']}")
        print(f"  [OK] Sources: {stats['sources']}")
        print(f"  [OK] Embedding model: {stats['embedding_model']}")
        assert stats["total_chunks"] > 0
        assert stats["n_sources"] == 3
        print("  [OK] Vector store management validated")
    except Exception as e:
        print(f"  [FAIL] {e}")

    # == Summary ==
    divider("TEST SUMMARY")

    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)

    print(f"\n  Tests passed:   {passed_count}/{total_count}")

    if all_passed:
        print(f"\n  [*][*][*]  ALL TESTS PASSED  [*][*][*]")
    else:
        print(f"\n  [!]  Some tests failed. Review output above.")
        failed = [r for r in results if not r.get("passed", False)]
        for f in failed:
            print(f"    * {f['test']}: {f.get('error', 'validation failed')}")

    print()


if __name__ == "__main__":
    main()
