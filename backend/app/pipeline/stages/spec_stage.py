import re
import jinja2
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.models import DifficultyRubric
from backend.app.config import get_prompts_dir

class PromptInjectionError(ValueError):
    pass

def sanitize_user_input(text: str) -> str:
    """Detect and neutralize potential prompt injection attempts in user-supplied strings."""
    if not text:
        return ""
    
    # Check for prompt injection signatures
    suspicious_patterns = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s*prompt",
        r"you\s+are\s+now\s+a",
        r"disregard\s+the\s+above",
        r"override\s+(the\s+)?rubric",
        r"drop\s+table",
        r"<script",
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise PromptInjectionError(f"Malicious input detected in parameter: matches injection pattern '{pattern}'")
    
    # Strip any control characters or dangerous markup
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text).strip()
    return cleaned

class SpecStage:
    def __init__(self, template_dir: Path = None):
        t_dir = template_dir or get_prompts_dir()
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(t_dir)),
            autoescape=False
        )

    def run(
        self,
        topic: str,
        difficulty: str,
        question_type: str = "coding",
        subtopic: str = None,
        languages: list = None,
        db: Session = None
    ) -> str:
        # Sanitize inputs
        clean_topic = sanitize_user_input(topic)
        clean_subtopic = sanitize_user_input(subtopic) if subtopic else None
        clean_difficulty = sanitize_user_input(difficulty)

        # Retrieve rubric from DB or use standard defaults
        rubric_data = {
            "concepts_count": 1,
            "time_complexity_target": "O(N) or O(N log N)",
            "max_solution_lines": 25,
            "constraints_guideline": "N <= 10^5, fitting in standard limits",
            "description": "Standard problem checking single fundamental concept"
        }

        if db:
            rubric_record = db.query(DifficultyRubric).filter(
                DifficultyRubric.difficulty.ilike(clean_difficulty)
            ).first()
            if rubric_record:
                rubric_data = {
                    "concepts_count": rubric_record.concepts_count,
                    "time_complexity_target": rubric_record.time_complexity_target,
                    "max_solution_lines": rubric_record.max_solution_lines,
                    "constraints_guideline": rubric_record.constraints_guideline or "",
                    "description": rubric_record.description or ""
                }
            else:
                # Fallback rubrics if not in DB
                if clean_difficulty.lower() == "easy":
                    rubric_data = {
                        "concepts_count": 1,
                        "time_complexity_target": "O(N) or O(N log N)",
                        "max_solution_lines": 20,
                        "constraints_guideline": "Small constraints: N <= 10^4",
                        "description": "Single concept, straightforward simulation or two-pointers, concise solution"
                    }
                elif clean_difficulty.lower() == "medium":
                    rubric_data = {
                        "concepts_count": 2,
                        "time_complexity_target": "O(N) or O(N log N)",
                        "max_solution_lines": 40,
                        "constraints_guideline": "N <= 2 * 10^5, requires optimal data structure",
                        "description": "Combines 2 concepts (e.g. prefix sum + hash map, greedy + heap), edge cases matter"
                    }
                elif clean_difficulty.lower() == "hard":
                    rubric_data = {
                        "concepts_count": 3,
                        "time_complexity_target": "O(N log N) or O(N sqrt(N))",
                        "max_solution_lines": 70,
                        "constraints_guideline": "N <= 5 * 10^5, strict time limit, large inputs",
                        "description": "Non-obvious insight, advanced algorithms/structures, multiple invariants"
                    }

        template = self.env.get_template("question_spec.j2")
        rendered_spec = template.render(
            topic=clean_topic,
            subtopic=clean_subtopic,
            difficulty=clean_difficulty,
            question_type=question_type,
            languages=languages or ["python", "java", "cpp"],
            rubric=rubric_data
        )
        return rendered_spec
