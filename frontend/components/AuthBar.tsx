"use client";

import { loginUrl } from "@/lib/api";

export function LoginButton({ className = "" }: { className?: string }) {
  return (
    <button
      type="button"
      className={`btn btn-outline ${className}`.trim()}
      onClick={() => {
        window.location.assign(loginUrl());
      }}
    >
      Log in with Spotify
    </button>
  );
}
