The dashboard shows a single status label for each account. We need a normalized string for the UI with no surrounding whitespace and a consistent casing convention.

Implement `format_label(value: str) -> str` in `src/labels.py`.

It should trim whitespace from the server-provided status and return the label used in the dashboard.
