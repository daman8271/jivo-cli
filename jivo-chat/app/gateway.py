"""MCP client for the JIVO read-only gateway (mcp-gateway/).

The gateway fronts all eight backends — SAP B1, Postgres, ecom, oms, factory,
HANA, EXIM, JSAP — behind one endpoint and one tool list. It is structurally
read-only: it can emit only initialize / notifications/initialized / tools/list
/ tools/call toward a backend, and there is no code path that emits anything
else. That guarantee is the reason this app never talks to a business system
directly. Everything goes through here.

We speak MCP over Streamable HTTP: JSON-RPC POSTs to one URL, session id
carried in the Mcp-Session-Id header once the server assigns one.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

PROTOCOL_VERSION = "2025-06-18"


class GatewayError(RuntimeError):
    """The gateway refused, failed, or returned something we can't use."""


class Gateway:
    def __init__(self, url: str, timeout: float = 120.0) -> None:
        self.url = url
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={
                "Content-Type": "application/json",
                # Streamable HTTP: the server may answer with either.
                "Accept": "application/json, text/event-stream",
            },
        )
        self._session_id: str | None = None
        self._next_id = 0
        self._tools: list[dict[str, Any]] | None = None

    async def aclose(self) -> None:
        await self._client.aclose()

    # ---------------------------------------------------------------- JSON-RPC

    def _rpc_id(self) -> int:
        self._next_id += 1
        return self._next_id

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        resp = await self._client.post(self.url, json=payload, headers=headers)
        if resp.status_code >= 400:
            raise GatewayError(
                f"gateway HTTP {resp.status_code} for {payload.get('method')}: "
                f"{resp.text[:400]}"
            )

        # The server assigns the session on initialize; keep it for every later call.
        sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
        if sid:
            self._session_id = sid

        # Notifications get 202 with no body.
        if resp.status_code == 202 or not resp.content:
            return None

        body = self._decode(resp)
        if body is None:
            return None
        if "error" in body:
            err = body["error"]
            raise GatewayError(
                f"gateway error {err.get('code')} on {payload.get('method')}: "
                f"{err.get('message')}"
            )
        return body.get("result", {})

    @staticmethod
    def _decode(resp: httpx.Response) -> dict[str, Any] | None:
        """Body is either plain JSON or a one-shot SSE frame. Handle both."""
        ctype = resp.headers.get("content-type", "")
        if "text/event-stream" in ctype:
            for line in resp.text.splitlines():
                if line.startswith("data:"):
                    chunk = line[5:].strip()
                    if chunk:
                        return json.loads(chunk)
            return None
        return resp.json()

    # ---------------------------------------------------------------- lifecycle

    async def connect(self) -> None:
        """initialize + notifications/initialized. Safe to call again."""
        await self._post(
            {
                "jsonrpc": "2.0",
                "id": self._rpc_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "jivo-chat", "version": "0.1.0"},
                },
            }
        )
        await self._post(
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        )
        log.info("gateway connected: %s (session=%s)", self.url, self._session_id)

    # -------------------------------------------------------------------- tools

    async def list_tools(self, refresh: bool = False) -> list[dict[str, Any]]:
        """Every tool the gateway advertises, in Anthropic tool-definition shape."""
        if self._tools is not None and not refresh:
            return self._tools

        if self._session_id is None:
            await self.connect()

        result = await self._post(
            {"jsonrpc": "2.0", "id": self._rpc_id(), "method": "tools/list", "params": {}}
        ) or {}

        tools: list[dict[str, Any]] = []
        for t in result.get("tools", []):
            schema = t.get("inputSchema") or {"type": "object", "properties": {}}
            tools.append(
                {
                    "name": t["name"],
                    "description": t.get("description", "") or t["name"],
                    "input_schema": schema,
                }
            )

        self._tools = tools
        log.info("gateway advertises %d tools", len(tools))
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
        """Run one tool. Returns (text, is_error).

        Never raises on a tool-level failure — the model needs to see the error
        text so it can correct itself, so failures come back as (message, True).
        """
        if self._session_id is None:
            await self.connect()

        try:
            result = await self._post(
                {
                    "jsonrpc": "2.0",
                    "id": self._rpc_id(),
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                }
            ) or {}
        except GatewayError as exc:
            return (str(exc), True)
        except httpx.HTTPError as exc:
            # Almost always the SAP tunnel being down. Say so plainly — this is
            # the single most common real-world failure of this app.
            return (
                f"Could not reach the JIVO gateway ({exc}). The tunnel to SAP is "
                f"probably down. Tell the user the systems are unreachable right "
                f"now — do not guess a number.",
                True,
            )

        parts: list[str] = []
        for block in result.get("content", []):
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
            else:
                parts.append(json.dumps(block))
        text = "\n".join(p for p in parts if p) or "(the tool returned nothing)"
        return (text, bool(result.get("isError", False)))
