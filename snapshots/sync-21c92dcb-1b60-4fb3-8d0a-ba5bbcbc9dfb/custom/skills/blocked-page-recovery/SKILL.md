---
name: blocked-page-recovery
description: Recover blocked/paywalled/WAF'd pages via fallbacks.
metadata:
  hermes:
    tags:
    - Research
    - Archives
    - Wayback
    - Paywall
    - WAF
    - Fallback
    related_skills:
    - grounded-citations
    version: 1.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# 被封锁页面恢复

当页面无法抓取——403/429、Cloudflare 的 "Just a moment..."、付费墙（paywall），
或机器人检测拦截页——不要放弃，也不要反复请求同一个
URL。第三方服务往往保存着该页面的**副本**。按下述
阶梯逐级尝试，先试成本最低的。

## 恢复阶梯

```
1. Wayback Machine  — archive.org "available" API  (snapshot + timestamp)
2. archive.today    — domain rotation: archive.ph → .md → .li → .is
3. Jina Reader      — only if JINA_API_KEY is set  (live server-side render)
4. API-first pivot  — look for /api/, /graphql, .json, or RSS on the same host
5. Real browser     — browser tool as the last, most expensive resort
```

用内置脚本一步运行:

```bash
python3 scripts/recover_page.py "https://example.com/blocked-article" --json
```

脚本按顺序依次尝试每条路径，校验每个响应体（见"虚假
成功"一节），并输出第一个真实命中及其来源信息（provenance）。

## 来源信息纪律（不可妥协）

每条恢复的副本都带有来源信息，引用时必须保留:

| 路径 | 来源 | 如何引用 |
|-------|-----------|-------------|
| Wayback / archive.today | `snapshot` | 引用时注明快照日期："as archived 2026-08-06"。切勿把快照当作实时页面——它可能已过期。 |
| Jina Reader | `live` | 实时页面的服务端重渲染，正常引用即可。 |
| 实时抓取 / 浏览器 | `live` | 正常引用即可。 |

如果用户需要的是*当前*数据（价格、可用性、突发新闻），
快照只是背景信息，不是答案——要明确说明并注明其时间。

## 手动路径

### 1. Wayback Machine（来源信息最佳，优先尝试）

```bash
# Discovery: returns closest snapshot URL + timestamp as JSON
curl -sL "https://archive.org/wayback/available?url={URL}"
# Then fetch archived_snapshots.closest.url
```

如需枚举大量快照（或恢复已删除页面），可用 CDX 索引:

```bash
curl -sL "https://web.archive.org/cdx/search/cdx?url={URL}&output=json&limit=10"
```

CDX 在高负载下会间歇性返回 503——遇到时改用
`available` API；不要反复重试轰炸它。

适用: 任何被公开爬取过的 URL。不适用: robots 屏蔽的站点、
从未被爬取的 URL、纯 JS 的 SPA（快照无法渲染）。

### 2. archive.today（付费墙、已删除内容）

用户提交的存档——往往收录了 Wayback Machine 没有的付费新闻文章。
限流很激进（429）且会轮换域名，所以迭代尝试:

```bash
for d in archive.ph archive.md archive.li archive.is; do
  curl -sL --max-time 20 "https://$d/newest/{URL}" -o /tmp/page.html \
    -w "%{http_code}" && break
done
```

**校验响应体，而不是状态码**——429 仍然会返回数 KB 的
限流 HTML，仅凭大小检查会误判为成功。

### 3. Jina Reader（需要 JINA_API_KEY）

`r.jina.ai` 在服务端用真实浏览器重新渲染实时页面并
返回 markdown。匿名访问已不可用（401 → Turnstile）；必须使用
密钥:

```bash
curl -s -H "Authorization: Bearer $JINA_API_KEY" "https://r.jina.ai/{URL}"
```

能处理存档无法处理的 JS SPA。当环境变量未设置时，完全
跳过此路径。

### 4. API 优先转向

WAF 对 HTML 表面的防护远比对其背后的数据端点严格。
在某个站点连续 2-3 次抓取受阻后，停止与 HTML 纠缠，
转而寻找:

- 页面 URL 的 `/api/...`、`/graphql` 或 `.json` 变体
- RSS/Atom 订阅源（`/feed`、`/rss`，或任何已恢复副本中的
  `<link rel="alternate">`）
- 站点地图（`/sitemap.xml`），其中可能暴露未受门禁的规范 URL

## 虚假成功——会撒谎的路径

以下路径返回 HTTP 200 且带有看似合理的响应体，但并非真实页面。
脚本会自动拒绝它们；手动操作时也要拒绝:

- **Google Cache 已死亡**（自 2024 年中起）。`webcache.googleusercontent.com`
  返回 200 和数十 KB 内容，但那是带 JS 重定向的 Google 搜索拦截页，
  不是缓存。绝不要使用。
- **AMP 缓存**（`*.cdn.ampproject.org`）大多返回一个约 300 字节、
  指向原始（被封锁）URL 的 `<title>Redirecting</title>` meta-refresh 存根。
  把它当成成功会造成抓取死循环。
- **限流响应体**: archive.today 的 429 页面是数 KB 的 HTML。要检查
  目标页面的实际内容（标题关键词、预期字符串），而不是只看大小。

脚本应用的检测启发式: 响应体低于每条路径的字节下限；
meta-refresh/JS 重定向存根指向原主机；拦截页
标题（"Just a moment"、"Redirecting"、"Google Search"、"Attention Required"）。

## 代理转发: 不要用

通用"web 代理"转发本质上是中间人。绝不要通过它们发送
cookie 或 Authorization 头，也不要用于任何
用户会依赖的操作——来源信息无法验证。优先使用存档，至少它们会
给副本打上时间戳。
