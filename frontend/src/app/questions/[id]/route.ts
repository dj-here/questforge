import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const sql = getDb();

    const questions = await sql`SELECT * FROM questions WHERE id = ${id} LIMIT 1`;
    if (!questions || questions.length === 0) {
      return NextResponse.json({ detail: "Question not found" }, { status: 404 });
    }

    const q = questions[0];
    const testCases = await sql`SELECT * FROM test_cases WHERE question_id = ${id}`;

    const parseJson = (val: any, fallback: any) => {
      if (!val) return fallback;
      if (typeof val === "object") return val;
      try {
        return JSON.parse(val);
      } catch {
        return fallback;
      }
    };

    return NextResponse.json({
      id: q.id,
      job_id: q.job_id || undefined,
      title: q.title,
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
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message }, { status: 500 });
  }
}

export async function PATCH(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await req.json();
    const sql = getDb();

    if (body.title !== undefined) {
      await sql`UPDATE questions SET title = ${body.title}, updated_at = NOW() WHERE id = ${id}`;
    }
    if (body.story !== undefined) {
      await sql`UPDATE questions SET story = ${body.story}, updated_at = NOW() WHERE id = ${id}`;
    }
    if (body.constraints !== undefined) {
      await sql`UPDATE questions SET constraints = ${body.constraints}, updated_at = NOW() WHERE id = ${id}`;
    }
    if (body.input_format !== undefined) {
      await sql`UPDATE questions SET input_format = ${body.input_format}, updated_at = NOW() WHERE id = ${id}`;
    }
    if (body.output_format !== undefined) {
      await sql`UPDATE questions SET output_format = ${body.output_format}, updated_at = NOW() WHERE id = ${id}`;
    }
    if (body.status !== undefined) {
      await sql`UPDATE questions SET status = ${body.status}, updated_at = NOW() WHERE id = ${id}`;
    }
    if (body.reference_solution !== undefined) {
      await sql`UPDATE questions SET reference_solution = ${JSON.stringify(body.reference_solution)}, updated_at = NOW() WHERE id = ${id}`;
    }
    if (body.editorial !== undefined) {
      await sql`UPDATE questions SET editorial = ${body.editorial}, updated_at = NOW() WHERE id = ${id}`;
    }

    return GET(req, { params });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message }, { status: 500 });
  }
}
