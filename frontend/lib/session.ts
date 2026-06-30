const SESSION_KEY = "vp_session";

export function getSessionId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(SESSION_KEY);
}

export function setSessionId(id: string) {
  localStorage.setItem(SESSION_KEY, id);
}

export function clearSessionId() {
  localStorage.removeItem(SESSION_KEY);
}

/** After OAuth redirect: ?session=... → save and strip from URL. */
export function captureSessionFromUrl() {
  if (typeof window === "undefined") return false;
  const params = new URLSearchParams(window.location.search);
  const sid = params.get("session");
  if (!sid) return false;
  setSessionId(sid);
  params.delete("session");
  params.delete("logged_in");
  const rest = params.toString();
  const path = window.location.pathname + (rest ? `?${rest}` : "");
  window.history.replaceState({}, "", path);
  return true;
}

export function authHeaders(): Record<string, string> {
  const sid = getSessionId();
  return sid ? { "X-VP-Session": sid } : {};
}
