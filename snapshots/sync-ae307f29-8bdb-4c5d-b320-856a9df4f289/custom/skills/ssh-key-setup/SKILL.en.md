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

# SSH Key Setup

Set up SSH key-pair authentication for remote server access. Covers key generation, server-side config, and Windows/PuTTY client compatibility.

## When to Use

- User needs SSH access to the Hermes server or another Linux host
- User wants key-based auth instead of password
- User connects from Windows with PuTTY and needs `.ppk` format

## Workflow

### Step 1 — Generate key pair on server

```bash
ssh-keygen -t ed25519 -f ~/.ssh/<key_name> -N "" -C "<comment>"
```

Prefer `ed25519` over RSA. Avoid passphrase (`-N ""`) for automation-friendly keys.

### Step 2 — Install public key

```bash
cat ~/.ssh/<key_name>.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Step 3 — Deliver private key

Send the private key file to user via `MEDIA:` attachment.

### Step 4 — PuTTY conversion (Windows users)

PuTTY uses `.ppk` format, not OpenSSH format.

**If user has PuTTYgen GUI:**
1. Open PuTTYgen
2. **Conversions → Import key** → select the private key file
3. **Save private key** → `.ppk`

**If user does NOT have PuTTYgen (portable/green PuTTY):**

Convert on the server:

```bash
# Install puttygen CLI
sudo apt-get install -y putty-tools

# Convert OpenSSH → .ppk
puttygen ~/.ssh/<key_name> -O private -o ~/.ssh/<key_name>.ppk
```

Then deliver the `.ppk` file to user.

### Step 5 — User connects

**OpenSSH client (Linux/macOS/Git Bash):**
```bash
ssh -i ~/.ssh/<key_name> ubuntu@<server_ip>
```

**PuTTY (Windows):**
1. Session → Host Name: `ubuntu@<server_ip>`
2. Connection → SSH → Auth → Credentials → Private key file: select `.ppk`
3. Save session, then Open

**VS Code Remote-SSH:**
```
Host <alias>
    HostName <server_ip>
    User ubuntu
    IdentityFile ~/.ssh/<key_name>
```

## Pitfalls

- **PuTTY "Host key not in manually configured list"** — Check Connection → SSH → Host keys, uncheck "Manually configure host keys..." if enabled.
- **PuTTY rejects OpenSSH key** — Must convert to `.ppk` first. PuTTY cannot read OpenSSH format directly.
- **Private key permissions** — `chmod 600` on both the OpenSSH key and `.ppk` file, or SSH will refuse.
- **`apt-get` warns "User sessions running outdated binaries" after installing `putty-tools`** — This is a harmless systemd banner about running daemons needing restart, not related to `puttygen`. Ignore it.
