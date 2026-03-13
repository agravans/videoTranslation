const BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export interface Job {
  id: string;
  title: string;
  source_language: string;
  target_languages: string[];
  tier: "starter" | "standard" | "premium";
  status: "pending" | "processing" | "awaiting_review" | "review_approved" | "completed" | "failed";
  client_name?: string;
  progress_pct: number;
  duration_seconds?: number;
  output_paths: Record<string, string>;
  stages: PipelineStage[];
  transcript: TranscriptSegment[];
  translations: Record<string, TranslatedSegment[]>;
  created_at: string;
  completed_at?: string;
  error?: string;
}

export interface PipelineStage {
  name: string;
  status: "pending" | "running" | "done" | "skipped" | "error";
  started_at?: string;
  completed_at?: string;
  error?: string;
  meta: Record<string, unknown>;
}

export interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  speaker?: string;
}

export interface TranslatedSegment {
  id: number;
  start: number;
  end: number;
  source_text: string;
  translated_text: string;
  language: string;
  reviewer_approved: boolean;
  reviewer_edited?: string;
  qa_flags: string[];
}

export interface Language {
  code: string;
  name: string;
}

export const api = {
  async getLanguages(): Promise<Language[]> {
    const res = await fetch(`${BASE}/languages`);
    return res.json();
  },

  async listJobs(): Promise<Job[]> {
    const res = await fetch(`${BASE}/jobs`);
    return res.json();
  },

  async getJob(id: string): Promise<Job> {
    const res = await fetch(`${BASE}/jobs/${id}`);
    if (!res.ok) throw new Error(`Job ${id} not found`);
    return res.json();
  },

  async createJob(formData: FormData): Promise<Job> {
    const res = await fetch(`${BASE}/jobs`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create job");
    }
    return res.json();
  },

  async getReviewData(jobId: string, langCode: string) {
    const res = await fetch(`${BASE}/jobs/${jobId}/review/${langCode}`);
    return res.json();
  },

  async updateSegment(
    jobId: string,
    langCode: string,
    segmentId: number,
    body: { reviewed_text?: string; approved?: boolean }
  ) {
    const res = await fetch(`${BASE}/jobs/${jobId}/review/${langCode}/segment/${segmentId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.json();
  },

  async approveAll(jobId: string, langCode: string) {
    const res = await fetch(`${BASE}/jobs/${jobId}/review/${langCode}/approve-all`, {
      method: "POST",
    });
    return res.json();
  },

  async completeReview(jobId: string) {
    const res = await fetch(`${BASE}/jobs/${jobId}/review/complete`, {
      method: "POST",
    });
    return res.json();
  },

  downloadUrl(jobId: string, outputKey: string) {
    return `${BASE}/jobs/${jobId}/download/${outputKey}`;
  },
};
