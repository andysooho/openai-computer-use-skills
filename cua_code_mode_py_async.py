"""Async Python analogue of cua_code_mode.ts.

Runs a Responses API loop with one persistent Playwright browser/context/page,
and tools that let the model execute short async Python snippets and ask the
user clarifying questions.

The model can return visual observations by calling:
    display(base64_png_string)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import traceback
from typing import Any

from openai import OpenAI
from playwright.async_api import async_playwright
from dotenv import load_dotenv

Phase = str | None


def _message_text(item: Any) -> str:
    try:
        parts = getattr(item, "content", None)
        if isinstance(parts, list) and parts:
            out: list[str] = []
            for p in parts:
                t = getattr(p, "text", None)
                if isinstance(t, str) and t:
                    out.append(t)
            if out:
                return "\n".join(out)
    except Exception:
        pass
    return str(item)


async def _ainput(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)


async def main(
    prompt: str = (
        "Go to Hacker News, click on the most interesting link "
        "(be prepared to justify your choice), take a screenshot, "
        "and give me a critique of the visual layout."
    ),
    max_steps: int = 20,
    model: str | None = None,
) -> None:
    load_dotenv()
    resolved_model = model or os.getenv("OPENAI_MODEL") or "gpt-5.4"
    client = OpenAI()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--window-size=1440,900"],
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        conversation: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        py_output: list[dict[str, Any]] = []

        def log(*xs: Any) -> None:
            text = " ".join(str(x) for x in xs)
            py_output.append({"type": "input_text", "text": text[:5000]})

        def display(base64_image: str) -> None:
            py_output.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{base64_image}",
                    "detail": "original",
                }
            )

        runtime_globals: dict[str, Any] = {
            "__builtins__": __builtins__,
            "asyncio": asyncio,
            "browser": browser,
            "context": context,
            "page": page,
            "display": display,
            "log": log,
        }

        for _ in range(max_steps):
            resp = client.responses.create(
                model=resolved_model,
                tools=[
                    {
                        "type": "function",
                        "name": "exec_py",
                        "description": (
                            "Execute provided interactive async Python in a "
                            "persistent runtime context."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": (
                                        "Python code to execute. Write small snippets. "
                                        "State persists across tool calls via globals(). "
                                        "This runtime uses Playwright's async Python API, "
                                        "so you may use await directly. "
                                        "Do not call asyncio.run(...), "
                                        "loop.run_until_complete(...), or manage the "
                                        "event loop yourself. "
                                        "You can use ONLY these prebound objects/helpers: "
                                        "log(x) for text output, "
                                        "display(base64_png_string) for image output, "
                                        "browser (async Playwright browser), "
                                        "context (viewport 1440x900), "
                                        "page (already created), "
                                        "asyncio (module). "
                                        "Be concise with log(x): do not send large base64 "
                                        "payloads, screenshots, buffers, page HTML, or "
                                        "other large blobs through log(). "
                                        "If you create an image or screenshot, pass the "
                                        "base64 PNG string to display(). "
                                        "Do not write screenshots or image data to "
                                        "temporary files or disk just to pass them back; "
                                        "keep image data in memory and send it directly to "
                                        "display(). "
                                        "Do not assume extra globals or helpers are "
                                        "available unless they are explicitly listed here. "
                                        "Do not close browser/context/page unless "
                                        "explicitly asked."
                                    ),
                                }
                            },
                            "required": ["code"],
                            "additionalProperties": False,
                        },
                    },
                    {
                        "type": "function",
                        "name": "ask_user",
                        "description": (
                            "Ask the user a clarification question and wait for "
                            "their response."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": (
                                        "The exact question to show the user. "
                                        "Use this instead of asking a freeform "
                                        "clarifying question in a final answer."
                                    ),
                                }
                            },
                            "required": ["question"],
                            "additionalProperties": False,
                        },
                    },
                ],
                input=conversation,
            )

            conversation.extend(resp.output)

            had_tool_call = False
            latest_phase: Phase = None

            for item in resp.output:
                item_type = getattr(item, "type", None)

                if item_type == "function_call" and getattr(item, "name", None) == "exec_py":
                    had_tool_call = True
                    raw_args = getattr(item, "arguments", "{}") or "{}"
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {}
                    code = args.get("code", "") if isinstance(args, dict) else ""

                    print(code)
                    print("----")

                    wrapped = "async def __codex_exec__():\n" + "".join(
                        f"    {line}\n" if line else "    \n"
                        for line in (code or "pass").splitlines()
                    )

                    try:
                        exec(wrapped, runtime_globals, runtime_globals)
                        await runtime_globals["__codex_exec__"]()
                    except Exception:
                        log(traceback.format_exc())

                    conversation.append(
                        {
                            "type": "function_call_output",
                            "call_id": getattr(item, "call_id", None),
                            "output": py_output[:],
                        }
                    )

                    for out in py_output:
                        if out.get("type") == "input_text":
                            print("PY LOG:", out.get("text", ""))
                        elif out.get("type") == "input_image":
                            print("PY IMAGE: [base64 string omitted]")
                    print("=====")

                    py_output.clear()

                elif item_type == "function_call" and getattr(item, "name", None) == "ask_user":
                    had_tool_call = True
                    raw_args = getattr(item, "arguments", "{}") or "{}"
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {}
                    question = (
                        args.get("question", "Please provide more information.")
                        if isinstance(args, dict)
                        else "Please provide more information."
                    )

                    print(f"MODEL QUESTION: {question}")
                    answer = await _ainput("> ")

                    conversation.append(
                        {
                            "type": "function_call_output",
                            "call_id": getattr(item, "call_id", None),
                            "output": answer,
                        }
                    )

                elif item_type == "message":
                    print(_message_text(item))
                    phase = getattr(item, "phase", None)
                    if isinstance(phase, str) or phase is None:
                        latest_phase = phase
                elif item_type == "output_item.done":
                    phase = getattr(item, "phase", None)
                    if isinstance(phase, str) or phase is None:
                        latest_phase = phase

            if not had_tool_call and latest_phase == "final_answer":
                return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="Override the default user prompt.")
    parser.add_argument(
        "--model",
        help="Override the model. Defaults to OPENAI_MODEL or gpt-5.4.",
    )
    args = parser.parse_args()
    asyncio.run(
        main(prompt=args.prompt, model=args.model)
        if args.prompt is not None or args.model is not None
        else main()
    )
