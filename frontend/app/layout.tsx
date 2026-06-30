import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "VibePilot",
  description: "Same feel, different blood.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="layout">
          <aside className="sidebar">
            <div className="logo">🎧 VibePilot</div>
            <Nav />
            <p className="tagline">Same feel, different blood.</p>
          </aside>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
