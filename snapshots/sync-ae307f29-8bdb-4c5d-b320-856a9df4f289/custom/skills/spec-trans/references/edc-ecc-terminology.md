# Bus Fabric EDC / ECC / Protection Code Terminology

Bus Fabric data integrity concepts encountered during N300 specification translation.

## EDC (Error Detection Code)

- **Detection only** — no correction capability.
- 6 bits of protection code per 32-bit data.
- Detects 1-bit and 2-bit errors.
- Stateless: generated per independent 32-bit slice, survives Bus Fab width conversion without regeneration.
- Contrast: ECC must be regenerated when data width changes (e.g. 64-bit → 32-bit splitting).

## ECC (Error Correction Code)

- Detection + correction (typically 1-bit correct, 2-bit detect).
- Correction depends on total data width → width conversion breaks ECC → must regenerate.
- Drawback in Bus Fab: Bus Fab minimum 32-bit width, but ECC at wider widths forces regeneration at width conversion nodes.

## On-the-Fly Correction

- Hardware corrects flipped bits transparently during the same bus transaction.
- Receiver sees correct data, no awareness of the error.
- Zero added latency.
- Contrast: detect-only → report busecc error → upper layer (software/exception handler) decides.

## Protection Code Sizing

- 32-bit data → 6 bits EDC protection code (1-bit + 2-bit error detection).
- Generically: hamming-distance-based encoding determines code width for given detection/correction target.
- EDC code carried alongside data on bus channels (Cmd Channel for wdata, Rsp Channel for rdata).

## Bus Fab EDC Flow

1. **Master Cmd Channel**: generates EDC for wdata → Slave checks → EDC error → busecc error.
2. **Slave Rsp Channel**: generates EDC for rdata → Master checks → EDC error → busecc error.
3. **Attribute/Addr signals**: also EDC-protected (or parity) at each node. Checked before use.
4. **Error injection**: CSR-controlled at each EDC-checking node, for testing busecc error detection logic.

## Translation Mapping

| Chinese | English |
|---------|---------|
| EDC 检查 | EDC checking |
| ECC 校验/检查 | ECC checking |
| busecc error | busecc error (literal) |
| 注错 | error injection |
| on-the-fly 纠错 | on-the-fly correction |
| protection code | protection code |
| 检错 | error detection |
| 纠错 | error correction |
| 信号真实可靠 | signal integrity |
| 重生成 | regenerate / regeneration |
