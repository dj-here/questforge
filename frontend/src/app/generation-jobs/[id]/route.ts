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

    const jobs = await sql`SELECT * FROM generation_jobs WHERE id = ${id} LIMIT 1`;
    if (!jobs || jobs.length === 0) {
      return NextResponse.json({ detail: "Job not found" }, { status: 404 });
    }

    const job = jobs[0];
    return NextResponse.json({
      id: job.id,
      topic: job.topic,
      subtopic: job.subtopic || undefined,
      difficulty: job.difficulty,
      question_type: job.question_type,
      languages: Array.isArray(job.languages) ? job.languages : [],
      count: job.count || 1,
      current_stage: job.current_stage || "completed",
      progress: Number(job.progress) || 100,
      status: job.status || "completed",
      error_message: job.error_message || undefined,
      auto_publish: Boolean(job.auto_publish),
      created_at: job.created_at ? new Date(job.created_at).toISOString() : new Date().toISOString(),
      updated_at: job.updated_at ? new Date(job.updated_at).toISOString() : undefined,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message }, { status: 500 });
  }
}
