import jinja2
from pathlib import Path
from backend.app.schemas import GeneratedQuestionSchema
from backend.app.pipeline.llm_client import LLMClient
from backend.app.config import get_prompts_dir

class GenerateStage:
    def __init__(self, llm_client: LLMClient = None, template_dir: Path = None):
        self.llm = llm_client or LLMClient()
        t_dir = template_dir or get_prompts_dir()
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(t_dir)),
            autoescape=False
        )

    def run(
        self,
        spec: str,
        topic: str,
        difficulty: str,
        subtopic: str = None,
        languages: list = None
    ) -> GeneratedQuestionSchema:
        template = self.env.get_template("question_generate.j2")
        prompt = template.render(
            spec=spec,
            topic=topic,
            subtopic=subtopic,
            difficulty=difficulty,
            languages=languages or ["python", "java", "cpp"],
            error_feedback=None
        )

        system_instruction = (
            "You are a Principal Software Engineer and Competitive Programming Lead. "
            "Generate rigorous, innovative questions with optimal reference solutions. "
            "Output must be STRICT JSON."
        )

        generated: GeneratedQuestionSchema = self.llm.generate_structured(
            prompt=prompt,
            schema=GeneratedQuestionSchema,
            system=system_instruction,
            max_retries=3
        )
        return generated
