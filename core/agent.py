"""
Core ReAct Agent implementation for OmniAgent Framework.
"""
from __future__ import annotations
import json
import re
from typing import Any, Callable, Dict, List, Optional

try:
    from pydantic import BaseModel
    class AgentTrace(BaseModel):
        step: int
        thought: str
        action: str
        action_input: Dict[str, Any]
        observation: str
except ImportError:
    class AgentTrace:
        def __init__(self, step: int, thought: str, action: str, action_input: Dict[str, Any], observation: str):
            self.step = step
            self.thought = thought
            self.action = action
            self.action_input = action_input
            self.observation = observation

try:
    from rich.console import Console
except ImportError:
    class Console:
        def rule(self, title: str = ""):
            print(f"=== {title} ===")
        def print(self, msg: str):
            # Strip simple rich tags like [bold green]
            clean = re.sub(r"\[.*?\]", "", str(msg))
            print(clean)

from core.memory import ShortTermMemory, LongTermMemory
from core.planner import Plan, SubTask, TaskPlanner, TaskStatus
from tools.base import ToolRegistry, ToolResult
from prompts.system_prompts import REACT_SYSTEM_PROMPT



class OmniAgent:
    """Production-grade ReAct agent loop supporting Tool execution, Planning, and Memory."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        llm_client: Optional[Callable[[List[Dict[str, Any]]], str]] = None,
        max_iterations: int = 10,
        verbose: bool = True,
    ):
        self.tools = tool_registry
        self.llm_client = llm_client or self._default_mock_llm
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.console = Console()
        self.short_memory = ShortTermMemory()
        self.long_memory = LongTermMemory()
        self.traces: List[AgentTrace] = []

    def _default_mock_llm(self, messages: List[Dict[str, Any]]) -> str:
        """Deterministic fallback model for self-contained demonstration."""
        all_text = " ".join([m.get("content", "") for m in messages])
        last_msg = messages[-1]["content"]

        if "Calculate" in all_text or "12 * (3.5 + 4.2)" in all_text:
            if "Observation" not in last_msg:
                return 'Thought: I need to calculate the mathematical expression accurately.\n```json\n{"action": "calculator", "action_input": {"expression": "12 * (3.5 + 4.2)"}}\n```'
            else:
                return 'Thought: I got the calculation result. Now I can formulate the final answer.\n```json\n{"action": "final_answer", "action_input": {"answer": "The calculation 12 * (3.5 + 4.2) equals 92.4."}}\n```'

        # Default fallback
        return 'Thought: I should finish this task directly.\n```json\n{"action": "final_answer", "action_input": {"answer": "Task successfully addressed."}}\n```'


    def _parse_action(self, response_text: str) -> tuple[str, str, Dict[str, Any]]:
        thought = ""
        thought_match = re.search(r"Thought:\s*(.*?)(?=```json|\Z)", response_text, re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if not json_match:
            # Fallback direct JSON search
            json_match = re.search(r"(\{.*\})", response_text, re.DOTALL)

        if json_match:
            try:
                data = json.loads(json_match.group(1))
                action = data.get("action", "")
                action_input = data.get("action_input", {})
                return thought, action, action_input
            except json.JSONDecodeError:
                pass

        return thought, "error", {"raw": response_text}

    def run(self, user_prompt: str) -> str:
        """Run the end-to-end ReAct loop."""
        if self.verbose:
            self.console.rule(f"[bold cyan]OmniAgent: Starting Task[/bold cyan]")
            self.console.print(f"[bold green]User Prompt:[/bold green] {user_prompt}\n")

        # Retrieve relevant context from long-term memory
        retrieved_docs = self.long_memory.search(user_prompt, top_k=2)
        memory_context = ""
        if retrieved_docs:
            memory_context = "\n### Relevant Episodic Memories:\n" + "\n".join(
                [f"- {d['text']}" for d in retrieved_docs]
            )

        # Build tools description
        tool_descriptions = "\n".join(
            [f"- {t.name}: {t.description}\n  Schema: {json.dumps(t.parameters)}" for t in self.tools.list_tools()]
        )

        system_msg = REACT_SYSTEM_PROMPT.format(tool_descriptions=tool_descriptions) + memory_context
        self.short_memory.clear()
        self.short_memory.add("system", system_msg)
        self.short_memory.add("user", user_prompt)
        self.traces.clear()

        for step in range(1, self.max_iterations + 1):
            if self.verbose:
                self.console.print(f"-- Step {step}/{self.max_iterations} --")

            # Call LLM
            response = self.llm_client(self.short_memory.get_context())
            thought, action, action_input = self._parse_action(response)

            if self.verbose and thought:
                self.console.print(f"[magenta]Thought:[/magenta] {thought}")

            # Check for final answer
            if action == "final_answer":
                final_answer = action_input.get("answer", "")
                if self.verbose:
                    self.console.print(f"[bold green]Final Answer:[/bold green]\n{final_answer}")
                    self.console.rule("[bold cyan]Task Completed[/bold cyan]")

                # Save successful experience into long-term memory
                self.long_memory.add_document(f"Q: {user_prompt} | A: {final_answer}")
                return final_answer

            if action == "error" or not action:
                obs = f"Failed to parse valid Action JSON from response: {action_input.get('raw')}"
            else:
                if self.verbose:
                    self.console.print(f"[yellow]Action:[/yellow] [bold]{action}[/bold] with input: {action_input}")
                tool_res = self.tools.execute(action, **action_input)
                obs = str(tool_res)
                if self.verbose:
                    self.console.print(f"[cyan]Observation:[/cyan] {obs}\n")

            # Record Trace
            trace = AgentTrace(
                step=step,
                thought=thought,
                action=action,
                action_input=action_input,
                observation=obs,
            )
            self.traces.append(trace)

            # Update context for next iteration
            step_prompt = f"Thought: {thought}\nAction: {action}\nObservation: {obs}"
            self.short_memory.add("assistant", response)
            self.short_memory.add("user", f"Observation from '{action}': {obs}")

        timeout_msg = f"Task reached maximum iterations ({self.max_iterations}) without concluding."
        if self.verbose:
            self.console.print(f"[red]{timeout_msg}[/red]")
        return timeout_msg
