"use client";

import { usePathname } from "next/navigation";

/** Force a fresh mount when switching sidebar routes (clears stale search results). */
export function MainContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <main className="main" key={pathname}>
      {children}
    </main>
  );
}
