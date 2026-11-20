import crypto from "crypto";

export function mapDifficultyToHackerRank(diff?: string): string {
  const d = (diff || "medium").toLowerCase();
  if (d.includes("easy")) return "easy";
  if (d.includes("hard")) return "hard";
  return "medium";
}

export function mapLanguagesToHackerRank(languages: string[]): string[] {
  const mapping: Record<string, string> = {
    c: "c",
    python: "python3",
    python3: "python3",
    java: "java15",
    "java 17": "java15",
    cpp: "cpp14",
    "cpp 20": "cpp14",
    "c++": "cpp14",
    "c++ 20": "cpp14",
    javascript: "javascript",
    sql: "sql",
  };
  return languages.map((l) => mapping[l.toLowerCase()] || l.toLowerCase());
}

export function buildProblemStatement(question: any): string {
  const parts: string[] = [];

  if (question.story) {
    parts.push(`### Description\n${question.story}\n`);
  }
  if (question.input_format) {
    parts.push(`### Input Format\n${question.input_format}\n`);
  }
  if (question.output_format) {
    parts.push(`### Output Format\n${question.output_format}\n`);
  }
  if (question.constraints) {
    parts.push(`### Constraints\n\`\`\`\n${question.constraints}\n\`\`\`\n`);
  }

  const sampleInputs = Array.isArray(question.sample_inputs)
    ? question.sample_inputs
    : typeof question.sample_inputs === "string"
    ? JSON.parse(question.sample_inputs || "[]")
    : [];

  const sampleOutputs = Array.isArray(question.sample_outputs)
    ? question.sample_outputs
    : typeof question.sample_outputs === "string"
    ? JSON.parse(question.sample_outputs || "[]")
    : [];

  if (sampleInputs.length > 0) {
    parts.push("### Sample Cases\n");
    sampleInputs.forEach((inp: string, idx: number) => {
      const out = sampleOutputs[idx] || "";
      parts.push(
        `**Sample Input ${idx}**\n\`\`\`\n${inp}\n\`\`\`\n**Sample Output ${idx}**\n\`\`\`\n${out}\n\`\`\`\n`
      );
    });
  }

  if (question.explanation) {
    parts.push(`### Explanation\n${question.explanation}\n`);
  }

  return parts.join("\n");
}

export function buildHackerRankPayload(question: any, testCases: any[]): any {
  const formattedTestcases = testCases.map((tc, idx) => ({
    testcase_id: idx + 1,
    input: tc.input_data || "",
    output: tc.output_data || "",
    score: Number(tc.score) || 5.0,
    is_sample: tc.is_sample ? 1 : 0,
    is_hidden: tc.is_hidden ? 1 : 0,
    explanation: tc.explanation || "",
  }));

  const refSol =
    typeof question.reference_solution === "string"
      ? JSON.parse(question.reference_solution || "{}")
      : question.reference_solution || {};

  const langs = Object.keys(refSol).length > 0 ? Object.keys(refSol) : ["python", "c"];
  const tags = Array.isArray(question.tags)
    ? question.tags
    : typeof question.tags === "string"
    ? JSON.parse(question.tags || "[]")
    : [question.topic || "algorithms"];

  return {
    name: question.title,
    type: "code",
    problem_statement: buildProblemStatement(question),
    input_format: question.input_format || "",
    output_format: question.output_format || "",
    constraints: question.constraints || "",
    difficulty: mapDifficultyToHackerRank(question.difficulty),
    tags: tags,
    allowed_languages: mapLanguagesToHackerRank(langs),
    time_limit: Math.max(1, Math.round(Number(question.time_limit) || 2)),
    memory_limit: Number(question.memory_limit) || 256,
    testcases: formattedTestcases,
  };
}

export interface PublishResultItem {
  question_id: string;
  success: boolean;
  remote_id?: string;
  url?: string;
  status?: string;
  error?: string;
}

export async function publishQuestionToHackerRank(
  question: any,
  testCases: any[],
  options: {
    token?: string;
    baseUrl?: string;
    dryRun?: boolean;
    testId?: string;
  } = {}
): Promise<PublishResultItem> {
  const token =
    options.token ||
    process.env.HACKERRANK_API_TOKEN ||
    process.env.HACKERRANK_ACCESS_TOKEN;

  const isDryRun =
    options.dryRun ||
    !token ||
    token === "mock-hr-token" ||
    token === "your_hackerrank_bearer_access_token_here";

  const baseUrl = (
    options.baseUrl ||
    process.env.HACKERRANK_BASE_URL ||
    "https://www.hackerrank.com/x/api/v3"
  ).replace(/\/$/, "");

  // If dry run, simulate remote ID and URL
  if (isDryRun) {
    const simId = `hr_q_${crypto.randomBytes(5).toString("hex")}`;
    return {
      question_id: question.id,
      success: true,
      remote_id: simId,
      url: `https://www.hackerrank.com/work/questions/${simId}`,
      status: "published_dry_run",
    };
  }

  // Live REST API call to HackerRank
  const payload = buildHackerRankPayload(question, testCases);
  const targetUrl = question.remote_hackerrank_id
    ? `${baseUrl}/tests/questions/${question.remote_hackerrank_id}`
    : `${baseUrl}/tests/questions`;
  const method = question.remote_hackerrank_id ? "PUT" : "POST";

  try {
    const res = await fetch(targetUrl, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errText = await res.text();
      let parsedDetail = errText;
      try {
        const parsed = JSON.parse(errText);
        parsedDetail = parsed.message || parsed.error || parsed.detail || errText;
      } catch {}
      return {
        question_id: question.id,
        success: false,
        error: `HackerRank API Error [${res.status}]: ${parsedDetail}`,
      };
    }

    const data = await res.json();
    const remoteId = String(
      data?.id || data?.data?.id || question.remote_hackerrank_id || ""
    );
    const url =
      data?.url || `https://www.hackerrank.com/work/questions/${remoteId}`;

    return {
      question_id: question.id,
      success: true,
      remote_id: remoteId,
      url: url,
      status: "published",
    };
  } catch (err: any) {
    return {
      question_id: question.id,
      success: false,
      error: `Network error connecting to HackerRank: ${err.message}`,
    };
  }
}
