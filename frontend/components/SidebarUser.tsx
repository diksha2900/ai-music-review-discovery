"use client";

import { useAuth } from "./AuthProvider";

export function SidebarGreeting() {
  const { user, loading } = useAuth();
  if (loading || !user?.logged_in) return null;
  return (
    <p className="sidebar-greeting">
      Hi, <strong>{user.display_name || "there"}</strong>
    </p>
  );
}

export function SidebarLogout() {
  const { user, loading, logout } = useAuth();
  if (loading || !user?.logged_in) return null;
  return (
    <button type="button" className="btn btn-outline btn-sm sidebar-logout" onClick={() => logout()}>
      Log out
    </button>
  );
}
