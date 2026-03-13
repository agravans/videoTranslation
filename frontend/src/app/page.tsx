"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Job } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-100 text-gray-600",
  processing: "bg-blue-100 text-blue-700",
  awaiting_review: "bg-yellow-100 text-yellow-700",
  review_approved: "bg-indigo-100 text-indigo-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

const STATUS_LABEL: Record<string, string> = {
  pending: "Pending",
  processing: "Processing",
  awaiting_review: "Needs Review",
  review_approved: "Review Done",
  completed: "Complete",
  failed: "Failed",
};

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listJobs().then(setJobs).finally(() => setLoading(false));
    const interval = setInterval(() => api.listJobs().then(setJobs), 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Translation Jobs</h1>
          <p className="text-gray-500 text-sm mt-1">
            BFSI compliance training videos → 11 Indian languages
          </p>
        </div>
        <Link
          href="/jobs/new"
          className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 transition"
        >
          + New Job
        </Link>
      </div>

      {loading ? (
        <div className="text-gray-400 text-center py-20">Loading...</div>
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-300 text-center py-20">
          <p className="text-gray-500 mb-4">No jobs yet.</p>
          <Link href="/jobs/new" className="text-brand-600 font-medium hover:underline">
            Upload your first video →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div key={job.id} className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Link href={`/jobs/${job.id}`} className="font-semibold text-gray-900 hover:text-brand-600 truncate">
                    {job.title}
                  </Link>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[job.status]}`}>
                    {STATUS_LABEL[job.status]}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-500">
                  <span>{job.target_languages.join(", ")}</span>
                  {job.client_name && <span>· {job.client_name}</span>}
                  {job.duration_seconds && (
                    <span>· {Math.round(job.duration_seconds / 60)}min video</span>
                  )}
                  <span>· {job.tier}</span>
                  <span className="ml-auto text-xs">
                    {new Date(job.created_at).toLocaleDateString("en-IN")}
                  </span>
                </div>
                {job.status === "processing" && (
                  <div className="mt-2">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                        <div
                          className="bg-brand-500 h-1.5 rounded-full transition-all"
                          style={{ width: `${job.progress_pct}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{job.progress_pct}%</span>
                    </div>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                {job.status === "awaiting_review" && (
                  <Link
                    href={`/review/${job.id}/${job.target_languages[0]}`}
                    className="text-xs bg-yellow-50 text-yellow-700 border border-yellow-200 px-3 py-1.5 rounded-lg hover:bg-yellow-100"
                  >
                    Review
                  </Link>
                )}
                {job.status === "completed" && Object.keys(job.output_paths).length > 0 && (
                  <Link
                    href={`/jobs/${job.id}`}
                    className="text-xs bg-green-50 text-green-700 border border-green-200 px-3 py-1.5 rounded-lg hover:bg-green-100"
                  >
                    Download
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
