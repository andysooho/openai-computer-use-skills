# computer-use

Python Computer Use examples wired for `uv`.

## Setup

```bash
uv sync
uv run --with playwright python -m playwright install chromium
```

Set `OPENAI_API_KEY` in `.env` file.

For the desktop harness on macOS, also grant your terminal app:

- `Accessibility`
- `Screen Recording`

## Run

Option 3, code-execution harness with Playwright:

```bash
uv run skills/public/computer-use-playwright-code/scripts/computer_use_playwright_code.py
uv run skills/public/computer-use-playwright-code/scripts/computer_use_playwright_code.py --prompt "Go to example.com and summarize the page."
uv run skills/public/computer-use-playwright-code/scripts/computer_use_playwright_code.py --model gpt-5.4
```

Option 1, built-in `computer` loop against the full macOS desktop:

```bash
uv run skills/public/computer-use-macos-desktop/scripts/computer_use_macos_desktop.py --prompt "Open Chrome and search for OpenAI."
uv run skills/public/computer-use-macos-desktop/scripts/computer_use_macos_desktop.py --max-steps 40
```

The desktop harness sends full-desktop screenshots to the Responses API and
executes the returned actions locally with PyAutoGUI. On Retina displays it
automatically rescales screenshots to the desktop input coordinate space so
model clicks land correctly. Before the run starts, it checks `Accessibility`
and `Screen Recording`; if either is missing, it triggers the macOS prompt when
possible and opens the matching System Settings pane.

Both skill scripts default to `gpt-5.4`. You can override that with
`OPENAI_MODEL` or `--model`.
