# Bus Signal Table Generation — OCR-first workflow (full guide)

Absorbed from the former `bus-signal-table` skill. The condensed workflow lives in
SKILL.md; this is the full verified guide, including the complete AXI4/AHB-Lite/ICB
signal description quick-reference.

## When to Use

- User sends a Verilog/SystemVerilog port list screenshot (image)
- User asks to "analyze signals", "生成描述", or "generate table"
- User is documenting bus interfaces (ICB, AHB-Lite, AXI, APB, etc.)

## Step 1 — Extract Signals from Image

**Primary method: tesseract OCR** (more reliable for code screenshots).

```bash
# Preprocess for dark-background code (4× scale + threshold)
python3 -c "
from PIL import Image
img = Image.open('image.png')
w, h = img.size
big = img.resize((w*4, h*4), Image.LANCZOS)
gray = big.convert('L')
binary = gray.point(lambda x: 0 if x < 100 else 255, '1')
binary.save('/tmp/clean.png')
"
tesseract /tmp/clean.png stdout -l eng --psm 6
```

Cross-verify with `--psm 4` if signal count seems wrong.

**Fallback: vision_analyze** for cases where tesseract fails (colored text on colored
background, complex layouts). Always cross-validate with tesseract afterwards — vision
models (especially Qwen3-VL) frequently hallucinate signal names, bit widths, and merge
separate signals.

Common OCR corrections for dark-background terminal screenshots:
- `6` → `0`, `©` → `0`, `:` → `,`, `.` → `,`
- `reg icb` → `reg_icb`, `cnd` → `cmd`
- Spaces in signal names need to be joined with `_`

## Step 2 — Assign Direction (M→S / S→M)

Convert `input`/`output` keywords to absolute bus direction:

| Verilog keyword | Bus direction |
|-----------------|---------------|
| `input` (master drives) | M→S |
| `output` (slave drives) | S→M |

**Never use `input`/`output` in the final table** — they are module-relative and
meaningless at the Fab/integration level. Always use M→S / S→M.

**Exception: global and clock/reset signals** — `clk`, `rst_n`, `clkgate_bypass`,
and per-channel clock/reset (e.g., `biu2iram_icb_clk`) are not bus channel signals.
Use `in` / `out` for these. They belong in separate tables: "Global Signals" and
"Channel Clock and Reset".

## Step 3 — Generate Descriptions

**Core principle: describe what the signal IS per protocol, not what Fab DOES with it.**

Three depth levels — user will tell you which is right:

| Level | Style | Example for `awvalid` | When |
|-------|-------|----------------------|------|
| Minimal | Bare protocol role | `Write address valid` | Too short — user will ask for more |
| Protocol | What the signal indicates | `Write address valid. Indicates master is driving valid write address and control.` | **Target** |
| Fab-heavy | What Fab does internally | `Write address valid. Fab uses this to latch address and start routing.` | Too much — user will reject |

**Rules:**
- Describe the signal, not the system's reaction to it
- Avoid: "Fab forwards / Fab uses / Fab routes / Fab backpressures"
- Prefer: "Indicates master is driving / Indicates slave is ready / Matches the original"
- For ID signals: "Used to match response with request"
- For handshake signals: "Indicates <side> is driving/ready to accept valid <channel>"

## Step 4 — Format Table

