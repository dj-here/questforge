import pytest
from backend.app.pipeline.stages.generate_stage import GenerateStage
from backend.app.pipeline.llm_client import LLMClient
from backend.app.schemas import GeneratedQuestionSchema

def test_generate_stage_mock_llm():
    client = LLMClient()
    client.mock_mode = True
    stage = GenerateStage(llm_client=client)

    generated = stage.run(
        spec="Topic: Arrays\nDifficulty: Medium",
        topic="Arrays",
        difficulty="Medium",
        languages=["python", "java", "cpp"]
    )

    assert isinstance(generated, GeneratedQuestionSchema)
    assert len(generated.title) > 0
    assert len(generated.story) > 0
    assert len(generated.sample_inputs) >= 1
    assert len(generated.sample_outputs) >= 1
    assert "def solve():" in generated.reference_solution.python
    assert generated.brute_force_solution is not None
    assert generated.test_case_generator_code is not None

def test_generate_stage_retries_on_malformed_json(monkeypatch):
    client = LLMClient()
    stage = GenerateStage(llm_client=client)

    # Simulate 1st call returning malformed JSON and 2nd call returning valid JSON
    calls = 0
    def mock_generate(prompt, system=None, max_tokens=4000):
        nonlocal calls
        calls += 1
        if calls == 1:
            return "Not a valid json response { broken"
        return client._get_mock_raw_response(prompt)

    monkeypatch.setattr(client, "generate", mock_generate)

    result = stage.run(
        spec="Topic: DP",
        topic="Dynamic Programming",
        difficulty="Medium"
    )
    assert calls == 2
    assert isinstance(result, GeneratedQuestionSchema)
