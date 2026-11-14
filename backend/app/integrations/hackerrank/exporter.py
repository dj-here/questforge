import io
import zipfile
from typing import List
from backend.app.models import Question, TestCase

class ChallengePackageExporter:
    """Generates HackerRank standard challenge package ZIP for manual upload."""
    
    @staticmethod
    def export_zip(question: Question, test_cases: List[TestCase]) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Problem Statement
            problem_md = [
                f"# {question.title}\n",
                f"**Difficulty**: {question.difficulty}\n",
                f"**Topic**: {question.topic}\n\n",
                f"## Problem Statement\n{question.story}\n\n",
                f"## Input Format\n{question.input_format}\n\n",
                f"## Output Format\n{question.output_format}\n\n",
                f"## Constraints\n{question.constraints}\n\n"
            ]
            if question.explanation:
                problem_md.append(f"## Explanation\n{question.explanation}\n\n")
            zf.writestr("problem.md", "".join(problem_md))

            # 2. Editorial
            if question.editorial:
                zf.writestr("editorial.md", f"# Editorial for {question.title}\n\n{question.editorial}\n")

            # 3. Reference Solutions
            if isinstance(question.reference_solution, dict):
                if question.reference_solution.get("python"):
                    zf.writestr("solution.py", question.reference_solution["python"])
                if question.reference_solution.get("java"):
                    zf.writestr("Solution.java", question.reference_solution["java"])
                if question.reference_solution.get("cpp"):
                    zf.writestr("solution.cpp", question.reference_solution["cpp"])

            # 4. Input / Output Test Cases
            for idx, tc in enumerate(test_cases):
                # HackerRank standard naming: input/input00.txt, output/output00.txt
                num_str = f"{idx:02d}"
                zf.writestr(f"input/input{num_str}.txt", tc.input_data)
                zf.writestr(f"output/output{num_str}.txt", tc.output_data)

            # 5. Metadata & HackerRank 1-Click Import Schemas
            import re
            slug = re.sub(r'[^a-z0-9]+', '-', question.title.lower()).strip('-')

            meta = {
                "title": question.title,
                "slug": slug,
                "difficulty": question.difficulty,
                "time_limit": question.time_limit,
                "memory_limit": question.memory_limit,
                "tags": question.tags,
                "test_cases_count": len(test_cases)
            }
            import json
            zf.writestr("metadata.json", json.dumps(meta, indent=2))

            # HackerRank Automated Challenge Importer format (challenge.json & config.json)
            challenge_json = {
                "name": question.title,
                "slug": slug,
                "body": question.story,
                "problem_statement": question.story,
                "input_format": question.input_format,
                "output_format": question.output_format,
                "constraints": question.constraints,
                "difficulty": question.difficulty.lower(),
                "tags": question.tags,
                "editorial": question.editorial or "",
                "time_limits": {
                    "python3": question.time_limit,
                    "cpp": max(1, question.time_limit // 2),
                    "java": question.time_limit
                },
                "memory_limits": {
                    "python3": question.memory_limit,
                    "cpp": question.memory_limit,
                    "java": question.memory_limit
                }
            }
            zf.writestr("challenge.json", json.dumps(challenge_json, indent=2))
            zf.writestr("config.json", json.dumps(challenge_json, indent=2))

        buffer.seek(0)
        return buffer.getvalue()
