"""'Remember me': the chess.com username (and the sidebar settings) are kept in a small browser cookie, so a returning visitor lands on their own
games without typing anything.

A cookie, not a database row, because the app has no sign-in: the browser is the only thing that identifies a visitor. The cookie holds nothing
secret (a public chess.com username, the analysis depth and the number of games) and is only ever read back after being checked."""
from __future__ import annotations

import json
import re
from urllib.parse import quote, unquote

import streamlit as st

from .state import DEPTHS

COOKIE = "cc_prefs"
_USER = re.compile(r"[a-z0-9_\-]{2,40}")

JS = """
export default function (component) {
  const { data } = component;
  const name = data.name;
  const hit = document.cookie.split('; ').find((c) => c.startsWith(name + '='));
  const current = hit ? hit.slice(name.length + 1) : '';
  const secure = location.protocol === 'https:' ? '; Secure' : '';
  if (data.forget) {
    if (current) document.cookie = name + '=; Max-Age=0; Path=/; SameSite=Lax' + secure;
    return;
  }
  if (data.value && current !== data.value) {
    document.cookie = name + '=' + data.value + '; Max-Age=31536000; Path=/; SameSite=Lax' + secure;
  }
}
"""

_component = st.components.v2.component("chess_coach_remember", js=JS)


def parse(raw) -> dict:
    """The saved preferences from a cookie value, checked. Anything odd gives {} (a stranger's or an old cookie must never break the app)."""
    if not raw or not isinstance(raw, str):
        return {}
    try:
        data = json.loads(unquote(raw))
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    out = {}
    user = data.get("u")
    if isinstance(user, str) and _USER.fullmatch(user.strip().lower()):
        out["u"] = user.strip().lower()
    depth = data.get("d")
    if isinstance(depth, int) and not isinstance(depth, bool) and 0 <= depth < len(DEPTHS):
        out["d"] = depth
    n = data.get("n")
    if isinstance(n, int) and not isinstance(n, bool) and 5 <= n <= 40:
        out["n"] = n
    return out


def serialize(user: str, depth_name: str, n_games: int) -> str:
    names = list(DEPTHS)
    d = names.index(depth_name) if depth_name in names else 1
    return quote(json.dumps({"u": user, "d": d, "n": int(n_games)}, separators=(",", ":")), safe="")


def read() -> dict:
    """The preferences cookie sent with this page load ({} when there is none, or when Streamlit can't tell, e.g. in tests)."""
    try:
        return parse(st.context.cookies.get(COOKIE))
    except Exception:                                             # noqa: BLE001
        return {}


def sync(user: str = "", depth_name: str = "", n_games: int = 20, forget: bool = False) -> None:
    """Writes (or, with forget=True, deletes) the cookie in the browser. Draws nothing."""
    value = "" if forget or not user else serialize(user, depth_name, n_games)
    with st.container(key="remembersync"):
        _component(key="remember_cookie", data={"name": COOKIE, "value": value, "forget": bool(forget)})
