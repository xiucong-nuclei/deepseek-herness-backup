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

# 公网 Web 暴露（域名 + DNS + TLS + 代理 + 防火墙）

在按名称把自托管服务公网化时使用：注册/绑定域名、添加 DNS 记录、获取 TLS 证书、反向代理、开放端口——或在诊断域名/端口为何不可达时使用。已在腾讯云 CVM（中国大陆）上验证，但流程适用于任何云主机。

## 操作顺序

1. **域名**——注册（≈¥60–80/年；`.cn` 更便宜但要求实名）。
2. **DNS A 记录**——把 `@` 和 `www`（或 `chat` 之类的子域名）指向服务器的公网 IP（不是私有的 10.x/172.x 地址）。两条记录，每条主机记录一条。验证：`dig +short xiucong.cyou A`（以及 `www.`）。
3. **端口**——在两层都开放 80 和 443：
   - 云安全组（入站规则；最常见的拦路虎），
   - 主机防火墙（如 ufw——查 `sudo ufw status`；常常未启用）。
   80 = ACME HTTP-01 校验 + http→https 重定向；443 = HTTPS 流量。缺少 80 ⇒ 证书签发与续期都会失败。
4. **证书**——免费方案（绝不付费）：
   - Caddy 自动（Let's Encrypt）：零配置，90 天自动续期。需要 80 可达且 A 记录已生效。
   - acme.sh + DNS-01（DNSPod token）：1–2 分钟签发，即使 80 不可用也能工作（见中国境内一节）——最快的快证路径。
   - 云免费 DV 证书（腾讯云/阿里）：手动 DNS TXT 验证，数小时–数天；加记录有 3 天期限；记录只能在签发后删除。
   预算：只花域名钱；证书 ¥0。
5. **反向代理**——Caddy：`domain.com { reverse_proxy 127.0.0.1:<port> }` 自动获得 HTTPS。对没有自带登录的服务（如回环的 Hermes dashboard）加 `basic_auth`（用 `/usr/bin/caddy hash-password --plaintext '<pw>'` 生成哈希）——已验证的 dashboard 模式见 hermes-operations skill（§1 Multi-user & shared-server access）。
6. **验证**——按端口 curl 盒子自己的公网 IP（超时与拒绝的语义区别见坑一节）；`curl 127.0.0.1:p` 对安全组什么都证明不了。

## 中国（境内）细节——真正的时间成本

- **ICP 备案是强制的**——大陆 IP 上用 80/443 提供服务的域名必须备案：1–2 周，实名 + 服务商审核。通过之前，云平台会在 80/443 上用"未备案"页面拦截该域名——证书有效也改变不了什么。备案前域名访问就是不通。
- 并行化：备案进行期间可同时做 DNS + 证书；服务在此期间通过 `http://IP:8080` 这类直连端口保持可达，这些端口不会被拦截。备案通过后再切到域名。
- Let's Encrypt HTTP-01 在拦截下可能失败（ACME 探测会打到拦截页）——优先用 DNS-01（acme.sh + `dns_dp`）或服务商的 DNS 验证证书（两者都完全避开 80 端口探测）。

## 证书验证记录（TXT）

- 逐字复制值（不要有空格/拼写错误）；主机记录可能是 `_dnsauth` 或类似 `fileauth.txt` 的格式——以控制台为准，不要想当然。
- 跨解析器检查传播：`dig +short TXT <host>.<domain> @119.29.29.29`（腾讯）、`@223.5.5.5`（阿里）、`@8.8.8.8`（Google）——点"验证"之前，所有解析器都必须显示该值。
- 只在签发后删除。

## 坑

- **安全组探测语义**：从盒子内部 `curl http://<public-ip>:<port>` → 超时 = 安全组拦截（丢包）；立即 `connection refused` = 安全组放行但没有监听。别把两者搞混；被拒绝的端口仍然需要启动一个服务。
- **端口冲突**：分配端口前查 `ss -tlnp`——例如 9119 已被另一个用户的回环 dashboard 占用；选不同的端口。
- **Caddy 默认的 :80 站点**会提供无鉴权的静态欢迎页——一个多余的公网暴露面；加入你的站点时替换或限制它。
- **公网明文 HTTP**（如 `:8080` Open WebUI、`:9120` basic-auth dashboard）会明文发送密码——只在可信网络上作为临时方案可接受；证书/备案切换后移除。公开绑定的 Hermes dashboard 上绝不要用 `--insecure`（会暴露 API key）。
- 别买 DNS 控制台推销的付费升级（如云解析个人版）——免费版够用。

## 证书签发路径（详情）

