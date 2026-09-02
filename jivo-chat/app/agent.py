"""The agent loop: Claude + the JIVO gateway's tools, streamed to the browser.

Manual loop rather than the SDK tool runner, because the browser needs more
than the final text: it wants live "running hana_turnover…" status, the context
bar, and the exact tool arguments to show under the answer. That means owning
each turn.

Three things this file is careful about:

  1. Permissions are enforced HERE, not in the prompt. A tool outside the
     user's role is never put in `tools`, so the model cannot call it — and a
     name that somehow arrives anyway is rejected before it reaches the gateway.
  2. Tool output is capped. One `--all` query returning 5,000 rows would
     otherwise eat the context window in a single call.
  3. Assistant content is stored verbatim, thinking blocks included, because
     they must be replayed unchanged on the same model.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import anthropic

from .db import Store
from .gateway import Gateway

log = logging.getLogger(__name__)

CONTEXT_WINDOW = 1_000_000          # Opus 5
MAX_TOKENS = 64_000
MAX_TOOL_CHARS = 60_000             # ~15k tokens; a hard stop on runaway results
MAX_TURNS = 25                      # loop guard

# Opus 5 list price, USD per million tokens.
PRICE_IN, PRICE_OUT = 5.00, 25.00
PRICE_CACHE_READ, PRICE_CACHE_WRITE = 0.50, 6.25
USD_INR = 88.0                      # approximate; for the spend cap only

MEMORY_TOOL = {"type": "memory_20250818", "name": "memory"}

SYSTEM = """You are JIVO's data assistant. People in the office ask you questions \
about the business in plain language and you answer with real numbers, pulled live.

HOW TO ANSWER
- Give the number first, then one line on how you got it. Offer the drill-down.
- Money is INR. Use Indian grouping and crores for large figures.
- Quantities in tonnes (MT) where the question is about volume.
- Name the company if it is not Oil. Give the date range for any sales question.
- If a tool fails or the systems are unreachable, say so plainly. Never guess a
  number, never present a remembered figure as a live one.
- Show the tool and arguments you used underneath the answer. Every number must
  be traceable to a query someone else could re-run.

WHAT YOU CAN DO
Everything you can reach is READ-ONLY by construction. You cannot create,
change or delete anything in any JIVO system, and you should not imply that you
can. If someone asks you to post, cancel or edit a document, tell them that has
to be done by a person in SAP B1.

THE CORRECTIONS BELOW ARE SETTLED FACT
Real JIVO operators corrected earlier versions of this assistant on each one.
They override your instincts and they override the general guidance above.
"""


class DeniedTool(Exception):
    """The model asked for a tool this user's role does not allow."""


def _cap(text: str) -> str:
    if len(text) <= MAX_TOOL_CHARS:
        return text
    keep = text[:MAX_TOOL_CHARS]
    return (
        keep
        + f"\n\n[… truncated: the result was {len(text):,} characters. Only the "
        f"first {MAX_TOOL_CHARS:,} are shown. Narrow the filter, add a date "
        f"range, or ask for a count instead of every row.]"
    )


def _cost_inr(usage: dict[str, int]) -> float:
    usd = (
        usage.get("input_tokens", 0) * PRICE_IN
        + usage.get("output_tokens", 0) * PRICE_OUT
        + usage.get("cache_read_input_tokens", 0) * PRICE_CACHE_READ
        + usage.get("cache_creation_input_tokens", 0) * PRICE_CACHE_WRITE
    ) / 1_000_000
    return usd * USD_INR


