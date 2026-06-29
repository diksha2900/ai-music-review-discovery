"""Local time for vibe suggestions — Streamlit Cloud runs in UTC, users don't."""

import datetime

import streamlit as st
import streamlit.components.v1 as components
from zoneinfo import ZoneInfo

_FALLBACK = "Asia/Kolkata"


def ensure_user_tz() -> ZoneInfo:
    """Use the phone/browser timezone (via ?tz= query param), not server UTC."""
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

    # First load: read timezone from the user's browser, then reload once.
    components.html(
        """
        <script>
        (function () {
            const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const url = new URL(window.parent.location.href);
            if (url.searchParams.get("tz") !== tz) {
                url.searchParams.set("tz", tz);
                window.parent.location.replace(url.toString());
            }
        })();
        </script>
        """,
        height=0,
        width=0,
    )
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
