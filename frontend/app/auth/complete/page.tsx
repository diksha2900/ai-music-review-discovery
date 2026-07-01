"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setSessionId } from "@/lib/session";

function AuthCompleteInner() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const err = params.get("auth_error");
    if (err) {
      router.replace(`/?auth_error=${encodeURIComponent(err)}`);
      return;
    }
    const sid = params.get("session");
    if (sid) {
      setSessionId(decodeURIComponent(sid));
      router.replace("/");
      return;
    }
    router.replace("/?auth_error=missing_session");
  }, [params, router]);

  return <div className="loading-pulse">Logging you in with Spotify…</div>;
}

export default function AuthCompletePage() {
  return (
    <Suspense fallback={<div className="loading-pulse">Logging you in with Spotify…</div>}>
      <AuthCompleteInner />
    </Suspense>
  );
}
