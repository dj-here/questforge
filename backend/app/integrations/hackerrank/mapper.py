from typing import Dict, Any, List
from backend.app.models import Question, TestCase

def map_difficulty_to_hackerrank(diff: str) -> str:
    d = diff.lower()
    if "easy" in d:
        return "easy"
    elif "hard" in d:
        return "hard"
    return "medium"

def map_languages_to_hackerrank(languages: List[str]) -> List[str]:
    mapping = {
        "c": "c",
        "python": "python3",
        "python3": "python3",
        "java": "java15",
        "cpp": "cpp14",
        "c++": "cpp14",
        "javascript": "javascript",
        "sql": "sql"
    }
    return [mapping.get(l.lower(), l.lower()) for l in languages]

def question_to_hackerrank_payload(
    question: Question,
    test_cases: List[TestCase]
) -> Dict[str, Any]:
    """Maps internal QuestForge Question model to HackerRank for Work REST v3 payload."""
    # Compose comprehensive markdown problem statement
    statement_parts = [
        f"### Description\n{question.story}\n",
        f"### Input Format\n{question.input_format}\n",
        f"### Output Format\n{question.output_format}\n",
        f"### Constraints\n```\n{question.constraints}\n```\n"
    ]
    if question.sample_inputs:
        statement_parts.append("### Sample Cases\n")
        for idx, (inp, out) in enumerate(zip(question.sample_inputs, question.sample_outputs)):
            statement_parts.append(
                f"**Sample Input {idx}**\n```\n{inp}\n```\n"
                f"**Sample Output {idx}**\n```\n{out}\n```\n"
            )
    if question.explanation:
        statement_parts.append(f"### Explanation\n{question.explanation}\n")

    full_statement = "\n".join(statement_parts)

    formatted_testcases = []
    for idx, tc in enumerate(test_cases):
        formatted_testcases.append({
            "testcase_id": idx + 1,
            "input": tc.input_data,
            "output": tc.output_data,
            "score": tc.score,
            "is_sample": 1 if tc.is_sample else 0,
            "is_hidden": 1 if tc.is_hidden else 0,
            "explanation": tc.explanation or ""
        })

    langs = list(question.reference_solution.keys()) if isinstance(question.reference_solution, dict) else ["python"]

    payload = {
        "name": question.title,
        "type": "code",
        "problem_statement": full_statement,
        "input_format": question.input_format,
        "output_format": question.output_format,
        "constraints": question.constraints,
        "difficulty": map_difficulty_to_hackerrank(question.difficulty),
        "tags": question.tags or [question.topic],
        "allowed_languages": map_languages_to_hackerrank(langs),
        "time_limit": int(question.time_limit),
        "memory_limit": int(question.memory_limit),
        "testcases": formatted_testcases
    }
    return payload
