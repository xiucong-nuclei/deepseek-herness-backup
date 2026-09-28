# hermes update through the proxy (China-mainland server)

`hermes update --yes` = git fetch + git pull/merge + `uv pip install -e .[all]`.
On a mainland box behind an airport proxy, all three stages have their own traps.

## Stage 1: git fetch — GitHub 429 rate limits

Symptom: `error: RPC failed; HTTP 429` / `GnuTLS recv error (-24)` / fetch hanging >2min.

Facts learned:
- The 429 is INTERMITTENT (per-window rate limit on the exit IP, ~1-2min window).
  Plain retry often succeeds — the same command that failed can pass 60s later.
- `export https_proxy=...` on the command line does NOT reliably reach the git
  subprocess hermes spawns. The reliable fix is git's own config so EVERY git
  invocation (manual or from hermes) uses the proxy:
  ```
  git config --global http.https://github.com/.proxy http://127.0.0.1:7891
  git config --global https.https://github.com/.proxy http://127.0.0.1:7891
  ```
  URL-scoped, so non-GitHub git ops stay direct. `hermes update` then fetches fine.
- `git fetch origin main` (unscoped ref fetch) is what hermes runs — pre-fetching
  yourself before `hermes update` does NOT skip hermes' own fetch; it still refetches.
- Tool-invoked `hermes update` must run as a background process
  (terminal background=true + notify_on_complete) — it takes 5-15min total.

## Stage 2: uv pip install — PyPI mirror vs exclude-newer

pyproject.toml sets `exclude-newer = "14 days"` (reproducible-build pin). This
breaks against mirrors that don't serve upload dates:

- aliyun mirror (`UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/`) →
  `warning: typing_extensions-4.12.x.whl is missing an upload date` →
  `No solution found ... certifi==2026.5.20 cannot be used` (filtered by exclude-newer).
  tuna mirror is slow (5s vs 2.8s aliyun) and likely same metadata issue.
- FIX: do NOT set UV_INDEX_URL. Let uv use official PyPI **through the proxy**:
  ```
  export https_proxy=http://127.0.0.1:7891 http_proxy=http://127.0.0.1:7891 all_proxy=http://127.0.0.1:7891
  hermes update --yes
  ```
  Official PyPI has full upload-date metadata, so exclude-newer resolves; proxy
  makes the fastly CDN fast (12MB/s seen).
- If running uv manually: needs `VIRTUAL_ENV=/home/ubuntu/.hermes/hermes-agent/venv`
  or it errors `No virtual environment found`.

## Stage 3: verification after update

- `hermes --version` → v0.20.2 (was v0.17.0).
- `git log -1 --format="%h %ci %s"` in ~/.hermes/hermes-agent → recent commit,
  HEAD moved off old release tag.
- `hermes doctor` — config v0→v37 migration is expected; npm vulns are pre-existing.
- Update is a long-lived background job; while it runs, `ps aux | grep uv` shows
  `uv pip install -e .[all]` — that's the slow stage, be patient (448+ packages).
- A failed/interrupted install leaves venv in a half-state; hermes self-heals on
  next launch ("Early interrupted-install completion failed ... next launch will retry").

## Stage 4: "Update partially complete" — Node deps did not refresh

Real outcome on this box: `hermes update` finished with
`⚠ Update partially complete — Node.js dependencies for ui-tui, web workspaces
did not refresh.` Code + Python deps were updated and the gateway restarted, but
the dashboard/TUI frontends stayed on old deps. `hermes doctor` then shows
npm vulnerabilities (web + ui-tui) that were NOT there before.

FIX — refresh the two npm workspaces manually:
```bash
cd ~/.hermes/hermes-agent/web && npm ci
cd ~/.hermes/hermes-agent/ui-tui && npm ci
```
(Each takes ~1-2min; runs fine in the foreground or as one background job.
npm on this box already uses the Tencent internal mirror
`registry=https://mirrors.tencentyun.com/npm` — no proxy needed.)
Re-run `hermes doctor` — npm vuln counts may change (new lockfile), but that's
the upstream baseline, not a regression.

Verify the gateway/dashboard after update (gateway is managed by the dashboard
service, not a standalone unit):
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9121/   # 200 = backend up
sudo systemctl is-active sing-box hermes-dashboard                 # both active
```
Note: `hermes update` output says "Restarted hermes-gateway" — there is no
`hermes-gateway.service` unit on this box; the gateway runs inside the dashboard
process. Don't go hunting for a unit file that doesn't exist.
