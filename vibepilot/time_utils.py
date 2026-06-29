"""Local time for vibe suggestions — Streamlit Cloud runs in UTC, users don't."""

import datetime

import streamlit as st
from zoneinfo import ZoneInfo

_FALLBACK = "Asia/Kolkata"


def ensure_user_tz() -> ZoneInfo:
    """Use browser timezone from ?tz= if present, else a sensible default."""
    cached = st.session_state.get("user_tz")
    if cached:
        try:
            return ZoneInfo(cached)
        except Exception:
            pass

    qp = st.query_params.get("tz")
    if qp:
        try:
            st.session_state["user_tz"] = qp
            return ZoneInfo(qp)
        except Exception:
            pass

    try:
        return ZoneInfo(_FALLBACK)
    except Exception:
        return ZoneInfo("UTC")


def local_now() -> datetime.datetime:
    return datetime.datetime.now(ensure_user_tz())


def format_clock(now: datetime.datetime | None = None) -> str:
    now = now or local_now()
    h = now.hour % 12 or 12
    return f"{h}:{now.minute:02d} {now.strftime('%p').lower()}"
