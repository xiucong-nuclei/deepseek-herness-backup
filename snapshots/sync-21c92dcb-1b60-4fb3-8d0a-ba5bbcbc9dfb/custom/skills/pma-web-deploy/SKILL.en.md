---
name: pma-web-deploy
description: Deploy the PMA config web tool (and any deliverables static site) to xiucong.cyou via /var/www + Caddy. Auto-deploy after every tool change, the root-owned directory permission trap, the sudo path, and post-deploy verification.
metadata:
  hermes:
    tags:
    - PMA
    - deploy
    - caddy
    - xiucong.cyou
    category: deployment
    related_skills:
    - nuclei-pma-config
    - public-web-exposure
    version: 1.1.0
    author: Hermes Agent + kiucong
    license: MIT
    platforms:
    - linux
---

# PMA Web Deploy (xiucong.cyou)

Sync the latest `~/deliverables/pma-config-tool/` build to `https://xiucong.cyou/`.

## Auto-deploy (standing user instruction, 2026-09)

**Deploy after every PMA tool change without asking.** Fixed flow:

1. Edit code under `~/deliverables/pma-config-tool/`.
2. Run the relevant test batches (`in-page-regression-suite` / `nuclei-pma-config`).
3. `git commit` + `git push origin main` (the repo's own remote).
4. **Run the deploy command below immediately, then verify.**
5. Report: commit id, live HTTP status, md5 match.

The old "推到域名上吧" trigger is retired — deployment is now automatic.

## Map

- Local source: `~/deliverables/pma-config-tool/` (ubuntu) — standalone git repo,
  remote `git@github.com:xiucong-nuclei/Nuclei_PMA_config.git`, branch `main`.
- Live dir: `/var/www/pma-calc-landing/` (**root-owned**)
- Caddy config: `/etc/caddy/Caddyfile` (port 443, xiucong.cyou)

The old path `~/deliverables/web/pma-calc-landing/` was deleted (deliverables
commit `a094293`) — never copy from there.

## Deploy

```bash
cd ~/deliverables/pma-config-tool
sudo cp index.html PMA_DESIGN.md /var/www/pma-calc-landing/
sudo cp tests/pma_test_suite.js /var/www/pma-calc-landing/tests/
```

- Three files: `index.html`, `PMA_DESIGN.md`, `tests/pma_test_suite.js`.
- **`README.md` is NOT deployed** (internal repo notes); `tests/logs/` is not synced.
- Run the bash call with `sandbox_permissions: danger-full-access`: `/var/www` is
  root-owned and the sandbox blocks sudo by default ("no new privileges flag").

## The permission trap (landmine of this deploy)

1. Plain `cp` to /var/www fails (root-owned, POSIX EACCES).
2. DSH bash `danger-full-access` alone does NOT help — it only lifts the landlock
   sandbox; the process is still ubuntu, so POSIX denials persist.
3. DSH write tool fails too (EACCES mkdir temp).
4. Actual fix: **`sudo cp`** (ubuntu is in the sudo group) combined with
   `sandbox_permissions: danger-full-access`. Go straight to it.

## Verify (mandatory)

```bash
curl -s -o /tmp/served.html -w "status=%{http_code} size=%{size_download}\n" https://xiucong.cyou/
md5sum /tmp/served.html ~/deliverables/pma-config-tool/index.html   # must match
```

Comparing served bytes against the local file (not just local vs local) proves
Caddy is actually serving the new build. Static files take effect instantly; no
reload needed for file updates.

## Common mistakes

- Forgetting to deploy ("page didn't change" → compare md5 first, don't rewrite code).
- Browser cache: tell the user to hard-refresh (Ctrl+F5).
- Caddy only needs action when Caddyfile changes.
- Wrong source dir: always copy from `~/deliverables/pma-config-tool/`.

## Commit discipline

- Commit + push before/right after deploying:
  ```bash
  cd ~/deliverables/pma-config-tool
  git add index.html tests/pma_test_suite.js   # relevant files only
  git commit -m "..." && git push origin main
  ```
- The `deliverables` monorepo does **not** track this directory (it is listed in
  `.git/info/exclude`); never `git add` it there.
- Leave unrelated working-tree changes (e.g. `tools/piccp/piccp.conf.json`) alone.
