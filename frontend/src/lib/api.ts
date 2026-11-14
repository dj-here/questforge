import { Question, GenerationJob, CreateJobPayload, PublishResult } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      // ignore
    }
    throw new Error(`API Error [${response.status}]: ${errorDetail}`);
  }

  return response.json();
}

// Jobs
export async function createGenerationJob(payload: CreateJobPayload): Promise<GenerationJob> {
  return request<GenerationJob>("/generation-jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchJobs(): Promise<GenerationJob[]> {
  return request<GenerationJob[]>("/generation-jobs");
}

export async function fetchJob(jobId: string): Promise<GenerationJob> {
  return request<GenerationJob>(`/generation-jobs/${jobId}`);
}

// Questions
export async function fetchQuestions(params?: {
  topic?: string;
  difficulty?: string;
  status?: string;
  search?: string;
  limit?: number;
  skip?: number;
}): Promise<Question[]> {
  const query = new URLSearchParams();
  if (params?.topic) query.set("topic", params.topic);
  if (params?.difficulty) query.set("difficulty", params.difficulty);
  if (params?.status) query.set("status", params.status);
  if (params?.search) query.set("search", params.search);
  if (params?.limit) query.set("limit", params.limit.toString());
  if (params?.skip) query.set("skip", params.skip.toString());

  const queryString = query.toString();
  return request<Question[]>(`/questions${queryString ? `?${queryString}` : ""}`);
}

export async function fetchQuestion(id: string): Promise<Question> {
  return request<Question>(`/questions/${id}`);
}

export async function updateQuestion(id: string, updates: Partial<Question>): Promise<Question> {
  return request<Question>(`/questions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}

export async function approveQuestion(id: string): Promise<Question> {
  return request<Question>(`/questions/${id}/approve`, {
    method: "POST",
  });
}

export async function rejectQuestion(id: string, reason?: string): Promise<Question> {
  return request<Question>(`/questions/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function regenerateQuestion(id: string): Promise<Question> {
  return request<Question>(`/questions/${id}/regenerate`, {
    method: "POST",
  });
}

// Publishing
export async function publishQuestion(
  id: string,
  dryRun = false,
  testId?: string
): Promise<PublishResult> {
  return request<PublishResult>(`/questions/${id}/publish`, {
    method: "POST",
    body: JSON.stringify({ dry_run: dryRun, test_id: testId }),
  });
}

export async function publishBulk(
  questionIds: string[],
  dryRun = false
): Promise<{ total: number; successful: number; failed: number; results: PublishResult[] }> {
  return request<{ total: number; successful: number; failed: number; results: PublishResult[] }>(
    "/publish/bulk",
    {
      method: "POST",
      body: JSON.stringify({ question_ids: questionIds, dry_run: dryRun }),
    }
  );
}

export function getExportZipUrl(id: string): string {
  return `${API_BASE}/questions/${id}/export`;
}
