# browser-harness ↔ headless Chrome on this server (verified Aug 2026)

How Hermes' `browser_exec` backend (browser-harness, ~/.config/browser-harness)
finds a Chrome to drive, and the launch recipe that actually works on this
headless Ubuntu box. This took a full debugging session — read before
retrying any "chrome-not-running" error.

## How browser-harness discovers Chrome (daemon.py `get_ws_url`, priority order)

1. Env var `BU_CDP_WS` — direct `ws://host:port/devtools/browser/<id>` URL.
2. Env var `BU_CDP_URL` — HTTP endpoint; harness GETs `/json/version` and
   resolves `webSocketDebuggerUrl` itself.
3. Scans standard profile dirs (`~/.config/google-chrome`,
   `~/.config/chromium`, ...) for a live `DevToolsActivePort` file, then
   resolves the ws URL via `/json/version` on that port. Hitting this path
   returns immediately — no process-name checks.
4. Last-resort probes ports 9222 / 9223.

The "chrome-not-running" error fires when step 3 finds nothing and the
liveness check (`supported_browser_running()`) fails, even though a CDP
server may actually be listening on 9222.

## Root causes seen on this machine

- Launching Chrome with a custom `--user-data-dir=/tmp/xxx` puts
  `DevToolsActivePort` outside the scanned profile dirs → harness never finds
  it → "chrome-not-running" while `curl :9222/json/version` returns 200.
- The Ubuntu `chromium-browser` SNAP wrapper remaps `--user-data-dir` into
  its sandbox (`~/snap/chromium/<rev>/...`) and its headless +
  `--remote-debugging-port` combo was unreliable — port never came up.
- `pkill -f "remote-debugging-port=9222"` matches and SIGTERMs your OWN shell
  (the string is in its command line). Use `pgrep -a -f ...` first, kill by
  PID.

## Verified working recipe

Use the PLAYWRIGHT-bundled Chromium binary (not the snap wrapper):

```bash
PW_CHROME=$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome | head -1)
"$PW_CHROME" --headless=new --no-sandbox --disable-gpu \
  --remote-debugging-port=9222 \
  --user-data-dir=/home/ubuntu/.config/chromium \
  about:blank   # background=true
```

Standard profile dir (`~/.config/chromium`) is REQUIRED so harness step 3
finds `DevToolsActivePort`. Sanity check:

```bash
curl -s http://127.0.0.1:9222/json/version   # 200 + Chrome/<ver>
```

Then in browser_exec code, set at the very top:

```python
import os
os.environ["BU_CDP_URL"] = "http://127.0.0.1:9222"
```

(`os.environ` in the exec body works because the harness daemon spawns per
call; setting it is harmless if the daemon already auto-discovered via the
profile dir.)

## browser_exec verification tips

- After editing the page, load with a cache-buster: `?v=N` — Chrome otherwise
  serves the OLD html and your fixes look broken.
- Inject strings via Python `json.dumps(...)`; nested JS template literals
  containing backticks cause `SyntaxError: Unexpected identifier` — avoid
  backticks inside injected code entirely.
- Register `window.onerror` capture early to collect JS errors across the
  whole session.
- Stub `window.alert` before testing limits/guards (headless has no dialog).
- HTTP server must be started INSIDE the project dir (serves its CWD);
  a stale server process can outlive `kill` on its parent shell — probe with
  curl, kill by PID, restart.

## Service state after this session

- HTTP: `cd ~/deliverables/web/pma-calc-landing && python3 -m http.server 8640 --bind 127.0.0.1`
- Chrome CDP: playwright chromium on 9222 with `--user-data-dir=/home/ubuntu/.config/chromium`