| 路径 | 速度 | 备注 |
|---|---|---|
| Caddy 自动（Let's Encrypt） | 分钟级 | 零配置，自动续期。需要 80 端口可达。 |
| acme.sh + DNS-01 | 分钟级 | 最可靠的快速方案；需要 DNS 服务商 API token；TXT 验证完全避开 80 端口 / 备案拦截。 |
| 云免费 DV（腾讯云/阿里云） | 数小时–数天 | 手动 DNS TXT 验证 + 人工审核；DNS 验证型，即使 HTTP-01 被拦截破坏也能工作。与快速路径并行跑——两证书并存，谁先落地用谁；快速路径进行中绝不要取消慢的那条。 |

acme.sh + DNSPod（腾讯云 DNS）配方：
- 用户创建一个**只限那一个域名**的 DNSPod API key——绝不用全账号 token（谁拿到它就能改写所有 DNS）。
- `acme.sh --issue --dns dns_dp -d <domain> -d www.<domain>` 然后 `--install-cert`；通过 cron 自动续期。
- Caddy 可以自己做 ACME，也可以用 `tls cert key` 指令加载 acme.sh 的证书文件。
- 云证书控制台的"一键部署"面向 CDN/CLB/轻量服务器——对跑 Caddy 的裸 CVM 无关；选手动部署。

## Caddy basic_auth 门禁（具体示例）

```bash
/usr/bin/caddy hash-password --plaintext "$PW"    # bcrypt for basic_auth
```
```
:9120 {
	basic_auth { user $2a$14$... }
	reverse_proxy 127.0.0.1:9121
}
```
需要校验 Host 头的应用，要在 reverse_proxy 块里加 `header_up Host {upstream_hostport}`，否则通过公网 IP 访问会报 `Invalid Host header`，而 curl localhost 却能通。用 `curl -H 'Host: <public-ip>:<port>' ...` 验证。备案通过后，把 `:port` 站点地址换成域名——Caddy 自动签发/续期 Let's Encrypt，basic_auth 门禁保持在前面。

## 验证层次（解析生效 ≠ 网站可访问）

DNS TTL + 拦截 + 安全组是三个独立的层次；每层用各自的工具探测：

1. `dig +short A <domain>` 以及跨解析器的证书 TXT——`dig +short TXT <host>.<domain> @119.29.29.29`（腾讯/DNSPod）、`@223.5.5.5`（阿里云）、`@8.8.8.8`（Google）；点"验证域名"之前必须全部一致。`scripts/check-dns.sh` 一次完成 A+TXT。
2. 从主机内部 `curl -m 6 http://<public-ip>:<port>/`——超时 ⇒ 安全组拦截；立即拒绝 ⇒ 安全组放行但无人监听；200 ⇒ 已开放。
3. `curl -vI https://domain`——证书已下发（或 Caddy 在首次请求时自动签发）；怪配置之前先检查是否有备案拦截页。

## 更多坑（实战中都踩过）

- **HTTPS ≠ 认证。** 加密挡不住陌生人连接；任何公网暴露的服务都需要登录保护（`ENABLE_SIGNUP=false` + 管理员账号、OAuth 门禁或 basic auth）。公开绑定的 Hermes dashboard 上绝不要用 `--insecure`（会暴露 API key）。
- **便宜 TLD（.icu/.cyou）同样受备案规则约束**——没有捷径。
- **`/proc/<PID>/environ` 需要把重定向放进 root shell 里**：`sudo bash -c "tr '\0' '\n' < /proc/PID/environ"`——`sudo tr ... < file` 会因 Permission denied 失败，因为 shell 在 sudo 之前就打开了 fd。
- **对 DNS 控制台截图的 OCR/视觉识别会误读主机记录**（`fileauth.txt` vs `_dnsauth`）；按控制台文字逐字读取并用 dig 确认。DNS 控制台表单各不相同（"快速添加解析" vs "添加记录"），但字段是一样的：记录类型 / 主机记录 / 记录值 / 解析请求来源 / TTL。
- **端口冲突**：分配前 `ss -tlnp`——某个端口（如 9119/9120）可能被另一个用户的回环 dashboard 占用；选不同的端口。
- **别买控制台推销的付费 DNS 附加组件**（如云解析个人版 19.9元）——免费套餐够用；证书反正免费。

## 支持文件

- `references/tencent-dnspod-walkthrough.md` — 会话走查：精确的腾讯/DNSPod 控制台表单、xiucong.cyou 示例、真实 dig 输出。
- `scripts/check-dns.sh` — 带期望值匹配的多解析器 A/TXT 探测。

## 相关

- `hermes-operations` — 安全的公网 dashboard 模式（回环 + Caddy basic_auth）、共享主机上的用户隔离（§1）。
- `ssh-key-setup` — 访问盒子本身。
