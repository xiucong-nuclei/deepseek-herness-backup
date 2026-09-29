# Sphinx Figures & Image References

How to embed figures and reference them from prose in Sphinx/RST docs
(learned while authoring the Nuclei SMP feature chapter, 2026-08).

## Embedding a figure with caption

```rst
.. figure:: ../figures/fig_clm_reset_arch.svg
   :name: fig-clm-reset-arch
   :align: center

   Reset Signal Propagation Architecture
```

- Path is relative to the current `.rst` file; keep figures in a shared
  `../figures/` dir.
- `:name:` = unique figure ID, REQUIRED for referencing from prose.
- The indented text below the directive = caption (figure title).
- SVG figures work directly; PNG also fine.

## Referencing figures from prose

| Role | Requirement | Renders as |
|---|---|---|
| `:numref:`fig-clm-reset-arch`` | `numfig = True` in conf.py | "Figure 5.1" (auto-numbered, clickable, renumbers on reorder) |
| `:ref:`fig-clm-reset-arch`` | none | the full caption text as link |

Rules:
- Backticks must touch the role: `:numref:`fig-x`` (no space).
- Put figure references at sentence END in spec docs:
  `... as shown in :numref:`fig-x`.`
- If `numfig` is not enabled, `:numref:` renders the literal label —
  fall back to `:ref:`.

## Inline image without caption

```rst
.. image:: ../figures/logo.png
   :align: center
```

## Naming conventions (Nuclei databook)

- Figure name (caption) = noun phrase, no a/an:
  `Reset Signal Propagation Architecture`,
  `Ways and CLM Relationship for Different WAY_EN Values`.
- `:name:` label = `fig-` prefix + short hyphenated id: `fig-clm-reset-arch`.
- Chinese figure reference in prose: `如图 :numref:`fig-xxx` 所示`
  (reference at sentence end).
- Figure numbers (xxx in "如图xxx所示") are placeholders until the figure
  file exists; replace after the user provides the figure.
