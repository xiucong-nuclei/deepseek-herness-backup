# Reusable section lead-in intros (Nuclei databook)

Section intros must LEAD INTO the table, not summarize its data. Pattern: one sentence
naming what the extension provides + "The following table lists the execute latency and
throughput of each X instruction." Keep to 1-2 sentences. No a/an, active voice (spec style).

## Standard extension sets (concrete, copy-adapt)

- **RV32I**: The RV32I base integer instruction set covers integer arithmetic, logical,
  load, store, and control-flow instructions. The following table lists the execute
  latency and throughput of each RV32I instruction.
- **RV32M**: The RV32M extension adds integer multiply and divide instructions. The
  following table lists the execute latency and throughput of each RV32M instruction.
- **RV32A**: The RV32A extension adds atomic instructions, including load-reserved,
  store-conditional, and read-modify-write operations. The following table lists the
  execute latency and throughput of each RV32A instruction.
- **RVC**: The RV32C extension provides 16-bit compressed instructions that reduce code
  size. The following table lists the execute latency and throughput of each compressed
  instruction.
- **RV32F**: The RV32F extension adds single-precision floating-point instructions. The
  following table lists the execute latency and throughput of each RV32F instruction.
  The Functional Unit column identifies the executing unit, `FSIM` or `FMIS`.
  (column-meaning sentence is structural, acceptable.)
- **RV32D**: The RV32D extension adds double-precision floating-point instructions. The
  following table lists the execute latency and throughput of each RV32D instruction.
- **RV32_ZFH**: The RV32_ZFH extension adds half-precision floating-point instructions,
  including conversions to and from integer and between half, single, and double
  precision. The following table lists the execute latency and throughput of each
  half-precision floating-point instruction.
- **P (DSP)**: The P extension adds DSP and SIMD instructions for 8-bit, 16-bit, and
  32-bit sub-word arithmetic, comparison, saturation, packing, and 64-bit operations.
  The following table lists the execute latency and throughput of each P DSP instruction.
- **P (DSP) Custom**: The custom DSP instructions extend the P extension with additional
  sub-word operations. The following table lists the execute latency and throughput of
  each custom DSP instruction.
- **B**: The B extension adds bit-manipulation instructions for shifts, bit-field
  operations, counting, and carry-less multiply. The following table lists the execute
  latency and throughput of each B-extension instruction.
- **K**: The K extension adds cryptography instructions, including AES, SHA-256,
  SHA-512, SM3, and SM4. The following table lists the execute latency and throughput
  of each K-extension instruction.
- **Zc (Zcb/Zcmp/Zcmt)**: The Zc extension provides code-size-reduction instructions.
  The following tables list the execute latency and throughput of the `Zcb`, `Zcmp`,
  and `Zcmt` instructions.
- **XLCZ**: The XLCZ extension adds custom load, store, MAC, bit-manipulation, and
  branch instructions. The following table lists the execute latency and throughput of
  each XLCZ instruction.

## Lead-in phrasing options for the pointer sentence

- "The following table lists the execute latency and throughput of each X instruction."
- "The following tables list the ... of the `Zcb`, `Zcmp`, and `Zcmt` instructions."
- Use the ending pointer form (spec-trans convention) for images/figures:
  "... as shown in the table below." (sentence-final).

## Anti-patterns (do NOT do these)

- Restating numeric data: "FDIV.S executes in 16 to 19 cycles", "loads take 2 cycles",
  "MUL takes 1 or 2 cycles" — this duplicates the table.
- Enumerating every instruction's latency in prose.
- Anything longer than ~2 sentences; the intro is a lead-in, not a summary.
