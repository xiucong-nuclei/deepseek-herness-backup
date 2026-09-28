---
name: bus-interface-analysis
description: Analyze hardware bus interface port lists (AXI, AHB-Lite, ICB, APB) from Verilog/SV code images — extract signals, format as documentation tables with M→S/S→M direction and spec-style English descriptions.
metadata:
  hermes:
    tags:
    - hardware
    - bus
    - axi
    - ahb
    - icb
    - verilog
    - documentation
    - verdi
    version: 1.0.0
    platforms:
    - linux
---

# Bus Interface Signal Analysis

Analyze bus interface Verilog/SystemVerilog port declarations from images and present them as documentation-ready tables.

## Trigger

User sends an image of Verilog/SV port declarations with signal names, directions, and bit widths. Typically from bus interface modules (AXI, AHB-Lite, ICB, APB). Phrases like "帮我分析这些信号", "一样的处理", or sending consecutive interface images.

## Workflow

### Step 1 — Extract Ports

Use `vision_analyze` to read each line from the image: direction (`input`/`output`), bit width `[N:M]`, and signal name. If no bracket, signal is 1-bit.

### Step 2 — Cross-Check with Known Bus Protocols

The vision model (Qwen3-VL) is unreliable for code screenshots. Cross-reference extracted signals against known bus protocol specs. Common hallucinations to correct:

| Vision Output | Likely Truth | Bus |
|---------------|-------------|-----|
| `input [63:0] wvalid` | `input [63:0] wdata` + `input wvalid` | AXI |
| `input [7:0] wlast` | `input wlast` | AXI |
| `output [1:0] bvalid` | `output bvalid` + `output [1:0] bresp` | AXI |
| Extra signals from known pattern | Hallucination, omit | Any |

When uncertain, flag the anomaly but present the spec-correct interpretation.

### Step 3 — Group by Channel

Group signals by their bus channel:

- **AXI**: AW (write addr), W (write data), B (write response), AR (read addr), R (read data)
- **ICB**: cmd (request), rsp (response)
- **AHB-Lite**: single channel (address + data phases share signals)
- **APB**: single channel

Present each channel as a separate sub-table with a label heading.

### Step 4 — Format Table

Column order: `信号` | `方向` | `位宽` | `说明`

**Direction MUST use M→S / S→M — NEVER input/output.** Reason: `input`/`output` is relative to the current module and meaningless to someone reading the bus fabric documentation. M→S / S→M is the absolute bus direction.

Mapping (when module is the slave side, `i_` prefix convention):
- `input` → M→S (Master drives this into the slave module)
- `output` → S→M (Slave drives this out to the master)

If the module is the master side (less common), swap. Apply bus-protocol knowledge to get it right.

### Step 5 — Write Descriptions (Spec-Style English)

Descriptions go in the `说明` column. Rules:
- **Concise, table-cell friendly**: short phrases, not full sentences
- **No articles (a/an)**: per Nuclei documentation convention
- **Use → for sequences**: `Read → Modify → Write back`
- **Signal names in monospace**: `` `araddr` ``
- **Encoding tables inline**: `0 = OKAY, 1 = EXOKAY, 2 = SLVERR, 3 = DECERR`
- **Standard bus terminology**: Use the terms from AMBA / bus protocol specs

For more detail on prose style, see `spec-trans` skill.

### Step 6 — Add Summary

After all tables, add a compact config summary:

| Parameter | Value |
|-----------|-------|
| Data width | 64b |
| Address width | 32b |
| ID width | 4b (16 outstanding) |
| Protocol | AXI4 Full |
| Total signals | ~37 |

## Direction Rules (Critical)

```
input/output  →  fab 里面看不出什么  →  USE M→S / S→M
```

- **M→S**: Master drives, Slave receives. AW/AR/W channel payload + valid, B/R ready.
- **S→M**: Slave drives, Master receives. AW/AR/W ready, B/R channel payload + valid.

Valid/Ready direction is per-channel:
- `*valid` goes with the payload direction
- `*ready` goes opposite to the payload direction

## Reference Documents for Bus Protocols

| Bus | Document | Key Specs |
|-----|----------|-----------|
| AXI4 Full | ARM IHI 0022 | 5 channels, Burst, ID, Out-of-Order |
| AHB-Lite | ARM IHI 0033 | Single channel, pipelined addr/data, no arbitration |
| APB | ARM IHI 0024 | Simple, no pipeline, low power |
| ICB | Nuclei internal | 2 channels (cmd+rsp), simplified AXI-like, no burst (basic) |

## OCR-First Extraction (tesseract) & Description Depth

When the source is a code screenshot, prefer **tesseract OCR** over vision models —
4× LANCZOS upscale + grayscale + threshold, `--psm 6` (cross-check `--psm 4`); use
`vision_analyze` only as a fallback and ALWAYS cross-validate. See
`references/bus-signal-table-workflow.md` for the full workflow, the complete
AXI4/AHB-Lite/ICB signal description quick-reference, and EDC (`_p`/`_edc`/`_hi`/`_lo`)
signal patterns.

Description depth — the user's tolerance window:
- Too short ("Request valid") → pushback; too Fab-heavy ("Fab forwards to
  downstream") → rejected.
- **Target**: protocol-level — "Indicates master is driving valid write address and
  control." Describe the signal, not the system's reaction to it.
- Global/clock/reset signals (`clk`, `rst_n`, per-channel `*_clk`) use `in`/`out`
  and live in separate "Global Signals" / "Channel Clock and Reset" tables.
- Signal ordering must exactly match the source image; column order is
  Signal | Dir | Width | Description (user preference).

## Pitfalls

- **Never use `input`/`output` in tables**: User explicitly rejected this. "input output 到 fab 里面看不出什么"
- **Vision model hallucinates signal names and widths**: Always cross-reference with known bus protocol specs. Qwen3-VL in particular confuses `wvalid`↔`wdata`, `wlast` width, `bvalid`↔`bresp`.
- **Direction mapping is protocol-dependent**: For the same module, AWREADY is S→M but AWVALID is M→S. Check the protocol, don't just map `input`→M→S blindly for every signal.
- **Column order matters**: Direction before bit width (`方向` → `位宽`). The user explicitly swapped these from the default order.
- **`i_` prefix in Nuclei codebase**: Signals like `i_axi_awvalid` use the `i_` prefix for slave-side module ports. The module receives master-driven signals as inputs and drives response signals as outputs.

## References

- `references/bus-signal-reference.md` — Signal tables for AXI4, AHB-Lite, ICB, APB with bit widths, directions, and descriptions.
