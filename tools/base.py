"""
Base classes for tools and tool registry in OmniAgent.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

try:
    from pydantic import BaseModel
    class ToolResult(BaseModel):
        """Encapsulates the execution result of a tool."""
        success: bool
        output: Any
        error: Optional[str] = None

        def __str__(self) -> str:
            if self.success:
                return str(self.output)
            return f"Error: {self.error}"
except ImportError:
    class ToolResult:
        def __init__(self, success: bool, output: Any = None, error: Optional[str] = None):
            self.success = success
            self.output = output
            self.error = error

        def __str__(self) -> str:
            if self.success:
                return str(self.output)
            return f"Error: {self.error}"

        def dict(self):
            return {"success": self.success, "output": self.output, "error": self.error}



class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    name: str
    description: str
    parameters: Dict[str, Any] = {}

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Export tool metadata in standard JSON schema format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class FunctionTool(BaseTool):
    """Adapter to wrap a standard python function into an Agent Tool."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}

    def run(self, **kwargs: Any) -> ToolResult:
        try:
            result = self.func(**kwargs)
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class ToolRegistry:
    """Central repository for discovering, validating, and invoking tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{name}' not found. Available tools: {list(self._tools.keys())}",
            )
        try:
            return tool.run(**kwargs)
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Execution error: {str(e)}")
