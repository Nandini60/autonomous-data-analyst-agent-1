"""
Code Execution Tool -- LLM-Generated Python for Analysis & Charts
===================================================================
Generates and executes Python code for statistical analysis,
calculations, and Plotly chart creation.

Pipeline:
  1. User asks a question requiring computation or visualization
  2. LLM generates Python code using pandas/plotly/numpy
  3. Code executes in a sandboxed namespace via exec()
  4. Results (text output, DataFrames, Plotly figures) are captured
  5. If execution fails, error is fed back to LLM for self-correction

Key features:
  * Sandboxed execution with restricted builtins
  * Plotly figure capture for Streamlit rendering
  * DataFrame result capture
  * Self-correction loop (up to 3 retries)
  * Stdout/stderr capture
  * Timeout protection

Usage:
    from agent.tools.code_tool import CodeTool

    tool = CodeTool()
    result = tool.run("Calculate the compound annual growth rate from 100 to 250 over 5 years")
    print(result.output)
    print(result.code)

    # With data context
    result = tool.run(
        "Create a bar chart of sales by category",
        data_context={"sales_by_category": df}
    )
    if result.figures:
        st.plotly_chart(result.figures[0])
"""

from __future__ import annotations

import io
import os
import re
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL: str = "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE: float = 0.1
MAX_RETRIES: int = 3
EXECUTION_TIMEOUT: int = 30  # seconds

# Safe builtins -- block dangerous functions
BLOCKED_BUILTINS: set[str] = {
    "eval", "exec", "compile", "open",
    "input", "breakpoint", "exit", "quit",
}