**Column order (user's preference):**

```
| Signal | Dir | Width | Description |
```

**Signal ordering:** Must exactly match the order in the source image. Do not reorder
or group by channel.

**Width format:**
- 1-bit signals: just `1` (not `[0:0]` or `1-bit`)
- Multi-bit: `[31:0]`, `[7:0]`, etc.

**Naming:** Preserve the original signal names from the port list exactly (trailing
commas stripped). Do not strip vendor prefixes like `i_axi_` or `dummy_ahbl_`.

## Step 5 — Group into Separate Tables

| Category | Table name | Direction |
|----------|-----------|-----------|
| AXI channels (AW/W/B/AR/R) | By channel | M→S / S→M |
| ICB channels (cmd/rsp) | By channel | M→S / S→M |
| AHB signals | One table (single channel) | M→S / S→M |
| Global clock/reset (`clk`, `rst_n`, `clkgate_bypass`) | **Global Signals** | `in` |
| Per-channel clock/reset (`biu2iram_icb_clk` etc.) | **Channel Clock and Reset** | `in` |
| EDC error reporting (`bus_fab_eccp_err` etc.) | **Error Reporting Signals** or by category | S→M |

**RST document naming convention:** "The [Table Name] of Bus Fab are depicted in
:numref:`table-label`."

## Step 6 — EDC-Protected Signal Patterns

When signals have `_p` (payload) and `_edc` (error detection code) suffixes:

- `_p` signals: Use the standard description + "Payload protected by EDC."
  Example: `Write address valid. Payload protected by EDC.`
- `_edc` signals: "EDC for [corresponding payload signal]."
  Example: `EDC for write data.`
- `_hi` / `_lo` suffixes: "EDC for high/low portion of [signal]."
  Example: `EDC for high portion of write address.`

## Signal Description Quick Reference

### AXI4 (Full)

| Channel | Signal | Description |
|---------|--------|-------------|
| AW/AR | `valid` | Indicates master is driving valid address and control. |
| AW/AR | `ready` | Indicates slave is ready to accept address. |
| AW/AR | `id` | Transaction ID. Used to match response with request. |
| AW/AR | `addr` | Start byte address of the burst. |
| AW/AR | `len` | Burst length. Number of data beats in the burst, minus one. |
| AW/AR | `size` | Burst size. Bytes per data beat = 2^size. |
| AW/AR | `burst` | Burst type: FIXED, INCR, or WRAP. |
| AW/AR | `lock` | Lock type. Indicates atomic or exclusive access. |
| AW/AR | `cache` | Cache type. Memory type and cache allocation hints. |
| AW/AR | `prot` | Protection type. Privilege, security, and instruction/data indicator. |
| AW/AR | `user` | User-defined sideband signal. |
| W | `valid` | Indicates master is driving valid write data. |
| W | `ready` | Indicates slave is ready to accept write data. |
| W | `data` | Write data. |
| W | `strb` | Write strobe. One bit per byte; low strobe bytes remain unchanged. |
| W | `last` | Indicates the final data beat of the burst. |
| B | `valid` | Indicates slave is driving valid write response. |
| B | `ready` | Indicates master is ready to accept write response. |
| B | `id` | Matches the awid of the completed write transaction. |
| B | `resp` | Write response status: OKAY, EXOKAY, SLVERR, or DECERR. |
| B | `user` | User-defined sideband signal. |
| R | `valid` | Indicates slave is driving valid read data. |
| R | `ready` | Indicates master is ready to accept read data. |
| R | `id` | Matches the arid of the completed read transaction. |
| R | `data` | Read data. |
| R | `resp` | Read response status: OKAY, EXOKAY, SLVERR, or DECERR. |
| R | `last` | Indicates the final data beat of the burst. |
| R | `user` | User-defined sideband signal. |

### AHB-Lite

| Signal | Description |
|--------|-------------|
| `htrans` | Transfer type: IDLE, BUSY, NONSEQ, or SEQ. |
| `hwrite` | Read/write indicator. 1 = write, 0 = read. |
| `hmastlock` | Locked transfer. Indicates master requires uninterrupted access. |
| `hsize` | Transfer size. Bytes per beat = 2^hsize (0 = 8b, 1 = 16b, 2 = 32b, 3 = 64b...). |
| `hburst` | Burst type: SINGLE, INCR, WRAP4/8/16, INCR4/8/16. |
| `hprot` | Protection control: opcode, privilege, bufferable, cacheable. |
| `hwdata` | Write data. |
| `haddr` | Address. Byte address of the transfer. |
| `hrdata` | Read data. |
| `hresp` | Response status: OKAY or ERROR. |
| `hready` | Transfer ready. Deasserted by slave to insert wait states. |

### ICB (Nuclei)

| Signal | Description |
|--------|-------------|
| `cmd_valid` / `cmd_ready` | Request handshake signals. |
| `cmd_sel` | Region select. Selects the target address region. |
| `cmd_read` | Read/write indicator. 1 = read, 0 = write. |
| `cmd_addr` | Address. Byte address of the access. |
| `cmd_wdata` | Write data. |
| `cmd_wmask` | Byte write mask. One bit per byte. |
| `cmd_size` | Transfer size. Bytes per beat = 2^size. |
| `cmd_lock` | Locked access. Indicates atomic or locked transfer. |
| `cmd_excl` | Exclusive access. Indicates exclusive (LDEX/STEX) transaction. |
| `cmd_xlen` | Burst length. Number of beats in the burst, minus one. |
| `cmd_xburst` | Burst type: FIXED, INCR, or WRAP. |
| `cmd_modes` | Privilege mode. Indicates the privilege level of the access. |
| `cmd_dmode` | Debug mode. Indicates debug access. |
| `cmd_attri` | Memory attribute. Cacheable, bufferable, and other memory type hints. |
| `cmd_beat` | Beat index. Current beat number within the burst. |
| `rsp_valid` / `rsp_ready` | Response handshake signals. |
| `rsp_err` | Error flag. Indicates the access encountered an error. |
| `rsp_excl_ok` | Exclusive access success. |
| `rsp_rdata` | Read data. |

## Pitfalls

- **Vision model hallucination**: Qwen3-VL models frequently misread Verilog port
  lists — they swap signal names with bit widths (e.g., `wdata [63:0]` becomes
  `wvalid [63:0]`), merge separate signals (e.g., `hresp [1:0]` + `hready 1` becomes
  `hready [1:0]`), and invent full names for abbreviations (e.g., `hmastlock` becomes
  `hmasterlock`). Always cross-validate with tesseract.
- **Description depth**: The user has a specific tolerance window. Too short ("Request
  valid") gets pushback. Too detailed with Fab behavior ("Fab forwards to downstream")
  gets rejected. The safe zone is protocol-level: "Indicates master is driving valid
  write address and control."
- **Direction format**: Never use `input`/`output`. Always M→S / S→M.
- **Signal ordering**: Must exactly match the source image order. Do not re-group by
  channel or re-sort alphabetically.
- **Missing signals**: If the user says "you missed signals", re-OCR the image with
  tesseract — the vision model almost certainly dropped lines.
- **Column order**: The user's preferred column order is Signal | Dir | Width |
  Description. They explicitly asked to swap Width and Dir from an earlier format.
