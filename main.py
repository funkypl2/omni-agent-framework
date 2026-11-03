"""
Main entry point and interactive CLI demo for OmniAgent Framework.
"""
import os
import sys

# Ensure local package import works regardless of working directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import argparse
import json
import requests
from tools import (

    ToolRegistry,
    CalculatorTool,
    SearchTool,
    PythonExecutorTool,
    FileOpsTool,
)
from core import OmniAgent, TaskPlanner


def create_openai_compatible_llm(
    api_base: str = "http://localhost:11434/v1",
    model: str = "qwen2.5:7b",
    api_key: str = "ollama",
):
    """Factory to create an LLM caller pointing to local Ollama, vLLM, or OpenAI."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    def call_llm(messages):
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
        }
        try:
            resp = requests.post(f"{api_base}/chat/completions", headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            # Fallback to local mock response if server not reached
            print(f"[Warning] LLM API Call to {api_base} failed ({e}), using built-in demonstration response.")
            last_content = messages[-1]["content"]
            if "Observation" in last_content:
                return 'Thought: I received the observation. I can formulate the final answer.\n```json\n{"action": "final_answer", "action_input": {"answer": "Completed based on tools observation: " + last_content[:100]}}\n```'
            return 'Thought: Let me calculate the expression.\n```json\n{"action": "calculator", "action_input": {"expression": "25 * 4 + 15"}}\n```'

    return call_llm


def main():
    parser = argparse.ArgumentParser(description="OmniAgent CLI")
    parser.add_argument("--query", type=str, default="Calculate 12 * (3.5 + 4.2) and save the result into results.txt", help="User task prompt")
    parser.add_argument("--api-base", type=str, default="http://localhost:11434/v1", help="OpenAI-compatible API base URL")
    parser.add_argument("--model", type=str, default="qwen2.5:7b", help="Model name")
    parser.add_argument("--demo", action="store_true", help="Run in self-contained deterministic demo mode")
    args = parser.parse_args()

    # 1. Initialize Tool Registry
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(SearchTool())
    registry.register(PythonExecutorTool())
    registry.register(FileOpsTool())

    # 2. Setup LLM client
    if args.demo:
        llm = None  # OmniAgent will use built-in deterministic demo runner
    else:
        llm = create_openai_compatible_llm(api_base=args.api_base, model=args.model)

    # 3. Instantiate Agent
    agent = OmniAgent(tool_registry=registry, llm_client=llm, verbose=True)

    # 4. Run task
    print(f"\n[*] Running OmniAgent on task: {args.query}\n")
    result = agent.run(args.query)
    print("\n[+] Execution Finished:")
    print(result)


if __name__ == "__main__":
    main()
