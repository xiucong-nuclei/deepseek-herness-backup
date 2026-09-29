---
name: ssh-key-setup
description: Set up SSH key-based authentication for remote servers, including PuTTY .ppk conversion for Windows clients.
metadata:
  hermes:
    tags:
    - ssh
    - putty
    - key-management
    - remote-access
    - windows
    version: 1.0.0
    platforms:
    - linux
    - windows
---

# SSH 密钥设置

为远程服务器访问设置 SSH 密钥对认证。涵盖密钥生成、服务端配置和 Windows/PuTTY 客户端兼容性。

## 何时使用

- 用户需要通过 SSH 访问 Hermes 服务器或其他 Linux 主机
- 用户希望使用基于密钥的认证而不是密码
- 用户从 Windows 使用 PuTTY 连接，需要 `.ppk` 格式

## 工作流程

### 第 1 步 — 在服务器上生成密钥对

```bash
ssh-keygen -t ed25519 -f ~/.ssh/<key_name> -N "" -C "<comment>"
```

优先使用 `ed25519` 而不是 RSA。为方便自动化的密钥避免使用口令（`-N ""`）。

### 第 2 步 — 安装公钥

```bash
cat ~/.ssh/<key_name>.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 第 3 步 — 交付私钥

通过 `MEDIA:` 附件把私钥文件发送给用户。

### 第 4 步 — PuTTY 转换（Windows 用户）

PuTTY 使用 `.ppk` 格式，而非 OpenSSH 格式。

**如果用户有 PuTTYgen 图形界面:**
1. 打开 PuTTYgen
2. **Conversions → Import key** → 选择私钥文件
3. **Save private key** → `.ppk`

**如果用户没有 PuTTYgen（便携版/绿色版 PuTTY）:**

在服务器上转换:

```bash
# Install puttygen CLI
sudo apt-get install -y putty-tools

# Convert OpenSSH → .ppk
puttygen ~/.ssh/<key_name> -O private -o ~/.ssh/<key_name>.ppk
```

然后把 `.ppk` 文件交付给用户。

### 第 5 步 — 用户连接

**OpenSSH 客户端（Linux/macOS/Git Bash）:**
```bash
ssh -i ~/.ssh/<key_name> ubuntu@<server_ip>
```

**PuTTY（Windows）:**
1. Session → Host Name: `ubuntu@<server_ip>`
2. Connection → SSH → Auth → Credentials → Private key file: 选择 `.ppk`
3. 保存会话，然后打开

**VS Code Remote-SSH:**
```
Host <alias>
    HostName <server_ip>
    User ubuntu
    IdentityFile ~/.ssh/<key_name>
```

## 常见陷阱

- **PuTTY 报 "Host key not in manually configured list"** — 检查 Connection → SSH → Host keys，若启用了 "Manually configure host keys..." 则取消勾选。
- **PuTTY 拒绝 OpenSSH 密钥** — 必须先用 `.ppk` 转换。PuTTY 无法直接读取 OpenSSH 格式。
- **私钥权限** — 对 OpenSSH 密钥和 `.ppk` 文件都要 `chmod 600`，否则 SSH 会拒绝。
- **安装 `putty-tools` 后 `apt-get` 提示 "User sessions running outdated binaries"** — 这是关于需要重启的运行中守护进程的无害 systemd 提示，与 `puttygen` 无关。忽略即可。
