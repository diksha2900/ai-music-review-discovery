import Link from "next/link";
import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/AuthProviderWrapper";
import { MainContent } from "@/components/MainContent";
import { Nav } from "@/components/Nav";
import { SidebarGreeting, SidebarLogout } from "@/components/SidebarUser";

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
              <SidebarGreeting />
              <Nav />
              <div className="sidebar-footer">
                <SidebarLogout />
                <p className="tagline">Same feel, different artists.</p>
              </div>
            </aside>
            <MainContent>{children}</MainContent>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
