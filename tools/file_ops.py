"""
File manipulation tools for OmniAgent.
"""
import os
from typing import Any
from tools.base import BaseTool, ToolResult


class FileOpsTool(BaseTool):
    name = "file_operations"
    description = "Read, write, or list files in the current workspace."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write", "list"],
                "description": "Action to perform",
            },
            "path": {
                "type": "string",
                "description": "Relative file or directory path",
            },
            "content": {
                "type": "string",
                "description": "Content to write when action is 'write'",
            },
        },
        "required": ["action", "path"],
    }

    def run(self, action: str, path: str, content: str = "", **kwargs: Any) -> ToolResult:
        try:
            if action == "read":
                if not os.path.exists(path):
                    return ToolResult(success=False, output=None, error=f"File not found: {path}")
                with open(path, "r", encoding="utf-8") as f:
                    data = f.read()
                return ToolResult(success=True, output=data)

            elif action == "write":
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return ToolResult(success=True, output=f"Successfully wrote {len(content)} bytes to {path}")

            elif action == "list":
                if not os.path.exists(path):
                    return ToolResult(success=False, output=None, error=f"Directory not found: {path}")
                items = os.listdir(path)
                return ToolResult(success=True, output=items)

            else:
                return ToolResult(success=False, output=None, error=f"Unsupported action: {action}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