class Agent:
    def __init__(
        self,
        store: Store,
        gateway: Gateway,
        corrections: str,
        model: str = "claude-opus-5",
        effort: str = "high",
        api_key: str | None = None,
    ) -> None:
        self.store = store
        self.gateway = gateway
        self.corrections = corrections
        self.model = model
        self.effort = effort
        self.client = anthropic.AsyncAnthropic(api_key=api_key) if api_key else anthropic.AsyncAnthropic()

    # ------------------------------------------------------------------- setup

    async def tools_for(self, role: str) -> list[dict[str, Any]]:
        """Gateway tools this role may see, plus the memory tool.

        Deny by default: an unknown role gets an empty prefix list and therefore
        no business tools at all.
        """
        prefixes = self.store.role_prefixes(role)
        allowed = [
            t for t in await self.gateway.list_tools()
            if any(t["name"].startswith(p) for p in prefixes)
        ]
        return allowed + [MEMORY_TOOL]

    def _system(self, user: Any, role: str) -> list[dict[str, Any]]:
        memories = self.store.memory_list(user["email"])
        mem_text = (
            "\n\nWHAT YOU HAVE LEARNED ABOUT THIS PERSON\n"
            + "\n".join(f"- {m['path']}: {m['content']}" for m in memories)
            if memories
            else ""
        )
        return [
            {
                # Stable prefix: identical on every request, so it caches. Never
                # put a timestamp or anything per-request above this line.
                "type": "text",
                "text": SYSTEM + "\n" + self.corrections,
                "cache_control": {"type": "ephemeral"},
            },
            {
                # Volatile: changes per user and as memory grows, so it sits
                # after the cache breakpoint.
                "type": "text",
                "text": (
                    f"You are talking to {user['name']} ({user['email']}), "
                    f"role: {role}." + mem_text
                ),
            },
        ]

    # ---------------------------------------------------------- the memory tool

    def _run_memory(self, email: str, cmd: dict[str, Any]) -> str:
        command = cmd.get("command")
        path = (cmd.get("path") or "").strip()
        if command == "view":
            if not path or path in ("/memories", "/memories/"):
                items = self.store.memory_list(email)
                return "\n".join(m["path"] for m in items) or "(no memories yet)"
            return self.store.memory_get(email, path) or f"{path} does not exist"
        if command == "create":
            self.store.memory_put(email, path, cmd.get("file_text", ""))
            return f"wrote {path}"
        if command == "str_replace":
            current = self.store.memory_get(email, path) or ""
            old, new = cmd.get("old_str", ""), cmd.get("new_str", "")
            if current.count(old) != 1:
                return f"error: {current.count(old)} matches for old_str, need exactly 1"
            self.store.memory_put(email, path, current.replace(old, new, 1))
            return f"updated {path}"
        if command == "insert":
            current = self.store.memory_get(email, path) or ""
            lines = current.splitlines()
            at = int(cmd.get("insert_line", len(lines)))
            lines.insert(at, cmd.get("insert_text", ""))
            self.store.memory_put(email, path, "\n".join(lines))
            return f"updated {path}"
        if command == "delete":
            self.store.memory_delete(email, path)
            return f"deleted {path}"
        if command == "rename":
            new_path = cmd.get("new_path", "")
            content = self.store.memory_get(email, path) or ""
            self.store.memory_delete(email, path)
            self.store.memory_put(email, new_path, content)
            return f"renamed {path} -> {new_path}"
        return f"unknown memory command: {command}"

    # -------------------------------------------------------------------- turn

    async def ask(self, user: Any, cid: str, question: str) -> AsyncIterator[dict[str, Any]]:
        """Run one question to completion. Yields events for the browser."""
        email, role = user["email"], user["role"]
        self.store.audit(email, cid, "question", {"text": question})

        tools = await self.tools_for(role)
        allowed_names = {t.get("name") for t in tools}
        system = self._system(user, role)

        self.store.add_message(cid, "user", [{"type": "text", "text": question}])
        messages = self.store.history(cid)

        total_cost = 0.0

        for turn in range(MAX_TURNS):
            assistant_blocks: list[dict[str, Any]] = []
            usage: dict[str, int] = {}
            stop_reason = None

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system,
                tools=tools,
                thinking={"type": "adaptive", "display": "summarized"},
                output_config={"effort": self.effort},
                messages=messages,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            yield {"type": "text", "text": event.delta.text}
                        elif event.delta.type == "thinking_delta":
                            yield {"type": "thinking", "text": event.delta.thinking}

                final = await stream.get_final_message()

            stop_reason = final.stop_reason
            assistant_blocks = [b.model_dump(exclude_none=True) for b in final.content]
            usage = final.usage.model_dump(exclude_none=True)

            used = (
                usage.get("input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
            )
            turn_cost = _cost_inr(usage)
            total_cost += turn_cost
            self.store.record_spend(email, self.model, usage, turn_cost)

            yield {
                "type": "context",
                "used": used,
                "window": CONTEXT_WINDOW,
                "percent": round(used / CONTEXT_WINDOW * 100, 1),
                "cost_inr": round(total_cost, 2),
            }

            self.store.add_message(cid, "assistant", assistant_blocks)
            messages.append({"role": "assistant", "content": assistant_blocks})

            if stop_reason == "refusal":
                yield {"type": "error", "text": "Claude declined this request."}
                self.store.audit(email, cid, "denied", {"reason": "refusal"})
                return

            if stop_reason != "tool_use":
                answer = "".join(
                    b.get("text", "") for b in assistant_blocks if b.get("type") == "text"
                )
                self.store.audit(email, cid, "answer", {"text": answer[:8000]})
                yield {"type": "done", "cost_inr": round(total_cost, 2)}
                return

            # --- run every tool the model asked for, results in ONE user turn
            results: list[dict[str, Any]] = []
            for block in assistant_blocks:
                if block.get("type") != "tool_use":
                    continue
                name, args, tuid = block["name"], block.get("input", {}), block["id"]
                yield {"type": "tool", "name": name, "input": args, "status": "running"}

                if name not in allowed_names:
                    # Should be unreachable — the tool was never advertised. Kept
                    # because a permission check that only exists upstream is not
                    # a permission check.
                    text, is_error = (f"'{name}' is not available to your role.", True)
                    self.store.audit(email, cid, "denied", {"tool": name, "role": role})
                elif name == "memory":
                    text, is_error = self._run_memory(email, args), False
                else:
                    text, is_error = await self.gateway.call_tool(name, args)

                text = _cap(text)
                self.store.audit(
                    email, cid, "tool_call",
                    {"tool": name, "input": args, "error": is_error, "chars": len(text)},
                )
                yield {
                    "type": "tool",
                    "name": name,
                    "input": args,
                    "status": "error" if is_error else "ok",
                    "chars": len(text),
                }
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tuid,
                        "content": text,
                        **({"is_error": True} if is_error else {}),
                    }
                )

            self.store.add_message(cid, "user", results)
            messages.append({"role": "user", "content": results})

        yield {"type": "error", "text": f"Stopped after {MAX_TURNS} steps without finishing."}
