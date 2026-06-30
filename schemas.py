from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional


class WorkflowDecision(BaseModel):
    outcome: Literal[
        "promise_to_pay",
        "paid_now",
        "callback_requested",
        "partial_payment",
        "dispute",
        "financial_distress",
        "refusal",
        "no_resolution",
    ]
    risk_score: int = Field(ge=1, le=5)
    next_action: str
    promise_date: Optional[str] = None
    escalation_required: bool = False
    reminder_required: bool = False
