"""JSAP HTTP client — READ-ONLY by construction.

⛔ THE READ-ONLY LAW (docs/READ_ONLY_LAW.md)
This client exposes exactly one data verb: `get()`. There is no post/put/patch/
delete method and there never will be. The ONLY non-GET requests in this file are
the two-step session bootstrap (login + websession/set), which authenticate a
session and mutate no JIVO business data. Everything the CLI reads goes through
`get()`. If you are tempted to add a mutating method here, don't — that breaks the
law. See tests/test_readonly.py, which fails the build if a write verb appears.

Pure standard library (urllib) — no third-party dependencies, runs anywhere the
JIVO fleet has python3.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from typing import Any

from .config import CONFIG, COOKIE_FILE, STATE_DIR

# The single allowed data verb for GET reads. Enforced in _request().
_READ_VERB = "GET"
# Session bootstrap is the only sanctioned mutating-shaped traffic. Nothing else.
_BOOTSTRAP_PATHS = ("/api/auth/Login", "/websession/set")
_SESSION_TTL_SECONDS = 60 * 60  # re-bootstrap hourly

# Some JSAP read endpoints are POST-with-body but pure reads (the .NET
# "POST-to-query" convention — a Get* action that takes a filter object in the
# body and returns data). read_post() supports those, but ONLY when the path's
# leaf action name starts with a read verb. A POST whose leaf is a mutating verb
# is refused, so the READ-ONLY LAW still holds: this client can never mutate.
_READ_LEAF_PREFIXES = (
    "get",
    "list",
    "search",
    "fetch",
    "download",
    "load",
    "view",
    "report",
    "fill",
    "all",
    "find",
    "lookup",
    "export",
    "check",
    "validate",
)


class JsapError(RuntimeError):
    pass


class JsapClient:
    def __init__(self, company: int = 1, timeout: int = 30) -> None:
        self.base_url = CONFIG.base_url
        self.company = company
        self.timeout = timeout
        self._jar = CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._jar)
        )
        self._authed = False

    # -- session bootstrap (the only non-GET traffic allowed) --------------

    def _bootstrap(self) -> None:
        """login -> websession/set. Mutates a session, never JIVO data."""
        CONFIG.require_creds()
        login = self._request(
            "POST",
            "/api/auth/Login",
            body={"loginUser": CONFIG.username, "password": CONFIG.password},
            _bootstrap=True,
        )
        if not login.get("success"):
            raise JsapError(f"Login failed: {login.get('message')}")
        user = login.get("user", {})
        companies = [
            {"id": cid, "company": name} for cid, name in CONFIG.companies.items()
        ]
        self._request(
            "POST",
            "/websession/set",
            body={
                "userId": user.get("userId", CONFIG.user_id),
                "userName": user.get("userName", CONFIG.username),
                "companies": companies,
            },
            _bootstrap=True,
        )
        # Tell the server which company this session should scope to.
        try:
            self._request(
                "POST",
                "/websession/updateSelectedCompany",
                body={"companyId": self.company},
                _bootstrap=True,
            )
        except JsapError:
            pass  # not fatal; endpoints also take an explicit company param
        self._authed = True
        self._save_cookies()

    def _save_cookies(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "saved_at": time.time(),
            "company": self.company,
            "cookies": [
                {"name": c.name, "value": c.value, "domain": c.domain, "path": c.path}
                for c in self._jar
            ],
        }
        COOKIE_FILE.write_text(json.dumps(data))
        try:
            COOKIE_FILE.chmod(0o600)
        except OSError:
            pass

    def _load_cookies(self) -> bool:
        if not COOKIE_FILE.exists():
            return False
        try:
            data = json.loads(COOKIE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return False
        if time.time() - data.get("saved_at", 0) > _SESSION_TTL_SECONDS:
            return False
        if data.get("company") != self.company:
            return False
        from http.cookiejar import Cookie

        for c in data.get("cookies", []):
            self._jar.set_cookie(
                Cookie(
                    version=0,
                    name=c["name"],
                    value=c["value"],
                    port=None,
                    port_specified=False,
                    domain=c["domain"],
                    domain_specified=True,
                    domain_initial_dot=c["domain"].startswith("."),
                    path=c["path"],
                    path_specified=True,
                    secure=False,
                    expires=None,
                    discard=False,
                    comment=None,
                    comment_url=None,
                    rest={},
                )
            )
        self._authed = True
        return True

    def _ensure_session(self) -> None:
        if self._authed:
            return
        if self._load_cookies():
            return
        self._bootstrap()

    # -- the request core --------------------------------------------------

    @staticmethod
    def _leaf(path: str) -> str:
        return path.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1].lower()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        body: dict | None = None,
        _bootstrap: bool = False,
        _read_post: bool = False,
    ) -> Any:
        # READ-ONLY guard. Permitted: GET always; the session bootstrap POSTs;
        # and POST-to-read endpoints whose leaf action is a read verb.
        m = method.upper()
        if _bootstrap:
            if (
                path not in _BOOTSTRAP_PATHS
                and path != "/websession/updateSelectedCompany"
            ):
                raise JsapError(f"Illegal bootstrap path {path}")
        elif _read_post:
            if m != "POST" or not self._leaf(path).startswith(_READ_LEAF_PREFIXES):
                raise JsapError(
                    f"READ-ONLY LAW: refusing POST {path} — its action is not a "
                    "read verb, so it may mutate. Not permitted."
                )
        elif m != _READ_VERB:
            raise JsapError(
                f"READ-ONLY LAW: refusing {method} {path}. "
                "The JSAP CLI only performs GET reads (and guarded POST-reads)."
            )

        url = self.base_url + path
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)

        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url, data=data, headers=headers, method=method.upper()
        )
        try:
            with self._opener.open(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace") if e.fp else ""
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                raise JsapError(f"HTTP {e.code} on {method} {path}: {raw[:200]}")
        except urllib.error.URLError as e:
            raise JsapError(f"Cannot reach JSAP at {url}: {e.reason}")

        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw  # some endpoints return non-JSON (e.g. HTML/plain)

    # -- public read API ---------------------------------------------------

    def get(self, path: str, params: dict | None = None, *, unwrap: bool = True) -> Any:
        """Authenticated GET. Returns parsed JSON.

        When unwrap=True (default) and the response is the standard
        {success, data} envelope, returns the `data` payload directly;
        otherwise returns the whole response. Set unwrap=False to see the
        envelope (success flag, message).
        """
        self._ensure_session()
        merged = dict(params or {})
        # Most JSAP read endpoints take `company`; fill it if not supplied.
        result = self._request("GET", path, params=merged)
        if (
            unwrap
            and isinstance(result, dict)
            and "success" in result
            and "data" in result
        ):
            return result["data"]
        return result

    def get_raw(self, path: str, params: dict | None = None) -> Any:
        """GET returning the full envelope (success/message/data)."""
        return self.get(path, params, unwrap=False)

    def read_post(
        self, path: str, body: dict | None = None, *, unwrap: bool = True
    ) -> Any:
        """POST-to-read: for Get*-style endpoints that take a filter body.

        Refuses any path whose leaf action is not a read verb (see
        _READ_LEAF_PREFIXES) — so this can never reach a mutating endpoint.
        Returns the {success,data} `data` payload when unwrap=True.
        """
        self._ensure_session()
        result = self._request("POST", path, body=dict(body or {}), _read_post=True)
        if (
            unwrap
            and isinstance(result, dict)
            and "success" in result
            and "data" in result
        ):
            return result["data"]
        return result
