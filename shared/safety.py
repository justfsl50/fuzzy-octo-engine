"""Shared safety confirmation gates for agent and MCP layers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfirmationRequest:
    """A structured request describing an action that needs confirmation."""

    action: str
    target: str
    reason: str = ""

    def prompt(self) -> str:
        reason_suffix = f" Reason: {self.reason}" if self.reason else ""
        return (
            f"Please confirm action '{self.action}' for '{self.target}'."
            f" Reply exactly with '{ConfirmationGate.CONFIRM_PHRASE}' to proceed."
            f"{reason_suffix}"
        )


class ConfirmationGate:
    """Utility to enforce explicit opt-in for destructive operations."""

    CONFIRM_PHRASE = "YES, PROCEED"

    @classmethod
    def is_confirmed(cls, user_confirmation: str | None) -> bool:
        if user_confirmation is None:
            return False
        return user_confirmation.strip() == cls.CONFIRM_PHRASE

    @classmethod
    def require_confirmation(cls, request: ConfirmationRequest, user_confirmation: str | None) -> None:
        if cls.is_confirmed(user_confirmation):
            return

        raise PermissionError(request.prompt())
