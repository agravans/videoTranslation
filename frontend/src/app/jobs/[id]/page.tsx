"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, Job } from "@/lib/api";

const STAGE_LABELS: Record<string, string> = {
  ingest: "Extract Audio",
  transcribe: "Transcribe",
};

function stageLabel(name: string) {
  if (STAGE_LABELS[name]) return STAGE_LABELS[name];
  const parts = name.split(":");
  if (parts.length === 2) {
    const [type, lang] = parts;
    const labels: Record<string, string> = {
      translate: "Translate",
      qa: "QA Check",
      subtitle: "Generate Subtitles",
      tts: "TTS Dubbing",
      sync: "Audio Sync",
      lipsync: "Lip Sync",
    };
    return `${labels[type] || type} [${lang}]`;
  }
  return name;
}

const STATUS_DOT: Record<string, string> = {
  pending: "bg-gray-300",
  running: "bg-blue-400 animate-pulse",
  done: "bg-green-500",
  skipped: "bg-gray-300",
  error: "bg-red-500",
};

export default function JobDetailPage() {
  const { id } = useParams() as { id: string };
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    api.getJob(id).then(setJob);
    const interval = setInterval(() => {
      api.getJob(id).then((j) => {
        setJob(j);
        if (["completed", "failed", "awaiting_review"].includes(j.status)) {
          clearInterval(interval);
        }
      });
    }, 3000);
    return () => clearInterval(interval);
  }, [id]);

  if (!job) return <div className="text-gray-400 py-20 text-center">Loading...</div>;

  const outputEntries = Object.entries(job.output_paths);

  return (
    <div className="max-w-4xl">
      <div className="flex items-start gap-4 mb-8">
        <div className="flex-1">
          <Link href="/" className="text-sm text-gray-400 hover:text-gray-600 mb-2 block">
            ← Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
          <p className="text-gray-500 text-sm mt-1">
            {job.target_languages.join(" · ")} · {job.tier} tier
            {job.client_name && ` · ${job.client_name}`}
          </p>
        </div>
        <div>
          {job.status === "awaiting_review" && (
            <Link
              href={`/review/${job.id}/${job.target_languages[0]}`}
              className="bg-yellow-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-yellow-600"
            >
              Open Review Interface →
            </Link>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Status</p>
          <p className="font-semibold text-gray-900 mt-1 capitalize">{job.status.replace("_", " ")}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Duration</p>
          <p className="font-semibold text-gray-900 mt-1">
            {job.duration_seconds ? `${Math.round(job.duration_seconds / 60)} min` : "—"}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Segments</p>
          <p className="font-semibold text-gray-900 mt-1">{job.transcript.length || "—"}</p>
        </div>
      </div>

      {/* Progress */}
      {job.status === "processing" && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <div className="flex items-center justify-between mb-3">
            <p className="font-medium text-gray-800">Processing Pipeline</p>
            <span className="text-sm text-gray-500">{job.progress_pct}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2 mb-4">
            <div
              className="bg-brand-500 h-2 rounded-full transition-all"
              style={{ width: `${job.progress_pct}%` }}
            />
          </div>
          <div className="space-y-1.5">
            {job.stages.map((stage) => (
              <div key={stage.name} className="flex items-center gap-2 text-sm">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${STATUS_DOT[stage.status]}`} />
                <span className="text-gray-700">{stageLabel(stage.name)}</span>
                {stage.error && <span className="text-red-500 text-xs ml-auto">{stage.error}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {job.status === "failed" && job.error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <p className="text-red-700 font-medium">Pipeline failed</p>
          <p className="text-red-600 text-sm mt-1 font-mono">{job.error}</p>
        </div>
      )}

      {/* Downloads */}
      {outputEntries.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h2 className="font-semibold text-gray-800 mb-3">Output Files</h2>
          <div className="grid grid-cols-2 gap-2">
            {outputEntries.map(([key]) => (
              <a
                key={key}
                href={api.downloadUrl(job.id, key)}
                className="flex items-center gap-2 text-sm text-brand-600 hover:text-brand-800 bg-brand-50 rounded-lg px-3 py-2 hover:bg-brand-100"
              >
                <span>↓</span>
                <span className="font-medium">{key}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Review links per language */}
      {job.status === "awaiting_review" && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5">
          <h2 className="font-semibold text-yellow-800 mb-2">Human Review Required</h2>
          <p className="text-yellow-700 text-sm mb-3">
            AI translation complete. A compliance reviewer must approve each language before delivery.
          </p>
          <div className="flex flex-wrap gap-2">
            {job.target_languages.map((lang) => (
              <Link
                key={lang}
                href={`/review/${job.id}/${lang}`}
                className="bg-yellow-500 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-yellow-600"
              >
                Review {lang}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
