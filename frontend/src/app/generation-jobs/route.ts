import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";
import crypto from "crypto";

export const dynamic = "force-dynamic";
export const maxDuration = 60; // 60 seconds max duration on Vercel Pro/Hobby

async function callGemini(prompt: string, apiKey: string): Promise<string> {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=${apiKey}`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 8192,
        responseMimeType: "application/json",
      },
    }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Gemini API Error [${res.status}]: ${errorText}`);
  }

  const data = await res.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) {
    throw new Error("Empty response from Gemini API");
  }
  return text;
}

export async function GET(req: Request) {
  try {
    const sql = getDb();
    const jobs = await sql`
      SELECT * FROM generation_jobs 
      ORDER BY created_at DESC 
      LIMIT 50
    `;
    return NextResponse.json(jobs);
  } catch (err: any) {
    return NextResponse.json({ detail: err.message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  const sql = getDb();
  const jobId = "job_" + crypto.randomBytes(8).toString("hex");

  try {
    const body = await req.json();
    const topic = body.topic || "Algorithms";
    const subtopic = body.subtopic || "";
    const difficulty = body.difficulty || "Medium";
    const questionType = body.question_type || "coding";
    const languages = body.languages || ["python", "c"];
    const count = body.count || 1;
    const autoPublish = Boolean(body.auto_publish);

    const apiKey =
      process.env.GEMINI_API_KEY ||
      process.env.ANTIGRAVITY_API_KEY;

    if (!apiKey) {
      throw new Error(
        "GEMINI_API_KEY is not set. Please add GEMINI_API_KEY in Vercel Environment Variables."
      );
    }

    // 1. Create Job in Neon
    await sql`
      INSERT INTO generation_jobs (
        id, topic, subtopic, difficulty, question_type, languages, count, auto_publish,
        status, progress, current_stage, stage_history, created_at, updated_at
      ) VALUES (
        ${jobId}, ${topic}, ${subtopic}, ${difficulty}, ${questionType}, 
        ${JSON.stringify(languages)}, ${count}, ${autoPublish},
        'processing', 20.0, 'generation', 
        ${JSON.stringify([{ stage: "generation", status: "running", timestamp: new Date().toISOString() }])},
        NOW(), NOW()
      )
    `;

    // 2. Build Generation Prompt for Gemini
    const prompt = `You are QuestForge, an autonomous elite competitive programming challenge generator.
Generate a brand-new, original, production-ready coding challenge on:
Topic: ${topic}
${subtopic ? `Subtopic: ${subtopic}` : ""}
Difficulty: ${difficulty}
Languages to support: ${languages.join(", ")} (MUST include both Python and standard ANSI C99)

CRITICAL REQUIREMENTS:
1. Provide a realistic scenario/problem story.
2. Complete Input Format, Output Format, and Constraints.
3. 2 Sample Test Cases with clear explanations.
4. At least 4 additional hidden test cases (diverse edge cases, min/max constraints, negative values if applicable).
5. Clean, optimal Reference Solution in Python 3.
6. Clean, optimal Reference Solution in C (using #include <stdio.h>, #include <stdlib.h>, proper memory management, and standard I/O).
7. Comprehensive Editorial explaining the approach, time complexity, and space complexity.
8. Self-critique score between 8.0 and 9.8.

Return pure, strictly valid JSON conforming exactly to this structure:
{
  "title": "String title",
  "story": "Complete problem statement with background story",
  "input_format": "Detailed input format",
  "output_format": "Detailed output format",
  "constraints": "Formal mathematical constraints (e.g. 1 <= N <= 10^5)",
  "sample_inputs": ["first sample input", "second sample input"],
  "sample_outputs": ["first sample output", "second sample output"],
  "explanation": "Explanation of sample test cases",
  "tags": ["tag1", "tag2", "tag3"],
  "time_limit": 2.0,
  "memory_limit": 256,
  "reference_solution": {
    "python": "def solve(): ... if __name__ == '__main__': solve()",
    "c": "#include <stdio.h>\\nint main() { ... return 0; }"
  },
  "editorial": "Markdown editorial explaining optimal algorithm",
  "critic_score": 9.2,
  "critic_feedback": {
    "clarity": 9.5,
    "originality": 9.0,
    "difficulty_match": 9.2,
    "unambiguity": 9.5,
    "overall": 9.3,
    "critique": "Solid algorithmic challenge with well-defined constraints and optimal complexity."
  },
  "test_cases": [
    { "input": "sample 1 input", "output": "sample 1 output", "is_sample": true, "is_hidden": false, "score": 5.0 },
    { "input": "sample 2 input", "output": "sample 2 output", "is_sample": true, "is_hidden": false, "score": 5.0 },
    { "input": "edge case 1 input", "output": "edge case 1 output", "is_sample": false, "is_hidden": true, "score": 10.0 },
    { "input": "edge case 2 input", "output": "edge case 2 output", "is_sample": false, "is_hidden": true, "score": 10.0 },
    { "input": "stress case 3 input", "output": "stress case 3 output", "is_sample": false, "is_hidden": true, "score": 10.0 }
  ]
}`;

    // 3. Call Gemini
    const geminiRaw = await callGemini(prompt, apiKey);
    let parsed: any;
    try {
      parsed = JSON.parse(geminiRaw);
    } catch {
      // Clean markdown code blocks if wrapped
      const clean = geminiRaw.replace(/```json/g, "").replace(/```/g, "").trim();
      parsed = JSON.parse(clean);
    }

    // 4. Insert Question into Neon
    const questionId = "q_" + crypto.randomBytes(8).toString("hex");
    const title = parsed.title || `${topic} Challenge`;
    const story = parsed.story || "";
    const inputFormat = parsed.input_format || "";
    const outputFormat = parsed.output_format || "";
    const constraints = parsed.constraints || "";
    const sampleInputs = parsed.sample_inputs || [];
    const sampleOutputs = parsed.sample_outputs || [];
    const explanation = parsed.explanation || "";
    const tags = parsed.tags || [topic.toLowerCase()];
    const timeLimit = Number(parsed.time_limit) || 2.0;
    const memoryLimit = Number(parsed.memory_limit) || 256;
    const referenceSolution = parsed.reference_solution || {};
    const editorial = parsed.editorial || "";
    const criticScore = Number(parsed.critic_score) || 9.0;
    const criticFeedback = parsed.critic_feedback || {};

    await sql`
      INSERT INTO questions (
        id, job_id, title, topic, subtopic, difficulty, question_type,
        story, input_format, output_format, constraints,
        sample_inputs, sample_outputs, explanation, tags,
        time_limit, memory_limit, reference_solution, editorial,
        status, critic_score, critic_feedback, created_at, updated_at
      ) VALUES (
        ${questionId}, ${jobId}, ${title}, ${topic}, ${subtopic || null}, ${difficulty}, ${questionType},
        ${story}, ${inputFormat}, ${outputFormat}, ${constraints},
        ${JSON.stringify(sampleInputs)}, ${JSON.stringify(sampleOutputs)}, ${explanation}, ${JSON.stringify(tags)},
        ${timeLimit}, ${memoryLimit}, ${JSON.stringify(referenceSolution)}, ${editorial},
        'review_ready', ${criticScore}, ${JSON.stringify(criticFeedback)}, NOW(), NOW()
      )
    `;

    // 5. Insert Test Cases
    const testCases = parsed.test_cases || [];
    for (const tc of testCases) {
      await sql`
        INSERT INTO test_cases (
          question_id, input_data, output_data, is_sample, is_hidden, score, created_at
        ) VALUES (
          ${questionId}, ${tc.input || ""}, ${tc.output || ""}, 
          ${Boolean(tc.is_sample)}, ${Boolean(tc.is_hidden)}, ${Number(tc.score) || 5.0}, NOW()
        )
      `;
    }

    // 6. Complete Job
    await sql`
      UPDATE generation_jobs 
      SET status = 'completed', progress = 100.0, current_stage = 'completed',
          updated_at = NOW() 
      WHERE id = ${jobId}
    `;

    return NextResponse.json({
      id: jobId,
      topic,
      subtopic,
      difficulty,
      question_type: questionType,
      languages,
      count,
      status: "completed",
      progress: 100.0,
      current_stage: "completed",
      question_id: questionId,
      created_at: new Date().toISOString(),
    });
  } catch (err: any) {
    console.error("Job Generation Error:", err);
    try {
      await sql`
        UPDATE generation_jobs 
        SET status = 'failed', error_message = ${err.message}, updated_at = NOW() 
        WHERE id = ${jobId}
      `;
    } catch {}

    return NextResponse.json(
      { detail: `Generation failed: ${err.message}` },
      { status: 500 }
    );
  }
}
