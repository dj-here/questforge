export type Difficulty = "Easy" | "Medium" | "Hard" | "Custom";
export type QuestionType = "coding" | "mcq" | "sql" | "debugging" | "output-prediction";
export type QuestionStatus = "generating" | "review_ready" | "approved" | "rejected" | "publishing" | "published" | "publish_failed";

export interface TestCase {
  id: string;
  stdin: string;
  expected_output: string;
  is_sample: boolean;
  is_hidden: boolean;
  score_weight: number;
  time_limit_sec?: number;
  memory_limit_mb?: number;
  description?: string;
}

export interface VerificationLog {
  id: string;
  language: string;
  run_type: string;
  passed: boolean;
  status: string;
  runtime_ms: number;
  memory_kb: number;
  stdout?: string;
  stderr?: string;
  created_at?: string;
}

export interface CriticScoreBreakdown {
  clarity: number;
  originality: number;
  difficulty_match: number;
  unambiguity: number;
}

export interface CriticResult {
  scores: CriticScoreBreakdown;
  overall_score: number;
  passed: boolean;
  critique: string;
  suggested_improvements: string[];
}

export interface ReferenceSolution {
  python?: string;
  java?: string;
  cpp?: string;
  sql?: string;
}

export interface Question {
  id: string;
  job_id?: string;
  title: string;
  story: string;
  input_format: string;
  output_format: string;
  constraints: string;
  sample_inputs: string[];
  sample_outputs: string[];
  explanation?: string;
  tags: string[];
  difficulty: Difficulty;
  subtopic?: string;
  question_type: QuestionType;
  time_limit: number;
  memory_limit: number;
  reference_solution: ReferenceSolution;
  brute_force_solution?: string;
  test_case_generator_code?: string;
  editorial?: string;
  critic_score?: number;
  critic_feedback?: CriticResult;
  status: QuestionStatus;
  hackerrank_question_id?: string;
  hackerrank_url?: string;
  test_cases: TestCase[];
  verification_logs: VerificationLog[];
  created_at: string;
  updated_at?: string;
}

export interface GenerationJob {
  id: string;
  topic: string;
  subtopic?: string;
  difficulty: string;
  question_type: string;
  languages: string[];
  count: number;
  current_stage: string;
  progress: number;
  status: "pending" | "running" | "completed" | "failed";
  error_message?: string;
  auto_publish: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CreateJobPayload {
  topic: string;
  subtopic?: string;
  difficulty: Difficulty;
  question_type: QuestionType;
  languages: string[];
  count: number;
  auto_publish?: boolean;
}

export interface PublishResult {
  question_id: string;
  hackerrank_question_id?: string;
  url?: string;
  status: string;
  error?: string;
}
