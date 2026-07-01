import Link from "next/link";
import type { Metadata } from "next";
import "./globals.css";
import { AuthBar } from "@/components/AuthBar";
import { AuthProvider } from "@/components/AuthProviderWrapper";
import { MainContent } from "@/components/MainContent";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "VibePilot",
  description: "Same feel, different artists.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <div className="layout">
            <aside className="sidebar">
              <Link href="/" className="logo logo-link">
                🎧 VibePilot
              </Link>
              <Nav />
              <AuthBar />
              <p className="tagline">Same feel, different artists.</p>
            </aside>
            <MainContent>{children}</MainContent>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
