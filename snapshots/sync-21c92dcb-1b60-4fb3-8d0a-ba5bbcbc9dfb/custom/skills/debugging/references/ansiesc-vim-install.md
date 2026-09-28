# AnsiEsc.vim — Offline Installation on CentOS 7

For rendering ANSI escape sequences (colors, bold, etc.) in vim when the machine has no internet access.

## Plugin Source

- Vim.org script ID: 302 (original), 4979 (Improved version)
- GitHub mirror: https://github.com/berdandy/AnsiEsc.vim
- Download URL: `https://www.vim.org/scripts/download_script.php?src_id=26454`

## File Layout

The vimball (.vmb) contains:

| File | Destination | Purpose |
| :-- | :-- | :-- |
| `autoload/AnsiEsc.vim` | `~/.vim/autoload/` | Core functions (AnsiEsc#BufReadPost, etc.) |
| `plugin/AnsiEscPlugin.vim` | `~/.vim/plugin/` | Plugin entry + auto-commands |
| `plugin/cecutil.vim` | `~/.vim/plugin/` | Utility library (window position save/restore) |
| `doc/AnsiEsc.txt` | `~/.vim/doc/` | Help file (optional) |

## Installation Steps

```bash
mkdir -p ~/.vim/autoload ~/.vim/plugin
# Transfer the three files to their destinations above
```

## Auto-activation

The plugin automatically hooks `BufReadPost` — it renders ANSI colors on file open WITHOUT any `.vimrc` configuration. **Do NOT add `autocmd BufReadPost * AnsiEsc` to `.vimrc`** — the plugin already does this internally, and a duplicate will cause `E492: Not an editor command`.

## Manual Toggle

`:AnsiEsc` toggles ANSI rendering on/off for the current buffer.

## Verification

```vim
:scriptnames          " should list AnsiEscPlugin.vim
:echo g:loaded_AnsiEsc " should show version string
```

Open a file with ANSI codes — colors should render immediately.

## Pitfalls

- If you see `E117: Unknown function: AnsiEsc#BufReadPost`, the `autoload/AnsiEsc.vim` file is missing or in the wrong directory.
- vim 7.4 (CentOS 7 default) supports `+conceal` which AnsiEsc requires — no additional patches needed.
- ANSI color codes that work in terminal (`\033[31m`) also work in AnsiEsc, including bright variants (`\033[91m`).
