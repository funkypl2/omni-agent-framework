"""
Task Planner and Goal Decomposition module.
"""
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field

    class TaskStatus(str, Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        FAILED = "failed"

    class SubTask(BaseModel):
        id: int
        description: str
        status: TaskStatus = TaskStatus.PENDING
        assigned_tool: Optional[str] = None
        result: Optional[str] = None

    class Plan(BaseModel):
        goal: str
        subtasks: List[SubTask] = Field(default_factory=list)

        def is_complete(self) -> bool:
            return all(t.status == TaskStatus.COMPLETED for t in self.subtasks)

        def current_task(self) -> Optional[SubTask]:
            for t in self.subtasks:
                if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
                    return t
            return None

        def summary(self) -> str:
            lines = [f"Goal: {self.goal}"]
            for t in self.subtasks:
                icon = {
                    TaskStatus.PENDING: "[P]",
                    TaskStatus.IN_PROGRESS: "[>]",
                    TaskStatus.COMPLETED: "[V]",
                    TaskStatus.FAILED: "[X]",
                }[t.status]
                res_info = f" -> {t.result[:60]}..." if t.result else ""
                lines.append(f"  {icon} [Task {t.id}] {t.description} ({t.assigned_tool or 'general'}){res_info}")
            return "\n".join(lines)

except ImportError:
    class TaskStatus(str, Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        FAILED = "failed"

    class SubTask:
        def __init__(self, id: int, description: str, status: TaskStatus = TaskStatus.PENDING, assigned_tool: Optional[str] = None, result: Optional[str] = None):
            self.id = id
            self.description = description
            self.status = status
            self.assigned_tool = assigned_tool
            self.result = result

    class Plan:
        def __init__(self, goal: str, subtasks: Optional[List[SubTask]] = None):
            self.goal = goal
            self.subtasks = subtasks or []

        def is_complete(self) -> bool:
            return all(t.status == TaskStatus.COMPLETED for t in self.subtasks)

        def current_task(self) -> Optional[SubTask]:
            for t in self.subtasks:
                if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
                    return t
            return None

        def summary(self) -> str:
            lines = [f"Goal: {self.goal}"]
            for t in self.subtasks:
                icon = {
                    TaskStatus.PENDING: "[P]",
                    TaskStatus.IN_PROGRESS: "[>]",
                    TaskStatus.COMPLETED: "[V]",
                    TaskStatus.FAILED: "[X]",
                }[t.status]
                res_info = f" -> {t.result[:60]}..." if t.result else ""
                lines.append(f"  {icon} [Task {t.id}] {t.description} ({t.assigned_tool or 'general'}){res_info}")
            return "\n".join(lines)



class TaskPlanner:
    """Plans and decomposes high-level goals into executable subtasks."""

    @staticmethod
    def create_plan_from_text(goal: str, steps: List[Dict[str, str]]) -> Plan:
        subtasks = []
        for i, s in enumerate(steps, 1):
            subtasks.append(
                SubTask(
                    id=i,
                    description=s.get("description", f"Step {i}"),
                    assigned_tool=s.get("tool"),
                )
            )
        return Plan(goal=goal, subtasks=subtasks)
