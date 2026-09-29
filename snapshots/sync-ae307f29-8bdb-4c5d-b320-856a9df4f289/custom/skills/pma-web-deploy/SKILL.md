---
name: pma-web-deploy
description: Deploy the PMA config web tool (and any deliverables static site) to the public domain xiucong.cyou via /var/www + Caddy. Auto-deploy after every tool change, root-owned directory permission trap, the sudo path, and post-deploy verification.
metadata:
  hermes:
    tags:
    - PMA
    - deploy
    - caddy
    - xiucong.cyou
    - web
    category: deployment
    related_skills:
    - nuclei-pma-config
    - public-web-exposure
    - single-file-web-tools
    version: 1.1.0
    author: Hermes Agent + kiucong
    license: MIT
    platforms:
    - linux
---

# PMA 网页部署（xiucong.cyou）

把 `~/deliverables/pma-config-tool/` 的最新版本同步到线上 `https://xiucong.cyou/`。

## 自动部署（用户标准指令，2026-09）

**改完 PMA 工具就自动部署到域名，不要问用户"要不要推"。** 流程固定为：

1. 在 `~/deliverables/pma-config-tool/` 改代码；
2. 跑相关测试批次（见 `in-page-regression-suite` / `nuclei-pma-config`）；
3. `git commit` + `git push origin main`（该仓库自己的 remote）；
4. **立即执行下面的部署命令并验证**；
5. 回复里报告：commit 号、线上 HTTP 状态、md5 是否一致。

用户过去说"推到域名上吧"才部署；该说法已作废，现在默认自动。

## 目录地图

| 角色 | 路径 | 属主 |
|---|---|---|
| 本地开发源 | `~/deliverables/pma-config-tool/` | ubuntu |
| 线上部署目录 | `/var/www/pma-calc-landing/` | **root** |
| 域名配置 | `/etc/caddy/Caddyfile`（root 指向 site 目录） | root |
| 公共站点 | `xiucong.cyou` / `www.xiucong.cyou` 端口 443 | caddy 进程 |

注意：源目录是 `pma-config-tool/`（独立 git 仓库，remote
`git@github.com:xiucong-nuclei/Nuclei_PMA_config.git`，分支 `main`）。
旧路径 `~/deliverables/web/pma-calc-landing/` 已删除（deliverables commit
`a094293`），不要再往那里拷。

## 部署命令

```bash
cd ~/deliverables/pma-config-tool
sudo cp index.html PMA_DESIGN.md /var/www/pma-calc-landing/
sudo cp tests/pma_test_suite.js /var/www/pma-calc-landing/tests/
```

- 部署 3 个文件：`index.html`、`PMA_DESIGN.md`、`tests/pma_test_suite.js`。
- **`README.md` 不部署**（含仓库内部说明，不放到公网）；`tests/logs/` 也不用同步。
- bash 调用需带 `sandbox_permissions: danger-full-access`：`/var/www` 是 root
  属主且沙箱默认禁用 sudo，否则报 "no new privileges flag"。

## 核心坑：/var/www 是 root 属主

1. **直接 cp 到 /var/www → Permission denied**（drwxr-xr-x root root）。
2. **DSH bash 的 `sandbox_permissions: danger-full-access` 单独不够** —— 它只放宽
   landlock 文件沙箱，进程仍是 ubuntu，POSIX 权限照样拒绝。
3. **DSH write 工具同样失败**（EACCES mkdir temp）。
4. **真正解法：`sudo cp`** —— ubuntu 在 sudo 组；在 DSH 里配合
   `sandbox_permissions: danger-full-access` 一起用即可成功。

结论：**部署直接 `sudo cp` + danger-full-access，不要浪费时间在 cp/write 上。**

## 部署后验证（必须做）

```bash
curl -s -o /tmp/served.html -w "status=%{http_code} size=%{size_download}\n" https://xiucong.cyou/
md5sum /tmp/served.html ~/deliverables/pma-config-tool/index.html   # 必须一致
```

用「线上内容 vs 本地文件」比对 md5，比只比本地文件更强：它能证明 Caddy
真的在服务新版。Caddy 静态文件即时生效，无需 reload/restart。

## 容易犯的错

- **改完忘记部署**：症状是用户说"网页没变化"，先比线上/本地 md5，不要急着改代码。
- **浏览器缓存**：报告时提醒用户 Ctrl+F5 强刷。
- **Caddyfile 改动才需要动 Caddy**：纯文件更新不需要。
- **拷错源目录**：只从 `~/deliverables/pma-config-tool/` 取文件。

## Git 提交纪律

- 部署前先 commit + push：
  ```bash
  cd ~/deliverables/pma-config-tool
  git add index.html tests/pma_test_suite.js   # 只加相关文件
  git commit -m "..." && git push origin main
  ```
- `deliverables` 主仓库**不跟踪**该目录（`.git/info/exclude` 里排除了
  `pma-config-tool/`），不要在 deliverables 里 `git add` 它。
- 只提交相关文件，不相干的改动（如 `tools/piccp/piccp.conf.json`）留在工作区。
