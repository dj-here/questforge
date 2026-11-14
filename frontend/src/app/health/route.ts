import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";

export async function GET() {
  try {
    const sql = getDb();
    const result = await sql`SELECT 1 as alive`;
    return NextResponse.json({
      status: "healthy",
      database: result[0]?.alive === 1 ? "connected" : "unknown",
      llm_provider: process.env.LLM_PROVIDER || "gemini",
      timestamp: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json(
      {
        status: "degraded",
        database_error: err?.message || String(err),
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  }
}
