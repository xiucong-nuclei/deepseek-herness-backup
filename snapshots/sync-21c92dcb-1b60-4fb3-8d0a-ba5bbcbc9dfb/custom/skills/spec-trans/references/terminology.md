# Terminology Decisions

## GUI vs Screen for Terminal-Based Interfaces

**Decision: Use "GUI" for ncurses/dialog-based terminal interfaces.**

Context: `nuclei_gen` opens an interactive terminal interface with menus, buttons,
and dialogs (built on ncurses or similar). The user's team refers to this as a
"GUI" internally.

| Term | Use when |
|------|----------|
| `GUI` | ncurses/dialog-based terminal interface with interactive elements (menus, buttons, dialogs) |
| `screen` | Simple text-based display or prompt without interactive widgets |
| `TUI` | Avoid — less familiar to non-native readers than GUI |
| `terminal-based GUI` | Explicit form when clarity matters |

Example: "Main Configuration GUI" for the nuclei_gen main config screen.

## configurable options

Keep the English phrase "configurable options" as-is — it is the standard term
in CPU configuration documentation. The Chinese source 可配置选项 maps to this.
