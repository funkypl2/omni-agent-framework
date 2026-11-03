# OmniAgent: Industrial-Grade Autonomous Agent Framework

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Architecture: ReAct](https://img.shields.io/badge/Architecture-ReAct%20%2B%20Plan%20%26%20Solve-green.svg)]()

**OmniAgent** 是一个模块化、生产级的自主 AI Agent 框架，完整实现了从**目标规划（Plan-and-Solve）**、**ReAct 循环推理（Thought -> Action -> Observation）**、**双层记忆（短时滑动窗口 + 语义长时记忆）** 到 **沙箱工具执行与安全熔断** 的全套核心工程流程。

---

## 🌟 核心架构与功能特性

```
                     ┌───────────────────────────────┐
                     │          User Request         │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │         Task Planner          │
                     │  (Goal Decomposition & State) │
                     └───────────────┬───────────────┘
                                     │
      ┌──────────────────────────────┴──────────────────────────────┐
      │                        ReAct Loop                           │
      │   ┌───────────────┐        ┌───────────────┐                │
      │   │  Thought /    │───────►│    Action     │                │
      │   │  Reasoning    │        │  (Tool Call)  │                │
      │   └───────▲───────┘        └───────┬───────┘                │
      │           │                        │                        │
      │           │                        ▼                        │
      │   ┌───────┴───────┐        ┌───────────────┐                │
      │   │  Observation  │◄───────│ Tool Registry │                │
      │   └───────────────┘        └───────┬───────┘                │
      └────────────────────────────────────┼────────────────────────┘
                                           ▼
                    ┌──────────────────────────────────────┐
                    │  Tool Execution Sandbox & Registry   │
                    │  • Calculator (AST Safe Evaluator)   │
                    │  • WebSearch (Semantic Knowledge)    │
                    │  • PythonInterpreter (Code Sandbox)  │
                    │  • FileOps (Workspace Read/Write)    │
                    └──────────────────────────────────────┘
```

1. **ReAct 推理引擎 (`core/agent.py`)**：严格遵循结构化 JSON Action 协议，具备自动容错、输出校验与最大轮次熔断保护。
2. **任务规划器 (`core/planner.py`)**：支持复杂宏观目标的任务拆解（Sub-task Decomposition）、状态机流转与动态重规划。
3. **分层记忆系统 (`core/memory.py`)**：
   - **短期工作记忆**：滑动窗口消息上下文，自动保留系统角色设定。
   - **长期情境记忆**：基于轻量化 TF-IDF 向量检索，自动沉淀任务成功经验并用于后续上下文注入。
4. **工具箱扩展体系 (`tools/`)**：统一抽象标准接口，内置 AST 安全数学计算器、网络检索器、Python 沙箱执行器以及本地文件操作工具。

---

## 🚀 快速上手 (Quick Start)

### 1. 安装依赖
```bash
cd 01-omni-agent-framework
pip install -r requirements.txt
```

### 2. 运行内置确定性 Demo
无需额外配置 API Key，直接体验 ReAct 完整闭环推理过程：
```bash
python main.py --demo
```

### 3. 连接本地 7B 模型（Ollama / vLLM / OpenAI API）
支持一键对接本地运行的开源大模型（如 `qwen2.5:7b`）：
```bash
# 本地 Ollama 部署 Qwen2.5-7B
ollama run qwen2.5:7b

# 运行 OmniAgent
python main.py --api-base http://localhost:11434/v1 --model qwen2.5:7b --query "计算 12 * (3.5 + 4.2) 并把结果写入 results.txt"
```

### 4. 运行单元测试
```bash
pytest tests/ -v
```

---

## 🛠️ 自定义工具开发示例

仅需继承 `BaseTool` 并实现 `run` 方法即可快速扩展自己的专属工具：

```python
from tools.base import BaseTool, ToolResult

class WeatherTool(BaseTool):
    name = "get_weather"
    description = "查询指定城市的当前实时天气"
    parameters = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称，例如 'Beijing'"}
        },
        "required": ["city"]
    }

    def run(self, city: str, **kwargs) -> ToolResult:
        # 实现你的业务逻辑或外部 API 调用
        return ToolResult(success=True, output=f"{city} 当前天气：晴朗，温度 22°C")
```

---

## 📄 开源许可证
本项目采用 [MIT License](LICENSE) 授权协议。
