---
name: computer-use-playwright-code
description: Run a persistent Playwright and async Python browser harness backed by Responses API function tools. Use when Codex should automate browser workflows, inspect or screenshot pages, execute short Playwright snippets in a shared runtime, or pause for user clarification without taking over the full desktop.
---

# Playwright Python Computer Use

Run the bundled Option 3 harness as a distributable skill. Prefer this skill for browser-only work, DOM inspection, visual review, repeatable navigation flows, and tasks that benefit from a persistent Playwright `browser`, `context`, and `page`. Prefer `computer-use-macos-desktop` for native apps or cross-app desktop workflows.

## Prerequisites

- Install `uv`.
- Set `OPENAI_API_KEY`, optionally through a local `.env` file.
- Install Chromium once:

```bash
uv run --with playwright python -m playwright install chromium
```

## Skill Path

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export CU_PW="$CODEX_HOME/skills/computer-use-playwright-code/scripts/computer_use_playwright_code.py"
```

When developing from a repository checkout instead of an installed skill, replace `"$CU_PW"` with the script's actual path.

## Quick Start

```bash
uv run "$CU_PW"
uv run "$CU_PW" --prompt "Go to example.com and summarize the page."
uv run "$CU_PW" --model gpt-5.4
uv run "$CU_PW" --max-steps 30
```

## Runtime Model

- Keep one persistent Chromium browser, context, and page alive for the whole run.
- Let the model call `exec_py` for short async Python snippets.
- Let the model call `ask_user` when required information is missing.
- Use `log(...)` for short textual diagnostics.
- Use `display(base64_png_string)` for screenshots or other visual observations.

## Bound Objects

- `browser`: persistent async Playwright browser
- `context`: persistent browser context with viewport `1440x900`
- `page`: persistent page created before the loop starts
- `asyncio`: Python `asyncio` module
- `log`: append concise text output
- `display`: append an in-memory base64 PNG image

## Guardrails

- Keep snippets small and incremental; the runtime state persists across tool calls.
- Do not send large blobs through `log(...)`.
- Do not write screenshots or image buffers to disk just to return them.
- Do not close `browser`, `context`, or `page` unless the user explicitly asks.
- Use `scripts/computer_use_playwright_code.py` as the canonical implementation.
