# WaveDrom in Sphinx RST

## Embedding

```rst
.. wavedrom::

   {
     "signal": [
       { "name": "clk", "wave": "p.............." },
       { "name": "addr", "wave": "x..2...|...2.x", "data": ["A", "A+N"] }
     ],
     "config": { "hscale": 2 }
   }
```

## Strict JSON vs Relaxed Format

WaveDrom officially supports relaxed JSON (`{ name: "clk" }`), but some editors (VS Code plugin, certain Sphinx extensions) require **strict JSON** with double-quoted keys: `{ "name": "clk" }`.

**Error symptom:** `Property keys must be doublequoted json`

**Fix:** Add double quotes around all object keys.

## Signal Name Alignment

Signal names default to right-aligned. For left alignment, inject CSS:

```rst
.. raw:: html

   <style>
     .wavedrom text.signal-name { text-anchor: start; }
   </style>
```

- `start` = left-align, `end` = right-align (default), `middle` = center.
- Alternative: pad shorter names with trailing spaces to match the longest name width.

## Omission / Gap in Waveforms

- `...` — three consecutive dots create a visual gap
- `|` — pipe character creates a break/omission marker between two waveform segments
- `P<->` in `edge` array draws a double-arrow over the gap with optional label:

```json
{
  "signal": [
    { "name": "addr", "wave": "x..2...|...2.x", "data": ["A", "A+N"] }
  ],
  "edge": ["P<-> 省略"]
}
```

## Address Sequences

For consecutive address values with step patterns (e.g., A, A+8, A+16...), use `...` gap + `data` array with start/end values:

```json
{ "name": "addr", "wave": "x.2...|...2.x", "data": ["A", "A+N"] }
```

Or for explicit intermediate steps:

```json
{ "name": "addr", "wave": "x.2.2.2.2.x", "data": ["A", "A+8", "A+16", "A+24"] }
```
