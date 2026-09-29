# Table Lead-in & Conclusion Sentences (Nuclei databook)

Learned while authoring the SMP feature chapter (CLM / IOCP sections,
2026-08). Complements `table-title-conventions.md`.

## Data/mapping tables: wrap with lead-in + conclusion

For data/mapping tables (not register-config lists), the user explicitly
wants a **lead-in sentence before** AND a **conclusion sentence after** the
table:

- Lead-in points at the table:
  - 中文: `...分三种情况，见下表`
  - EN: `... in three cases, as shown in the table below.`
- Conclusion draws the takeaway and any recommendation:
  - 中文: `由表可见，恰好一个 Cacheline 的 Burst 对 Entry 利用率最高；因此...推荐...`
  - EN: `As the table shows, ... Therefore, ... is recommended.`

User request verbatim: "这句话加上一些对表的描述，放在表前或表后很合适"
(also phrased as "加上一些对表的描述"). So when prose contains a table,
wrap it: pointing sentence before, "由表可见 / As the table shows" conclusion
after.

## Register-config tables: lead-in only

The simpler register list-table form keeps lead-in only (e.g.
`Related register configuration:`) — no conclusion sentence needed there.
Distinguish the two cases: data/mapping tables get the full wrap;
register lists get just the lead-in.
