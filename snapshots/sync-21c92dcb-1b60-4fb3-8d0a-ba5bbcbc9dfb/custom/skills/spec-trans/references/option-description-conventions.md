# Option Description Conventions

Standard pattern for documenting configuration options in Nuclei databook / integration guide.

## Pattern

```
The `OptionName` option <brief single-sentence description of purpose>.
Two options are selectable:

– <Value1> — <concise description, one sentence>.
– <Value2> — <concise description, one sentence>.
```

## Sub-Interface with Multi-Select Options

When a parent option opens a sub-interface containing multiple independent checkable options (not a radio-list dropdown):

```markdown
The `OptionName` sub-interface provides additional <feature> support, with the following options available:

– `SubOption1`
– `SubOption2`
– `SubOption3`
```

## Sub-Screen Documentation Structure

When a GUI sub-screen contains multiple logical sections separated by `*** ... ***` dividers, split documentation by functional domain rather than flat-listing all options:

```
Parent Option
├── 3.1 Domain A Configuration    ← options under first *** divider
├── 3.2 Domain B Configuration    ← options under second *** divider
├── 3.3 Domain C Configuration    ← ...
```

The section title itself serves as the categorization — no need for a separate "overview" paragraph per section before listing options. Each option gets one sentence.

## Single-Line Bullet Format for Option Summaries

When the user requests a concise list of options (\"介绍这几个选项，注意字数\"), use single-line bullets with `---` separators:

```markdown
- `OptionName` — <one-line description, as concise as possible> ---
- `OptionName2` — <one-line description> ---
```

Each bullet is self-contained on one line. No separate elaboration paragraph follows.

## Rules

- **Start with "The `OptionName` option..."** — always.
- **First sentence only** — describe what the option does, no rationale, no trade-offs unless explicitly asked.
- **Option values in monospace** — `32`, `64`, `none`, `zba_zb` etc.
- **List items use en-dash `–`** — not `-` or `•`.
- **One sentence per option** — short, factual, no elaboration.
- **No detail unless asked** — user explicitly says "不用详细" (no need for detail) for option introductions.
- **No current/default state** — Do not mention the currently selected value or default state of an option unless the user explicitly asks. Phrases like "当前选中" or "currently selected" are excluded from option descriptions.
- **Abbreviations expanded** — Technical abbreviations used in option names (e.g., `fmax`) are expanded to full form (`maximum frequency`) in the description body.
- **Product naming**: `N600`, `N300`, `N900` — prefix with `N`, never bare `600` or `the 600`.

## Example

The `I/DCACHE Cacheline Size in Byte` option sets the cacheline size of Icache and Dcache, in bytes, controlling the amount of data transferred per cacheline fill. Two options are selectable:

– 32 — 32 bytes of data fetched from memory per cacheline fill.
– 64 — 64 bytes of data fetched from memory per cacheline fill.
