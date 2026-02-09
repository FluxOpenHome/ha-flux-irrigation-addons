# CLAUDE.md

## Critical Rules

### Python Triple-Quoted Strings with JavaScript onclick Handlers

**CRITICAL: In Python triple-quoted strings (`"""`), the escape `\'` produces a plain single quote `'` — it does NOT produce a backslash-quote `\'` in the output.**

When building JavaScript `onclick` handlers inside HTML that's embedded in a Python triple-quoted string, you MUST use `\\'` (backslash-backslash-quote) to produce `\'` in the JS output.

**WRONG (causes JS parse error — kills entire script block silently):**
```python
html += '<button onclick="myFunc(\'' + val + '\')">Click</button>';
```
Output: `onclick="myFunc('' + val + '')"` — JS sees empty strings, syntax error.

**CORRECT:**
```python
html += '<button onclick="myFunc(\\'' + val + '\\')">Click</button>';
```
Output: `onclick="myFunc(\'' + val + '\')"` — JS sees proper escaped quotes.

This applies to ALL files: `management_ui.py`, `admin.py`, `homeowner_ui.py`.

Similarly, `\d` in a Python triple-quoted string is an invalid escape sequence (SyntaxWarning in Python 3.12+). Use `\\d` to produce `\d` for JS regex patterns.

**General rule: Any backslash intended for the JS/HTML output must be doubled (`\\`) in the Python source.**
