# Debugging uneven control spacing in table rows

From the PMA config generator session (2026-08): user complained twice that
"the gap between the ATTR and BASE inputs didn't change" while all other gaps
were already fine. Padding/margin fixes had NO effect. Root cause was neither
padding nor margin.

## Root cause

A hard-coded column width in the table header:

```html
<th style="width:7.5vw">ATTR</th>
```

The `select` inside that column was only ~38px wide but the column rendered
~60px (7.5vw at the viewport used). The control is left-aligned, so the slack
appeared as a ~20px gap on its right — while every OTHER adjacent control pair
measured 1.2px (just td padding). Tuning `td { padding }`, removing
`.attr-sel { margin-right }`, and fixing `select` widths did nothing because
the gap came from column width, not spacing properties.

Fix: drop the fixed `<th width>` and let the column hug its content, or set
the control to `width:100%` so it fills the column. After removing the
7.5vw, all adjacent gaps measured 1.2px uniformly.

## Measurement method (do this FIRST, before editing CSS)

Collect every control of the row in ONE document-order query and compute
adjacent bounding-box gaps:

```python
out = js("""(() => {
  const ctls = document.querySelectorAll('#region-tbody select, #region-tbody input[type=text]');
  const boxes = [];
  for (const c of ctls) {
    const r = c.getBoundingClientRect();
    boxes.push(r);
  }
  const gaps = [];
  for (let i = 0; i < boxes.length - 1; i++)
    gaps.push((boxes[i+1].left - boxes[i].right).toFixed(1));
  return {n: ctls.length, gaps};
})()""")
print(json.dumps(out))
```

A large outlier in the array (e.g. `20.5` among `1.2`s) names the exact
offending control pair. A negative gap = the pair wraps to the next line
(row break) — expected at row boundaries, ignore.

## Trap: never query selects and inputs separately

`querySelectorAll('select')` + `querySelectorAll('input')` concatenated gives
wrong order (all selects first), so adjacent pairs are not adjacent in the
DOM — gaps come out negative/absurd (e.g. -79.6, 54.6) and send you chasing
phantom layout bugs. Always one selector with commas, document order.
