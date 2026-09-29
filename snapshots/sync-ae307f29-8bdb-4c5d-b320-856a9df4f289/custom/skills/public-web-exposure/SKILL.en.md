---
name: public-web-exposure
description: 'Expose a self-hosted service (Hermes dashboard, Open WebUI, any web app) on a cloud box to the public internet: domain binding, DNS records, free TLS certs, Caddy reverse proxy, cloud security group + host firewall, and China ICP-备案 constraints.'
metadata:
  hermes:
    tags:
    - dns
    - tls
    - caddy
    - reverse-proxy
    - security-group
    - firewall
    - lets-encrypt
    - icp
    - 备案
    - domain
    related_skills:
    - hermes-operations
    - ssh-key-setup
    version: 1.0.0
---

# Public Web Exposure (Domain + DNS + TLS + Proxy + Firewall)

Use when taking a self-hosted service public by name: register/bind a domain,
add DNS records, obtain a TLS certificate, reverse-proxy, and open ports —
or when diagnosing why a domain/port isn't reachable. Verified on a Tencent
Cloud (腾讯云) CVM in mainland China, but the flow applies to any cloud box.

## Order of operations

1. **Domain** — register (≈¥60–80/yr; `.cn` cheaper but requires real-name).
2. **DNS A records** — point `@` and `www` (or a subdomain like `chat`) at the
   server's PUBLIC IP (not the private 10.x/172.x address). Two entries, one
   per host record. Verify: `dig +short xiucong.cyou A` (+ `www.`).
3. **Ports** — open 80 AND 443 at BOTH layers:
   - cloud security group (inbound rules; the most common blocker),
   - host firewall (e.g. ufw — check `sudo ufw status`; often inactive).
   80 = ACME HTTP-01 validation + http→https redirect; 443 = HTTPS traffic.
   Missing 80 ⇒ cert issuance AND renewal fail.
4. **Certificate** — free options (never pay):
   - Caddy auto (Let's Encrypt): zero config, 90-day auto-renew. Needs 80
     reachable and the A record live.
   - acme.sh + DNS-01 (DNSPod token): issuance in 1–2 min, works even when 80
     is unusable (see CN section) — best fast-cert path.
   - Cloud free DV cert (腾讯云/阿里): manual DNS TXT validation, hours–days;
     3-day deadline to add the record; record deletable only AFTER issuance.
   Budget: domain only; cert ¥0.
5. **Reverse proxy** — Caddy: `domain.com { reverse_proxy 127.0.0.1:<port> }`
   gives automatic HTTPS. For services without their own login (e.g. a
   loopback Hermes dashboard) add `basic_auth` (hash via
   `/usr/bin/caddy hash-password --plaintext '<pw>'`) — see
   hermes-operations skill (§1 Multi-user & shared-server access) for the verified dashboard pattern.
6. **Verify** — curl the box's OWN public IP per port (see pitfalls for
   timeout vs refused semantics); `curl 127.0.0.1:p` proves nothing about the
   security group.

## China (境内) specifics — the real time cost

- **ICP 备案 is mandatory** for a domain serving 80/443 from a mainland IP:
  1–2 weeks, real-name + provider review. Until it passes, the cloud platform
  intercepts the domain on 80/443 with a "未备案" page — the cert being valid
  changes nothing. Domain access simply does not work pre-备案.
- Parallelize: DNS + cert can be done while 备案 runs; the service stays
  reachable in the interim via direct `http://IP:8080`-style ports, which are
  NOT intercepted. Switch to the domain after 备案.
- Let's Encrypt HTTP-01 can fail under interception (ACME probe hits the
  intercept page) — prefer DNS-01 (acme.sh + `dns_dp`) or the provider's
  DNS-validation cert (both avoid port-80 probing entirely).

## Certificate validation records (TXT)

- Copy the value EXACTLY (no spaces/typos); host record may be `_dnsauth` or
  something like `fileauth.txt` — trust the console, don't assume.
- Propagation check across resolvers:
  `dig +short TXT <host>.<domain> @119.29.29.29` (Tencent), `@223.5.5.5` (Ali),
  `@8.8.8.8` (Google) — all must show the value before clicking 验证.
- Delete only after issuance.

## Pitfalls

- **Security-group probe semantics**: from inside the box,
  `curl http://<public-ip>:<port>` → timeout = SG blocks (packet dropped);
  instant `connection refused` = SG allows but no listener. Don't confuse
  them; a refused port still needs a service started.
- **Port clashes**: check `ss -tlnp` before assigning a port — e.g. 9119 was
  already held by another user's loopback dashboard; pick distinct ports.
- **Caddy default :80 site** serves a static welcome page with no auth — an
  unnecessary public surface; replace or restrict when adding your site.
