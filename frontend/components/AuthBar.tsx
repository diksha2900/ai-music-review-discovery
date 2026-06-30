"use client";

import { useAuth } from "./AuthProvider";
import { loginUrl } from "@/lib/api";

export function AuthBar() {
  const { user, loading, logout } = useAuth();

  if (loading) return null;

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
