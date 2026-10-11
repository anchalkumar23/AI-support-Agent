# Paylane support agent — design

Approved 2026-10-11.

## Goal
Support agent for Paylane (cards, transfers, refunds) on Groq `openai/gpt-oss-120b` (llama-3.3-70b was planned but is retired on Groq), with 4 mock tools, 12 scripted conversations, deterministic eval, a web UI (chat + eval report), and a customer note.

## Files
| File | Purpose |
|---|---|
| `tools.py` | Mock API + data, fixed "today", policy guard on `issue_refund` |
| `agent.py` | System prompt / rulebook, Groq tool loop, per-session state |
| `conversations.py` | 12 conversations + pass/fail checks |
| `run_eval.py` | Runs all → `transcripts/`, `results.json`, `REPORT.md` |
| `server.py` | FastAPI: `POST /api/chat`, `POST /api/reset`, `GET /api/results`, static `web/` |
| `web/` | Chat view (tool trace, verified badge) + eval view |

## Rules — two layers
1. Prompt rulebook (model behaviour).
2. Code guard: `issue_refund` executes only if session verified, txn owned by that customer, `settled`, not refunded, txn amount ≤ $75, `days_ago` < 30, amount == txn amount.

The eval fails a conversation if the model *attempts* a disallowed refund, even though the guard blocks it.

## Verification
LLM-facing tool is `get_customer(email, card_last4)`; code compares last4 against `get_customer(email)` and returns a generic mismatch on failure. The LLM never sees the stored last4 or an email it wasn't given. Account tools require a verified session.

## Interpretations (also listed as questions for Paylane)
- `verified` = passed in-chat identity check this session.
- "Up to $75" inclusive; limit applies to the transaction amount, not the refund amount. Full refunds only.
- "Under 30 days" → `days_ago >= 30` escalates.
- All fraud claims escalate (brief mandates > $500 only).
- Frozen card reason: mock adds `freeze_reason` (not in spec).
- Pending: tell customer to wait for settlement; escalate if fraud / urgent cancellation.

## Eval
Deterministic checks per conversation over tool-call log + replies (refund attempted?, escalated?, leaks?, asked a question?, verification before details?). No LLM judge. One real failure documented with before/after.
