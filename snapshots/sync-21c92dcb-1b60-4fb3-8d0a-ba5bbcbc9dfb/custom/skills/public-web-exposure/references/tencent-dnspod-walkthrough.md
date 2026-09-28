# Tencent Cloud / DNSPod walkthrough (xiucong.cyou, Aug 2026)

Server: Tencent CVM, public IP 124.223.140.171 (private 10.0.0.10), Ubuntu, hostname VM-0-10-ubuntu. Domain `xiucong.cyou`, DNS managed by DNSPod (Tencent). Web targets: Hermes built-in dashboard (127.0.0.1:9119) and friend's Open WebUI (0.0.0.0:8080).

## DNS console forms seen

1. **"快速添加解析"** (quick add, radio-driven): 业务需求 (将网站域名解析到服务器IPv4地址 / IPv6 / 另外的目标域名=CNAME), 选择网站域名 (@ / www / custom host input), IP 输入框 (multi-line, "一行一个，最多10个"). Buttons 确定/取消.
2. **"添加记录"** (full form): 记录类型 dropdown (A/TXT/CNAME/MX...), 主机记录 text, 解析请求来源 dropdown (默认/默认), TTL | 记录值负载策略 (默认), 记录值集合 table (记录值 + 状态 toggle + 备注 0/50 + 删除, "+ 添加条目"), buttons 确定/添加并继续/取消.

Filled: A `@` → 124.223.140.171; A `www` → 124.223.140.171. Propagated in minutes.

## Cert validation TXT record (Tencent free DV console)

Console requested: 主机记录 **`fileauth.txt`** (NOT `_dnsauth` — earlier unrelated request used `_dnsauth`; host names vary per CA/request, read the console literally), 类型 TXT, 值 `202608170525309c1qvqf26lyb4z2sagr6bl1zhuwt46f`. 3-day deadline, don't delete until issued.

Verified before telling the user to click 验证域名:

```
$ dig +short TXT fileauth.txt.xiucong.cyou @119.29.29.29
"202608170525309c1qvqf26lyb4z2sagr6bl1zhuwt46f"
$ dig +short TXT fileauth.txt.xiucong.cyou @223.5.5.5     # same
$ dig +short TXT fileauth.txt.xiucong.cyou @8.8.8.8       # same
```

A records also confirmed: `xiucong.cyou` and `www` → 124.223.140.171.

## Ports/security state

- ufw inactive (system layer wide open); Tencent security group is the outer gate.
- Listening: 22, 80 (Caddy default welcome page, no proxy, no auth), 8080 (Open WebUI, 0.0.0.0), 9119/8642/2019 loopback-only.
- Plan: open 80/443 in security group; Caddy reverse proxy https://xiucong.cyou → 127.0.0.1:8080; close 8080 after 备案; use acme.sh DNS-01 (DNSPod API key scoped to xiucong.cyou only) as the fast cert path, Tencent DV cert as the slow parallel path.
