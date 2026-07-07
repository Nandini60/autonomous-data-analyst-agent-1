"""
Phase 3 Test Script -- Code Execution Tool
=============================================
End-to-end test that:
  1. Tests pure computation (no data)
  2. Tests pandas DataFrame analysis
  3. Tests Plotly chart generation
  4. Tests self-correction on bad code
  5. Tests sandbox safety (blocked operations)
  6. Tests combined data + chart workflow

Usage:
    cd autonomous-data-analyst
    python test_phase3.py

Prerequisites:
    * pip install -r requirements.txt
    * Set GROQ_API_KEY in .env
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from pathlib import Path

import pandas as pd
import numpy as np

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
    """Run the full Phase 3 test suite."""
    results: list[dict] = []
    total_retries = 0

    divider("PHASE 3 -- CODE EXECUTION TOOL TEST SUITE")

    # Import the tool
    from agent.tools.code_tool import CodeTool

    tool = CodeTool(verbose=True)

    # =========================================================================
    # Test 1: Pure Computation
    # =========================================================================
    step_header(1, "Pure Computation (No Data)")
    try:
        r = tool.run(
            "Calculate the compound annual growth rate (CAGR) from "
            "an initial value of 10000 to a final value of 25000 over 5 years. "
            "Print the result as a percentage."
        )

        print(f"  Code:\n    {r.code[:200].replace(chr(10), chr(10) + '    ')}")
        print(f"  Output: {r.output.strip()[:300]}")
        print(f"  Success: {r.success}")
        print(f"  Retries: {r.retries_used}")
        total_retries += r.retries_used

        passed = r.success and ("20" in r.output or "CAGR" in r.output.upper())
        results.append({"test": "Pure computation (CAGR)", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Pure computation", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")
        traceback.print_exc()

    # =========================================================================
    # Test 2: DataFrame Analysis
    # =========================================================================
    step_header(2, "DataFrame Analysis")
    try:
        # Create a sample sales DataFrame
        np.random.seed(42)
        sales_df = pd.DataFrame({
            "Product": np.random.choice(
                ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard"], 50
            ),
            "Category": np.random.choice(
                ["Technology", "Office Supplies", "Furniture"], 50
            ),
            "Region": np.random.choice(
                ["East", "West", "Central", "South"], 50
            ),
            "Sales": np.random.uniform(100, 5000, 50).round(2),
            "Quantity": np.random.randint(1, 20, 50),
            "Profit": np.random.uniform(-500, 2000, 50).round(2),
        })

        r = tool.run(
            "Analyze the sales_df DataFrame. "
            "Calculate total sales, average profit, and sales by category. "
            "Print a summary of the findings.",
            data_context={"sales_df": sales_df},
        )

        print(f"  Code:\n    {r.code[:300].replace(chr(10), chr(10) + '    ')}")
        print(f"  Output: {r.output.strip()[:400]}")
        print(f"  Success: {r.success}")
        print(f"  Retries: {r.retries_used}")
        print(f"  DataFrames captured: {len(r.dataframes)}")
        total_retries += r.retries_used

        passed = r.success and r.output.strip() != ""
        results.append({"test": "DataFrame analysis", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "DataFrame analysis", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")
        traceback.print_exc()

    # =========================================================================
    # Test 3: Plotly Chart Generation
    # =========================================================================
    step_header(3, "Plotly Chart Generation")
    try:
        r = tool.run(
            "Create a bar chart showing sales by category using the sales_df data. "
            "Use plotly express with a dark template. "
            "Title it 'Sales by Category'.",
            data_context={"sales_df": sales_df},
        )

        print(f"  Code:\n    {r.code[:300].replace(chr(10), chr(10) + '    ')}")
        print(f"  Success: {r.success}")
        print(f"  Figures: {len(r.figures)}")
        print(f"  Retries: {r.retries_used}")
        total_retries += r.retries_used

        if r.figures:
            fig = r.figures[0]
            print(f"  Figure title: {fig.layout.title.text if fig.layout.title else 'N/A'}")
            print(f"  Figure type: {type(fig).__name__}")

        passed = r.success and len(r.figures) >= 1
        results.append({"test": "Plotly chart generation", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Plotly chart", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")
        traceback.print_exc()

    # =========================================================================
    # Test 4: Multiple Charts
    # =========================================================================
    step_header(4, "Multiple Charts")
    try:
        r = tool.run(
            "Create TWO charts using the sales_df data:\n"
            "1. A pie chart of sales distribution by Region (call it fig1)\n"
            "2. A scatter plot of Sales vs Profit colored by Category (call it fig2)\n"
            "Use plotly_dark template for both.",
            data_context={"sales_df": sales_df},
        )

        print(f"  Code:\n    {r.code[:400].replace(chr(10), chr(10) + '    ')}")
        print(f"  Success: {r.success}")
        print(f"  Figures: {len(r.figures)}")
        print(f"  Retries: {r.retries_used}")
        total_retries += r.retries_used

        passed = r.success and len(r.figures) >= 2
        results.append({"test": "Multiple charts", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Multiple charts", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")
        traceback.print_exc()

    # =========================================================================
    # Test 5: Sandbox Safety
    # =========================================================================
    step_header(5, "Sandbox Safety Check")
    try:
        from agent.tools.code_tool import _create_sandbox_namespace

        ns = _create_sandbox_namespace()

        # Verify dangerous builtins are blocked
        blocked = ["eval", "exec", "compile", "open"]
        blocked_count = 0
        for fn_name in blocked:
            if fn_name not in ns:
                print(f"  [OK] '{fn_name}' is blocked")
                blocked_count += 1
            else:
                print(f"  [!] '{fn_name}' is NOT blocked")

        # Verify __import__ is restricted (exists but blocks unsafe modules)
        import_fn = ns.get("__import__")
        if import_fn:
            try:
                import_fn("os")
                print("  [!] '__import__' allows unsafe 'os' import")
            except ImportError:
                print("  [OK] '__import__' blocks unsafe modules (os)")
                blocked_count += 1
        else:
            print("  [OK] '__import__' is fully blocked")
            blocked_count += 1

        # Verify safe libraries are available
        safe = ["pd", "np", "px", "go", "math"]
        safe_count = 0
        for lib in safe:
            if lib in ns:
                print(f"  [OK] '{lib}' is available")
                safe_count += 1
            else:
                print(f"  [!] '{lib}' is NOT available")

        # blocked_count = 4 (eval,exec,compile,open) + 1 (restricted __import__)
        passed = blocked_count == len(blocked) + 1 and safe_count == len(safe)
        results.append({"test": "Sandbox safety", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Sandbox safety", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")
        traceback.print_exc()

    # =========================================================================
    # Test 6: Statistical Computation
    # =========================================================================
    step_header(6, "Statistical Computation")
    try:
        r = tool.run(
            "Given this data, calculate the mean, median, standard deviation, "
            "and correlation between Sales and Profit. "
            "Print all statistics clearly.",
            data_context={"sales_df": sales_df},
        )

        print(f"  Output: {r.output.strip()[:400]}")
        print(f"  Success: {r.success}")
        print(f"  Retries: {r.retries_used}")
        total_retries += r.retries_used

        passed = r.success and (
            "mean" in r.output.lower() or
            "average" in r.output.lower() or
            "std" in r.output.lower() or
            "median" in r.output.lower()
        )
        results.append({"test": "Statistical computation", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Statistical computation", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")
        traceback.print_exc()

    # =========================================================================
    # Test 7: Code Explanation
    # =========================================================================
    step_header(7, "Code Explanation Generation")
    try:
        r = tool.run(
            "What is 2 raised to the power of 10? Print the result.",
        )

        print(f"  Output: {r.output.strip()}")
        print(f"  Explanation: {r.explanation[:300]}")
        print(f"  Success: {r.success}")
        total_retries += r.retries_used

        passed = r.success and "1024" in r.output and r.explanation
        results.append({"test": "Code explanation", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Code explanation", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")
        traceback.print_exc()

    # =========================================================================
    # Test 8: Self-Correction
    # =========================================================================
    step_header(8, "Self-Correction (Tricky Query)")
    try:
        # Use a tricky request that might fail on first attempt
        messy_df = pd.DataFrame({
            "date_str": ["2024-01-15", "2024-02-20", "2024-03-10", "2024-04-05"],
            "revenue_k": ["$125.5K", "$98.2K", "$143.7K", "$112.1K"],
            "status": ["active", "inactive", "active", "active"],
        })

        r = tool.run(
            "Parse the revenue_k column (remove $ and K, convert to float and "
            "multiply by 1000 to get actual revenue). "
            "Calculate total revenue. Print the cleaned data and total.",
            data_context={"messy_df": messy_df},
        )

        print(f"  Output: {r.output.strip()[:400]}")
        print(f"  Success: {r.success}")
        print(f"  Retries: {r.retries_used}")
        total_retries += r.retries_used

        passed = r.success
        results.append({"test": "Self-correction (messy data)", "passed": passed})
        print(f"  {'[OK] PASS' if passed else '[FAIL]'}")

    except Exception as e:
        results.append({"test": "Self-correction", "passed": False, "error": str(e)})
        print(f"  [FAIL] {e}")
        traceback.print_exc()

    # =========================================================================
    # Summary
    # =========================================================================
    divider("TEST SUMMARY")

    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)

    print(f"\n  Tests passed:   {passed_count}/{total_count}")
    print(f"  Total retries:  {total_retries}")

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
