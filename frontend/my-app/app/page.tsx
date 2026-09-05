"use client";

import { useState } from "react";
import Link from "next/link";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import {
  Sparkles,
  Upload,
  ScanLine,
  AlertTriangle,
  Brain,
  Wand2,
  ArrowRight,
  Menu,
  X,
  CheckCircle2,
} from "lucide-react";

const display = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
});

const body = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
});

interface Row {
  id: string;
  email: string;
  date: string;
  country: string;
  amount: string;
  issues: string[];
}

const rows: Row[] = [
  { id: "1001", email: "sam.k@acme.io", date: "2024-01-12", country: "US", amount: "$129.00", issues: [] },
  { id: "1002", email: "", date: "2024-01-13", country: "US", amount: "$89.50", issues: ["email"] },
  { id: "1002", email: "j.lee@acme.io", date: "2024-01-13", country: "US", amount: "$89.50", issues: ["id"] },
  { id: "1004", email: "m.diaz@acme", date: "13/25/2024", country: "CA", amount: "$210.00", issues: ["email", "date"] },
  { id: "1005", email: "k.omar@acme.io", date: "2024-01-15", country: "—", amount: "$15,200.00", issues: ["country", "amount"] },
  { id: "1006", email: "r.chen@acme.io", date: "2024-01-16", country: "UK", amount: "$76.20", issues: [] },
];

const columns: { key: keyof Row; label: string }[] = [
  { key: "id", label: "id" },
  { key: "email", label: "email" },
  { key: "date", label: "signup_date" },
  { key: "country", label: "country" },
  { key: "amount", label: "revenue" },
];

const pipeline = [
  { icon: Upload, title: "Upload", desc: "Drop in a CSV. No schema setup, no config files.", live: true },
  { icon: ScanLine, title: "Profile", desc: "Row and column counts, types, and a quality score computed automatically.", live: true },
  { icon: AlertTriangle, title: "Detect issues", desc: "Missing values, duplicates, anomalies, and invalid formats flagged by severity.", live: true },
  { icon: Brain, title: "Root cause", desc: "AI explains why each issue happened, in plain language.", live: false },
  { icon: Wand2, title: "Fix & export", desc: "One-click corrections and a clean CSV ready to download.", live: false },
];

const detections = [
  { title: "Missing values", desc: "Empty cells and null-like placeholders across every column." },
  { title: "Duplicate records", desc: "Rows and keys that repeat when they shouldn't." },
  { title: "Anomalies", desc: "Values that sit far outside a column's normal range." },
  { title: "Invalid formats", desc: "Malformed emails, dates, and mismatched types." },
];

const stack = ["Next.js", "TypeScript", "Django REST", "Simple JWT", "Pandas", "HttpOnly cookies"];

