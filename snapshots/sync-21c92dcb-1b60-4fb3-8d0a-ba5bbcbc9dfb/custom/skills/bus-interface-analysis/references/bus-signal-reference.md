# Bus Signal Quick Reference

## AXI4 Full (Standard)

### Write Address (AW) — M→S unless noted

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| AWID | ID_W | M→S | Transaction ID |
| AWADDR | ADDR_W | M→S | Write address |
| AWLEN | 8 | M→S | Burst length (beats − 1) |
| AWSIZE | 3 | M→S | Bytes per beat: 0=1B, 1=2B, 2=4B, 3=8B, 4=16B... |
| AWBURST | 2 | M→S | 00=FIXED, 01=INCR, 10=WRAP |
| AWLOCK | 1 | M→S | Atomic lock |
| AWCACHE | 4 | M→S | Cache attribute |
| AWPROT | 3 | M→S | Protection: [2]=data/inst, [1]=privileged, [0]=secure |
| AWVALID | 1 | M→S | Handshake Valid |
| AWREADY | 1 | S→M | Handshake Ready |

### Write Data (W) — M→S unless noted

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| WDATA | DATA_W | M→S | Write data |
| WSTRB | DATA_W/8 | M→S | Byte write strobe (1 bit per byte) |
| WLAST | 1 | M→S | Last beat of burst |
| WVALID | 1 | M→S | Handshake Valid |
| WREADY | 1 | S→M | Handshake Ready |

### Write Response (B) — S→M unless noted

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| BID | ID_W | S→M | Transaction ID echo |
| BRESP | 2 | S→M | 00=OKAY, 01=EXOKAY, 10=SLVERR, 11=DECERR |
| BVALID | 1 | S→M | Handshake Valid |
| BREADY | 1 | M→S | Handshake Ready |

### Read Address (AR) — M→S unless noted

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| ARID | ID_W | M→S | Transaction ID |
| ARADDR | ADDR_W | M→S | Read address |
| ARLEN | 8 | M→S | Burst length |
| ARSIZE | 3 | M→S | Bytes per beat |
| ARBURST | 2 | M→S | Burst type |
| ARLOCK | 1 | M→S | Atomic lock |
| ARCACHE | 4 | M→S | Cache attribute |
| ARPROT | 3 | M→S | Protection |
| ARVALID | 1 | M→S | Handshake Valid |
| ARREADY | 1 | S→M | Handshake Ready |

### Read Data (R) — S→M unless noted

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| RID | ID_W | S→M | Transaction ID echo |
| RDATA | DATA_W | S→M | Read data |
| RRESP | 2 | S→M | Response status |
| RLAST | 1 | S→M | Last beat of burst |
| RVALID | 1 | S→M | Handshake Valid |
| RREADY | 1 | M→S | Handshake Ready |

### AXI Optional Sideband

| Signal | Channels | Typical Width |
|--------|----------|---------------|
| AxUSER | AW/AR/W/B/R | configurable |
| AxQOS | AW/AR | 4 |
| AxREGION | AW/AR | 4 |

---

## AHB-Lite (AMBA 3)

Single channel, pipelined address/data phases.

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| HADDR | 32 | M→S | Byte address |
| HTRANS | 2 | M→S | 00=IDLE, 01=BUSY, 10=NONSEQ, 11=SEQ |
| HWRITE | 1 | M→S | 1=write, 0=read |
| HSIZE | 3 | M→S | 000=8b, 001=16b, 010=32b, 011=64b |
| HBURST | 3 | M→S | 000=SINGLE, 001=INCR, 010=WRAP4, 011=INCR4, 100=WRAP8, 101=INCR8, 110=WRAP16, 111=INCR16 |
| HPROT | 4 | M→S | Protection control |
| HMASTLOCK | 1 | M→S | Locked transfer |
| HWDATA | DATA_W | M→S | Write data |
| HRDATA | DATA_W | S→M | Read data |
| HRESP | 1 | S→M | 0=OKAY, 1=ERROR |
| HREADYOUT | 1 | S→M | Transfer done from slave |
| HREADY | 1 | M→S | Transfer done (interconnect-combined) |

AHB-Lite is single-master: no HBUSREQ/HGRANT. No split/retry (HRESP only OKAY/ERROR, no SPLIT/RETRY).

---

## ICB (Nuclei Internal Chip Bus)

2-channel simplified protocol. Basic mode: no burst, no ID, no out-of-order.

### Command (cmd) — M→S unless noted

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| cmd_valid | 1 | M→S | Handshake Valid |
| cmd_ready | 1 | S→M | Handshake Ready |
| cmd_read | 1 | M→S | 1=read, 0=write |
| cmd_addr | ADDR_W | M→S | Byte address |
| cmd_wdata | DATA_W | M→S | Write data |
| cmd_wmask | DATA_W/8 | M→S | Byte write strobe |
| cmd_size | 3 | M→S | 0=8b, 1=16b, 2=32b, 3=64b... |

### Response (rsp) — S→M unless noted

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| rsp_valid | 1 | S→M | Handshake Valid |
| rsp_ready | 1 | M→S | Handshake Ready |
| rsp_rdata | DATA_W | S→M | Read data |
| rsp_err | 1 | S→M | Error flag |

### ICB Extended (with burst/exclusive)

Additional signals beyond basic:

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| cmd_sel | 1 | M→S | Region select |
| cmd_lock | 1 | M→S | Locked (atomic) access flag |
| cmd_excl | 1 | M→S | Exclusive access flag |
| cmd_xlen | 8 | M→S | Burst length (beats − 1) |
| cmd_xburst | 2 | M→S | Burst type |
| cmd_modes | 1 | M→S | Privilege mode |
| cmd_dmode | 1 | M→S | Debug mode |
| cmd_attri | 3 | M→S | Memory attribute |
| cmd_beat | 2 | M→S | Current beat index |
| rsp_excl_ok | 1 | S→M | Exclusive access success |

---

## Vision Model Hallucination Patterns

When using vision_analyze on Verilog code screenshots, Qwen3-VL frequently:

1. **Swaps wvalid ↔ wdata**: Reports `input [63:0] i_axi_wvalid` — should be `input [63:0] i_axi_wdata` + `input i_axi_wvalid`
2. **Wrong wlast width**: Reports `input [7:0] i_axi_wlast` — should be `input i_axi_wlast` (1-bit)
3. **Swaps bvalid ↔ bresp**: Reports `output [1:0] i_axi_bvalid` — should be `output i_axi_bvalid` + `output [1:0] i_axi_bresp`
4. **Omits nearby signals**: Adjacent signals on same line may be missed
5. **Hallucinates missing signals**: Adds signals that aren't in the image (e.g., hburst when not present)

**Always cross-reference with the protocol spec tables above before presenting results.**
