# Converter Review Notes (from examples/everything.md)

## Bugs / Fixes Needed

### 1. `---` maps to `#pagebreak()` instead of `#line(length: 100%)`
- File: `mdtyp/converter.py`, line 118
- Current: `ctx.write("#pagebreak()\n\n")`
- Should be: `ctx.write("#line(length: 100%)\n\n")`
- Impact: First page is nearly empty; thematic breaks become forced page breaks

### 2. No `table.header()` for table headers
- File: `mdtyp/converter.py`, `_render_table()` function
- Currently header cells are just bold text: `[*Parameter*]`
- Should wrap header row in `table.header(...)` for proper semantics and repeat-on-page-break

### 3. No document-level setup emitted
- The output has no `#set page(...)`, `#set text(font: ...)`, `#set heading(numbering: ...)` etc.
- Could add a preamble option or default preamble to the converter
- Arguably out of scope for a pure converter, but worth considering as an opt-in flag

### 4. `^` in text isn't handled
- `kg/m^3`, `10^-5`, `10^6` render as literal caret characters
- Could detect `^` followed by digits/text and convert to `#super[...]`
- Tricky to get right without false positives — may want to limit to common patterns

### 5. Text immediately after table closing `)` has no blank line
- Lines like 109 and 180 in the .typ output
- Text runs right into the table — should have a blank line separator

## What's Working Well
- Tables render correctly with proper column counts and alignment
- Bold/italic/strikethrough markup converts properly
- Lists (ordered and bullet) work correctly including nesting
- Code blocks preserved with language info
- Special character escaping (fixed in this session: `*`, `_`, `#`, `@`, `~`, `<`, `>`, `$`)
