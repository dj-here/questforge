import jinja2
from pathlib import Path
from backend.app.schemas import GeneratedQuestionSchema, CriticResultSchema
from backend.app.pipeline.llm_client import LLMClient
from backend.app.config import settings, get_prompts_dir

class QualityStage:
    def __init__(self, llm_client: LLMClient = None, template_dir: Path = None):
        self.llm = llm_client or LLMClient()
        t_dir = template_dir or get_prompts_dir()
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(t_dir)),
            autoescape=False
        )

    def run(
        self,
        question: GeneratedQuestionSchema,
        min_score: float = None
    ) -> CriticResultSchema:
        threshold = min_score or settings.CRITIC_MIN_SCORE
        template = self.env.get_template("question_critic.j2")
        prompt = template.render(
            question=question,
            min_score=threshold
        )

        system_instruction = (
            "You are a rigorous, uncompromising quality critic and problem reviewer. "
            "Evaluate programming challenges objectively against production standards."
        )

        critic_result: CriticResultSchema = self.llm.generate_structured(
            prompt=prompt,
            schema=CriticResultSchema,
            system=system_instruction,
            max_retries=2
        )

        # Enforce threshold programmatically
        if critic_result.overall_score < threshold:
            critic_result.passed = False
            if "Score below threshold" not in critic_result.critique:
                critic_result.critique += f" (Score below threshold: overall score {critic_result.overall_score} < minimum required {threshold})"

        return critic_result
