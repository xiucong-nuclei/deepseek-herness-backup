# AMO Intrinsic Type Portability: `long *` Trap

## Problem

AMO (Atomic Memory Operation) intrinsics like `__AMOSWAP_W`, `__AMOADD_W` etc. in Nuclei SDK
expect `volatile uint32_t *` / `volatile int32_t *` for `_W` (word) variants and
`volatile uint64_t *` / `volatile int64_t *` for `_D` (doubleword) variants.

Using `long *` or `unsigned long *` works on RV32 (where `long` = 32-bit) but **fails on RV64**
(where `long` = 64-bit) with:

```
error: passing argument 1 of '__AMOSWAP_W' from incompatible pointer type
  [-Wincompatible-pointer-types]
note: expected 'volatile uint32_t *' but argument is of type 'long int *'
```

## Root Cause

| Architecture | `sizeof(long)` | `sizeof(int32_t)` | Match? |
|---|---|---|---|
| RV32 (N300) | 4 | 4 | ✅ |
| RV64 (N900) | 4 | 8 | ❌ |

## Fix

Replace all `long *` / `unsigned long *` with `stdint.h` exact-width types:

```c
// ❌ Non-portable — breaks on RV64
long *addr;
unsigned long *uaddr;

// ✅ Portable — works on both RV32 and RV64
int32_t  *addr;       // for all _W AMO functions
uint32_t *uaddr;      // for unsigned _W functions (__AMOMAXU_W etc.)
#if __riscv_xlen == 64
int64_t  *addr64;     // for all _D AMO functions
uint64_t *uaddr64;    // for unsigned _D functions (__AMOMAXU_D etc.)
#endif
```

Then call accordingly:

```c
// 32-bit AMO (always available)
data = __AMOSWAP_W(addr, 0x12345678);    // addr is int32_t *
udata = __AMOMAXU_W(uaddr, 0x98654321U); // uaddr is uint32_t *

// 64-bit AMO (RV64 only, guarded by #if)
#if __riscv_xlen == 64
data = __AMOSWAP_D(addr64, 0x12345678);   // addr64 is int64_t *
udata = __AMOMAXU_D(uaddr64, 0x98654321U);// uaddr64 is uint64_t *
#endif
```

## Why the SDK Uses `int32_t *` (Not `long *`)

The AMO function declarations in `core_feature_base.h` use `volatile uint32_t *` / `volatile int32_t *`
precisely to guarantee portability across XLEN. The AMO.W instruction always operates on 32-bit words
regardless of whether the core is RV32 or RV64 — so the pointer type must be 32-bit on both.
