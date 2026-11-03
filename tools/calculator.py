"""
Safe mathematical calculation tool using AST parsing.
"""
import ast
import operator
import math
from typing import Any
from tools.base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Perform mathematical calculations safely. Supports basic arithmetic, powers, and standard math constants (pi, e)."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate, e.g., '12 * (3.5 + 4.2) / 2' or 'sqrt(144)'",
            }
        },
        "required": ["expression"],
    }

    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    _allowed_names = {
        "pi": math.pi,
        "e": math.e,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "abs": abs,
        "round": round,
    }

    def _eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return self._eval(node.body)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            op = self._operators.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            op = self._operators.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self._allowed_names:
                func = self._allowed_names[node.func.id]
                args = [self._eval(arg) for arg in node.args]
                return func(*args)
            raise ValueError(f"Unsupported function call: {ast.dump(node)}")
        elif isinstance(node, ast.Name):
            if node.id in self._allowed_names:
                return self._allowed_names[node.id]
            raise ValueError(f"Unknown variable name: {node.id}")
        else:
            raise TypeError(f"Unsupported AST node type: {type(node).__name__}")

    def run(self, expression: str, **kwargs: Any) -> ToolResult:
        try:
            tree = ast.parse(expression, mode="eval")
            res = self._eval(tree)
            return ToolResult(success=True, output=res)
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Calculation error: {str(e)}")
