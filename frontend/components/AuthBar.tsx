"use client";

import { useAuth } from "./AuthProvider";
import { loginUrl } from "@/lib/api";

export function LoginButton({ className = "" }: { className?: string }) {
  return (
    <a href={loginUrl()} className={`btn btn-outline ${className}`.trim()}>
      Log in with Spotify
    </a>
  );
}
