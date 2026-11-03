"""
Unit tests for OmniAgent Framework components.
"""
import os
import sys

# Ensure parent directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pytest
from tools.base import ToolRegistry
from tools.calculator import CalculatorTool
from tools.search import SearchTool
from tools.python_executor import PythonExecutorTool
from core.memory import ShortTermMemory, LongTermMemory
from core.planner import TaskPlanner, TaskStatus
from core.agent import OmniAgent


def test_calculator_tool():
    calc = CalculatorTool()
    res = calc.run("10 + 2 * 5")
    assert res.success is True
    assert res.output == 20

    res_func = calc.run("sqrt(144) + sin(0)")
    assert res_func.success is True
    assert res_func.output == 12.0


def test_python_executor():
    py = PythonExecutorTool()
    code = "x = [i**2 for i in range(5)]\nprint('SUM:', sum(x))"
    res = py.run(code)
    assert res.success is True
    assert "SUM: 30" in res.output


def test_memory_systems():
    # Short term memory
    stm = ShortTermMemory(max_messages=3)
    stm.add("user", "Hello 1")
    stm.add("assistant", "Hi 1")
    stm.add("user", "Hello 2")
    stm.add("assistant", "Hi 2")
    assert len(stm.messages) == 3

    # Long term episodic memory
    ltm = LongTermMemory()
    ltm.add_document("Qwen2.5 is an LLM with 7B parameters developed by Alibaba.")
    ltm.add_document("PyTorch is an open-source machine learning framework.")

    results = ltm.search("tell me about qwen parameters", top_k=1)
    assert len(results) == 1
    assert "Qwen2.5" in results[0]["text"]


def test_agent_react_loop():
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    agent = OmniAgent(tool_registry=registry, verbose=False)
    answer = agent.run("Calculate 12 * (3.5 + 4.2)")
    assert "92.4" in answer
