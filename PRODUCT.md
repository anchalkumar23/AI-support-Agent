# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated: FastAPI backend (Python, user's choice) serving one static HTML/CSS/JS page, no build step, so a reviewer runs `pip install` + `uvicorn` and nothing else.

## Users

- Fini hiring reviewers judging a take-home assignment: does the agent follow Paylane's policy under pushback, are the failures caught, is the work clear.
- Paylane's head of support (fictional customer) who wants to see what the agent does and won't do before launch.

## Product Purpose

Demo console for a Paylane customer-support agent (Groq `openai/gpt-oss-120b` (llama-3.3-70b was planned but is retired on Groq)). Two jobs: talk to the agent live and see every tool call it makes; read the 12 scripted test conversations with their pass/fail checks and overall score.

## Operating Context

Run locally on a laptop during review. Viewed next to the repo and README. Sessions are short (minutes). Reviewers will try to break the agent.

## Capabilities and Constraints

- Tools: get_customer (verifies with email + card last 4), get_transaction, issue_refund (policy-guarded in code), escalate_to_human.
- Mock data: 3 customers (Maya Chen, Daniel Okafor, Priya Nair), fixed "today" 2026-10-12.
- Eval results come from `results.json` produced by `run_eval.py`; UI must handle it being absent.
- No auth, no persistence; in-memory sessions.

## Evidence on Hand

Real eval output (results.json, transcripts/). Nothing else: no testimonials, metrics, or brand assets. Paylane is fictional; no logo exists.

## Product Principles

1. Show the agent's actions, not just its words: tool calls and results are first-class.
2. Failures are as visible as passes.
3. Zero setup friction for reviewers.

## Accessibility & Inclusion

WCAG AA contrast, keyboard operable, works at phone width.
