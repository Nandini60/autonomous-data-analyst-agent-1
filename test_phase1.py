"""
Phase 1 Test Script -- SQL Tool
================================
End-to-end test that:
  1. Generates the Superstore dataset (CSVs)
  2. Loads CSVs into SQLite
  3. Runs a battery of natural language questions through the SQL tool
  4. Validates results and prints a summary

Usage:
    cd autonomous-data-analyst
    python test_phase1.py

Prerequisites:
    * pip install -r requirements.txt
    * Set GROQ_API_KEY in .env
"""

from __future__ import annotations

import os
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
    """Run the full Phase 1 test suite."""
    results: list[dict] = []
    all_passed = True

    # -- Step 1: Generate dataset -------------------------------------
    divider("PHASE 1 -- SQL TOOL TEST SUITE")

    step_header(1, "Generate Superstore Dataset")
    try:
        from utils.generate_data import generate_all

        generate_all(data_dir="data", n_orders=2000)
        print("  [OK] Dataset generated successfully")

        # Verify CSVs exist
        for fname in ["orders.csv", "customers.csv", "products.csv", "returns.csv"]:
            fpath = Path("data") / fname
            assert fpath.exists(), f"Missing: {fpath}"
            print(f"  [OK] {fname} exists")

    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # -- Step 2: Load into SQLite -------------------------------------
    step_header(2, "Load CSVs into SQLite")
    try:
        from utils.db_loader import load_csvs_to_sqlite, get_schema_description

        engine = load_csvs_to_sqlite(data_dir="data", db_path="data/database.db")
        print("  [OK] Database created")

        schema = get_schema_description("data/database.db")
        print("  [OK] Schema description generated")
        print(f"  Schema length: {len(schema):,} chars")

        # Quick sanity check
        assert "orders" in schema.lower()
        assert "customers" in schema.lower()
        assert "products" in schema.lower()
        assert "returns" in schema.lower()
        print("  [OK] All 4 tables present in schema")

    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # -- Step 3: Initialize SQL Tool ----------------------------------
    step_header(3, "Initialize SQL Tool")
    try:
        from agent.tools.sql_tool import SQLTool

        sql_tool = SQLTool(db_path="data/database.db", verbose=True)
        print("  [OK] SQL Tool initialized")
        print(f"  Tables: {sql_tool.get_table_names()}")

    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # -- Step 4: Test queries -----------------------------------------
    step_header(4, "Run Test Queries")

    test_questions: list[dict] = [
        {
            "question": "How many total orders are there?",
            "validate": lambda r: r.success and r.row_count >= 1,
            "description": "Simple COUNT query",
        },
        {
            "question": "What are the top 5 products by total sales?",
            "validate": lambda r: r.success and r.row_count == 5,
            "description": "Top-N with GROUP BY + ORDER BY",
        },
        {
            "question": "What is the total sales and profit by category?",
            "validate": lambda r: r.success and r.row_count == 3,  # 3 categories
            "description": "Aggregation with GROUP BY",
        },
        {
            "question": "Which region has the highest average discount?",
            "validate": lambda r: r.success and r.row_count >= 1,
            "description": "AVG aggregation with ranking",
        },
        {
            "question": "Show me all returned orders along with the customer name and return reason",
            "validate": lambda r: r.success and r.row_count >= 1,
            "description": "Multi-table JOIN (orders + returns)",
        },
        {
            "question": "What are the monthly sales trends for 2024?",
            "validate": lambda r: r.success and r.row_count >= 1,
            "description": "Date extraction + GROUP BY month",
        },
        {
            "question": "Which customers from the East region have spent more than $5000 total?",
            "validate": lambda r: r.success,
            "description": "Filter + aggregation + HAVING clause",
        },
        {
            "question": "What is the return rate by product category?",
            "validate": lambda r: r.success and r.row_count >= 1,
            "description": "Complex JOIN + calculation",
        },
    ]

    for i, test in enumerate(test_questions, start=1):
        print(f"\n  -- Test {i}/{len(test_questions)}: {test['description']}")
        print(f"     Q: \"{test['question']}\"")

        try:
            result = sql_tool.run(test["question"])

            passed = test["validate"](result)
            status = "[OK] PASS" if passed else "[FAIL] FAIL"
            if not passed:
                all_passed = False

            results.append({
                "test": test["description"],
                "passed": passed,
                "rows": result.row_count,
                "retries": result.retries_used,
                "time": result.execution_time,
                "sql": result.sql_query,
                "error": result.error,
            })

            print(f"     {status}")
            print(f"     SQL: {result.sql_query[:120]}{'...' if len(result.sql_query) > 120 else ''}")
            print(f"     Rows: {result.row_count}  |  Retries: {result.retries_used}  |  Time: {result.execution_time:.2f}s")

            if result.success and not result.dataframe.empty:
                print(f"     Preview:\n{result.dataframe.head(3).to_string(index=False)}")

            if result.explanation:
                # Truncate long explanations for the test output
                expl = result.explanation[:200] + "..." if len(result.explanation) > 200 else result.explanation
                print(f"     Explanation: {expl}")

            if result.error:
                print(f"     Error: {result.error}")

        except Exception as e:
            all_passed = False
            results.append({
                "test": test["description"],
                "passed": False,
                "error": str(e),
            })
            print(f"     [FAIL] EXCEPTION: {e}")
            traceback.print_exc()

    # -- Step 5: Schema refresh test ----------------------------------
    step_header(5, "Test Schema Refresh")
    try:
        new_schema = sql_tool.refresh_schema()
        assert len(new_schema) > 0
        print("  [OK] Schema refresh works")
    except Exception as e:
        print(f"  [FAIL] Schema refresh failed: {e}")

    # -- Summary ------------------------------------------------------
    divider("TEST SUMMARY")

    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)
    avg_time = sum(r.get("time", 0) for r in results) / max(total_count, 1)
    total_retries = sum(r.get("retries", 0) for r in results)

    print(f"\n  Tests passed:   {passed_count}/{total_count}")
    print(f"  Avg query time: {avg_time:.2f}s")
    print(f"  Total retries:  {total_retries}")

    if all_passed:
        print(f"\n  {'[*]' * 3}  ALL TESTS PASSED  {'[*]' * 3}")
    else:
        print(f"\n  [!]  Some tests failed. Review output above.")
        failed = [r for r in results if not r.get("passed", False)]
        for f in failed:
            print(f"    * {f['test']}: {f.get('error', 'validation failed')}")

    print()
    return


if __name__ == "__main__":
    main()
