import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";
import { Question } from "@/lib/types";

export const dynamic = "force-dynamic";
export const revalidate = 0;

function mapQuestion(q: any, testCases: any[] = []): Question {
  const parseJson = (val: any, fallback: any) => {
    if (!val) return fallback;
    if (typeof val === "object") return val;
    try {
      return JSON.parse(val);
    } catch {
      return fallback;
    }
  };

  return {
    id: q.id,
    job_id: q.job_id || undefined,
    title: q.title || "Untitled Challenge",
    story: q.story || "",
    input_format: q.input_format || "",
    output_format: q.output_format || "",
    constraints: q.constraints || "",
    sample_inputs: parseJson(q.sample_inputs, []),
    sample_outputs: parseJson(q.sample_outputs, []),
    explanation: q.explanation || "",
    tags: parseJson(q.tags, []),
    difficulty: q.difficulty || "Medium",
    subtopic: q.subtopic || undefined,
    question_type: q.question_type || "coding",
    time_limit: Number(q.time_limit) || 2.0,
    memory_limit: Number(q.memory_limit) || 256,
    reference_solution: parseJson(q.reference_solution, {}),
    brute_force_solution: q.brute_force_solution || "",
    test_case_generator_code: q.test_case_generator_code || "",
    editorial: q.editorial || "",
    critic_score: q.critic_score != null ? Number(q.critic_score) : 8.5,
    critic_feedback: parseJson(q.critic_feedback, undefined),
    status: q.status || "review_ready",
    hackerrank_question_id: q.remote_hackerrank_id || undefined,
    hackerrank_url: q.hackerrank_url || undefined,
    test_cases: testCases.map((tc) => ({
      id: String(tc.id),
      stdin: tc.input_data || "",
      expected_output: tc.output_data || "",
      is_sample: Boolean(tc.is_sample),
      is_hidden: Boolean(tc.is_hidden),
      score_weight: Number(tc.score) || 5.0,
      description: tc.explanation || undefined,
    })),
    verification_logs: [],
    created_at: q.created_at ? new Date(q.created_at).toISOString() : new Date().toISOString(),
    updated_at: q.updated_at ? new Date(q.updated_at).toISOString() : undefined,
  };
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const topic = searchParams.get("topic");
    const difficulty = searchParams.get("difficulty");
    const status = searchParams.get("status");
    const search = searchParams.get("search");
    const limit = parseInt(searchParams.get("limit") || "50", 10);
    const skip = parseInt(searchParams.get("skip") || "0", 10);

    const sql = getDb();

    // Query questions directly with status filter if present to avoid pagination misses
    const questionsRows = status
      ? await sql`
          SELECT * FROM questions 
          WHERE status = ${status}
          ORDER BY created_at DESC 
          LIMIT ${limit} OFFSET ${skip}
        `
      : await sql`
          SELECT * FROM questions 
          ORDER BY created_at DESC 
          LIMIT ${limit} OFFSET ${skip}
        `;

    if (!questionsRows || questionsRows.length === 0) {
      return NextResponse.json([], {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
        },
      });
    }

    const questionIds = questionsRows.map((q: any) => q.id);
    const testCaseRows = await sql`
      SELECT * FROM test_cases WHERE question_id = ANY(${questionIds})
    `;

    const testCaseMap: Record<string, any[]> = {};
    for (const tc of testCaseRows) {
      if (!testCaseMap[tc.question_id]) {
        testCaseMap[tc.question_id] = [];
      }
      testCaseMap[tc.question_id].push(tc);
    }

    let results = questionsRows.map((q: any) =>
      mapQuestion(q, testCaseMap[q.id] || [])
    );

    // Apply optional memory filters if requested
    if (topic) {
      results = results.filter((r) =>
        r.tags.some((t: string) => t.toLowerCase().includes(topic.toLowerCase())) ||
        (r.subtopic && r.subtopic.toLowerCase().includes(topic.toLowerCase()))
      );
    }
    if (difficulty) {
      results = results.filter(
        (r) => r.difficulty.toLowerCase() === difficulty.toLowerCase()
      );
    }
    if (search) {
      const s = search.toLowerCase();
      results = results.filter(
        (r) =>
          r.title.toLowerCase().includes(s) ||
          r.story.toLowerCase().includes(s) ||
          r.tags.some((t: string) => t.toLowerCase().includes(s))
      );
    }

    return NextResponse.json(results, {
      headers: {
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
      },
    });
  } catch (err: any) {
    console.error("GET /questions error:", err);
    return NextResponse.json(
      { error: err?.message || "Failed to fetch questions" },
      {
        status: 500,
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
        },
      }
    );
  }
}
