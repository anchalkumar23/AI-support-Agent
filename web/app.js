// Paylane agent console. All untrusted text goes through textContent (h()), never innerHTML.
const $ = (sel, root = document) => root.querySelector(sel);
const SVG = "http://www.w3.org/2000/svg";

function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid instanceof Node ? kid : String(kid));
  return el;
}

function mark(passed) {
  const m = h("span", { class: "mark " + (passed ? "pass" : "fail") }, passed ? "Pass" : "Fail");
  if (!passed) {
    const svg = document.createElementNS(SVG, "svg");
    svg.setAttribute("viewBox", "0 0 100 40");
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("aria-hidden", "true");
    const e = document.createElementNS(SVG, "ellipse");
    Object.entries({ cx: 50, cy: 20, rx: 47, ry: 17, transform: "rotate(-3 50 20)" }).forEach(([k, v]) => e.setAttribute(k, v));
    svg.append(e);
    m.append(svg);
  }
  return m;
}

// ---- tool call ("clearance") formatting --------------------------------
const fmtArgs = (args) => Object.entries(args || {}).map(([k, v]) => `${k}=${typeof v === "string" ? v : JSON.stringify(v)}`).join("  ");

function fmtResult(r) {
  if (!r || typeof r !== "object") return String(r);
  if (r.error) return r.error;
  if ("ok" in r) return r.ok ? `ok · refund ${r.refund_id}` : `refused · ${r.reason}`;
  if (r.ticket_id) return `ticket ${r.ticket_id}`;
  if ("verified" in r && !r.verified) return "verification failed";
  return Object.entries(r).map(([k, v]) => `${k}=${v}`).join("  ");
}

function clrState(r) {
  if (r && r.ok === false) return "blocked";
  if (r && (r.error || r.verified === false)) return "denied";
  if (r && (r.ok || r.verified || r.ticket_id)) return "ok";
  return "";
}

function line(kind, who, ...content) {
  return h("li", { class: "line " + kind }, h("span", { class: "who" }, who), h("div", { class: "what" }, ...content));
}

function clearances(tools) {
  if (!tools || !tools.length) return null;
  return line("clr", "Action", tools.map((t) =>
    h("div", { class: "clr-row " + clrState(t.result) },
      h("span", { class: "tool" }, t.name), "  ", h("span", { class: "args" }, fmtArgs(t.args)),
      h("span", { class: "res" }, fmtResult(t.result)))));
}

function turnLines(t) {
  return [line("cust", "Customer", h("p", {}, t.user)), clearances(t.tools), line("agent", "Agent", h("p", {}, t.reply))].filter(Boolean);
}

// ---- state + routing ----------------------------------------------------
let results = null;
const live = { sessionId: null, turns: [], customer: null, busy: false, el: null };

async function getJSON(url, opts) {
  const res = await fetch(url, opts);
  let body = null;
  try { body = await res.json(); } catch { /* non-JSON error page */ }
  if (!res.ok) throw new Error(typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`);
  return body;
}

function renderBay() {
  const list = $("#strips");
  list.replaceChildren();
  if (!results) {
    list.append(h("li", {}, h("p", { class: "bay-empty" }, "No eval run yet. Run ", h("code", {}, "python run_eval.py"), " and reload.")));
    $("#tally").replaceChildren();
    return;
  }
  for (const c of results.conversations) {
    const n = c.checks.filter((x) => x.passed).length;
    list.append(h("li", {}, h("a", { class: "strip", href: `#/run/${encodeURIComponent(c.id)}`, "data-id": c.id },
      h("span", { class: "cs" }, c.id.slice(0, 2)),
      h("span", { class: "strip-main" }, h("span", { class: "strip-title" }, c.title), h("span", { class: "strip-why" }, c.why)),
      h("span", { class: "strip-res" }, mark(c.passed), h("span", { class: "strip-checks" }, `${n}/${c.checks.length}`)))));
  }
  const fails = results.total - results.passed;
  $("#run-meta").textContent = `${results.model} · ${results.run_at}`;
  $("#tally").replaceChildren(
    h("b", {}, `${results.passed}/${results.total}`), " cleared",
    fails ? h("span", { class: "fails" }, ` · ${fails} failed`) : null,
    h("span", { class: "dim" }, ` · ${results.checks_passed}/${results.checks_total} checks`));
}

function setCurrent(id) {
  document.querySelectorAll(".strip").forEach((s) => s.removeAttribute("aria-current"));
  const el = id === "live" ? $("#live-link") : document.querySelector(`.strip[data-id="${CSS.escape(id)}"]`);
  if (el) el.setAttribute("aria-current", "page");
}

