import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";
import { publishQuestionToHackerRank, PublishResultItem } from "@/lib/hackerrank";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const questionIds: string[] = body.question_ids || [];
    const dryRun: boolean = Boolean(body.dry_run);
    const testId: string | undefined = body.test_id;
    const token: string | undefined =
      body.token || req.headers.get("x-hackerrank-token") || undefined;

    if (!questionIds || questionIds.length === 0) {
      return NextResponse.json(
        { detail: "No question IDs provided for bulk publishing." },
        { status: 400 }
      );
    }

    const sql = getDb();
    const results: PublishResultItem[] = [];
    let publishedCount = 0;
    let failedCount = 0;

    for (const qid of questionIds) {
      // 1. Fetch Question
      const questions = await sql`
        SELECT * FROM questions WHERE id = ${qid} LIMIT 1
      `;

      if (!questions || questions.length === 0) {
        results.push({
          question_id: qid,
          success: false,
          error: "Question not found",
        });
        failedCount++;
        continue;
      }

      const q = questions[0];

      // 2. Fetch Test Cases
      const testCases = await sql`
        SELECT * FROM test_cases WHERE question_id = ${qid} ORDER BY id ASC
      `;

      // 3. Publish to HackerRank
      const res = await publishQuestionToHackerRank(q, testCases, {
        token,
        dryRun,
        testId,
      });

      if (res.success) {
        // 4. Update status in Database
        await sql`
          UPDATE questions 
          SET status = 'published',
              remote_hackerrank_id = ${res.remote_id || null},
              hackerrank_url = ${res.url || null},
              published_at = NOW(),
              updated_at = NOW()
          WHERE id = ${qid}
        `;
        publishedCount++;
      } else {
        failedCount++;
      }

      results.push(res);
    }

    return NextResponse.json(
      {
        total: questionIds.length,
        published: publishedCount,
        failed: failedCount,
        results: results,
      },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
        },
      }
    );
  } catch (err: any) {
    console.error("Bulk publish handler error:", err);
    return NextResponse.json(
      { detail: err.message || "Bulk publish failed" },
      { status: 500 }
    );
  }
}