export default function Home() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <main
      className={`${display.variable} ${body.variable} ${mono.variable} min-h-screen bg-[#05070c] text-[#e7ebf3] [font-family:var(--font-body)]`}
    >
      <style>{`
        @keyframes cellFix {
          0%, 8% { background-color: rgba(248,113,113,0.14); color: #fca5a5; border-color: rgba(248,113,113,0.35); }
          18%, 24% { background-color: rgba(59,130,246,0.18); color: #93c5fd; border-color: rgba(59,130,246,0.4); }
          34%, 92% { background-color: rgba(52,211,153,0.12); color: #6ee7b7; border-color: rgba(52,211,153,0.35); }
          100% { background-color: rgba(248,113,113,0.14); color: #fca5a5; border-color: rgba(248,113,113,0.35); }
        }
        @keyframes scanBeam {
          0% { transform: translateY(-10%); opacity: 0; }
          8% { opacity: 1; }
          45% { opacity: 1; }
          55% { opacity: 0; }
          100% { transform: translateY(2400%); opacity: 0; }
        }
        .cell-issue { animation: cellFix 7s ease-in-out infinite; }
        .scan-beam { animation: scanBeam 7s ease-in-out infinite; }
        @media (prefers-reduced-motion: reduce) {
          .cell-issue { animation: none; background-color: rgba(52,211,153,0.12); color: #6ee7b7; border-color: rgba(52,211,153,0.35); }
          .scan-beam { display: none; }
        }
      `}</style>

      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/3 h-96 w-96 rounded-full bg-blue-600/10 blur-3xl" />
        <div className="absolute top-1/3 right-0 h-96 w-96 rounded-full bg-violet-600/10 blur-3xl" />
      </div>

      <nav className="relative z-20 border-b border-white/[0.06] bg-[#05070c]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-violet-600">
              <Sparkles className="h-4 w-4" />
            </div>
            <span className="text-sm font-semibold [font-family:var(--font-display)]">
              Data Quality AI
            </span>
          </div>

          <div className="hidden items-center gap-8 md:flex">
            <a href="#how-it-works" className="text-sm text-slate-400 transition hover:text-white">
              How it works
            </a>
            <a href="#what-we-detect" className="text-sm text-slate-400 transition hover:text-white">
              What we detect
            </a>
            <Link href="/login" className="text-sm text-slate-400 transition hover:text-white">
              Log in
            </Link>
            <Link
              href="/signup"
              className="flex items-center gap-1.5 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
            >
              Get started
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 md:hidden"
          >
            {menuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>

        {menuOpen && (
          <div className="flex flex-col gap-4 border-t border-white/[0.06] px-6 py-5 md:hidden">
            <a href="#how-it-works" onClick={() => setMenuOpen(false)} className="text-sm text-slate-400">
              How it works
            </a>
            <a href="#what-we-detect" onClick={() => setMenuOpen(false)} className="text-sm text-slate-400">
              What we detect
            </a>
            <Link href="/login" className="text-sm text-slate-400">
              Log in
            </Link>
            <Link
              href="/signup"
              className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-slate-950"
            >
              Get started
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        )}
      </nav>

      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-20 pt-16 md:pb-28 md:pt-24">
        <div className="grid gap-14 lg:grid-cols-[1.05fr_1fr] lg:items-center">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs font-medium uppercase tracking-wider text-blue-300">
              <Sparkles className="h-3 w-3" />
              AI-powered data quality
            </div>

            <h1 className="text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl lg:text-6xl [font-family:var(--font-display)]">
              Upload your data.
              <br />
              Find what&apos;s wrong.
              <br />
              Understand why.{" "}
              <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
                Fix it.
              </span>
            </h1>

            <p className="mt-6 max-w-lg text-base leading-7 text-slate-400">
              Data Quality AI profiles every dataset you upload, scores it,
              and flags missing values, duplicates, anomalies, and invalid
              formats before they cost you a bad decision.
            </p>

            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="group flex items-center justify-center gap-2 rounded-xl bg-white px-6 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
              >
                Upload a dataset
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
              
               <a href="#how-it-works"
                className="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-6 py-3.5 text-sm font-medium text-slate-200 transition hover:bg-white/[0.06]">
                See how it works
              </a>
            </div>

            <p className="mt-5 text-xs text-slate-600">
              No credit card. Just a CSV.
            </p>
          </div>

          <div className="relative">
            <div className="absolute -inset-px rounded-2xl bg-gradient-to-br from-blue-500/20 via-transparent to-violet-500/20 blur-xl" />

            <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0c1120] shadow-2xl shadow-black/40">
              <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
                <span className="text-xs text-slate-500 [font-family:var(--font-mono)]">
                  customers.csv
                </span>
                <span className="flex items-center gap-1.5 text-xs text-emerald-400">
                  <CheckCircle2 className="h-3 w-3" />
                  scanning
                </span>
              </div>

              <div className="relative overflow-hidden">
                <div className="scan-beam pointer-events-none absolute left-0 right-0 top-0 h-8 bg-gradient-to-b from-transparent via-blue-400/10 to-transparent" />

                <table className="w-full border-collapse text-xs [font-family:var(--font-mono)]">
                  <thead>
                    <tr>
                      {columns.map((col) => (
                        <th
                          key={col.key}
                          className="border-b border-white/[0.06] px-3 py-2.5 text-left font-normal text-slate-500"
                        >
                          {col.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, i) => (
                      <tr key={i}>
                        {columns.map((col) => {
                          const hasIssue = row.issues.includes(col.key as string);
                          const value = row[col.key] || "—";
                          return (
                            <td
                              key={col.key}
                              className={
                                hasIssue
                                  ? "cell-issue border border-white/[0.04] px-3 py-2.5"
                                  : "border-b border-white/[0.04] px-3 py-2.5 text-slate-300"
                              }
                              style={hasIssue ? { animationDelay: `${i * 0.9}s` } : undefined}
                            >
                              {value}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between border-t border-white/[0.06] px-4 py-3">
                <span className="text-xs text-slate-500">4 issues found</span>
                <span className="text-xs font-semibold text-blue-300">
                  Quality score: 78.4%
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="relative z-10 border-t border-white/[0.06] bg-white/[0.015]">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="mb-14 max-w-xl">
            <p className="text-xs font-medium uppercase tracking-wider text-blue-400">
              The pipeline
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl [font-family:var(--font-display)]">
              From raw CSV to trusted data
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              Every dataset moves through the same five stages. The first
              three run the moment you upload.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-5">
            {pipeline.map((step, i) => (
              <div
                key={step.title}
                className="relative rounded-2xl border border-white/[0.07] bg-white/[0.025] p-5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-600 [font-family:var(--font-mono)]">
                    0{i + 1}
                  </span>
                  {!step.live && (
                    <span className="rounded-full border border-amber-500/25 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-400">
                      Coming soon
                    </span>
                  )}
                </div>

                <div
                  className={
                    step.live
                      ? "mt-4 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400"
                      : "mt-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.05] text-slate-500"
                  }
                >
                  <step.icon className="h-5 w-5" />
                </div>

                <h3 className="mt-4 text-sm font-semibold">{step.title}</h3>
                <p className="mt-1.5 text-xs leading-5 text-slate-500">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="what-we-detect" className="relative z-10 mx-auto max-w-7xl px-6 py-20">
        <div className="mb-12 max-w-xl">
          <p className="text-xs font-medium uppercase tracking-wider text-blue-400">
            Detection
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl [font-family:var(--font-display)]">
            What gets caught
          </h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            Every issue is tagged with a severity so you know what to fix
            first.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {detections.map((d) => (
            <div
              key={d.title}
              className="rounded-2xl border border-white/[0.07] bg-white/[0.025] p-5 transition hover:border-white/[0.12] hover:bg-white/[0.04]"
            >
              <h3 className="text-sm font-semibold">{d.title}</h3>
              <p className="mt-2 text-xs leading-5 text-slate-500">
                {d.desc}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3 rounded-2xl border border-white/[0.07] bg-white/[0.025] px-5 py-4">
          <span className="text-xs text-slate-500">Severity:</span>
          <span className="flex items-center gap-1.5 text-xs text-red-400">
            <span className="h-1.5 w-1.5 rounded-full bg-red-400" /> High
          </span>
          <span className="flex items-center gap-1.5 text-xs text-amber-400">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" /> Medium
          </span>
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="h-1.5 w-1.5 rounded-full bg-slate-400" /> Low
          </span>
        </div>
      </section>

      <section className="relative z-10 border-t border-white/[0.06] bg-white/[0.015]">
        <div className="mx-auto max-w-7xl px-6 py-14">
          <p className="text-center text-xs font-medium uppercase tracking-wider text-slate-500">
            Built with production-grade foundations
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            {stack.map((item) => (
              <span
                key={item}
                className="rounded-full border border-white/10 bg-white/[0.03] px-3.5 py-1.5 text-xs text-slate-400 [font-family:var(--font-mono)]"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-7xl px-6 py-24 text-center">
        <h2 className="mx-auto max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl [font-family:var(--font-display)]">
          Stop guessing what&apos;s wrong with your data.
        </h2>
        <p className="mx-auto mt-4 max-w-md text-sm text-slate-400">
          Upload a CSV and get a quality score, a full issue breakdown, and a
          clear place to start fixing it.
        </p>

        <div className="mt-8 flex flex-col items-center gap-4">
          <Link
            href="/signup"
            className="group flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
          >
            Create free account
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link href="/login" className="text-xs text-slate-500 hover:text-slate-300">
            Already have an account? Log in
          </Link>
        </div>
      </section>

      <footer className="relative z-10 border-t border-white/[0.06] px-6 py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-violet-600">
              <Sparkles className="h-3 w-3" />
            </div>
            <span className="text-xs text-slate-500">Data Quality AI</span>
          </div>
          <p className="text-xs text-slate-600">
            Upload your data. Find what&apos;s wrong. Understand why. Fix it.
          </p>
        </div>
      </footer>
    </main>
  );
}