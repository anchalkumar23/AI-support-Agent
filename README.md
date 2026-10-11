# Paylane support agent

An AI support agent for Paylane (cards, transfers, refunds). It runs on Groq (`openai/gpt-oss-120b`) and calls 4 mock API tools. It's tested on 12 scripted customer conversations with automatic pass/fail checks, and comes with a web console where you can read every transcript or chat with the agent yourself.

## Requirements

- Python 3.10 or newer
- A Groq API key (free at https://console.groq.com/keys)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate              # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env              # macOS/Linux: cp .env.example .env
```

Open `.env` and replace the placeholder with your Groq API key.

## Run the web console (frontend)

The frontend has no separate build or start step: the Python server also serves the page.

```bash
uvicorn server:app --port 8765
```

Open **http://127.0.0.1:8765**.

- **Left column:** the 12 test conversations, each marked Pass or Fail. Click one to see the full transcript, every tool call the agent made, and each check.
- **Live (top left):** chat with the agent yourself. The test accounts and transactions are listed on the page.

The left column shows the latest eval results (`results.json`). Run the eval (below) to refresh them.

## Run the eval

```bash
python run_eval.py          # runs all 12 conversations, prints the score
python run_eval.py -n 3     # runs each one 3 times; a conversation passes only if all 3 pass
python run_eval.py 03 11    # runs only conversations 03 and 11
```

This writes [REPORT.md](REPORT.md) (every transcript plus pass/fail checks), `results.json` (used by the console) and `transcripts/`.

**Free Groq keys** allow about 200k tokens a day, and a full run uses about 42k. The eval waits out rate limits automatically and saves after every conversation, so it may take a while on a free key.

## Other commands

```bash
python agent.py             # chat with the agent in the terminal
python tools.py             # self-check of the refund rules (no API calls)
```

## Results

**Score: `SCORE_PLACEHOLDER`.** Every transcript is in [REPORT.md](REPORT.md).

## Where to find each part of the assignment

| Brief | Where |
|---|---|
| 1. Agent: system prompt + rulebook | [agent.py](agent.py) (`SYSTEM_PROMPT`), with the hard rules also enforced in code in [tools.py](tools.py) |
| 2. API tools (4 mock functions) | [tools.py](tools.py) (`PaylaneAPI`), wired to the model in [agent.py](agent.py) |
| 3. 12 conversations + transcripts | [conversations.py](conversations.py), [REPORT.md](REPORT.md), `transcripts/` |
| Which edge cases I chose and why | [docs/WRITEUP.md](docs/WRITEUP.md#the-12-conversations) |
| 4. Eval, score, a failure and its fix | [docs/WRITEUP.md](docs/WRITEUP.md#failures-i-found-and-how-i-fixed-them) |
| 5. Customer note | [CUSTOMER_NOTE.md](CUSTOMER_NOTE.md) |
| Questions for Paylane | [docs/WRITEUP.md](docs/WRITEUP.md#my-readings-of-the-ambiguous-parts-and-questions-for-paylane) |

## Notes

- **Model:** the default is `openai/gpt-oss-120b`. To try another Groq model, set `GROQ_MODEL` in `.env`.
- **Run locally only:** the console has no login or rate limiting.
- **Mock data:** "today" is fixed at 2026-10-12 so results are reproducible.

## License

Proprietary, all rights reserved. Fini may view and run this code only to evaluate this assignment. See [LICENSE](LICENSE).
