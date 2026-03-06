---
name: computer-use-macos-desktop
description: Run a full-desktop macOS computer-use harness backed by the Responses API `computer` tool and local PyAutoGUI execution. Use when Codex must operate native macOS apps, move across multiple desktop applications, or interact with the real desktop through screenshots, clicks, typing, scrolling, drags, and safety acknowledgements.
---

# macOS Desktop Computer Use

Run the bundled Option 1 harness as a distributable skill. Prefer this skill for Finder, Notes, System Settings, Chrome, or any cross-app workflow on the real macOS desktop. Prefer `computer-use-playwright-code` for browser-only flows that are easier to handle inside a persistent Playwright page.

## Prerequisites

- Run only on macOS.
- Install `uv`.
- Set `OPENAI_API_KEY`, optionally through a local `.env` file.
- Grant the terminal app `Accessibility` and `Screen Recording`.

## Skill Path

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export CU_MAC="$CODEX_HOME/skills/computer-use-macos-desktop/scripts/computer_use_macos_desktop.py"
```

When developing from a repository checkout instead of an installed skill, replace `"$CU_MAC"` with the script's actual path.

## Quick Start

```bash
uv run "$CU_MAC" --prompt "Open Chrome and search for OpenAI."
uv run "$CU_MAC" --max-steps 40
uv run "$CU_MAC" --model gpt-5.4
```

## Workflow

1. Use the bundled script instead of rewriting the harness.
2. Let the permission preflight run unless the user explicitly asks to skip it.
3. Read printed safety checks before acknowledging them.
4. Stop and ask the user before submitting data, deleting content, installing software, changing settings, or typing sensitive information.
5. Move the cursor to the top-left corner if you need to trigger PyAutoGUI's failsafe and abort control immediately.

## Common Commands

```bash
uv run "$CU_MAC" --prompt "Open Finder and create a new folder named Demo."
uv run "$CU_MAC" --wait-seconds 3
uv run "$CU_MAC" --skip-permission-check
```

## Behavior

- Capture a fresh full-desktop screenshot after each action batch.
- Rescale screenshots to the desktop coordinate space before sending them back to the model.
- Execute click, double click, move, scroll, keypress, type, drag, and wait locally with PyAutoGUI.
- Prompt for acknowledgement when the model emits Responses API safety checks.
- Use `scripts/computer_use_macos_desktop.py` as the canonical implementation.
