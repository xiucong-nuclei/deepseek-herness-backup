---
name: airport-proxy-setup
description: Set up a local proxy (sing-box) on a China-mainland server from an airport subscription (机场订阅 vless:// links) to accelerate GitHub/git/pip access — subscribe decode, sing-box 1.13 config, local SOCKS/HTTP proxy, speed verification.
metadata:
  hermes:
    tags:
    - proxy
    - sing-box
    - vless
    - reality
    - airport
    - github
    - accelerator
    - china
    - git
    - socks5
    version: 1.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
---

# Airport Proxy Setup (sing-box)

Stand up a working local proxy on a mainland server from a 机场 (airport) subscription
link, then route git/curl/pip through it to reach GitHub reliably.

## When to use

- User provides an airport subscription URL (`https://host/subscribe?token=...`) and wants
  it usable on this server.
- GitHub direct access from a mainland IP fails: 429 rate limits, `git fetch` hanging >2min,
  downloads silently truncating (gzip with `unexpected end of file`).
- Any "加速 GitHub / 用机场 / 挂代理" request.

## Quick path (verified working, sing-box 1.13.18)

1. **Validate the subscription** (token is sensitive — never echo it back; pass as arg):
   ```bash
   curl -sk -o /tmp/sub.bin -w "HTTP %{http_code} | %{size_download}B\n" "$SUB_URL"
   file /tmp/sub.bin          # base64 text → 16 nodes, all vless://
   base64 -d /tmp/sub.bin | grep -o 'vless://' | wc -l
   rm -f /tmp/sub.bin /tmp/sub_decoded.txt
   ```
   Note: `urllib` often times out on subscription servers — prefer `curl`. The script
   below falls back to curl automatically.

2. **Install sing-box** (x86_64). GitHub direct download often truncates — use a mirror:
   ```bash
   curl -skL -o /tmp/sb.tar.gz "https://ghfast.top/https://github.com/SagerNet/sing-box/releases/download/v1.13.18/sing-box-1.13.18-linux-amd64.tar.gz"
   tar tzf /tmp/sb.tar.gz >/dev/null 2>&1 && echo VALID   # ALWAYS validate; direct downloads truncate silently
   tar xzf /tmp/sb.tar.gz && sudo install -m 755 sing-box-*/sing-box /usr/local/bin/sing-box
   sing-box version
   ```

3. **Generate config**: run `scripts/gen_singbox_config.py "$SUB_URL"` (in this skill).
   It parses vless:// URIs (reality + xtls-rprx-vision), picks 香港/日本/新加坡/美国 nodes,
   writes `config.json` with mixed inbound :7890 (SOCKS+HTTP) and http inbound :7891.

4. **Validate + run**:
   ```bash
   sing-box check -c config.json && echo OK
   # run in background (long-lived process), then:
   curl -s --max-time 12 -x http://127.0.0.1:7891 -o /dev/null -w "github: HTTP %{http_code} | %{time_total}s\n" https://github.com
   ```

5. **Route tools through the proxy**:
   ```bash
   export https_proxy=http://127.0.0.1:7891 http_proxy=http://127.0.0.1:7891   # per-command: unset after
   git fetch origin main    # ~46s for 11k commits vs 2min+ timeout direct
   ```
   For persistent git use — scope the proxy to github.com ONLY (other git hosts
   like gitee stay direct):
   ```bash
   git config --global http.https://github.com/.proxy http://127.0.0.1:7891
   git config --global https.https://github.com/.proxy http://127.0.0.1:7891
   ```
   Do NOT use a global `http.proxy` — it routes every git host through the proxy.

## Rule mode (国内直连 / 国外走代理) — user explicitly wants this

sing-box 1.12+ removed inline `geosite`/`geoip` database references. Build local
rule-sets from the downloaded DBs, then reference them:

```bash
cd ~/singbox
sing-box geosite export cn --file geosite.db --output geosite-cn.json   # also geoip
sing-box geoip export cn --file geoip.db --output geoip-cn.json
```
Download DBs through the proxy: `curl -x http://127.0.0.1:7891 -L -o geoip.db
"https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db"` (same for
`SagerNet/sing-geosite` → `geosite.db`).

Config shape that passes `sing-box check` (1.13.x):
```json
{
  "dns": {
    "servers": [
      {"type": "udp", "tag": "local", "server": "223.5.5.5", "server_port": 53},
      {"type": "udp", "tag": "remote", "server": "8.8.8.8", "server_port": 53, "detour": "node-X"}
    ],
    "rules": [
      {"rule_set": ["geosite-cn"], "server": "local"},
      {"rule_set": ["geoip-cn"], "server": "local"},
      {"server": "remote"}
    ]
  },
  "route": {
    "default_domain_resolver": {"server": "local"},
    "rule_set": [
      {"type": "local", "tag": "geosite-cn", "format": "source", "path": "/home/ubuntu/singbox/geosite-cn.json"},
      {"type": "local", "tag": "geoip-cn", "format": "source", "path": "/home/ubuntu/singbox/geoip-cn.json"}
    ],
    "rules": [
      {"rule_set": ["geosite-cn"], "outbound": "direct"},
      {"rule_set": ["geoip-cn"], "outbound": "direct"},
      {"ip_is_private": true, "outbound": "direct"}
    ],
    "final": "node-X"
  }
}
```
Verify split: baidu/taobao ~0.05s (direct), google/github ~0.4s (proxy),
`curl -x http://127.0.0.1:7891 https://api.ipify.org` shows a foreign exit IP.

## systemd service (常驻, user wants this)

`/etc/systemd/system/sing-box.service`:
```ini
[Unit]
Description=sing-box proxy (vless reality, rule mode)
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/singbox
ExecStart=/usr/local/bin/sing-box run -c /home/ubuntu/singbox/config.json
Restart=on-failure
RestartSec=5
LimitNOFILE=65535
[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now sing-box
sudo systemctl status sing-box --no-pager   # verify active (running)
ss -tlnp | grep -E "7890|7891"              # verify ports
```
Pitfall: a manually-started sing-box still holding 7890/7891 makes the service
flap (`activating (auto-restart)`, exit 1). Kill the manual process first, then
`systemctl restart sing-box`.

## Pitfalls (all hit in real use, sing-box 1.13.x)

- **Rules are FLAT, not nested**: 1.13 rejects `"dns": {"rules": [{"rule": {...}, "server": ...}]}`
  and `"route": {"rules": [{"rule": {...}, "outbound": ...}]}` with
  `json: unknown field "rule"`. Rule fields (`geosite`, `geoip`, `rule_set`,
  `ip_is_private`) go at the TOP level of each rule object, alongside
  `server`/`outbound`/`action`. Same for the DNS server format — flat fields.
- **Legacy DNS format removed**: `"dns": {"servers": [{"tag":"local","address":"223.5.5.5"}]}`
  fails with `ENABLE_DEPRECATED_LEGACY_DNS_SERVERS=true` hint. Use new format:
  `"dns": {"servers": [{"type":"udp","tag":"local","server":"223.5.5.5"}]}`.
- **`transport: {"type":"tcp"}` is rejected** in 1.13 (`unknown transport type: tcp`).
  Omit it entirely — tcp is the default for vless.
- **reality requires utls**: `tls.utls.enabled: true` + `fingerprint` (chrome/safari),
  plus `reality.public_key` (pbk) and `reality.short_id` (sid) from the URI query params.
- **URI parsing**: split `@`, then split hostport from `?` BEFORE `rpartition(":")` for the
  port, else port = `443?mode=multi&...` → int() ValueError. Query params: `sni`/`servername`,
  `pbk`, `sid`, `flow`, `fp`.
- **GitHub direct downloads truncate** at ~0.8MB with HTTP 200 — always `tar tzf ... >/dev/null`
  to validate. `ghfast.top/https://github.com/...` mirror downloaded 23.9MB in 11.7s (~2MB/s);
  through the proxy it was 12.7MB/s. Try proxy first, mirror second.
- **`sing-box run` must be a background process** (terminal background=true, no `&` in
  foreground) — verify with `process(action='poll')`; a FATAL config error exits in ~8s.
- Subscription sometimes includes a "状态/余额" (status/balance) pseudo-node — the
  name-picker avoids it; don't assume every vless:// line is a real node.
- Do not hardcode the subscription token anywhere in scripts/configs you share.

## Verification (do all three before declaring success)

1. `curl -x http://127.0.0.1:7891 https://www.google.com` → HTTP 200, <1s.
2. `curl -x http://127.0.0.1:7891 https://github.com` → HTTP 200, <1s (direct was slow/429).
3. Real workload: `git fetch` through the proxy completes (timing beats direct).
4. `sing-box check -c config.json` passes before every run.

## Support files

- `scripts/gen_singbox_config.py` — fetch subscription, parse vless:// nodes, emit config.json.
- `references/hermes-update-through-proxy.md` — running `hermes update` through the
  proxy: git URL-scoped proxy config (429 retry pattern), uv vs mirror exclude-newer
  trap, verification after update.
