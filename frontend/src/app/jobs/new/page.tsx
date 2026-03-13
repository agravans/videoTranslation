"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, Language } from "@/lib/api";

const TIERS = [
  {
    id: "starter",
    name: "Starter",
    price: "₹150/min/lang",
    desc: "Subtitles (SRT) only",
    margin: "~88% margin",
  },
  {
    id: "standard",
    name: "Standard",
    price: "₹350–500/min/lang",
    desc: "Subtitles + AI dubbing",
    margin: "~85–94% margin",
  },
  {
    id: "premium",
    name: "Premium",
    price: "₹700–1,000/min/lang",
    desc: "Dubbing + Lip Sync + Review",
    margin: "~93–94% margin",
  },
];

export default function NewJobPage() {
  const router = useRouter();
  const [languages, setLanguages] = useState<Language[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [selectedLangs, setSelectedLangs] = useState<string[]>(["hi-IN"]);
  const [tier, setTier] = useState("standard");
  const [clientName, setClientName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getLanguages().then(setLanguages);
  }, []);

  const toggleLang = (code: string) => {
    setSelectedLangs((prev) =>
      prev.includes(code) ? prev.filter((l) => l !== code) : [...prev, code]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return setError("Please select a video file.");
    if (selectedLangs.length === 0) return setError("Select at least one target language.");

    setSubmitting(true);
    setError("");
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", title || file.name.replace(/\.[^.]+$/, ""));
    fd.append("target_languages", selectedLangs.join(","));
    fd.append("tier", tier);
    if (clientName) fd.append("client_name", clientName);

    try {
      const job = await api.createJob(fd);
      router.push(`/jobs/${job.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">New Translation Job</h1>
      <p className="text-gray-500 text-sm mb-8">
        Upload an English training video — we'll translate, dub, and subtitle it.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Video Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Video File *</label>
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition
              ${file ? "border-brand-400 bg-brand-50" : "border-gray-300 hover:border-brand-400"}`}
            onClick={() => document.getElementById("file-input")?.click()}
          >
            {file ? (
              <div>
                <p className="font-medium text-brand-700">{file.name}</p>
                <p className="text-sm text-gray-500 mt-1">{(file.size / (1024 * 1024)).toFixed(1)} MB</p>
              </div>
            ) : (
              <div>
                <p className="text-gray-500">Drag & drop or click to upload</p>
                <p className="text-xs text-gray-400 mt-1">MP4, MOV, AVI · Max 500 MB</p>
              </div>
            )}
          </div>
          <input
            id="file-input"
            type="file"
            accept="video/*"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) {
                setFile(f);
                if (!title) setTitle(f.name.replace(/\.[^.]+$/, ""));
              }
            }}
          />
        </div>

        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Job Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. AML Compliance Training 2026"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Client Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Client Name (optional)</label>
          <input
            type="text"
            value={clientName}
            onChange={(e) => setClientName(e.target.value)}
            placeholder="e.g. HDFC Bank"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Languages */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target Languages * <span className="text-gray-400 font-normal">(select 1–11)</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {languages.map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => toggleLang(lang.code)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition
                  ${selectedLangs.includes(lang.code)
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-white text-gray-600 border-gray-300 hover:border-brand-400"}`}
              >
                {lang.name}
              </button>
            ))}
          </div>
        </div>

        {/* Tier */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Processing Tier *</label>
          <div className="grid grid-cols-3 gap-3">
            {TIERS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTier(t.id)}
                className={`p-3 rounded-xl border text-left transition
                  ${tier === t.id
                    ? "border-brand-500 bg-brand-50 ring-2 ring-brand-500"
                    : "border-gray-200 hover:border-brand-300"}`}
              >
                <p className="font-semibold text-sm text-gray-900">{t.name}</p>
                <p className="text-xs text-brand-600 mt-0.5">{t.price}</p>
                <p className="text-xs text-gray-500 mt-1">{t.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={submitting || !file}
          className="w-full bg-brand-600 text-white py-2.5 rounded-lg font-medium hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {submitting ? "Uploading & Processing..." : "Start Translation Job"}
        </button>
      </form>
    </div>
  );
}
