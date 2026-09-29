#!/usr/bin/env python3
"""Fetch an airport subscription, parse vless:// URIs, emit a sing-box config.

Usage: python3 gen_singbox_config.py "https://host/subscribe?token=XXX"

Behavior:
  - Fetches the subscription (urllib with curl fallback — urllib often times out).
  - Base64-decodes, keeps vless:// lines, prints node index + name.
  - Picks up to 3 nodes by name keywords (香港/日本/新加坡/美国), falls back to first 2.
  - Writes config.json: mixed inbound :7890 (SOCKS+HTTP), http inbound :7891,
    first chosen node as route final. Outbounds tagged node-<idx>.
  - sing-box 1.13 compatible: new DNS format, no transport field (tcp is default).

Validate after generation:  sing-box check -c config.json
"""
import base64, json, subprocess, sys, urllib.request, urllib.parse

SUB_URL = sys.argv[1] if len(sys.argv) > 1 else ""
OUT = "/home/ubuntu/singbox/config.json"

req = urllib.request.Request(SUB_URL, headers={"User-Agent": "curl/8"})
try:
    raw = urllib.request.urlopen(req, timeout=20).read()
except Exception as e:
    print(f"urllib failed ({e}); falling back to curl")
    raw = subprocess.run(
        ["curl", "-sk", "--max-time", "30", SUB_URL],
        capture_output=True, check=True).stdout
try:
    text = base64.b64decode(raw).decode()
except Exception:
    text = raw.decode(errors="ignore")

nodes = []
for line in text.splitlines():
    line = line.strip()
    if line.startswith("vless://"):
        nodes.append(line)

print(f"parsed {len(nodes)} nodes")
for i, n in enumerate(nodes):
    name = ""
    if "#" in n:
        name = urllib.parse.unquote(n.split("#", 1)[1])
    print(f"  [{i}] {name}")


def pick(keys):
    for i, n in enumerate(nodes):
        nm = urllib.parse.unquote(n.split("#", 1)[1]) if "#" in n else ""
        if any(k in nm for k in keys):
            return i
    return None


chosen = []
for keys in (["香港"], ["日本"], ["新加坡"], ["美国"]):
    idx = pick(keys)
    if idx is not None and idx not in chosen:
        chosen.append(idx)
    if len(chosen) >= 3:
        break
if not chosen:
    chosen = [0, 1]


def parse_vless(uri):
    body = uri[len("vless://"):]
    head, _, frag = body.partition("#")
    userinfo, _, hostport = head.partition("@")
    hostport, _, query = hostport.partition("?")   # strip query BEFORE port split
    host, _, port = hostport.rpartition(":")
    params = dict(urllib.parse.parse_qsl(query))
    return {
        "uuid": userinfo, "host": host, "port": int(port),
        "sni": params.get("sni") or params.get("servername") or host,
        "pbk": params.get("pbk", ""), "sid": params.get("sid", ""),
        "flow": params.get("flow", ""), "fp": params.get("fp", "chrome"),
    }


outbounds = []
for idx in chosen:
    v = parse_vless(nodes[idx])
    nm = urllib.parse.unquote(nodes[idx].split("#", 1)[1]) if "#" in nodes[idx] else f"node{idx}"
    ob = {
        "type": "vless", "tag": f"node-{idx}",
        "server": v["host"], "server_port": v["port"], "uuid": v["uuid"],
        "tls": {
            "enabled": True, "server_name": v["sni"],
            "utls": {"enabled": True, "fingerprint": v["fp"]},
            "reality": {"enabled": True, "public_key": v["pbk"], "short_id": v["sid"]},
        },
    }
    if v["flow"]:
        ob["flow"] = v["flow"]
    outbounds.append(ob)
    print(f"  -> using [{idx}] {nm} @ {v['host']}:{v['port']} sni={v['sni']}")

config = {
    "log": {"level": "info"},
    "dns": {"servers": [{"type": "udp", "tag": "local", "server": "223.5.5.5"}]},
    "inbounds": [
        {"type": "mixed", "tag": "mixed-in", "listen": "127.0.0.1", "listen_port": 7890},
        {"type": "http", "tag": "http-in", "listen": "127.0.0.1", "listen_port": 7891},
    ],
    "outbounds": outbounds + [{"type": "direct", "tag": "direct"}],
    "route": {"final": outbounds[0]["tag"]},
}
with open(OUT, "w") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
print("config written:", OUT)
