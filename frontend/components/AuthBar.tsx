"use client";

import { useEffect, useState } from "react";
import { authMe, loginUrl } from "@/lib/api";
import { captureSessionFromUrl, clearSessionId } from "@/lib/session";

export function AuthBar() {
  const [user, setUser] = useState<{ logged_in: boolean; display_name?: string } | null>(null);

  async function refresh() {
    const me = await authMe();
    setUser(me);
  }

  useEffect(() => {
    if (captureSessionFromUrl()) {
      refresh();
      return;
    }
    refresh();
  }, []);

  async function logout() {
    clearSessionId();
    setUser({ logged_in: false });
  }

  if (user?.logged_in) {
    return (
      <div className="auth-bar">
        <span className="auth-name">Hi, {user.display_name || "listener"}</span>
        <button type="button" className="btn btn-outline btn-sm" onClick={logout}>
          Log out
        </button>
      </div>
    );
  }

  return (
    <div className="auth-bar">
      <a href={loginUrl()} className="btn btn-outline btn-sm">
        Log in with Spotify
      </a>
    </div>
  );
}
