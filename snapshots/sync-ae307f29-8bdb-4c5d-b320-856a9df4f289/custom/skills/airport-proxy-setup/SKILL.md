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

# 机场代理搭建（sing-box）

在国内服务器上根据机场订阅链接搭建一个可用的本地代理，然后让 git/curl/pip 走代理，稳定访问 GitHub。

## 何时使用

- 用户提供机场订阅 URL（`https://host/subscribe?token=...`），希望在本服务器上使用。
- 国内 IP 直连 GitHub 失败：429 限流、`git fetch` 挂起超过 2 分钟、下载静默截断（gzip 报 `unexpected end of file`）。
- 任何"加速 GitHub / 用机场 / 挂代理"请求。

## 快速路径（已验证可用，sing-box 1.13.18）

1. **校验订阅**（token 敏感——切勿回显；以参数传入）：
   ```bash
   curl -sk -o /tmp/sub.bin -w "HTTP %{http_code} | %{size_download}B\n" "$SUB_URL"
   file /tmp/sub.bin          # base64 text → 16 nodes, all vless://
   base64 -d /tmp/sub.bin | grep -o 'vless://' | wc -l
   rm -f /tmp/sub.bin /tmp/sub_decoded.txt
   ```
   注意：`urllib` 访问订阅服务器时常超时——优先用 `curl`。下面的脚本会自动回退到 curl。

2. **安装 sing-box**（x86_64）。GitHub 直连下载经常截断——使用镜像：
   ```bash
   curl -skL -o /tmp/sb.tar.gz "https://ghfast.top/https://github.com/SagerNet/sing-box/releases/download/v1.13.18/sing-box-1.13.18-linux-amd64.tar.gz"
   tar tzf /tmp/sb.tar.gz >/dev/null 2>&1 && echo VALID   # ALWAYS validate; direct downloads truncate silently
   tar xzf /tmp/sb.tar.gz && sudo install -m 755 sing-box-*/sing-box /usr/local/bin/sing-box
   sing-box version
   ```

3. **生成配置**：运行 `scripts/gen_singbox_config.py "$SUB_URL"`（本 skill 内）。它会解析 vless:// URI（reality + xtls-rprx-vision），挑选香港/日本/新加坡/美国节点，写出 `config.json`，包含混合入站 :7890（SOCKS+HTTP）和 http 入站 :7891。

4. **校验并运行**：
   ```bash
   sing-box check -c config.json && echo OK
   # run in background (long-lived process), then:
   curl -s --max-time 12 -x http://127.0.0.1:7891 -o /dev/null -w "github: HTTP %{http_code} | %{time_total}s\n" https://github.com
   ```

5. **让工具走代理**：
   ```bash
   export https_proxy=http://127.0.0.1:7891 http_proxy=http://127.0.0.1:7891   # per-command: unset after
   git fetch origin main    # ~46s for 11k commits vs 2min+ timeout direct
   ```
   若需长期使用 git——只让 github.com 走代理（gitee 等其他 git 主机保持直连）：
   ```bash
   git config --global http.https://github.com/.proxy http://127.0.0.1:7891
   git config --global https.https://github.com/.proxy http://127.0.0.1:7891
   ```
   不要使用全局 `http.proxy`——它会让所有 git 主机都走代理。

## 规则模式（国内直连 / 国外走代理）——用户明确要求时

sing-box 1.12+ 移除了内联的 `geosite`/`geoip` 数据库引用。先从下载的 DB 构建本地 rule-set，再在配置中引用：

```bash
cd ~/singbox
sing-box geosite export cn --file geosite.db --output geosite-cn.json   # also geoip
sing-box geoip export cn --file geoip.db --output geoip-cn.json
```
通过代理下载 DB：`curl -x http://127.0.0.1:7891 -L -o geoip.db "https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db"`（`SagerNet/sing-geosite` 同理 → `geosite.db`）。

能通过 `sing-box check`（1.13.x）的配置形态：
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
验证分流：baidu/taobao 约 0.05s（直连），google/github 约 0.4s（代理），`curl -x http://127.0.0.1:7891 https://api.ipify.org` 显示的是国外出口 IP。

## systemd 服务（常驻，用户要求时）

`/etc/systemd/system/sing-box.service`：
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
陷阱：手动启动的 sing-box 仍占用 7890/7891 会导致服务反复重启（`activating (auto-restart)`，退出码 1）。先杀掉手动进程，再 `systemctl restart sing-box`。

## 常见陷阱（均为实际使用中遇到，sing-box 1.13.x）

- **规则是扁平的（FLAT），不嵌套**：1.13 会拒绝 `"dns": {"rules": [{"rule": {...}, "server": ...}]}` 和 `"route": {"rules": [{"rule": {...}, "outbound": ...}]}`，报 `json: unknown field "rule"`。规则字段（`geosite`、`geoip`、`rule_set`、`ip_is_private`）要放在每个规则对象的顶层，与 `server`/`outbound`/`action` 同级。DNS server 格式同理——扁平字段。
- **旧版 DNS 格式已移除**：`"dns": {"servers": [{"tag":"local","address":"223.5.5.5"}]}` 会失败，并提示 `ENABLE_DEPRECATED_LEGACY_DNS_SERVERS=true`。改用新格式：`"dns": {"servers": [{"type":"udp","tag":"local","server":"223.5.5.5"}]}`。
- **`transport: {"type":"tcp"}` 会被拒绝**（1.13 报 `unknown transport type: tcp`）。直接省略——tcp 是 vless 的默认传输。
- **reality 需要 utls**：`tls.utls.enabled: true` + `fingerprint`（chrome/safari），再加上 URI 查询参数中的 `reality.public_key`（pbk）和 `reality.short_id`（sid）。
- **URI 解析**：先按 `@` 切分，再从 `?` 处切出主机端口，之后才 `rpartition(":")` 取端口，否则端口会变成 `443?mode=multi&...` → int() 报 ValueError。查询参数：`sni`/`servername`、`pbk`、`sid`、`flow`、`fp`。
- **GitHub 直连下载会截断**：约 0.8MB 处返回 HTTP 200 但内容截断——始终用 `tar tzf ... >/dev/null` 校验。`ghfast.top/https://github.com/...` 镜像 11.7s 下载了 23.9MB（约 2MB/s）；走代理时达到 12.7MB/s。先试代理，再试镜像。
- **`sing-box run` 必须是后台进程**（terminal 的 background=true，前台不要用 `&`）——用 `process(action='poll')` 验证；配置出现 FATAL 错误约 8s 内退出。
- 订阅里有时会包含"状态/余额"伪节点——名称挑选逻辑会避开它；不要假设每行 vless:// 都是真实节点。
- 不要在你要分享的脚本/配置中硬编码订阅 token。

## 验证（宣布成功前必须全部完成）

1. `curl -x http://127.0.0.1:7891 https://www.google.com` → HTTP 200，<1s。
2. `curl -x http://127.0.0.1:7891 https://github.com` → HTTP 200，<1s（直连之前很慢/429）。
3. 真实负载：走代理 `git fetch` 能完成（耗时优于直连）。
4. 每次运行前 `sing-box check -c config.json` 必须通过。

## 支持文件

- `scripts/gen_singbox_config.py` — 拉取订阅、解析 vless:// 节点、生成 config.json。
- `references/hermes-update-through-proxy.md` — 让 `hermes update` 走代理：git 按 URL 限定的代理配置（429 重试模式）、uv 与镜像 exclude-newer 的坑、更新后的验证。
