# Design: Flight Strip Bay

The console treats each conversation as an air-traffic-control flight progress strip: a buff card in a plastic holder, racked in a bay. Opening one slides it into the work position and unrolls it into a transcript, where every agent action is printed as a clearance line.

## Tokens (web/app.css `:root`)
| Token | Value | Role |
|---|---|---|
| `--board` / `--board-deep` | #2f3b37 / #26302d | The bay board (page ground, header) |
| `--strip` / `--strip-hi` | #e9dfc4 / #f3ecd8 | Strip card (all reading surfaces) / composer |
| `--holder` | #a9c6dc | Strip holder |
| `--holder-active` | #5cc8d6 | Reserved: the active strip and focus ring only |
| `--ink` / `--ink-soft` | #16191a / #4a4b45 | Text on strips |
| `--alert` / `--alert-ink` | #e4572e / #b23a17 | Failures, blocked actions. Nothing else. |

Ink discipline: board, strip, ink, one alert. No other greys or accents.

## Type
- Barlow Condensed: callsigns, titles, labels (uppercase, tracked 0.08–0.14em).
- Barlow: body and transcript text.
- JetBrains Mono: tool calls, IDs, check counts. Used for data only.
- Kalam 700: the controller's pencil marks only (Pass / Fail, ✓ / ✗).

## Components
- **Strip**: a grid of callsign | title + why | result, divided by 1px ink rules at 22%. The holder is drawn with a box-shadow (3px all round, plus a 9px grip at the left). The active strip gets a cyan holder and slides 10px right.
- **Sheet**: the same anatomy as a strip, unrolled. Speaker column (88px) on the left, content on the right, ruled.
- **Clearance line**: mono text, `tool  args` then `= result`. Green means the action succeeded, alert means it was denied, and strike-through means the guard blocked it.
- **Pencil mark**: a failure gets a hand-drawn SVG ellipse around "Fail". A passing strip has no circle.
- **Buttons**: square, condensed uppercase, filled ink or quiet outline. No radius anywhere.

## Motion
One movement: the strip slides out (220ms, `cubic-bezier(.16,1,.3,1)`). It is turned off under `prefers-reduced-motion`.

## Responsive
At 900px and below, the bay stacks above the work area, speaker columns narrow to 64px, and the verdict moves under the title.
