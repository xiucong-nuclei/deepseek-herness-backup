# Browser-exec harness script pitfalls (PMA tool session)

All learned the hard way while iterating the PMA config generator
(`~/deliverables/web/pma-calc-landing/index.html`) — reuse in any
browser_exec verification script on headless Linux.

## Mock native dialogs FIRST

Code paths calling `confirm()` / `alert()` (clear-all buttons, per-attribute
limit guards, invalid-input alerts, fix-apply guards) hang the headless page
forever with no visible dialog — the `js()` call times out and the whole
script dies mid-way. Start EVERY script with:

```python
js("window.confirm=()=>true; window.alert=()=>true;")
```

Forgetting it costs a timeout on the first `clearAll()` / `applyFix()`.

## Drive listeners with dispatched events

Setting `el.value = x` alone does NOT fire `oninput` / `onchange`
(vanilla-JS listeners). Always follow with:

```python
js("el.value='0x10000000'; el.dispatchEvent(new Event('input',{bubbles:true}))")
```

Use `change` for `<select>`. Same for `focusin`: real `focus()` does not
fire it in headless (no window focus) — dispatch the event manually to
verify focus listeners.

## Python traps inside the exec script

- Plain dicts reject attribute assignment: `out.k = v` raises
  `AttributeError: 'dict' object has no attribute 'k'`. Use `out["k"] = v`.
- JS regex literals containing `\n` (e.g. `split(/\n/)`) get mangled by
  Python string escapes. Join/split lines in Python, or avoid the regex.
- Reuse the same js() error-capture block at the top of every script:
  `window.__errs` + `window.onerror`, print at the end.

## Blob / CSV download capture

For CSV exports built via `URL.createObjectURL(blob)`, monkey-patch to grab
the blob then read it back with FileReader (inside a Promise):

```python
csv = js("""(() => {
  let cap=null; const orig=URL.createObjectURL;
  URL.createObjectURL=(b)=>{cap=b;return orig.call(URL,b);};
  exportCsv();
  return new Promise(res=>{const r=new FileReader(); r.onload=()=>res(String(r.result)); r.readAsText(cap);});
})()""")
```

(js() with awaitPromise is fine for this pattern.)

## Group-header rows pollute table selectors

When the region table has section header rows (e.g. per-attribute group
headers), `#tbody tr` includes them — `rows[0]` is a header and has no
inputs/selects. Count and iterate with `tr:not(.grp-hdr)`.

## http.server single-thread wedges

`python3 -m http.server` is single-threaded: a stale keep-alive connection
can block it so curl returns 000 while the process is alive. Fix:
`pkill -f "http.server 8640"` then restart via terminal(background=true).
Always `curl -s -o /dev/null -w "%{http_code}"` before driving the browser
— "ERR_EMPTY_RESPONSE / didn't send any data" in the browser means the
server died, not the page.
