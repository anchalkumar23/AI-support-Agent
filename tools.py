"""Mock Paylane API (matches the spec) plus the refund policy guard."""
import copy
import uuid
from datetime import date

# Fixed "today" so the eval is reproducible.
TODAY = date(2026, 10, 12)

REFUND_LIMIT = 75.00
REFUND_MAX_DAYS = 30  # "under 30 days old" -> 30+ escalates

SEED = {
    "customers": {
        "maya.chen@example.com": {"id": "C001", "name": "Maya Chen", "card_last4": "4821", "status": "active", "verified": False},
        "d.okafor@example.com": {"id": "C002", "name": "Daniel Okafor", "card_last4": "7390", "status": "frozen", "verified": False,
                                 # Not in the spec: the brief says the agent explains *why* a card is frozen, so the API must expose it.
                                 "freeze_reason": "Three incorrect PIN attempts at an ATM on 2026-10-10"},
        "priya.nair@example.com": {"id": "C003", "name": "Priya Nair", "card_last4": "1157", "status": "active", "verified": False},
    },
    "transactions": {
        "C001": {
            "T1001": {"amount": 42.50, "date": "2026-10-07", "merchant": "Brewline Coffee Gear", "status": "settled"},
            "T1002": {"amount": 75.00, "date": "2026-10-02", "merchant": "Northside Fitness", "status": "settled"},
            "T1003": {"amount": 120.00, "date": "2026-10-09", "merchant": "Lumen Audio", "status": "settled"},
            "T1004": {"amount": 30.00, "date": "2026-09-12", "merchant": "PageTurn Books", "status": "settled"},
            "T1005": {"amount": 18.99, "date": "2026-09-30", "merchant": "StreamBox", "status": "refunded"},
        },
        "C002": {
            "T2001": {"amount": 54.00, "date": "2026-10-08", "merchant": "GreenCart Grocery", "status": "settled"},
        },
        "C003": {
            "T3001": {"amount": 640.00, "date": "2026-10-10", "merchant": "ElectroMart Online", "status": "settled"},
            "T3002": {"amount": 25.00, "date": "2026-10-11", "merchant": "CityRide", "status": "pending"},
        },
    },
}


class PaylaneAPI:
    """The 4 endpoints from the spec, backed by an in-memory copy of SEED (one per session)."""

    def __init__(self):
        self.db = copy.deepcopy(SEED)
        self.tickets = []

    def get_customer(self, email):
        c = self.db["customers"].get(str(email).strip().lower())
        return dict(c, email=str(email).strip().lower()) if c else None

    def get_transaction(self, customer_id, txn_id):
        t = self.db["transactions"].get(customer_id, {}).get(str(txn_id).strip().upper())
        return dict(t) if t else None

    def issue_refund(self, txn_id, amount):
        t = next((txns[txn_id] for txns in self.db["transactions"].values() if txn_id in txns), None)
        if not t:
            return {"ok": False, "reason": "transaction not found"}
        if t["status"] == "refunded":
            return {"ok": False, "reason": "already refunded"}
        t["status"] = "refunded"
        return {"ok": True, "refund_id": "R-" + uuid.uuid4().hex[:8].upper()}

    def escalate_to_human(self, customer_id, summary):
        ticket = {"ticket_id": "TKT-" + uuid.uuid4().hex[:6].upper()}
        self.tickets.append(dict(ticket, customer_id=customer_id, summary=summary))
        return ticket


def days_ago(txn):
    return (TODAY - date.fromisoformat(txn["date"])).days


def refund_block_reason(txn, amount):
    """None if policy allows auto-refunding `amount` on `txn`, else why not. Runs in code, whatever the LLM decides."""
    if txn is None:
        return "transaction not found for this customer"
    if txn["status"] == "refunded":
        return "already refunded; never refund twice"
    if txn["status"] == "pending":
        return "transaction is still pending; it can't be refunded until it settles"
    if txn["amount"] > REFUND_LIMIT:
        return f"transaction is over ${REFUND_LIMIT:.0f}; escalate to a human"
    if days_ago(txn) >= REFUND_MAX_DAYS:
        return f"transaction is {REFUND_MAX_DAYS}+ days old; escalate to a human"
    try:
        amount = round(float(amount), 2)
    except (TypeError, ValueError):
        return "invalid amount"
    if amount != txn["amount"]:
        return "only full refunds of the transaction amount are allowed; partial refunds go to a human"
    return None


if __name__ == "__main__":
    api = PaylaneAPI()
    tx = lambda t: api.get_transaction("C001", t)
    assert refund_block_reason(tx("T1001"), 42.5) is None
    assert refund_block_reason(tx("T1002"), 75) is None              # exactly $75 is allowed
    assert "over" in refund_block_reason(tx("T1003"), 75)           # can't split $120 into a $75 refund
    assert "days" in refund_block_reason(tx("T1004"), 30)           # exactly 30 days escalates
    assert "already" in refund_block_reason(tx("T1005"), 18.99)
    assert "pending" in refund_block_reason(api.get_transaction("C003", "T3002"), 25)
    assert "full" in refund_block_reason(tx("T1001"), 20)
    assert refund_block_reason(None, 1)
    assert api.issue_refund("T1001", 42.5)["ok"] and not api.issue_refund("T1001", 42.5)["ok"]
    assert PaylaneAPI().get_transaction("C001", "T1001")["status"] == "settled"  # sessions don't share state
    print("tools.py checks passed")
