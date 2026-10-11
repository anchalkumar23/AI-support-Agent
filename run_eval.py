"""Run the 12 conversations through the agent and score them.

    python run_eval.py            # all, once each
    python run_eval.py -n 3       # each conversation 3 times; it passes only if every run passes
    python run_eval.py 03 07     # only conversations whose id starts with these (merged into results.json)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from agent import MODEL, Session
from conversations import CONVERSATIONS

ROOT = Path(__file__).parent
OUT = ROOT / "transcripts"
RESULTS = ROOT / "results.json"


def run(conv):
    s, turns = Session(wait_on_rate_limit=True), []
    for msg in conv["turns"]:
        reply, tools = s.send(msg)
        turns.append({"user": msg, "reply": reply, "tools": tools})
    r = {"id": conv["id"], "title": conv["title"], "why": conv["why"], "turns": turns, "tokens": s.tokens}
    r["checks"] = []
    for name, fn in conv["checks"]:
        try:
            ok = bool(fn(r))
        except Exception as e:  # a check that crashes is a failed check, not a crashed eval
            ok, name = False, f"{name} (check error: {e})"
        r["checks"].append({"name": name, "passed": ok})
    r["passed"] = all(c["passed"] for c in r["checks"])
    return r


def report(results):
    lines = [f"# Eval report\n\nModel: `{results['model']}` · run {results['run_at']}\n",
             f"**Score: {results['passed']}/{results['total']} conversations passed** "
             f"({results['checks_passed']}/{results['checks_total']} checks)\n"]
    for r in results["conversations"]:
        lines.append(f"\n## {'PASS' if r['passed'] else 'FAIL'} · {r['id']} · {r['title']} ({r.get('runs_passed', int(r['passed']))}/{r.get('runs', 1)} runs)\n\n_{r['why']}_\n"
                     + ("\nTranscript below is the first failing run.\n" if not r["passed"] else ""))
        for t in r["turns"]:
            lines.append(f"\n**Customer:** {t['user']}\n")
            for c in t["tools"]:
                lines.append(f"\n> `{c['name']}({json.dumps(c['args'])})` → `{json.dumps(c['result'])}`\n")
            lines.append(f"\n**Agent:** {t['reply']}\n")
        lines.append("\n" + "\n".join(f"- [{'x' if c['passed'] else ' '}] {c['name']}" for c in r["checks"]) + "\n")
    (ROOT / "REPORT.md").write_text("".join(lines), encoding="utf-8")


def run_n(conv, n):
    """LLMs aren't deterministic even at temperature 0, so one pass proves little. Keep the first failing run (or the last)."""
    runs = [run(conv) for _ in range(n)]
    r = next((x for x in runs if not x["passed"]), runs[-1])
    r["runs"], r["runs_passed"] = n, sum(x["passed"] for x in runs)
    r["passed"] = r["runs_passed"] == n
    return r


def main(prefixes, n=1):
    old = {r["id"]: r for r in json.loads(RESULTS.read_text(encoding="utf-8"))["conversations"]} if prefixes and RESULTS.exists() else {}
    OUT.mkdir(exist_ok=True)
    for conv in CONVERSATIONS:
        if prefixes and not conv["id"].startswith(tuple(prefixes)):
            continue
        r = run_n(conv, n)
        old[conv["id"]] = r
        (OUT / f"{conv['id']}.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        failed = [c["name"] for c in r["checks"] if not c["passed"]]
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {conv['id']}  ({r['runs_passed']}/{n} runs)"
              + (f"   failed: {failed}" if failed else ""), flush=True)
        save(old)  # after every conversation, so a crash or Ctrl+C keeps what ran
    results = save(old)
    print(f"\nScore: {results['passed']}/{results['total']} conversations, "
          f"{results['checks_passed']}/{results['checks_total']} checks. See REPORT.md")


def save(old):
    convs = [old[c["id"]] for c in CONVERSATIONS if c["id"] in old]
    results = {
        "model": MODEL, "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "passed": sum(r["passed"] for r in convs), "total": len(convs),
        "checks_passed": sum(c["passed"] for r in convs for c in r["checks"]),
        "checks_total": sum(len(r["checks"]) for r in convs),
        "conversations": convs,
    }
    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    report(results)
    return results


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    n = int(args.pop(args.index("-n") + 1)) if "-n" in args else 1
    main([a for a in args if a != "-n"], n)
