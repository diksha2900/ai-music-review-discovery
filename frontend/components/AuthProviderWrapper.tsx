"use client";

import { Suspense } from "react";
import { AuthProvider as Provider } from "./AuthProvider";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={null}>
      <Provider>{children}</Provider>
    </Suspense>
  );
}
