# Vi & Vim Basics

> [← Back to Main Index](README.md)

## Table of Contents

- [Search & Replace](#search--replace)
- [Essential Keyboard Shortcuts](#essential-keyboard-shortcuts)

---

## Search & Replace

Replace a string across a range of lines in a file (from line `i` to the end of the file `$`):

```vim
:i,$ s/string-to-replace/replacement-string
```

---

## Essential Keyboard Shortcuts

| Shortcut / Command | Action |
| :--- | :--- |
| `Ctrl + V` | Enter visual block edit mode |
| `Ctrl + A` | Increment the number under the cursor by `+1` |
| `Ctrl + X` | Decrement the number under the cursor by `-1` |
| `G` | Jump to End of File (EOF) |
| `g` (or `gg`) | Jump to Beginning of File (BOF) |
| `O` | Insert a new line **above** the current line and enter insert mode |
| `o` | Insert a new line **below** the current line and enter insert mode |
| `/` | Search forward in the file |
| `Esc` then `u` (or `U`) | Undo (`Ctrl + Z` equivalent) |
| `dd` / `d` | Delete a line |
| `d$` | Delete from the cursor position to the end of the current line |
