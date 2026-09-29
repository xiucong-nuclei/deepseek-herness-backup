# Nuclei Databook Table Authoring Conventions

Learned while authoring the SMP feature chapter (Cluster Cache / CLM / IOCP
sections, 2026-08). Applies to Sphinx/RST tables in Nuclei BSD-style docs.

## Table-title convention: `The <Name> of <Component>`

Use noun-phrase titles in the `The <Name> of <Component>` family, applied
consistently across a chapter:

- Mapping tables → `The <X> of <Y>`:
  - `The Burst-to-Entry Mapping of IOCP` (Burst 到 Entry 映射表)
  - support matrices → `... Support by ...` (e.g. `Memory Interface Type
    Support by N300 CPU Type`)
- Keep the whole title family consistent; don't mix styles within one doc.
- Set both the English caption and the `:name:` label (label convention in
  `figures-and-images.md`).

## Register-config sections → three-column table

When a section lists register bit-fields / thresholds / timeouts (e.g. the
IOCP Write-Streaming / Prefetch configs: `STM_CTRL`, `STM_CFG`, `STM_TIMEOUT`),
prefer a column table over a bullet list:

```rst
.. list-table:: Related register configuration
   :name: iocp-write-streaming-cfg
   :header-rows: 1

   * - Register
     - Field
     - Description
   * - ``STM_CTRL``
     - bit1
     - Enables the write-streaming feature
   * - ``STM_CFG``
     - [29:20]
     - Write-streaming training threshold; triggered when the bytes of
       consecutive writes reach this value
   * - ``STM_TIMEOUT``
     - [10:0]
     - Write-streaming timeout; if no data within the same cache line is
       received within the configured time, the IOCP stops waiting and sends
       the received data
```

Guidelines:
- Columns: Register | Field | Description.
- Lead-in sentence before the table (`Related register configuration:`),
  no redundant summary after.
- Register names / bit-ranges in inline code monospace (`` `` ``STM_CTRL`` `` ``).
- Keep each Description to one non-breaking clause; split long defs at the
  logical break (threshold → trigger; timeout → fallback action).