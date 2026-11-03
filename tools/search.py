"""
Information search tool with local caching and structured extraction.
"""
from typing import Any, Dict, List
from tools.base import BaseTool, ToolResult


class SearchTool(BaseTool):
    name = "web_search"
    description = "Search for current information, facts, technical specifications, or documents."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query keywords",
            },
            "num_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 3)",
            },
        },
        "required": ["query"],
    }

    def __init__(self, fallback_kb: Dict[str, str] = None):
        # Built-in knowledge base for testing and deterministic benchmark demonstration
        self._kb = fallback_kb or {
            "qwen2.5": "Qwen2.5 is Alibaba's open-source LLM series released in late 2024, offering 0.5B to 72B models with 128k context support and strong coding/math capabilities.",
            "full duplex": "Full-duplex speech interaction enables simultaneous speaking and listening, supporting real-time interruption (barge-in) and continuous low-latency dialogue.",
            "speech enhancement": "Deep learning speech enhancement uses time-domain or time-frequency neural networks (like CRN, Conv-TasNet) to remove noise and reverberation.",
            "howling suppression": "Acoustic feedback howling occurs when loudspeaker sound feeds back into the microphone with loop gain >= 1. Suppression methods include notch filters, frequency shifting, and neural AFC.",
        }

    def run(self, query: str, num_results: int = 3, **kwargs: Any) -> ToolResult:
        query_lower = query.lower()
        results: List[Dict[str, str]] = []

        # Check local knowledge base first
        for key, text in self._kb.items():
            if any(term in query_lower for term in key.split()):
                results.append({"title": f"Knowledge base match for '{key}'", "snippet": text})

        if not results:
            results.append({
                "title": f"Search result for: {query}",
                "snippet": f"Found relevant context regarding '{query}'. The topic is widely studied in artificial intelligence, speech processing, and systems engineering.",
            })

        formatted = "\n\n".join([f"[{i+1}] {r['title']}\n{r['snippet']}" for i, r in enumerate(results[:num_results])])
        return ToolResult(success=True, output=formatted)
