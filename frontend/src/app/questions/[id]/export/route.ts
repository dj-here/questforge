import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";
import JSZip from "jszip";

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
    const testCases = await sql`SELECT * FROM test_cases WHERE question_id = ${id} ORDER BY id ASC`;

    const zip = new JSZip();
    const slug = (q.title || "challenge")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");

    const refSol =
      typeof q.reference_solution === "string"
        ? JSON.parse(q.reference_solution || "{}")
        : q.reference_solution || {};

    const pythonSolution =
      refSol.python || "# Reference solution in Python\nprint('Hello World')\n";
    const cSolution =
      refSol.c ||
      "// Reference solution in C\n#include <stdio.h>\n\nint main() {\n    return 0;\n}\n";

    // 1. HackerRank challenge.json
    const challengeJson = {
      name: q.title,
      slug: slug,
      preview: q.story ? q.story.slice(0, 150) + "..." : "",
      description: q.story || "",
      input_format: q.input_format || "",
      output_format: q.output_format || "",
      constraints: q.constraints || "",
      difficulty: (q.difficulty || "medium").toLowerCase(),
      time_limit: Number(q.time_limit) || 2.0,
      memory_limit: (Number(q.memory_limit) || 256) * 1024,
      default_language: "python3",
      languages: ["python3", "c", "cpp", "java8"],
      tags: Array.isArray(q.tags) ? q.tags : [],
    };
    zip.file("challenge.json", JSON.stringify(challengeJson, null, 2));

    // 2. config.json
    const configJson = {
      version: 1,
      name: q.title,
      slug: slug,
      type: "code",
      languages: ["python3", "c", "cpp14", "java8"],
    };
    zip.file("config.json", JSON.stringify(configJson, null, 2));

    // 3. metadata.json
    zip.file(
      "metadata.json",
      JSON.stringify(
        {
          id: q.id,
          title: q.title,
          difficulty: q.difficulty,
          topic: q.topic,
          time_limit: q.time_limit,
          memory_limit: q.memory_limit,
          test_cases_count: testCases.length,
        },
        null,
        2
      )
    );

    // 4. problem.md
    const problemMd = `# ${q.title}

${q.story}

### Input Format
${q.input_format}

### Constraints
${q.constraints}

### Output Format
${q.output_format}
`;
    zip.file("problem.md", problemMd);

    // 5. editorial.md
    zip.file("editorial.md", q.editorial || "No editorial provided.");

    // 6. Reference solutions
    zip.file("solution.py", pythonSolution);
    zip.file("solution.c", cSolution);

    // 7. Test cases
    const inputFolder = zip.folder("input");
    const outputFolder = zip.folder("output");

    testCases.forEach((tc: any, index: number) => {
      const idxStr = String(index).padStart(2, "0");
      inputFolder?.file(`input${idxStr}.txt`, tc.input_data || "");
      outputFolder?.file(`output${idxStr}.txt`, tc.output_data || "");
    });

    const zipBuffer = await zip.generateAsync({ type: "uint8array" });

    return new Response(zipBuffer, {
      status: 200,
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename="${slug}-hackerrank.zip"`,
      },
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message }, { status: 500 });
  }
}
