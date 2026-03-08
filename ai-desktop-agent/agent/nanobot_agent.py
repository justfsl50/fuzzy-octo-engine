"""Core orchestration logic for the Nanobot desktop agent."""

from dataclasses import dataclass


@dataclass
class NanobotAgent:
    name: str = "nanobot"

    def run(self, task: str) -> str:
        return f"{self.name} received task: {task}"
