from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from typing import Dict, List


@dataclass
class BorrowerAccount:
    borrower_id: str
    name: str
    language: str
    city: str
    product: str
    emi_amount: int
    overdue_days: int
    due_date: str
    risk_band: str
    last_outcome: str
    phone: str


ACCOUNTS: Dict[str, BorrowerAccount] = {
    "BRW001": BorrowerAccount(
        borrower_id="BRW001",
        name="Ramesh Kumar",
        language="Hindi",
        city="Lucknow",
        product="Two-wheeler loan",
        emi_amount=4850,
        overdue_days=7,
        due_date="2026-06-23",
        risk_band="Medium",
        last_outcome="No answer",
        phone="+91-98XXXXXX11",
    ),
    "BRW002": BorrowerAccount(
        borrower_id="BRW002",
        name="Asha Patil",
        language="Marathi/Hinglish",
        city="Pune",
        product="Personal loan",
        emi_amount=7200,
        overdue_days=3,
        due_date="2026-06-27",
        risk_band="Low",
        last_outcome="Callback requested",
        phone="+91-98XXXXXX22",
    ),
    "BRW003": BorrowerAccount(
        borrower_id="BRW003",
        name="Imran Shaikh",
        language="Hindi/Hinglish",
        city="Bhopal",
        product="Consumer durable loan",
        emi_amount=2650,
        overdue_days=15,
        due_date="2026-06-15",
        risk_band="High",
        last_outcome="Broken promise-to-pay",
        phone="+91-98XXXXXX33",
    ),
}

CRM_EVENTS: List[dict] = []
REMINDER_QUEUE: List[dict] = []
ESCALATION_QUEUE: List[dict] = []


def get_account(borrower_id: str) -> BorrowerAccount:
    return ACCOUNTS[borrower_id]


def list_accounts() -> List[dict]:
    return [asdict(v) for v in ACCOUNTS.values()]


def add_crm_event(event: dict) -> None:
    event["event_date"] = str(date.today())
    CRM_EVENTS.append(event)


def add_reminder(event: dict) -> None:
    event["created_date"] = str(date.today())
    REMINDER_QUEUE.append(event)


def add_escalation(event: dict) -> None:
    event["created_date"] = str(date.today())
    ESCALATION_QUEUE.append(event)
