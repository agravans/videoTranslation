import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI L&D Translation Platform",
  description: "BFSI compliance training in every language your team speaks",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        <nav className="bg-brand-700 text-white px-6 py-3 flex items-center gap-4">
          <span className="font-bold text-lg tracking-tight">L&D Translate</span>
          <span className="text-brand-100 text-sm">BFSI Compliance Training Localization</span>
          <div className="ml-auto flex gap-4 text-sm">
            <a href="/" className="hover:text-brand-100">Dashboard</a>
            <a href="/jobs/new" className="hover:text-brand-100">New Job</a>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
