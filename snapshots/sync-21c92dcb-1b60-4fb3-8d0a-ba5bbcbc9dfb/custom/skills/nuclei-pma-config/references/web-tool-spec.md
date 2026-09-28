# PMA Web Tool — Session Spec (Aug 2026)

Source: user requirement file `~/input/PMA 生成网页工具.md` + in-session
confirmations. Durable spec for maintaining ~/deliverables/web/pma-calc-landing/index.html.

## Original Requirement (from user doc, condensed)

Purpose: PMA config is complex/error-prone; tool has two modes:
- GENERATE: user inputs requirements -> emits the corresponding config snippet.
- CHECK: user pastes a .config -> parse, verify rules, and (per user amendment)
  generate the corrected code, replace the bad lines in the file, offer download.

## The 3 User Confirmations (do not re-negotiate)

1. PMA_CSR_NUM — "先不管": generate by total region count (matches sample
   DEVICE1+CACHEABLE1+NC0 -> 2), never validate it in check mode.
2. Check mode — no PA Size input needed. Output is the corrected full file
   (original lines preserved, bad PMA lines replaced) + a download button.
3. SPLIT scheme with >8 blocks -> show red warning; do NOT auto-switch to WRAP.

## Tool Layout (v1 implementation)

- Single file index.html, zero deps, dark tech style (#0a0f1e bg, grid
  backdrop, #38bdf8/#818cf8 accents), pure-ASCII English UI.
- Header + GENERATE/CHECK tabs.
- GENERATE left panel: PA SIZE radio (32/64), PREFIX input (default N600),
  region table rows [ATTR select | BASE | MODE select(end/size) | END/SIZE |
  delete], "+ ADD REGION" (per-attr cap 8). Right panel: address bar,
  VALIDATION info box (per-region [OK]/[ERR]/[FIX] + WRAP/SPLIT toggle),
  CONFIG OUTPUT pre + COPY.
- CHECK: textarea + file-name input (default "config") + CHECK button; right
  side results list (OK/ERR/WARN with source line + fix hint), FIXED CONFIG
  pre + DOWNLOAD FIXED (Blob + a[download]).
- Default demo rows on load: DEVICE 0x10000000 end 0x20000000; CACHEABLE
  0x20000000 size 0x10000000.

## Implementation Notes (as built)

- All address math in BigInt; hex parse regex /[0-9a-fA-F_]+$/ also accepts
  Verilog `` `MACRO'hHEX `` and underscores.
- fixSchemes map holds per-region chosen scheme ("wrap" default / "split").
- Effective regions = valid rows as-is + invalid rows via chosen scheme;
  overlap check runs over effective list sorted by lo (same-attr ERR,
  cross-attr WARN).
- Check parser keeps every original line; fixes map lineNo -> replacement;
  NUM lines rewritten, missing NUM lines appended with auto-added comment.
- fmtSize() renders B/KB/MB/GB/TB for human-readable info.

## Verification Checklist (interrupted — NOT yet done)

1. Serve from the project dir (server serves CWD): python3 -m http.server 8640
   with workdir = ~/deliverables/web/pma-calc-landing.
2. GENERATE: default demo rows -> preview must match the Kconfig sample in
   SKILL.md exactly; add misaligned region -> WRAP/SPLIT toggle works,
   address bar updates.
3. CHECK: paste the sample config (it is valid -> all OK); then corrupt it
   (e.g. mask 0x0FFFFF0F, base 0x1000_0100, NUM mismatch) -> ERR rows with
   fix hints, FIXED CONFIG shows corrected lines, download button produces
   file.
4. Console/network: no errors; COPY works.
5. git commit in ~/deliverables.
