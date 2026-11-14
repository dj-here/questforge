import type { Metadata } from "next";
import "./globals.css";
import Navbar from "../components/Navbar";

export const metadata: Metadata = {
  title: "QuestForge - AI Question Engineering & HackerRank Publishing",
  description: "Production-grade automated coding question generation, sandbox validation, and HackerRank publishing pipeline.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans antialiased">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
          <p>QuestForge • Autonomous AI Question Generation & Sandbox Verification Platform</p>
        </footer>
      </body>
    </html>
  );
}
