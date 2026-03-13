"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, TranslatedSegment } from "@/lib/api";

function formatTime(sec: number) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function ReviewPage() {
  const { jobId, lang } = useParams() as { jobId: string; lang: string };
  const router = useRouter();
  const [segments, setSegments] = useState<TranslatedSegment[]>([]);
  const [summary, setSummary] = useState({ total: 0, flagged: 0, approved: 0 });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editText, setEditText] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getReviewData(jobId, lang).then((data) => {
      setSegments(data.segments);
      setSummary(data.qa_summary);
    });
  }, [jobId, lang]);

  const handleApprove = async (seg: TranslatedSegment) => {
    await api.updateSegment(jobId, lang, seg.id, { approved: true });
    setSegments((prev) =>
      prev.map((s) => (s.id === seg.id ? { ...s, reviewer_approved: true } : s))
    );
    setSummary((prev) => ({ ...prev, approved: prev.approved + 1 }));
  };

  const handleSaveEdit = async (seg: TranslatedSegment) => {
    setSaving(true);
    await api.updateSegment(jobId, lang, seg.id, {
      reviewed_text: editText,
      approved: true,
    });
    setSegments((prev) =>
      prev.map((s) =>
        s.id === seg.id
          ? { ...s, reviewer_edited: editText, reviewer_approved: true }
          : s
      )
    );
    setSummary((prev) => ({ ...prev, approved: prev.approved + 1 }));
    setEditingId(null);
    setSaving(false);
  };

  const handleApproveAll = async () => {
    await api.approveAll(jobId, lang);
    setSegments((prev) => prev.map((s) => ({ ...s, reviewer_approved: true })));
    setSummary((prev) => ({ ...prev, approved: prev.total }));
  };

  const handleCompleteReview = async () => {
    await api.completeReview(jobId);
    router.push(`/jobs/${jobId}`);
  };

  const allApproved = segments.every((s) => s.reviewer_approved);

  return (
    <div className="max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link href={`/jobs/${jobId}`} className="text-sm text-gray-400 hover:text-gray-600 block mb-1">
            ← Back to Job
          </Link>
          <h1 className="text-xl font-bold text-gray-900">Review: {lang}</h1>
          <div className="flex gap-4 text-sm text-gray-500 mt-1">
            <span>{summary.total} segments</span>
            {summary.flagged > 0 && (
              <span className="text-yellow-600">⚠ {summary.flagged} QA flags</span>
            )}
            <span className="text-green-600">✓ {summary.approved} approved</span>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleApproveAll}
            className="text-sm bg-white border border-gray-300 text-gray-700 px-3 py-1.5 rounded-lg hover:bg-gray-50"
          >
            Approve All
          </button>
          <button
            onClick={handleCompleteReview}
            disabled={!allApproved}
            className="text-sm bg-green-600 text-white px-4 py-1.5 rounded-lg hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Complete Review →
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 bg-gray-100 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all"
            style={{ width: `${summary.total ? (summary.approved / summary.total) * 100 : 0}%` }}
          />
        </div>
        <span className="text-sm text-gray-500">
          {summary.approved}/{summary.total}
        </span>
      </div>

      <div className="space-y-2">
        {segments.map((seg) => {
          const isEditing = editingId === seg.id;
          const displayText = seg.reviewer_edited || seg.translated_text;
          const hasFlags = seg.qa_flags.length > 0;

          return (
            <div
              key={seg.id}
              className={`bg-white rounded-xl border p-4 transition
                ${seg.reviewer_approved ? "border-green-200" : hasFlags ? "border-yellow-300" : "border-gray-200"}`}
            >
              <div className="flex items-start gap-3">
                {/* Timestamp */}
                <span className="text-xs text-gray-400 font-mono pt-0.5 w-16 flex-shrink-0">
                  {formatTime(seg.start)}
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {/* Source */}
                  <p className="text-sm text-gray-500 mb-1.5">{seg.source_text}</p>

                  {/* Translation */}
                  {isEditing ? (
                    <textarea
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      className="w-full border border-brand-400 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                      rows={3}
                    />
                  ) : (
                    <p className={`text-sm font-medium ${seg.reviewer_edited ? "text-brand-700" : "text-gray-900"}`}>
                      {displayText}
                      {seg.reviewer_edited && (
                        <span className="ml-2 text-xs text-brand-500 font-normal">(edited)</span>
                      )}
                    </p>
                  )}

                  {/* QA Flags */}
                  {hasFlags && !isEditing && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {seg.qa_flags.map((flag, i) => (
                        <span key={i} className="text-xs bg-yellow-50 text-yellow-700 border border-yellow-200 px-2 py-0.5 rounded">
                          ⚠ {flag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  {isEditing ? (
                    <>
                      <button
                        onClick={() => handleSaveEdit(seg)}
                        disabled={saving}
                        className="text-xs bg-brand-600 text-white px-2.5 py-1 rounded hover:bg-brand-700 disabled:opacity-50"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="text-xs text-gray-500 px-2 py-1 rounded hover:bg-gray-100"
                      >
                        Cancel
                      </button>
                    </>
                  ) : seg.reviewer_approved ? (
                    <span className="text-xs text-green-600 font-medium">✓ Approved</span>
                  ) : (
                    <>
                      <button
                        onClick={() => {
                          setEditingId(seg.id);
                          setEditText(displayText);
                        }}
                        className="text-xs text-gray-500 border border-gray-200 px-2 py-1 rounded hover:bg-gray-50"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleApprove(seg)}
                        className="text-xs bg-green-600 text-white px-2.5 py-1 rounded hover:bg-green-700"
                      >
                        Approve
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
