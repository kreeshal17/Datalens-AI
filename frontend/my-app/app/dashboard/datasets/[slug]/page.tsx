"use client";

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Database,
  Download,
  FileSpreadsheet,
  Loader2,
  Sparkles,
  Wand2,
} from "lucide-react";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import api, { extractErrorMessage } from "@/lib/api";

interface Dataset {
  id: number;
  slug: string;
  name: string;
  file: string;
  status: string;
  row_count: number;
  column_count: number;
  quality_score: number | null;
  created_at: string;
  updated_at: string;
}

interface Issue {
  id: number;
  issue_type: string;
  column: string | null;
  row: number | null;
  severity: string;
  description: string;
  is_resolved: boolean;
}

export default function DatasetPage() {
  const params = useParams();
  const router = useRouter();

  const slug = params.slug as string;

  const [dataset, setDataset] =
    useState<Dataset | null>(null);

  const [issues, setIssues] =
    useState<Issue[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [downloading, setDownloading] =
    useState(false);

  const [applyingAll, setApplyingAll] =
    useState(false);

  const [fixAllMessage, setFixAllMessage] =
    useState("");

  const [analyzingAll, setAnalyzingAll] =
    useState(false);

  const [analyzeAllMessage, setAnalyzeAllMessage] =
    useState("");

  useEffect(() => {
    loadDataset();
  }, [slug]);

  async function analyzeAllIssues() {
    try {
      setAnalyzingAll(true);
      setAnalyzeAllMessage("");
      setError("");

      const response = await api.post<{
        analyzed_count: number;
        failed_count: number;
        failed: { issue_id: number; details: string }[];
      }>(`/api/datasets/${slug}/analyze/`);

      const { analyzed_count, failed_count } = response.data;

      if (analyzed_count === 0 && failed_count === 0) {
        setAnalyzeAllMessage("No unresolved issues to analyze.");
      } else if (failed_count === 0) {
        setAnalyzeAllMessage(
          `Analyzed ${analyzed_count} issue${analyzed_count === 1 ? "" : "s"}.`
        );
      } else {
        setAnalyzeAllMessage(
          `Analyzed ${analyzed_count} issue${analyzed_count === 1 ? "" : "s"}, ` +
          `${failed_count} failed - try again or analyze those individually.`
        );
      }

      // Suggested values may have changed (AI analysis can fill in
      // ai_suggested_value for issues that had none), so "Fix all"'s
      // count of what's fixable should reflect that too.
      await loadDataset();

    } catch (error) {
      console.error(error);
      setError(
        extractErrorMessage(
          (error as { response?: { data?: unknown } })?.response?.data,
          "Unable to analyze issues."
        )
      );

    } finally {
      setAnalyzingAll(false);
    }
  }

  async function applyAllFixes() {
    try {
      setApplyingAll(true);
      setFixAllMessage("");
      setError("");

      const response = await api.post<{
        fixed_count: number;
        skipped_count: number;
        skipped: { issue_id: number; reason: string }[];
        quality_score: number | null;
      }>(`/api/issues/${slug}/apply-all/`);

      const { fixed_count, skipped_count } = response.data;

      if (fixed_count === 0 && skipped_count === 0) {
        setFixAllMessage("No unresolved issues to fix.");
      } else if (skipped_count === 0) {
        setFixAllMessage(
          `Fixed ${fixed_count} issue${fixed_count === 1 ? "" : "s"}.`
        );
      } else {
        setFixAllMessage(
          `Fixed ${fixed_count} issue${fixed_count === 1 ? "" : "s"}, ` +
          `skipped ${skipped_count} (need AI analysis first).`
        );
      }

      // Row numbers may have shifted (duplicates removed) and the
      // quality score changed - reload everything from scratch rather
      // than patching state in place.
      await loadDataset();

    } catch (error) {
      console.error(error);
      setError(
        extractErrorMessage(
          (error as { response?: { data?: unknown } })?.response?.data,
          "Unable to apply fixes."
        )
      );

    } finally {
      setApplyingAll(false);
    }
  }

  async function downloadDataset() {
    try {
      setDownloading(true);

      const response = await api.get(
        `/api/datasets/${slug}/download/`,
        { responseType: "blob" }
      );

      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement("a");

      link.href = url;
      link.download = `${slug}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error(error);
      setError("Unable to download the dataset.");

    } finally {
      setDownloading(false);
    }
  }

  async function loadDataset() {
    try {
      setLoading(true);
      setError("");

      /*
       * First get datasets belonging to
       * the authenticated user.
       */

      const datasetResponse =
        await api.get<Dataset[]>(
          "/api/datasets/"
        );

      const foundDataset =
        datasetResponse.data.find(
          (dataset) =>
            dataset.slug === slug
        );

      if (!foundDataset) {
        setError("Dataset not found.");
        return;
      }

      setDataset(foundDataset);

      /*
       * Now use the slug to get issues.
       */

      const issueResponse =
        await api.get<Issue[]>(
          `/api/issues/${slug}/issues/`
        );

      setIssues(issueResponse.data);

    } catch (error) {
      console.error(error);

      setError(
        "Unable to load dataset details."
      );

    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-[#060910] flex items-center justify-center text-white">

        <div className="text-center">

          <Loader2 className="mx-auto h-7 w-7 animate-spin text-blue-400" />

          <p className="mt-4 text-sm text-slate-500">
            Loading dataset...
          </p>

        </div>

      </main>
    );
  }

  if (!dataset) {
    return (
      <main className="min-h-screen bg-[#060910] text-white">

        <div className="mx-auto max-w-5xl px-6 py-10">

          <button
            onClick={() =>
              router.push("/dashboard")
            }
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            Dashboard
          </button>

          <div className="mt-12 rounded-2xl border border-red-500/20 bg-red-500/[0.04] p-12 text-center">

            <AlertTriangle className="mx-auto h-8 w-8 text-red-400" />

            <h2 className="mt-4 text-lg font-semibold">
              Dataset not found
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              {error}
            </p>

          </div>

        </div>

      </main>
    );
  }

  const highIssues = issues.filter(
    (issue) =>
      issue.severity === "HIGH"
  ).length;

  const mediumIssues = issues.filter(
    (issue) =>
      issue.severity === "MEDIUM"
  ).length;

  const lowIssues = issues.filter(
    (issue) =>
      issue.severity === "LOW"
  ).length;

  const unresolvedCount = issues.filter(
    (issue) => !issue.is_resolved
  ).length;

  return (
    <main className="min-h-screen bg-[#060910] text-white">

      <header className="border-b border-white/[0.06]">

        <div className="mx-auto max-w-7xl px-6 py-8">

          <button
            onClick={() =>
              router.push("/dashboard")
            }
            className="mb-7 flex items-center gap-2 text-sm text-slate-500 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            Dashboard
          </button>

          <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">

            <div>

              <div className="flex items-center gap-4">

                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10">
                  <FileSpreadsheet className="h-6 w-6 text-emerald-400" />
                </div>

                <div>

                  <h1 className="text-3xl font-semibold">
                    {dataset.name}
                  </h1>

                  <p className="mt-1 font-mono text-xs text-slate-600">
                    slug: {dataset.slug}
                  </p>

                </div>

              </div>

            </div>

            <div className="flex items-center gap-3">

              <button
                onClick={downloadDataset}
                disabled={downloading}
                className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition hover:border-emerald-500/30 hover:text-white disabled:opacity-50"
              >
                {downloading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                {downloading ? "Preparing..." : "Download CSV"}
              </button>

              <div
                className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                  dataset.status === "ANALYZED"
                    ? "bg-emerald-500/10 text-emerald-400"
                    : dataset.status === "PROCESSING"
                    ? "bg-yellow-500/10 text-yellow-400"
                    : "bg-red-500/10 text-red-400"
                }`}
              >
                {dataset.status}
              </div>

            </div>

          </div>

        </div>

      </header>

      <div className="mx-auto max-w-7xl px-6 py-8">

        {/* Dataset information */}

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <InfoCard
            icon={<Database className="h-5 w-5" />}
            label="Rows"
            value={dataset.row_count.toLocaleString()}
          />

          <InfoCard
            icon={<FileSpreadsheet className="h-5 w-5" />}
            label="Columns"
            value={dataset.column_count.toString()}
          />

          <InfoCard
            icon={<BarChart3 className="h-5 w-5" />}
            label="Quality score"
            value={
              dataset.quality_score !== null
                ? `${dataset.quality_score.toFixed(1)}%`
                : "—"
            }
          />

          <InfoCard
            icon={<AlertTriangle className="h-5 w-5" />}
            label="Issues"
            value={issues.length.toString()}
          />

        </section>

        {/* Severity */}

        <section className="mt-6 grid gap-4 sm:grid-cols-3">

          <SeverityCard
            label="High"
            value={highIssues}
            className="text-red-400"
          />

          <SeverityCard
            label="Medium"
            value={mediumIssues}
            className="text-yellow-400"
          />

          <SeverityCard
            label="Low"
            value={lowIssues}
            className="text-blue-400"
          />

        </section>

        {/* Issues */}

        <section className="mt-8">

          <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">

            <div>

              <div className="flex items-center gap-2">

                <Sparkles className="h-5 w-5 text-blue-400" />

                <h2 className="text-xl font-semibold">
                  Detected issues
                </h2>

              </div>

              <p className="mt-2 text-sm text-slate-500">
                Problems discovered during dataset analysis. Fix them
                one at a time below, or handle everything at once.
              </p>

            </div>

            {unresolvedCount > 0 && (
              <div className="flex shrink-0 flex-wrap items-center gap-3">

                <button
                  onClick={analyzeAllIssues}
                  disabled={analyzingAll || applyingAll}
                  className="flex items-center gap-2 rounded-xl border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-400 transition hover:bg-blue-500/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {analyzingAll ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                  {analyzingAll
                    ? "Analyzing... (can take a while)"
                    : `Analyze all (${unresolvedCount})`}
                </button>

                <button
                  onClick={applyAllFixes}
                  disabled={applyingAll || analyzingAll}
                  className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-sm font-medium text-emerald-400 transition hover:bg-emerald-500/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {applyingAll ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Wand2 className="h-4 w-4" />
                  )}
                  {applyingAll
                    ? "Applying fixes..."
                    : `Fix all (${unresolvedCount})`}
                </button>

              </div>
            )}

          </div>

          {analyzeAllMessage && (
            <div className="mb-3 rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-3 text-sm text-blue-300">
              {analyzeAllMessage}
            </div>
          )}

          {fixAllMessage && (
            <div className="mb-5 rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-3 text-sm text-blue-300">
              {fixAllMessage}
            </div>
          )}

          {issues.length === 0 ? (

            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.04] p-12 text-center">

              <CheckCircle2 className="mx-auto h-9 w-9 text-emerald-400" />

              <h3 className="mt-4 font-semibold">
                No issues detected
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                This dataset looks clean.
              </p>

            </div>

          ) : (

            <div className="space-y-3">

              {issues.map((issue) => (

                <div
                  key={issue.id}
                  onClick={() =>
                    router.push(
                      `/dashboard/datasets/${slug}/issues/${issue.id}`
                    )
                  }
                  className="cursor-pointer rounded-2xl border border-white/[0.07] bg-white/[0.025] p-5 transition hover:border-blue-500/20 hover:bg-white/[0.04]"
                >

                  <div className="flex items-start justify-between gap-5">

                    <div>

                      <div className="flex flex-wrap items-center gap-3">

                        <h3 className="font-medium">
                          {issue.issue_type.replaceAll(
                            "_",
                            " "
                          )}
                        </h3>

                        <span
                          className={`rounded-full px-2 py-1 text-[10px] font-medium ${
                            issue.severity === "HIGH"
                              ? "bg-red-500/10 text-red-400"
                              : issue.severity === "MEDIUM"
                              ? "bg-yellow-500/10 text-yellow-400"
                              : "bg-blue-500/10 text-blue-400"
                          }`}
                        >
                          {issue.severity}
                        </span>

                        {issue.is_resolved && (
                          <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-1 text-[10px] font-medium text-emerald-400">
                            <CheckCircle2 className="h-3 w-3" />
                            Fixed
                          </span>
                        )}

                      </div>

                      <p className="mt-2 text-sm text-slate-400">
                        {issue.description}
                      </p>

                      <div className="mt-3 flex gap-5 text-xs text-slate-600">

                        {issue.column && (
                          <span>
                            Column: {issue.column}
                          </span>
                        )}

                        {issue.row !== null && (
                          <span>
                            Row: {issue.row}
                          </span>
                        )}

                      </div>

                    </div>

                    <ArrowRight className="h-4 w-4 shrink-0 text-slate-700" />

                  </div>

                </div>

              ))}

            </div>

          )}

        </section>

      </div>

    </main>
  );
}


function InfoCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.025] p-5">

      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/[0.05] text-slate-400">
        {icon}
      </div>

      <p className="mt-4 text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-2xl font-semibold">
        {value}
      </p>

    </div>
  );
}


function SeverityCard({
  label,
  value,
  className,
}: {
  label: string;
  value: number;
  className: string;
}) {
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.025] p-5">

      <p className="text-xs text-slate-500">
        {label} severity
      </p>

      <p className={`mt-2 text-2xl font-semibold ${className}`}>
        {value}
      </p>

    </div>
  );
}