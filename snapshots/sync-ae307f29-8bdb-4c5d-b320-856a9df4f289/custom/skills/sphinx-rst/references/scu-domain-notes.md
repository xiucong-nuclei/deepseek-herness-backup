# SCU Domain Notes (Nuclei SMP feature)

Confirmed user-provided domain facts about the SCU (Snoop Control Unit) for the
SMP feature chapter. The chapter content is **in-draft / unconfirmed** — the section
structure (title, "several approaches" comparison) was proposed but not yet approved
by the user. Only the technical facts below are settled.

## SCU role (confirmed)

SCU (Snoop Control Unit) is the **coherency point in an SMP cluster**. It maintains
cache coherency among the L1 data caches of the cores, snoops each core's coherent
requests, and routes requests that miss in the local caches to the shared Cluster Cache.

Concise intro the user asked for (43 words → 34): "The SCU (Snoop Control Unit) is the
coherency point in an SMP cluster. It maintains coherency among the cores' L1 data
caches, snoops coherent requests, and routes cache misses to the shared Cluster Cache."
(Compression: `...of the L1 data caches of the cores` → `among the cores' L1 data
caches`; `the requests that miss in the local caches` → `cache misses`.)

## SCU implementation — shadow data tag (confirmed user fact)

There are several ways to implement the SCU. Nuclei's chosen scheme keeps a
**shadow data tag** in the SCU: when a core updates its data tag, the shadow data tag
in the SCU is updated **synchronously**. On a coherent request, the SCU checks the
shadow tag (instead of hitting each core's data-tag RAM) to determine address
ownership without disturbing the cores.

## Icache-snoop-Dcache mechanism (confirmed)

Icache miss → external fetch request → SCU. SCU snoops whether the Dcache holds the
address:
- Hit → data returned to Icache directly, **Cluster Cache not accessed**.
- Miss → request forwarded to Cluster Cache.
Software-gated by `I_SNOOP_D_EN` in the `CC_CTRL` register (SMP config).

## Style note (from the related SCU draft, user's conventions)

SCU intro and mechanism follow the SMP chapter prose conventions: flowing paragraphs,
no "Concept/Configuration/Overview" keyword headings, verb-first numbered steps for the
mechanism flow, `.. note::` for the software-gate (`CC_CTRL.I_SNOOP_D_EN`). See
`smp-chapter-style-conventions.md` for the full prose rules.
