# Case Study: N900 ecall Trap Cascade (Nuclei N900)

## Symptoms

Software executing on Nuclei N900 (dual-issue, CLIC interrupt controller):

1. `ecall` triggered intentionally (`mcause=9` — S-mode environment call)
2. Followed by **continuous** `mcause=2` (illegal instruction) exceptions
3. iaddr jumps but never exits trap handler — infinite loop of mcause=2

## Root Cause

**`mtvec` not yet initialized** when `ecall` executed.

The code sequence:
```asm
# ecall intended to enter M-mode
loop_finish0:
    ecall                   # @ 0x80000ab2  ← S-mode ecall
```

But `ECLIC_Interrupt_Init()` (which sets `mtvec`) runs **after** BSS clear and after the code path containing `ecall`:
```
Reset vector
  → BSS clear                  ← ecall here
  → _init()
      → ECLIC_Interrupt_Init()  ← mtvec set here (too late)
```

Since `mtvec` defaults to 0 at reset:
```
ecall → PC = mtvec.BASE = 0x00000000
       → fetch 0x00000000 from address 0 → mcause=2
       → PC = 0 again → infinite mcause=2 loop
```

## Trap Handler Setup Code (Nuclei SDK)

```c
void ECLIC_Interrupt_Init(void) {
    // ...
    __RV_CSR_WRITE(CSR_MTVT, (unsigned long)vector_base);
    __RV_CSR_WRITE(CSR_MTVEI, (unsigned long)irq_entry | 0x1);
    __RV_CSR_WRITE(CSR_MTVEC, (unsigned long)exc_entry | 0x3);
    // 0x3 → MODE = CLIC vectored

#ifdef __SMODE_PRESENT
    if (csr_val & (1 << 18)) {  // S-mode present in MISA
        __RV_CSR_WRITE(CSR_STVT, (unsigned long)vector_table_s);
        __RV_CSR_WRITE(CSR_STVT2, (unsigned long)irq_entry_s);
        __RV_CSR_WRITE(CSR_STVEC, (unsigned long)exc_entry_s);
    }
#endif
}
```

### MTVEC Mode Bits

```c
// The la + addi + ori sequence:
la a1, ecall_handler_smode    // a1 = 0x80000a4a (handler address)
addi a1, a1, 66               // a1 = 0x80000a4a
ori a1, a1, 3                 // a1 = 0x80000a4b (set MODE=11)
csrrw zero, mtvec, a1         // mtvec = 0x80000a4b

// mtvec breakdown:
//   BASE = 0x80000a48 (handler at exc_entry)
//   MODE = 0x3 (CLIC vectored)
```

Note: `ori a1, a1, 3` ORs with binary **0b11** (= decimal 3), setting **both** low bits to 1. The MODE field becomes `11` (CLIC vectored mode), correctly.

## Key Debug Signals

| Signal | Value | Interpretation |
|---|---|---|
| `mcause` | 9 → 2 → 2 → 2 → ... | ecall cascade confirmed |
| `mepc` | 0x80000ab2 | ecall instruction address (origin confirmed) |
| `mtvec` | 0 | Not initialized (root cause) |
| `mtval` | 0 for mcause=9; instruction encoding for mcause=2 | Confirms mcause=2 from fetching 0x00000000 |

## Fix

**Option A**: Move `ecall` after `ECLIC_Interrupt_Init()` — ensure `mtvec` is set first.

**Option B**: Add early trap init before any ecall:
```c
void early_trap_init(void) {
    __RV_CSR_WRITE(CSR_MTVEC, (unsigned long)early_handler | 0x3);
}
```

**Option C**: For bare-metal test programs, ensure the core stays in M-mode (don't switch to S-mode) if S-mode is not needed.

## Related Hardware Detail

ecall cannot skip `mtvec` jump — it's architecturally mandatory in RISC-V:

```
ecall → mepc ← current PC
      → mcause ← 9 or 11
      → privilege ← M-mode
      → PC ← mtvec.BASE     ← ALWAYS happens
```

There is no configuration bit to make ecall fall through to the next instruction.
