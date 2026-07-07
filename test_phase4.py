"""
Phase 4 Test Script -- LangGraph Agent
=========================================
End-to-end test that verifies:
  1. Router correctly classifies question types
  2. SQL routing and execution
  3. RAG routing and execution
  4. Code routing and execution
  5. Multi-hop query handling
  6. Direct response (no tool needed)
  7. Conversation memory
  8. Error handling

Usage:
    cd autonomous-data-analyst
    python test_phase4.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()


def divider(title: str) -> None:
    print(f"\n{'=' * 64}")
    print(f"  {title}")
    print(f"{'=' * 64}")


def step_header(step: int, title: str) -> None:
    print(f"\n{'-' * 48}")
    print(f"  Test {step}: {title}")
    print(f"{'-' * 48}")


def main() -> None:
    results: list[dict] = []

    divider("PHASE 4 -- LANGGRAPH AGENT TEST SUITE")

    # Ensure data exists
    from utils.generate_data import generate_all
    from utils.db_loader import load_all_csvs
    from utils.generate_docs import generate_all_docs

    db_path = Path("data/superstore.db")
    if not db_path.exists():
        print("  Generating dataset ...")
        generate_all(outdir="data")
        load_all_csvs(csv_dir="data", db_path=str(db_path))

    docs_dir = Path("data/docs")
    if not list(docs_dir.glob("*.pdf")):
        print("  Generating PDF documents ...")
        generate_all_docs(outdir=str(docs_dir))

    # Initialize agent
    print("\n  Initializing agent ...")
    from agent.graph import DataAnalystAgent

    agent = DataAnalystAgent(
        db_path=str(db_path),
        docs_dir=str(docs_dir),
        vectorstore_dir="vectorstore",
        verbose=True,
    )

    # =========================================================================
    # Test 1: SQL Routing
    # =========================================================================
    step_header(1, "SQL Routing - Database Query")
    try:
        r = agent.run("How many orders are in the database?")

        print(f"  Route: {r.get('route')}")
        print(f"  Tools: {r.get('tools_used')}")
        print(f"  Answer: {r.get('answer', '')[:300]}")
        print(f"  Confidence: {r.get('confidence')}%")
        print(f"  Time: {r.get('execution_time', 0):.2f}s")

        passed = (
            r.get("route") == "sql"
            and "SQL" in r.get("tools_used", [])
            and r.get("answer")
        )
        results.append({"test": "SQL routing", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "SQL routing", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")

    # =========================================================================
    # Test 2: RAG Routing
    # =========================================================================
    step_header(2, "RAG Routing - Document Query")
    try:
        r = agent.run("What is the return policy for furniture products?")

        print(f"  Route: {r.get('route')}")
        print(f"  Tools: {r.get('tools_used')}")
        print(f"  Answer: {r.get('answer', '')[:300]}")
        print(f"  Sources: {r.get('sources', [])}")
        print(f"  Time: {r.get('execution_time', 0):.2f}s")

        passed = (
            r.get("route") == "rag"
            and "RAG" in r.get("tools_used", [])
            and r.get("answer")
        )
        results.append({"test": "RAG routing", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "RAG routing", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")

    # =========================================================================
    # Test 3: Code Routing
    # =========================================================================
    step_header(3, "Code Routing - Calculation")
    try:
        r = agent.run(
            "Calculate the compound interest on $10,000 at 8% annual rate "
            "compounded monthly for 5 years."
        )

        print(f"  Route: {r.get('route')}")
        print(f"  Tools: {r.get('tools_used')}")
        print(f"  Answer: {r.get('answer', '')[:300]}")
        print(f"  Figures: {len(r.get('figures', []))}")
        print(f"  Time: {r.get('execution_time', 0):.2f}s")

        passed = (
            r.get("route") == "code"
            and "CODE" in r.get("tools_used", [])
            and r.get("answer")
        )
        results.append({"test": "Code routing", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Code routing", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")

    # =========================================================================
    # Test 4: Direct Routing
    # =========================================================================
    step_header(4, "Direct Routing - Greeting")
    try:
        r = agent.run("Hello! What can you help me with?")

        print(f"  Route: {r.get('route')}")
        print(f"  Tools: {r.get('tools_used')}")
        print(f"  Answer: {r.get('answer', '')[:300]}")
        print(f"  Time: {r.get('execution_time', 0):.2f}s")

        passed = (
            r.get("route") == "direct"
            and "DIRECT" in r.get("tools_used", [])
            and r.get("answer")
        )
        results.append({"test": "Direct routing", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Direct routing", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")

    # =========================================================================
    # Test 5: Multi-hop Query
    # =========================================================================
    step_header(5, "Multi-hop - SQL + Code")
    try:
        r = agent.run(
            "Get total sales by category from the database, "
            "then create a bar chart showing the results."
        )

        print(f"  Route: {r.get('route')}")
        print(f"  Tools: {r.get('tools_used')}")
        print(f"  Answer: {r.get('answer', '')[:300]}")
        print(f"  Figures: {len(r.get('figures', []))}")
        print(f"  Time: {r.get('execution_time', 0):.2f}s")

        passed = (
            r.get("route") == "multi"
            and len(r.get("tools_used", [])) >= 2
            and r.get("answer")
        )
        results.append({"test": "Multi-hop query", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Multi-hop query", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")

    # =========================================================================
    # Test 6: Conversation Memory
    # =========================================================================
    step_header(6, "Conversation Memory")
    try:
        # First ask a question
        r1 = agent.run("What is the top selling category?")
        print(f"  Q1: What is the top selling category?")
        print(f"  A1: {r1.get('answer', '')[:200]}")

        # Then ask a follow-up
        r2 = agent.run("And what about the bottom one?")
        print(f"  Q2: And what about the bottom one?")
        print(f"  A2: {r2.get('answer', '')[:200]}")

        memory = agent.get_memory()
        print(f"  Memory messages: {len(memory)}")

        passed = len(memory) >= 4 and r2.get("answer")  # at least 2 Q&A pairs
        results.append({"test": "Conversation memory", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Conversation memory", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")

    # =========================================================================
    # Test 7: Complex SQL Query
    # =========================================================================
    step_header(7, "Complex SQL - Top 5 Products by Profit")
    try:
        r = agent.run("Show me the top 5 products by total profit.")

        print(f"  Route: {r.get('route')}")
        print(f"  Tools: {r.get('tools_used')}")
        print(f"  Answer: {r.get('answer', '')[:400]}")
        print(f"  Time: {r.get('execution_time', 0):.2f}s")

        passed = r.get("answer") and len(r.get("answer", "")) > 20
        results.append({"test": "Complex SQL query", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Complex SQL query", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")

    # =========================================================================
    # Test 8: Agent State Completeness
    # =========================================================================
    step_header(8, "State Completeness Check")
    try:
        r = agent.run("What were total sales in the West region?")

        required_keys = ["question", "route", "answer", "tools_used",
                         "confidence", "execution_time"]
        missing = [k for k in required_keys if k not in r]

        print(f"  State keys: {list(r.keys())}")
        print(f"  Missing keys: {missing}")
        print(f"  Confidence: {r.get('confidence')}%")
        print(f"  Execution time: {r.get('execution_time', 0):.2f}s")

        passed = len(missing) == 0 and r.get("answer")
        results.append({"test": "State completeness", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "State completeness", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")

    # =========================================================================
    # Summary
    # =========================================================================
    divider("TEST SUMMARY")

    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)

    print(f"\n  Tests passed:   {passed_count}/{total_count}")

    if passed_count == total_count:
        print(f"\n  [*][*][*]  ALL TESTS PASSED  [*][*][*]")
    else:
        print(f"\n  [!]  Some tests failed. Review output above.")
        failed = [r for r in results if not r.get("passed", False)]
        for f in failed:
            print(f"    * {f['test']}: {f.get('error', 'validation failed')}")

    print()


if __name__ == "__main__":
    main()
