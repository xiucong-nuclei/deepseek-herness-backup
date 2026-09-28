# PMA Config Import Rules & UI Decisions

Source: PMA generator tool (`~/deliverables/web/pma-calc-landing/index.html`),
iteration history 2026-08 (session "PMA").

## Import parsing (parseConfig / loadRegionsFromConfig)

Two accepted formats:
- Kconfig: `CONFIG_<PFX>_CFG_<ATTR>_REGIONn_BASE="`<PFX>_CFG_PA_SIZE'hXXXX"`
- Verilog: `` `define <PFX>_CFG_<ATTR>_REGIONn_BASE `<PFX>_CFG_PA_SIZE'hXXXX `` (values may contain underscores like 'h8000_0000)

Order of operations (explicit user requirement):
1. Extract PA SIZE FIRST (`CONFIG_..._CFG_PA_SIZE=N` or `` `define ..._CFG_PA_SIZE N ``) → write into the PA SIZE input. Mask width = max(hexDigitLen*4, paSize).
2. Parse BASE/MASK against paSize.
3. Trim filler rows BEFORE creating regions:
   - idx >= that attr's REGION_NUM → skip (rows beyond the declared count are fillers)
   - base == 0 → skip (PMA never configures address 0; real N600 files pad unused slots with 0)
   - mask == all-ones → skip. Detect as `mask === ((1n<<bits)-1n)` (full-width mask in the resolved bit width), NOT as the literal value 0xffffffff — in a 48-bit context 0xffffffff is a legitimate 4GB low mask and must survive.

Without trimming, a real N600 48-bit file imported ~9 junk rows: base=0 rows became empty rows, and mask=0xffffffff computed as a bogus 4GB block (base 0, size 2^32).

Mask semantics: size = mask+1 (low-1s mask) or (~mask & all)+1 (high-1s mask). Low masks auto-convert to high (1s-leading) form in generated output.

Imported SIZE field: display in HUMAN form via fmtSize ("32 MB"), not "0x...". Safe because PMA region sizes are always powers of two → fmtSize output is always an integer → parseSize("32 MB") round-trips exactly. Never feed raw hex into the SIZE field.

## END/SIZE mode-switch auto-convert

On MODE select change (user requirement): if the source value parses AND base parses:
- end → size: r.val = fmtSize(end - base)
- size → end: r.val = "0x" + hexStr(base + size)
Invalid source or missing base → keep old value untouched.

## fmtAddr grouping (user requirement)

Underscore every 4 hex digits from the right: 32-bit `0x4400_0000`, 48-bit `0x0000_4400_0000`, 40-bit `0xFF_4400_0000`, unpadded `0x1_0000_0000`. Shared by address bar and validation info.

## Address bar

- Priority NC > CA > DEV > Default; recursive split-flatten (high priority cuts low-priority blocks: full cover → delete, partial → split into segments).
- Block min height = BLK pt (user bumped 25 → 30 → 33pt); GAP 1pt. If the min-height stack fits the PANEL's visible height → blocks grow equally to fill; else all stay at min height and the panel scrolls. Scrollbar decision must use the panel's visible clientHeight, not a fixed canvas height.
- Block info line: f1 attr+num, f2 base+" -", f3 end, f4 size — 4 fixed-width monospace flex columns (rb-f1..rb-f4), f4 right-aligned.
- Click feedback = scale pop animation: `el.animate([{transform:'scale(1)'},{transform:'scale(1.07)'},{transform:'scale(1)'}], {duration:150, easing:'ease-out'})`. User EXPLICITLY rejected color/highlight feedback: "让用户感觉到点击了一下,比如放大一下这种特效,而不是变色和高亮". Clicking a cfg block still highlights the matching table row (setActiveRow); clicking a default block clears the selection.

## Panel scroll pattern (user requirement)

All panels: title fixed, content scrolls. Regions panel: SETTINGS + REGIONS heading stay put, only table rows scroll — wrap `<table>` in `.table-wrap { flex:1 1 auto; overflow-y:auto; min-height:0 }`, panel becomes flex column. Validation panel: VALIDATION heading fixed, `.info-box` scrolls (panel max-height ~24vh). Same pattern the code `<pre>` and address bar already used.
