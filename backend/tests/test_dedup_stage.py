import pytest
from backend.app.pipeline.stages.dedup_stage import DedupStage, cosine_similarity, DedupResult
from backend.app.pipeline.llm_client import LLMClient
from backend.app.models import Question
from backend.app.schemas import GeneratedQuestionSchema, ReferenceSolutionSchema

def test_cosine_similarity_calculation():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2)) == 1.0

    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v3)) == 0.0

def test_dedup_stage_detects_near_duplicate(db_session):
    llm = LLMClient()
    stage = DedupStage(llm_client=llm)

    # Question with same text as existing seed
    existing = db_session.query(Question).first()
    assert existing is not None

    # Calculate embedding for existing question if not present
    if not existing.embedding:
        existing.embedding = llm.get_embedding(f"{existing.title}\n{existing.story}\n{existing.input_format}\n{existing.constraints}")
        db_session.commit()

    duplicate_q = GeneratedQuestionSchema(
        title=existing.title,
        story=existing.story,
        input_format=existing.input_format,
        output_format=existing.output_format,
        constraints=existing.constraints,
        sample_inputs=existing.sample_inputs,
        sample_outputs=existing.sample_outputs,
        explanation="Exp",
        tags=existing.tags,
        difficulty=existing.difficulty,
        time_limit=2.0,
        memory_limit=256,
        reference_solution=ReferenceSolutionSchema(python="print(1)"),
        brute_force_solution="print(1)",
        test_case_generator_code="print(1)",
        editorial="Ed"
    )

    res: DedupResult = stage.run(question=duplicate_q, db=db_session, threshold=0.85)
    assert res.is_duplicate is True
    assert res.max_similarity > 0.85
    assert res.matched_question_id == existing.id

def test_dedup_stage_accepts_novel_question(db_session):
    llm = LLMClient()
    stage = DedupStage(llm_client=llm)

    novel_q = GeneratedQuestionSchema(
        title="Intergalactic Hyperloop Route Optimizer",
        story="Given an uncharted cosmic constellation of wormholes...",
        input_format="Wormholes N M...",
        output_format="Min antimatter fuel...",
        constraints="1 <= N <= 100",
        sample_inputs=["3 2"],
        sample_outputs=["5"],
        explanation="Take warp gate 1",
        tags=["space", "hyperloop"],
        difficulty="Hard",
        time_limit=2.0,
        memory_limit=256,
        reference_solution=ReferenceSolutionSchema(python="print(5)"),
        brute_force_solution="print(5)",
        test_case_generator_code="print('3 2')",
        editorial="Dijkstra on interstellar graph"
    )

    res: DedupResult = stage.run(question=novel_q, db=db_session, threshold=0.85)
    assert res.is_duplicate is False