function renderRun(id) {
  const c = results && results.conversations.find((x) => x.id === id);
  if (!c) return renderLive();
  setCurrent(id);
  const n = c.checks.filter((x) => x.passed).length;
  const sheet = h("article", { class: "sheet" },
    h("header", { class: "sheet-head" },
      h("span", { class: "cs cs-lg" }, c.id.slice(0, 2)),
      h("div", { class: "sheet-title" }, h("h1", {}, c.title), h("p", {}, c.why)),
      h("div", { class: "sheet-verdict" }, mark(c.passed), h("span", { class: "strip-checks" }, `${n}/${c.checks.length} checks`),
        c.runs > 1 ? h("span", { class: "strip-checks" }, `${c.runs_passed}/${c.runs} runs passed`) : null)),
    !c.passed && c.runs > 1 ? h("p", { class: "sheet-note" }, "Transcript below is the first failing run.") : null,
    h("ol", { class: "log" }, c.turns.flatMap(turnLines)),
    h("section", { class: "checks", "aria-label": "Checks" },
      h("h2", {}, "Checks"),
      h("ul", {}, c.checks.map((k) => h("li", { class: k.passed ? "pass" : "fail" },
        h("span", { class: "box", "aria-label": k.passed ? "passed" : "failed" }, k.passed ? "✓" : "✗"),
        h("span", { class: "txt" }, k.name))))));
  $("#work").replaceChildren(sheet);
}

// ---- live session -------------------------------------------------------
function renderIdBox() {
  const box = $("#id-box", live.el);
  const c = live.customer;
  box.replaceChildren(h("span", { class: "k" }, "Identity"),
    h("span", { class: "v" }, c ? `Verified · ${c.name}` : "Not verified"),
    ...(c && c.status === "frozen" ? [h("span", { class: "v alert" }, "Card frozen")] : []));
}

function renderLog(extra) {
  const log = $("#live-log", live.el);
  const lines = live.turns.flatMap(turnLines);
  if (extra) lines.push(extra);
  log.replaceChildren(...(lines.length ? lines : [h("li", { class: "empty-log" }, "No messages yet. Start as the customer, e.g. “I want a refund for T1001.”")]));
  log.lastElementChild?.scrollIntoView({ block: "nearest" });
}

function renderLive() {
  setCurrent("live");
  if (!live.el) {
    live.el = $("#live-tpl").content.firstElementChild.cloneNode(true);
    const form = $("#composer", live.el), msg = $("#msg", live.el);
    form.addEventListener("submit", (e) => { e.preventDefault(); send(); });
    msg.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); form.requestSubmit(); }
    });
    $("#reset", live.el).addEventListener("click", () => {
      Object.assign(live, { sessionId: null, turns: [], customer: null });
      renderIdBox(); renderLog(); msg.focus();
    });
    renderIdBox(); renderLog();
  }
  $("#work").replaceChildren(live.el);
  // replaying the slide each time the strip is pulled
  live.el.style.animation = "none"; void live.el.offsetWidth; live.el.style.animation = "";
}

async function send() {
  const msg = $("#msg", live.el), btn = $("#send", live.el);
  const text = msg.value.trim();
  if (!text || live.busy) return;
  live.busy = true; btn.disabled = true; msg.value = "";
  renderLog(h("li", { class: "line cust pending" }, h("span", { class: "who" }, "Customer"),
    h("div", { class: "what" }, h("p", {}, text), h("p", {}, "Agent is working…"))));
  try {
    const r = await getJSON("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: live.sessionId, message: text }),
    });
    live.sessionId = r.session_id; live.customer = r.customer;
    live.turns.push({ user: text, reply: r.reply, tools: r.tools });
    renderIdBox(); renderLog();
  } catch (err) {
    msg.value = text;  // give the message back so nothing is lost
    renderLog(line("error", "Error", h("p", {}, err.message)));
  } finally {
    live.busy = false; btn.disabled = false; msg.focus();
  }
}

function route() {
  const m = location.hash.match(/^#\/run\/(.+)$/);
  if (m) renderRun(decodeURIComponent(m[1]));
  else renderLive();
  if (window.innerWidth <= 900 && location.hash) $("#work").focus({ preventScroll: true }), $("#work").scrollIntoView({ block: "start" });
}

(async function init() {
  try { results = await getJSON("/api/results"); } catch { results = null; }
  renderBay();
  window.addEventListener("hashchange", route);
  route();
})();
