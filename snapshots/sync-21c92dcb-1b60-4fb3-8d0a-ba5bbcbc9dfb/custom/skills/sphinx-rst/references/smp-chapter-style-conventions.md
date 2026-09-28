# SMP Chapter Content-Style Conventions (Nuclei databook)

Learned while authoring the SMP feature chapter (Cluster Cache / CLM / IOCP
sections, 2026-08). These are the user's explicit style corrections for
prose content in databook sections — apply BEFORE translating.

## No Concept/Configuration section keywords

User: "我觉得不需要写 concept，configuration 这些关键词" — do NOT insert
English-style subsection keywords (`Concept`, `Configuration`, `Overview`)
when organizing a long section. Use flowing paragraphs with natural
transitions, not labeled mini-headings.

## No "1. 短语：描述" phrase+colon format

User: "不要先总结一个短语，再使用 :，直接一段话就 ok" — for
notes/注意事项/特性 content, write coherent paragraphs, one point per
paragraph. Do NOT use `1. Phrase: description` structure. Exception: the
user explicitly requested verb-first numbered steps for the pipeline
mechanism section (see next).

## Verb-first numbered steps (approved style)

User: "之前流水线哪块的内容风格就很符合我的需求" — when a mechanism is
best shown as steps, use numbered items each STARTING WITH A VERB PHRASE
(接收 / 发起访问 / 并行接收 / 反馈释放 / 周而复始 → Reception / Access
initiation / Parallel reception / Response and release / Iteration).
Each step is one short sentence; total 4–6 steps; compress aggressively
(drop scenario description, waveform detail, implementation extras).

## "先执行" vs "执行"

Do not add 先 (first) without a genuine sequencing contrast. E.g. partial
write: "需执行 Read-Modify-Write" — NOT "需先执行". The user corrected this
verbatim. 先 is only for real ordering emphasis.

## No examples in body text

Continuation of the 5.3 rule (正文纯规则/公式，零例子): CLM/IOCP content
sections repeatedly got "不需要例子". Examples (waveforms, address samples)
are carried by user-drawn figures or omitted; prose states rules/formulas
only. Exceptions only when the example IS the semantic (e.g. device
attribute → AxCache value mapping).

## Section-title style (IOCP chapter)

`<Component> <Noun Phrase>` family: `IOCP Line Buffer Mechanism`,
`IOCP Read and Write Operations`, `IOCP Outstanding`, `IOCP Write
Streaming`, `IOCP Prefetch`, `IOCP Transfer Support`, `IOCP Usage Notes`.
Out-of-order (乱序) must NOT appear in a title — mention it only in content
(strongly related to Outstanding but user split it out).
