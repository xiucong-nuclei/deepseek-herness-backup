---
name: dsh-web-service
description: "Manage the dsh web systemd user service on this box: status, restart, logs, and verify for the DeepSeek Harness browser UI (port 3080)."
---

# dsh web 服务管理

本机 DeepSeek Harness 浏览器 UI（`dsh web`）已托管为 **systemd 用户级服务**。本 skill 用于查看状态、重启、看日志、验证可用性。

## 服务基本信息

- 服务名：`dsh-web.service`（用户级，用 `systemctl --user`，不需要 sudo）
- 单元文件：`~/.config/systemd/user/dsh-web.service`
- 启动命令：`/usr/bin/node /usr/bin/dsh --profile web --no-open`
- 运行用户：`ubuntu`；DSH_HOME=`/home/ubuntu/.dsh`
- 监听：`127.0.0.1:3080`（外部访问靠 SSH 隧道转发，隧道断不影响服务）
- 开机自启：已通过 `loginctl enable-linger ubuntu`（Linger=yes）实现；单元 `WantedBy=default.target`
- 崩溃恢复：`Restart=on-failure`，3 秒后自动拉起

## 常用操作

```bash
# 查看状态
systemctl --user status dsh-web --no-pager

# 重启（用户要求"刷新功能"时的标准操作）
systemctl --user restart dsh-web

# 停止 / 启动
systemctl --user stop dsh-web
systemctl --user start dsh-web

# 看最近日志
journalctl --user -u dsh-web -n 100 --no-pager

# 实时跟随日志
journalctl --user -u dsh-web -f

# 验证服务可用（应返回 200）
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3080
ss -ltnp | grep 3080
```

## 何时重启

- 安装/升级了插件、改了 profile 配置，需要重新加载时
- UI 行为异常、页面加载不出内容时
- 用户明确要求"刷新功能"时

## 重要注意事项（必须遵守）

1. **重启会中断当前所有会话**：`dsh-web` 进程被杀掉时，正在跑的 agent 回合、GUI 界面会立刻中断。会话数据持久化在 `~/.dsh/sessions/`，重启后可在 GUI 里恢复会话，但进行中的回合会丢失。**如果你（agent）自己就运行在这个进程里，重启会把自己干掉**——动手前必须明确告知用户"将短暂中断当前对话"，或确认用户同意后再执行。
2. **重启 ≠ 重新构建**：重启只重新加载已安装的文件。如果要让代码改动生效（apps/web 或插件包），需要先构建 web 产物（checkout 在 `/usr/lib/node_modules/@deepseek-ai/dsh/`，构建或 `pnpm run dev:web` 监视器），单纯 `restart` 不会刷新构建产物。
3. **端口冲突排查**：如果 `start` 失败，先看 `journalctl --user -u dsh-web -n 50`；常见原因是 3080 被旧的临时实例占用（`ss -ltnp | grep 3080`），先把旧进程杀掉再 start。
4. **从临时实例切换到服务**：如果 3080 上跑的是 SSH 会话里手动启动的旧实例（ps 可见 `pts/0` 下的 `node /usr/bin/dsh web`），需要先结束旧进程（`kill <pid>`），再 `systemctl --user start dsh-web`。

## 故障排查

| 症状 | 排查 |
|---|---|
| 服务起不来 | `journalctl --user -u dsh-web -n 50`；检查 3080 端口占用 |
| 开机不自启 | `loginctl show-user ubuntu -p Linger` 应为 `yes`；`systemctl --user is-enabled dsh-web` 应为 `enabled` |
| 修改单元文件后不生效 | 改完必须 `systemctl --user daemon-reload` 再 restart |
| 页面能开但功能异常 | 先 restart 服务；不行则检查是否需要重新构建产物（见注意事项 2） |
