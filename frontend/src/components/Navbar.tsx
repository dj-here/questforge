"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, Layers, CheckCircle2, Send, History, Activity } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = () => {
      fetch("/health", { cache: "no-store" })
        .then((res) => setHealthy(res.ok))
        .catch(() => {
          fetch("http://localhost:8000/health", { cache: "no-store" })
            .then((res) => setHealthy(res.ok))
            .catch(() => setHealthy(false));
        });
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const navLinks = [
    { name: "Dashboard", href: "/", icon: Layers },
    { name: "Review Queue", href: "/review", icon: CheckCircle2 },
    { name: "Publishing", href: "/publish", icon: Send },
    { name: "History & Archive", href: "/history", icon: History },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-900 border-b border-slate-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
        {/* Brand */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">
                QuestForge
              </span>
              <span className="px-1.5 py-0.5 text-[10px] uppercase font-bold tracking-wider bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 rounded">
                v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400">AI Coding Question Engine</p>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          {navLinks.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/70"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Status / Role */}
        <div className="flex items-center space-x-3">
          <div
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
              healthy === true
                ? "bg-emerald-950/60 text-emerald-400 border-emerald-800"
                : healthy === false
                ? "bg-rose-950/60 text-rose-400 border-rose-800"
                : "bg-slate-800 text-slate-400 border-slate-700"
            }`}
            title={healthy ? "Backend API Online" : "Backend API Offline"}
          >
            <Activity className="w-3.5 h-3.5 animate-pulse" />
            <span>{healthy === true ? "Online" : healthy === false ? "Offline" : "Checking"}</span>
          </div>
          <div className="hidden sm:flex items-center space-x-2 bg-slate-800/80 px-3 py-1 rounded-lg border border-slate-700 text-xs">
            <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
            <span className="text-slate-300 font-medium">Reviewer</span>
          </div>
        </div>
      </div>
    </header>
  );
}