# Allowed imports for the sandbox
ALLOWED_MODULES: set[str] = {
    "pandas", "pd",
    "numpy", "np",
    "plotly", "plotly.express", "plotly.graph_objects", "plotly.subplots",
    "math", "statistics", "collections", "itertools", "functools",
    "datetime", "re", "json", "csv",
    "scipy", "scipy.stats",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CodeResult:
    """Structured result from the code execution tool.

    Attributes:
        success:        Whether code executed successfully.
        question:       The original natural language question.
        code:           The generated Python code.
        output:         Captured stdout from execution.
        error:          Error message if execution failed.
        figures:        List of captured Plotly figure objects.
        dataframes:     List of captured pandas DataFrames.
        variables:      Dict of notable variables from execution namespace.
        retries_used:   Number of retry attempts used.
        execution_time: Wall-clock time for the full pipeline.
        explanation:    LLM's explanation of the results.
    """
    success: bool = False
    question: str = ""
    code: str = ""
    output: str = ""
    error: str = ""
    figures: list = field(default_factory=list)
    dataframes: list = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    retries_used: int = 0
    execution_time: float = 0.0
    explanation: str = ""


# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------

CODE_SYSTEM_PROMPT = """You are an expert Python data analyst. Generate Python code
to answer the user's question. Follow these rules strictly:

1. Output ONLY executable Python code. ALWAYS wrap your code in ```python ... ``` markdown fences. No explanations outside the fences.
2. Use these libraries as needed: pandas (as pd), numpy (as np), plotly.express (as px),
   plotly.graph_objects (as go), math, statistics, datetime.
3. For visualizations, ALWAYS use Plotly (never matplotlib).
4. Store any Plotly figure in a variable named `fig` (or `fig1`, `fig2`, etc.).
5. Store any result DataFrame in a variable named `result_df` (or `result_df1`, etc.).
6. Use `print()` to output text results, summaries, and key findings.
7. When making charts:
   - Use professional color schemes
   - Add proper titles, axis labels, and legends
   - Use appropriate chart types for the data
   - Set a clean layout with `fig.update_layout(template="plotly_dark")`
8. Store the final answer/summary in a variable called `answer`.
9. If data is provided as DataFrames, they will be available as variables in your namespace.
10. Do NOT use plt.show(), fig.show(), or any display commands.
11. Do NOT read or write files. Work only with provided data.
12. Do NOT use exec(), eval(), or __import__().
13. Make your code robust with error handling where appropriate.

{data_context}
"""

CODE_FIX_PROMPT = """The previous code failed with this error:

Code:
```python
{code}
```

Error:
{error}

Fix the code. Output ONLY the corrected Python code -- nothing else.
Common fixes:
- Check variable names and column names
- Ensure imports are correct
- Handle edge cases (empty data, type errors)
- Use proper pandas/plotly syntax
"""

CODE_EXPLAIN_PROMPT = """Given the code output below, provide a clear, concise
explanation of the results. Focus on key findings and insights.

Question: {question}

Code output:
{output}

Number of charts generated: {n_figures}

Provide a 2-3 sentence summary of the results."""


# ---------------------------------------------------------------------------
# Sandbox
# ---------------------------------------------------------------------------

def _create_sandbox_namespace(
    data_context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Create a sandboxed execution namespace.

    Provides safe builtins and pre-imported data science libraries.
    Blocks dangerous functions like eval, exec, open, etc.
    Provides a safe __import__ that blocks dangerous modules.

    Args:
        data_context: Optional dict of variable names to DataFrames
                      or other data to inject into the namespace.

    Returns:
        A dict representing the execution namespace.
    """
    import builtins as _builtins

    # Modules that are BLOCKED from import (dangerous / system access)
    BLOCKED_IMPORTS = {
        "os", "subprocess", "shutil", "sys", "socket", "http",
        "urllib", "requests", "ftplib", "smtplib", "telnetlib",
        "ctypes", "signal", "multiprocessing", "threading",
        "code", "codeop", "compileall", "importlib",
        "pickle", "shelve", "marshal",
        "webbrowser", "antigravity",
    }

    # -- Pre-import all libraries BEFORE restricting __import__ ------
    pre_imported: dict[str, Any] = {}

    try:
        import numpy as np
        pre_imported["np"] = np
        pre_imported["numpy"] = np
    except ImportError:
        pass

    try:
        pre_imported["pd"] = pd
        pre_imported["pandas"] = pd
        pre_imported["DataFrame"] = pd.DataFrame
    except Exception:
        pass

    try:
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        pre_imported["px"] = px
        pre_imported["go"] = go
        pre_imported["make_subplots"] = make_subplots
        pre_imported["plotly"] = __import__("plotly")
    except ImportError:
        pass

    try:
        import math
        import statistics
        pre_imported["math"] = math
        pre_imported["statistics"] = statistics
    except ImportError:
        pass

    try:
        import datetime
        pre_imported["datetime"] = datetime
        pre_imported["timedelta"] = datetime.timedelta
    except ImportError:
        pass

    try:
        import json
        pre_imported["json"] = json
    except ImportError:
        pass

    try:
        import re as re_module
        pre_imported["re"] = re_module
    except ImportError:
        pass

    try:
        import collections
        pre_imported["collections"] = collections
        pre_imported["Counter"] = collections.Counter
        pre_imported["defaultdict"] = collections.defaultdict
    except ImportError:
        pass

    # -- Build safe builtins dict ------
    safe_builtins = {
        name: getattr(_builtins, name)
        for name in dir(_builtins)
        if not name.startswith("_") and name not in BLOCKED_BUILTINS
    }

    # Add a restricted __import__ that blocks dangerous modules
    _real_import = _builtins.__import__

    def _safe_import(name, *args, **kwargs):
        top_level = name.split(".")[0]
        if top_level in BLOCKED_IMPORTS:
            raise ImportError(
                f"Import of '{name}' is blocked in the sandbox for security."
            )
        return _real_import(name, *args, **kwargs)

    safe_builtins["__import__"] = _safe_import
    safe_builtins["__builtins__"] = safe_builtins

    # -- Build final namespace ------
    namespace: dict[str, Any] = dict(safe_builtins)
    namespace.update(pre_imported)

    # Inject user data context
    if data_context:
        for name, value in data_context.items():
            namespace[name] = value

    return namespace


def _extract_results(
    namespace: dict[str, Any],
) -> tuple[list, list[pd.DataFrame], dict[str, Any]]:
    """Extract notable results from the execution namespace.

    Looks for Plotly figures, DataFrames, and named result variables.

    Args:
        namespace: The post-execution namespace dict.

    Returns:
        A tuple of (figures, dataframes, variables).
    """
    figures = []
    dataframes = []
    variables: dict[str, Any] = {}

    try:
        import plotly.graph_objects as go
        plotly_available = True
    except ImportError:
        plotly_available = False

    for name, value in namespace.items():
        # Skip builtins and modules
        if name.startswith("_") or name in (
            "pd", "np", "px", "go", "math", "statistics", "datetime",
            "json", "re", "collections", "Counter", "defaultdict",
            "numpy", "pandas", "plotly", "DataFrame", "make_subplots",
            "timedelta",
        ):
            continue

        # Capture Plotly figures
        if plotly_available and isinstance(value, go.Figure):
            figures.append(value)
            continue

        # Capture DataFrames
        if isinstance(value, pd.DataFrame):
            dataframes.append(value)
            if name.startswith("result"):
                variables[name] = f"DataFrame({len(value)} rows x {len(value.columns)} cols)"
            continue

        # Capture named results
        if name in ("answer", "result", "summary") or name.startswith("result_"):
            variables[name] = value

    return figures, dataframes, variables


# ---------------------------------------------------------------------------
# Code Tool class
# ---------------------------------------------------------------------------

class CodeTool:
    """LLM-generated Python code execution tool.

    Generates Python code using an LLM to answer data analysis questions,
    executes it in a sandboxed environment, and captures results including
    Plotly charts, DataFrames, and text output.

    Args:
        model:       Groq LLM model identifier.
        temperature: LLM temperature for code generation.
        max_retries: Max self-correction attempts on code errors.
        verbose:     If True, print progress messages.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_retries: int = MAX_RETRIES,
        verbose: bool = True,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.verbose = verbose

        # Initialize LLM
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key.startswith("gsk_your"):
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Get a free key at https://console.groq.com/keys"
            )

        self._llm = ChatGroq(
            model=model,
            temperature=temperature,
            api_key=api_key,
            max_tokens=2048,
        )

    # -- Private helpers -------------------------------------------------------

    def _log(self, msg: str) -> None:
        """Print a message if verbose mode is enabled."""
        if self.verbose:
            print(f"  [Code Tool] {msg}")

    def _extract_code(self, raw: str) -> str:
        """Extract clean Python code from LLM output.

        Handles cases where the LLM wraps code in markdown fences
        or adds explanatory text.

        Args:
            raw: Raw LLM output string.

        Returns:
            Cleaned Python code string.
        """
        # Remove markdown code fences
        fenced = re.search(
            r"```(?:python)?\s*\n?(.*?)```", raw, re.DOTALL | re.IGNORECASE
        )
        if fenced:
            return fenced.group(1).strip()

        # If it looks like code already (has imports or assignments), use as-is
        lines = raw.strip().split("\n")
        code_lines = []
        in_code = False
        for line in lines:
            stripped = line.strip()
            # Heuristic: line looks like Python code
            if (
                stripped.startswith(("import ", "from ", "def ", "class ",
                                    "for ", "while ", "if ", "try:", "with "))
                or "=" in stripped
                or stripped.startswith(("print(", "fig", "result", "answer", "#"))
                or stripped == ""
                or in_code
            ):
                code_lines.append(line)
                in_code = True

        if code_lines:
            return "\n".join(code_lines).strip()

        return raw.strip()

    def _build_data_context_prompt(
        self, data_context: Optional[dict[str, Any]] = None
    ) -> str:
        """Build a description of available data for the LLM.

        Args:
            data_context: Dict of variable names to DataFrames/values.

        Returns:
            Formatted string describing available data.
        """
        if not data_context:
            return "No external data is provided. Work with the question directly."

        parts = ["AVAILABLE DATA IN YOUR NAMESPACE:"]
        for name, value in data_context.items():
            if isinstance(value, pd.DataFrame):
                cols = ", ".join(f"{c} ({value[c].dtype})" for c in value.columns[:15])
                if len(value.columns) > 15:
                    cols += f", ... ({len(value.columns) - 15} more columns)"
                parts.append(
                    f"\n  Variable: `{name}` (pandas DataFrame)\n"
                    f"  Shape: {value.shape[0]} rows x {value.shape[1]} columns\n"
                    f"  Columns: {cols}\n"
                    f"  Sample (first 3 rows):\n{value.head(3).to_string(index=False)}"
                )
            else:
                parts.append(f"\n  Variable: `{name}` = {repr(value)[:200]}")

        return "\n".join(parts)

    def _generate_code(
        self,
        question: str,
        data_context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Call the LLM to generate Python code.

        Args:
            question:     The user's question.
            data_context: Available data description.

        Returns:
            Generated Python code string.
        """
        context_desc = self._build_data_context_prompt(data_context)
        system = CODE_SYSTEM_PROMPT.format(data_context=context_desc)

        messages = [
            SystemMessage(content=system),
            HumanMessage(content=question),
        ]
        response = self._llm.invoke(messages)
        return self._extract_code(response.content)

    def _fix_code(
        self,
        question: str,
        failed_code: str,
        error: str,
        data_context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Ask the LLM to fix failed code.

        Args:
            question:     Original question.
            failed_code:  The code that failed.
            error:        The error message.
            data_context: Available data for context.

        Returns:
            Corrected Python code string.
        """
        context_desc = self._build_data_context_prompt(data_context)
        system = CODE_SYSTEM_PROMPT.format(data_context=context_desc)
        fix_msg = CODE_FIX_PROMPT.format(code=failed_code, error=error)

        messages = [
            SystemMessage(content=system),
            HumanMessage(content=question),
            HumanMessage(content=fix_msg),
        ]
        response = self._llm.invoke(messages)
        return self._extract_code(response.content)

    def _execute_code(
        self,
        code: str,
        data_context: Optional[dict[str, Any]] = None,
    ) -> tuple[str, str, dict[str, Any]]:
        """Execute Python code in a sandboxed namespace.

        Args:
            code:         The Python code to execute.
            data_context: Data to inject into the namespace.

        Returns:
            A tuple of (stdout_output, stderr_output, namespace).

        Raises:
            Exception: Any execution error from the code.
        """
        namespace = _create_sandbox_namespace(data_context)

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, namespace)  # noqa: S102

        return (
            stdout_capture.getvalue(),
            stderr_capture.getvalue(),
            namespace,
        )

    def _explain_results(
        self,
        question: str,
        output: str,
        n_figures: int,
    ) -> str:
        """Generate a natural language explanation of code results.

        Args:
            question:  The original question.
            output:    Captured stdout from code execution.
            n_figures: Number of Plotly figures generated.

        Returns:
            A concise explanation string.
        """
        prompt = CODE_EXPLAIN_PROMPT.format(
            question=question,
            output=output[:1500] if output else "(no text output)",
            n_figures=n_figures,
        )

        messages = [
            SystemMessage(content="You are a helpful data analyst. Be concise."),
            HumanMessage(content=prompt),
        ]
        response = self._llm.invoke(messages)
        return response.content

    # -- Public API ------------------------------------------------------------

    def run(
        self,
        question: str,
        data_context: Optional[dict[str, Any]] = None,
    ) -> CodeResult:
        """Generate and execute Python code to answer a question.

        Pipeline:
          1. LLM generates Python code
          2. Code executes in sandboxed namespace
          3. If execution fails, error fed back to LLM (up to max_retries)
          4. Results (stdout, figures, DataFrames) are captured
          5. LLM generates explanation of results

        Args:
            question:     Natural language question or task.
            data_context: Optional dict of variable names to values
                          (DataFrames, lists, etc.) available in code.

        Returns:
            A CodeResult with code, output, figures, and metadata.
        """
        start = time.time()
        result = CodeResult(question=question)

        self._log(f"Question: {question}")

        # -- Step 1: Generate code --
        try:
            code = self._generate_code(question, data_context)
        except Exception as e:
            result.error = f"Code generation failed: {e}"
            result.execution_time = time.time() - start
            self._log(f"[FAIL] Generation error: {e}")
            return result

        self._log(f"Generated code ({len(code)} chars)")

        # -- Step 2: Execute with self-correction loop --
        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            try:
                stdout_out, stderr_out, namespace = self._execute_code(
                    code, data_context
                )

                # Extract results
                figures, dataframes, variables = _extract_results(namespace)

                result.success = True
                result.code = code
                result.output = stdout_out
                result.figures = figures
                result.dataframes = dataframes
                result.variables = variables
                result.retries_used = attempt - 1

                if stderr_out.strip():
                    # Warnings are not failures
                    self._log(f"Stderr (warnings): {stderr_out[:200]}")

                self._log(
                    f"[OK] Executed successfully "
                    f"(attempt {attempt}, {len(figures)} figures, "
                    f"{len(dataframes)} DataFrames)"
                )
                break

            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                tb = traceback.format_exc()
                self._log(
                    f"[FAIL] Attempt {attempt}/{self.max_retries}: {last_error}"
                )

                if attempt < self.max_retries:
                    try:
                        code = self._fix_code(
                            question, code, f"{last_error}\n\nTraceback:\n{tb}",
                            data_context,
                        )
                        self._log(f"  Fixed code ({len(code)} chars)")
                    except Exception as fix_err:
                        self._log(f"  Fix failed: {fix_err}")
                        result.error = f"Self-correction failed: {fix_err}"
                        result.code = code
                        break
                else:
                    result.error = (
                        f"Code failed after {self.max_retries} attempts. "
                        f"Last error: {last_error}"
                    )
                    result.code = code

        # -- Step 3: Generate explanation --
        if result.success:
            try:
                result.explanation = self._explain_results(
                    question,
                    result.output,
                    len(result.figures),
                )
                self._log("[OK] Explanation generated")
            except Exception as e:
                result.explanation = f"(Could not generate explanation: {e})"
                self._log(f"[!] Explanation failed: {e}")

        result.execution_time = time.time() - start
        self._log(f"Total time: {result.execution_time:.2f}s")
        return result
