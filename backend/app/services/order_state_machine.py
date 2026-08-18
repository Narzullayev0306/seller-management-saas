"""Order status transition rules (single source of truth)."""

from __future__ import annotations

from app.core.exceptions import ApiError

ORDER_STATUSES = (
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
)
FINAL_STATUSES = ("delivered", "cancelled")

# Allowed forward transitions; any non-final state may be cancelled.
_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"confirmed", "cancelled"}),
    "confirmed": frozenset({"processing", "cancelled"}),
    "processing": frozenset({"shipped", "cancelled"}),
    "shipped": frozenset({"delivered", "cancelled"}),
    "delivered": frozenset(),
    "cancelled": frozenset(),
}


class OrderStateMachine:
    @staticmethod
    def can_transition(current: str, new: str) -> bool:
        return new in _TRANSITIONS.get(current, frozenset())

    @staticmethod
    def assert_transition(current: str, new: str) -> None:
        """Raise when the transition is not allowed. Same-status is a no-op."""
        if current == new:
            return
        if not OrderStateMachine.can_transition(current, new):
            raise ApiError(
                400,
                "INVALID_STATUS_TRANSITION",
                f"Cannot move order from '{current}' to '{new}'",
            )
