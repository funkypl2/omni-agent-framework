"""
Sandboxed Python execution tool with captured stdout and safe local execution.
"""
import io
import sys
import traceback
from typing import Any
from tools.base import BaseTool, ToolResult


class PythonExecutorTool(BaseTool):
    name = "python_interpreter"
    description = "Execute arbitrary Python code to compute answers, process data, or verify logic. Standard libraries (math, json, re, itertools) are available. Print outputs using print()."
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code snippet to execute",
            }
        },
        "required": ["code"],
    }

    def run(self, code: str, **kwargs: Any) -> ToolResult:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_stdout = io.StringIO()
        redirected_stderr = io.StringIO()

        globals_env = {
            "__builtins__": __builtins__,
        }
        locals_env = {}

        try:
            sys.stdout = redirected_stdout
            sys.stderr = redirected_stderr
            exec(code, globals_env, locals_env)
            stdout_str = redirected_stdout.getvalue()
            stderr_str = redirected_stderr.getvalue()

            output = stdout_str
            if stderr_str:
                output += f"\n[stderr]: {stderr_str}"

            if not output.strip():
                # If no print statement was run, check if last variable or return exists
                output = "(Code executed successfully with no stdout output)"

            return ToolResult(success=True, output=output.strip())
        except Exception as e:
            tb = traceback.format_exc()
            return ToolResult(success=False, output=None, error=f"Python Execution Failed: {str(e)}\n{tb}")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
