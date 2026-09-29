# Nuclei SDK benchmark projects: source file sets & duplicate-symbol cases

Each Nuclei benchmark owns its own `main()` and timing helpers. Compiling two
benchmark source sets into one project (or leaving the SDK template `main.c`
in) produces `multiple definition of 'main'` / `time` / `Proc_*` / globals at
link time. The linker error's two object files name the conflict directly:
`./application/X.o` vs `./application/Y.o` — read those, not the reported
source line.

## File ownership per benchmark (jinghui_* projects, NucleiStudio)

CoreMark  — entry in core_main.c (main at ~line 112). SDK template main.c is an
            EMPTY placeholder (`int main(void){return 0;}`) — delete it, or
            remove it from the build. Keep: core_main.c core_list_join.c
            core_matrix.c core_portme.c core_state.c core_util.c coremark.h
Dhrystone — two interchangeable packagings of the SAME benchmark:
            A) dhry_1.c + dhry_2.c + dhry_stubs.c + strcmp_xlcz.S + dhry.h
               (Nuclei SDK standard layout; dhry_stubs.c = csr_cycle/instret/
               reset + long time(); strcmp_xlcz.S = optimized strcmp)
            B) dry.c + dry_pass2.c (single-file 2.2 variant split by PASS2
               macro: dry.c = main+globals+Proc_1..5, dry_pass2.c =
               Proc_6..8+Func_1..3)
            Compiling A AND B together → every symbol doubles. Keep ONE set.
Whetstone — whets.c (main) + cpuidc.c (SPDP time()/start_time/end_time) +
            config.h (SPDP=double for lp64d) + cpuidh.h. If dhry_*.c files
            leaked in, they bring a second main (dhry_1.c) AND a second
            `time` (dhry_stubs.c long time) → two link errors at once.

## Concrete cases (all resolved by removing the wrong set)

1. jinghui_coremark: main.c:6 vs core_main.c:113 both define main.
   Fix: drop the template main.c.
2. jinghui_dhrystone: dry.o vs dhry_1.o (main, Proc_1..5, all globals) and
   dry_pass2.o vs dhry_2.o (Proc_6..8, Func_1..3). Fix: drop dry.c +
   dry_pass2.c, keep the dhry_1/dhry_2/stubs/strcmp_xlcz set.
3. jinghui_whetstone: whets.o main vs dhry_1.o main; cpuidc.o `time` vs
   dhry_stubs.o `time`. Fix: drop all dhry_* files, keep whets/cpuidc.

## Pitfall: ld location attribution points at a header, not the real conflict

When the duplicated symbol is a thin wrapper around a header inline — e.g. both
`time()` bodies call `SysTimer_GetLoadValue()` (NMSIS core_feature_timer.h) —
ld reports:
    ./application/dhry_stubs.o: in function `SysTimer_GetLoadValue':
        core_feature_timer.h:193: multiple definition of `time'
The header line is the INLINE body's location (symbols attributed to the
inlined function's definition site), NOT where the duplicate lives. The real
conflict is the two global definitions in the .c files. Ignore the line
number; trust the two object files.

## Fix mechanics

- NucleiStudio: right-click file → Resource Configurations → Exclude from Build
  (or delete from project; keep the file on disk).
- Makefile: remove the .c/.S from the SRCS list (link rule is usually
  makefile:<line>: <proj>.elf).
- Then rebuild; the benchmark's own main/time survive intact.
