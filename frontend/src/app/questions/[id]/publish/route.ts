import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";
import { publishQuestionToHackerRank } from "@/lib/hackerrank";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function POST(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await req.json().catch(() => ({}));
    const dryRun: boolean = Boolean(body.dry_run);
    const testId: string | undefined = body.test_id;
    const token: string | undefined =
      body.token || req.headers.get("x-hackerrank-token") || undefined;

    const sql = getDb();

    // 1. Fetch Question
    const questions = await sql`
      SELECT * FROM questions WHERE id = ${id} LIMIT 1
    `;

    if (!questions || questions.length === 0) {
      return NextResponse.json({ detail: "Question not found" }, { status: 404 });
    }

    const q = questions[0];

    // 2. Fetch Test Cases
    const testCases = await sql`
      SELECT * FROM test_cases WHERE question_id = ${id} ORDER BY id ASC
    `;

    // 3. Publish to HackerRank
    const res = await publishQuestionToHackerRank(q, testCases, {
      token,
      dryRun,
      testId,
    });

    if (res.success) {
      await sql`
        UPDATE questions 
        SET status = 'published',
            remote_hackerrank_id = ${res.remote_id || null},
            hackerrank_url = ${res.url || null},
            published_at = NOW(),
            updated_at = NOW()
        WHERE id = ${id}
      `;
    }

    return NextResponse.json(res, {
      headers: {
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
      },
    });
  } catch (err: any) {
    console.error(`Publish question ${params.id} error:`, err);
    return NextResponse.json(
      { detail: err.message || "Failed to publish question" },
      { status: 500 }
    );
  }
}
