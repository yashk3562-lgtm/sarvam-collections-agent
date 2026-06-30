from __future__ import annotations

from datetime import date
from typing import Dict

from mock_crm import add_crm_event, add_reminder, add_escalation, get_account
from policies import RISK_KEYWORDS
from schemas import WorkflowDecision


def classify_borrower_intent(text: str) -> WorkflowDecision:
    t = text.lower()

    if any(k in t for k in RISK_KEYWORDS["dispute"]):
        return WorkflowDecision(
            outcome="dispute",
            risk_score=5,
            next_action="Escalate to dispute-resolution specialist",
            escalation_required=True,
        )
    if any(k in t for k in RISK_KEYWORDS["distress"]):
        return WorkflowDecision(
            outcome="financial_distress",
            risk_score=4,
            next_action="Escalate for hardship handling and compliant repayment options",
            escalation_required=True,
        )
    if any(k in t for k in RISK_KEYWORDS["refusal"]):
        return WorkflowDecision(
            outcome="refusal",
            risk_score=5,
            next_action="Escalate to senior collections agent with no repeat bot call today",
            escalation_required=True,
        )
    if any(k in t for k in RISK_KEYWORDS["promise"]):
        return WorkflowDecision(
            outcome="promise_to_pay",
            risk_score=2,
            next_action="Queue reminder and suppress repeated calls until promised date",
            promise_date="Friday",
            reminder_required=True,
        )
    return WorkflowDecision(
        outcome="no_resolution",
        risk_score=3,
        next_action="Ask one clarifying question or schedule callback",
    )


def execute_workflow(borrower_id: str, borrower_text: str, agent_text: str) -> Dict:
    account = get_account(borrower_id)
    decision = classify_borrower_intent(borrower_text)

    crm_event = {
        "borrower_id": borrower_id,
        "borrower_name": account.name,
        "outcome": decision.outcome,
        "risk_score": decision.risk_score,
        "promise_date": decision.promise_date,
        "next_action": decision.next_action,
        "borrower_text": borrower_text,
        "agent_text": agent_text,
    }
    add_crm_event(crm_event)

    if decision.reminder_required:
        add_reminder({
            "borrower_id": borrower_id,
            "channel": "WhatsApp/SMS",
            "send_on": decision.promise_date or str(date.today()),
            "message": f"Reminder queued for EMI payment of INR {account.emi_amount}",
        })

    if decision.escalation_required:
        add_escalation({
            "borrower_id": borrower_id,
            "reason": decision.outcome,
            "priority": "High" if decision.risk_score >= 4 else "Medium",
            "assigned_queue": "Human Collections Specialist",
        })

    return {"decision": decision.model_dump(), "crm_event": crm_event}
