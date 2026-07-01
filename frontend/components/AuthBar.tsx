"use client";

import { useAuth } from "./AuthProvider";
import { loginUrl } from "@/lib/api";

/** Sidebar: logout only when logged in. Login lives on the home hero. */
export function AuthBar() {
  const { user, loading, logout } = useAuth();

  if (loading || !user?.logged_in) return null;

  return (
    <div className="auth-bar">
      <span className="auth-name">{user.display_name || "Logged in"}</span>
      <button type="button" className="btn btn-outline btn-sm" onClick={logout}>
        Log out
      </button>
    </div>
  );
}

export function LoginButton({ className = "" }: { className?: string }) {
  return (
    <a href={loginUrl()} className={`btn btn-outline ${className}`.trim()}>
      Log in with Spotify
    </a>
  );
}