- **Public plaintext HTTP** (e.g. `:8080` Open WebUI, `:9120` basic-auth
  dashboard) sends passwords in the clear — acceptable interim on trusted
  networks only; the cert/备案 switchover removes it. Never use `--insecure`
  on a Hermes dashboard bound publicly (exposes API keys).
- Don't buy paid upgrades pitched in the DNS console (e.g. 云解析个人版) —
  free tier suffices.

## Cert issuance paths (detail)

| Path | Speed | Notes |
|---|---|---|
| Caddy auto (Let's Encrypt) | minutes | Zero config, auto-renew. Needs port 80 reachable. |
| acme.sh + DNS-01 | minutes | Fastest reliable option; needs DNS provider API token; TXT validation avoids port-80 / 备案 interception entirely. |
| Cloud free DV (Tencent/Aliyun) | hours–days | Manual DNS TXT validation + human review; DNS-validated so it works even while HTTP-01 is broken by interception. Run in parallel with the fast path — two certs coexist, use whichever lands first; never cancel the slow one while the fast path is in flight. |

acme.sh + DNSPod (Tencent DNS) recipe:
- User creates a DNSPod API key **scoped to the one domain only** — never a
  full-account token (whoever holds it can rewrite all DNS).
- `acme.sh --issue --dns dns_dp -d <domain> -d www.<domain>` then
  `--install-cert`; auto-renew via cron.
- Caddy can either do its own ACME or load the acme.sh cert files with a
  `tls cert key` directive.
- Cloud cert consoles' "一键部署" targets CDN/CLB/lightweight servers —
  irrelevant for a raw CVM with Caddy; choose manual deployment.

## Caddy basic_auth gate (concrete)

```bash
/usr/bin/caddy hash-password --plaintext "$PW"    # bcrypt for basic_auth
```
```
:9120 {
	basic_auth { user $2a$14$... }
	reverse_proxy 127.0.0.1:9121
}
```
Apps that validate the Host header need `header_up Host {upstream_hostport}`
in the reverse_proxy block, or public-IP access fails with
`Invalid Host header` while curl to localhost works. Verify with
`curl -H 'Host: <public-ip>:<port>' ...`. After 备案 clears, swap the `:port`
site address for the domain — Caddy auto-issues/renews Let's Encrypt and the
basic_auth gate stays in front.

## Verification layers (解析生效 ≠ 网站可访问)

DNS TTL + interception + security group are three separate layers; probe each
with its own tool:

1. `dig +short A <domain>` and cert TXT across resolvers —
   `dig +short TXT <host>.<domain> @119.29.29.29` (Tencent/DNSPod),
   `@223.5.5.5` (Aliyun), `@8.8.8.8` (Google); all must match before clicking
   验证域名. `scripts/check-dns.sh` does A+TXT in one pass.
2. `curl -m 6 http://<public-ip>:<port>/` from inside the host — timeout ⇒ SG
   blocks; instant refused ⇒ SG allows but nothing listens; 200 ⇒ open.
3. `curl -vI https://domain` — cert served (or Caddy auto-provisioned on the
   first request); check for the 备案 interception page before blaming config.

## More pitfalls (all hit in real use)

- **HTTPS ≠ authentication.** Encryption does not stop strangers connecting;
  any publicly exposed service needs login protection (`ENABLE_SIGNUP=false`
  + admin account, OAuth gate, or basic auth). Never use `--insecure` on a
  publicly bound Hermes dashboard (exposes API keys).
- **Cheap TLDs (.icu/.cyou) are subject to the same 备案 rules** — no shortcut.
- **`/proc/<PID>/environ` needs the redirect inside the root shell**:
  `sudo bash -c "tr '\0' '\n' < /proc/PID/environ"` — `sudo tr ... < file`
  fails with Permission denied because the shell opens the fd before sudo.
- **OCR/vision on DNS console screenshots misreads host records**
  (`fileauth.txt` vs `_dnsauth`); read the console text literally and confirm
  with dig. DNS console forms vary ("快速添加解析" vs "添加记录") but the
  fields are the same: 记录类型 / 主机记录 / 记录值 / 解析请求来源 / TTL.
- **Port clashes**: `ss -tlnp` before assigning — a port (e.g. 9119/9120) may
  be held by another user's loopback dashboard; pick distinct ports.
- **Don't buy paid DNS add-ons** (e.g. 云解析个人版 19.9元) pitched in the
  console — the free plan suffices; the cert is free either way.

## Support files

- `references/tencent-dnspod-walkthrough.md` — session walkthrough: exact
  Tencent/DNSPod console forms, the xiucong.cyou example, real dig outputs.
- `scripts/check-dns.sh` — multi-resolver A/TXT probe with expected-value
  matching.

## Related

- `hermes-operations` — safe public dashboard pattern (loopback + Caddy
  basic_auth), user isolation on the shared box (§1).
- `ssh-key-setup` — access to the box itself.
