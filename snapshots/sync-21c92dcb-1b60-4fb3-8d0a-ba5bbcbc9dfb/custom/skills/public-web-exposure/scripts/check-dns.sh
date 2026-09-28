#!/usr/bin/env bash
# Multi-resolver DNS probe for domain + HTTPS setup.
# Checks A records, then (optionally) a TXT record against expected value.
# Usage: check-dns.sh <domain> [txt_host] [expected_txt_value]
set -u
RESOLVERS="119.29.29.29 223.5.5.5 8.8.8.8"
D="${1:?usage: check-dns.sh <domain> [txt_host] [expected_txt_value]}"
TXT_HOST="${2:-}"
EXPECT="${3:-}"

echo "== A records: $D =="
for r in $RESOLVERS; do
  echo -n "  $r: "
  dig +short A "$D" @"$r" | tr '\n' ' '
  echo
done

if [ -n "$TXT_HOST" ]; then
  echo "== TXT records: $TXT_HOST.$D =="
  for r in $RESOLVERS; do
    V=$(dig +short TXT "$TXT_HOST.$D" @"$r" | tr -d '"')
    if [ -n "$EXPECT" ]; then
      if [ "$V" = "$EXPECT" ]; then
        echo "  $r: MATCH ($V)"
      else
        echo "  $r: MISMATCH (got '$V', want '$EXPECT')"
      fi
    else
      echo "  $r: $V"
    fi
  done
fi
