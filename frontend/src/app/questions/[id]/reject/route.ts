import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";

export async function POST(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await req.json().catch(() => ({}));
    const reason = body?.reason || "Rejected by reviewer";
    const sql = getDb();

    await sql`
      UPDATE questions 
      SET status = 'rejected', 
          critic_feedback = jsonb_set(COALESCE(critic_feedback, '{}'::jsonb), '{rejection_reason}', to_jsonb(${reason}::text)),
          updated_at = NOW() 
      WHERE id = ${id}
    `;

    const updated = await sql`SELECT * FROM questions WHERE id = ${id} LIMIT 1`;
    return NextResponse.json(updated[0]);
  } catch (err: any) {
    return NextResponse.json({ detail: err.message }, { status: 500 });
  }
}
