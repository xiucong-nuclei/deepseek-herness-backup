# Databook feature subsection — Lockstep/Split Local Memory (2026-08 session)

User corrections for writing a databook feature subsection (lockstep/split local
memory). These are durable style/workflow rules; fold the SKILL.md bullets into
a foreground session if needed (background curator SKILL.md patch is blocked by
read-before-write guard).

## Rule 1 — Narrow the scope; don't restate covered background

When a feature (lockstep/split, safety, etc.) has its mode/mechanism introduced
in an upstream section, this subsection covers ONLY its own specific aspect
(e.g. how local memory is allocated/accessed), NOT the mechanism again.

> User: "这里主要是介绍 lockstep 和 split 模式下 local memory 的特性，别的地方
> 已经介绍了 lockstep 模式 和 split 模式。"

So: do NOT repeat "two cores execute same instructions, compare results to
detect fault", nor the software `split_en` switch description — those live in
the lockstep/split mode sections. Confirm the intended coverage before writing.

## Rule 2 — One continuous section; do NOT auto-split into sub-subsections

> User: "我不想分 Lockstep mode 和 split mode 两个小节，写到一块就行。"

Write both modes as natural flow paragraphs in ONE section — lockstep one
sentence/paragraph, split one paragraph. Do not create `Lockstep Mode` /
`Split Mode` sub-headings unless the user asks.

## Rule 3 — Formal wording; avoid colloquial "1 unit"

"1 unit" is colloquial. When "2 units = full capacity", use formal written
phrasing:

- `the full ILM and DLM capacity` (lockstep master access)
- `half of the ILM capacity and half of the DLM capacity` (split, per core)
- `two times the configured capacity` (SRAM physical size)
- address range: `the full ILM and DLM address range` / `the upper half`

Corresponds to Chinese "1 单位的 ILM/DLM".

## Accepted final shape (this topic)

1. One-line scoping opener: `For CPU executing ASIL-D:`
2. Physical SRAM size sentence (shared, sized 2x configured).
3. Lockstep paragraph: master uses the full ILM/DLM capacity.
4. Split paragraph: each core gets half; cores still decode the full address
   range; access to the upper half not backed by valid SRAM —
   - write access is ignored;
   - read access returns an unspecified value.
   Do not access the upper half; accessing it causes erroneous behavior.
5. NOTE: set ILM/DLM base addresses so each region reserves the full two-part
   space and does not overlap other address regions.

## Illustration guidance

Focus on the memory/address-map figure (this is the mechanism), not a
re-rounded block diagram (modes already drawn elsewhere):

- Recommended: dual-mode memory/address map — ILM & DLM rows, each with lower
  (unit0) + upper (unit1) cells; lockstep = both cells solid "master full
  access"; split = lower cell solid "assigned to this core", upper cell hatched
  amber = "not backed by SRAM — read random / write ignore".
- Legend: solid = valid SRAM; hatched = no valid SRAM backing (read
  unspecified / write ignored).
- Optional: physical shared-SRAM side view — lockstep master takes all, split
  halves to two cores.