# Browser Verification (browser-harness + headless Chrome) — full recipe

Absorbed from the former `browser-verification` skill. The condensed workflow lives
in SKILL.md (Verification section); this is the full verified environment recipe.

## When to Use

- Any task whose completion standard is "page loads and interactions work in a real
  browser" (web tools, dashboards, landing pages)
- Debugging JS interactivity that unit checks can't see (focus loss, re-render races,
  clipboard/download behavior)

## Environment (this machine, as of 2026-08)

- Chrome for automation: **playwright chromium** (NOT snap chromium):
  `/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`
- snap chromium (`/usr/bin/chromium-browser`) is a TRAP: headless mode never opens the
  CDP port and silently redirects `--user-data-dir` into its sandbox
  (`~/snap/chromium/<rev>/`), so `DevToolsActivePort` never lands where the harness
  scans. Do not use it.

## Setup (once per boot)

Start headless Chrome on port 9222 with a STANDARD profile dir:

```bash
/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome \
  --headless=new --no-sandbox --disable-gpu --remote-debugging-port=9222 \
  --user-data-dir=/home/ubuntu/.config/chromium about:blank
```

Run as a background process (terminal background=true). Verify:
`curl -s http://127.0.0.1:9222/json/version` → 200.

Serve the page under test: `cd <dir> && python3 -m http.server <port> --bind 127.0.0.1`
(background).

## Connecting browser_exec to the running Chrome

`browser-harness` (the CLI behind browser_exec) finds Chrome in this order:
1. env `BU_CDP_WS` (ws:// URL)
2. env `BU_CDP_URL` (http endpoint; harness resolves /json/version → ws) — **use this**
3. `DevToolsActivePort` inside standard profile dirs (~/.config/chromium, etc.)
4. probing ports 9222/9223

Failure symptom: `chrome-not-running: no supported Chromium-family browser is running`
— means steps 3-4 failed (snap binary not recognized as running, or the CDP instance
isn't reachable by the daemon).

Working recipe — in the FIRST line of browser_exec `code`:

```python
import os
os.environ["BU_CDP_URL"] = "http://127.0.0.1:9222"
```

then `new_tab("http://127.0.0.1:8640/index.html?v=2")` — always append a `?v=N`
cache-buster: http.server sends no cache headers and headless Chrome serves stale
copies after an edit (edits then "don't apply" mysteriously).

## Verification checklist

- Capture JS errors from the start:
  `js("(() => { window.__errs=[]; window.onerror=(m,s,l)=>{window.__errs.push(String(m)+' @'+l)}; })()")`
  and print `window.__errs` at the end. Empty = clean.
- Check title/DOM presence first (page actually loaded), then exercise the feature,
  then assert on generated/rendered values.
- Read layout state with getComputedStyle where CSS is the thing under test.

## Pitfalls

- **Injection escaping**: never build a JS template literal with backticks inside
  browser_exec code — nested backticks break the harness's exec. For long payloads
  (config text, JSON), build the string in Python with `chr(96)` for backtick and
  inject via `js("el.value = " + json.dumps(payload))` — json.dumps handles all quoting.
- **Focus loss = re-render bug**: "can only type one character" in an input almost
  always means the oninput handler rebuilds the DOM (innerHTML=""), destroying the
  focused element. Fix: update data + refresh non-input outputs only; rebuild the
  table only on structural changes (add/remove/select).
- **Stub side effects you can't see**: headless downloads/clipboard may not behave;
  intercept instead: `HTMLAnchorElement.prototype.click` → record {href, download}; or
  stub `navigator.clipboard.writeText`.
- **Server died**: a python http.server can die silently (killed by pkill patterns,
  port reuse). Re-check `curl -s -o /dev/null -w %{http_code}` before blaming the
  page. 404/000 on the page while the file is fine = serving from the wrong cwd;
  restart in the project dir.
- `pkill -f <pattern>` can match and kill the very shell running it (pattern appears
  in the shell's own command line) → SIGTERM(-15) on the terminal call. Use
  `pgrep -a` first, kill by exact pid.

## Done criteria

Report only after: page loads, key interactions exercised, generated output asserted,
`window.__errs` empty. Then git commit (deliverables repo).
