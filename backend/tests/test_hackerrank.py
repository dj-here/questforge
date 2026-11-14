import pytest
import zipfile
import io
from backend.app.models import Question, TestCase
from backend.app.integrations.hackerrank.mapper import question_to_hackerrank_payload, map_difficulty_to_hackerrank
from backend.app.integrations.hackerrank.client import HackerRankClient
from backend.app.integrations.hackerrank.exporter import ChallengePackageExporter

@pytest.fixture
def sample_question_model():
    q = Question(
        id="q_test_hr",
        title="Array Peak Index",
        topic="Arrays",
        difficulty="Medium",
        question_type="coding",
        story="Find peak index in array...",
        input_format="First line N...",
        output_format="Peak index...",
        constraints="1 <= N <= 10^5",
        sample_inputs=["3\n1 3 2"],
        sample_outputs=["1"],
        explanation="Index 1 is peak",
        tags=["arrays", "binary-search"],
        time_limit=2.0,
        memory_limit=256,
        reference_solution={"python": "print(1)"},
        editorial="Binary search"
    )
    tc1 = TestCase(question_id=q.id, input_data="3\n1 3 2", output_data="1", is_sample=True, is_hidden=False, score=0.0)
    tc2 = TestCase(question_id=q.id, input_data="4\n1 2 3 1", output_data="2", is_sample=False, is_hidden=True, score=10.0)
    q.test_cases = [tc1, tc2]
    return q

def test_map_difficulty():
    assert map_difficulty_to_hackerrank("Easy") == "easy"
    assert map_difficulty_to_hackerrank("Medium") == "medium"
    assert map_difficulty_to_hackerrank("Hard") == "hard"

def test_question_to_hackerrank_payload(sample_question_model):
    payload = question_to_hackerrank_payload(sample_question_model, sample_question_model.test_cases)
    assert payload["name"] == "Array Peak Index"
    assert payload["type"] == "code"
    assert "Peak index" in payload["problem_statement"]
    assert len(payload["testcases"]) == 2
    assert payload["testcases"][0]["is_sample"] == 1
    assert payload["testcases"][1]["is_hidden"] == 1
    assert payload["difficulty"] == "medium"

def test_hackerrank_client_dry_run_create(sample_question_model):
    client = HackerRankClient(dry_run=True)
    res = client.create_question(sample_question_model, sample_question_model.test_cases)
    assert res["status"] == "published_dry_run"
    assert res["id"].startswith("hr_q_")
    assert "https://www.hackerrank.com/work/questions/" in res["url"]

def test_hackerrank_client_dry_run_list():
    client = HackerRankClient(dry_run=True)
    res = client.list_questions()
    assert res["total"] >= 1
    assert len(res["questions"]) >= 1

def test_hackerrank_client_dry_run_delete():
    client = HackerRankClient(dry_run=True)
    assert client.delete_question("hr_q_123") is True

def test_hackerrank_client_dry_run_add_to_test():
    client = HackerRankClient(dry_run=True)
    assert client.add_to_test("hr_q_123", "test_456") is True

def test_challenge_package_exporter_zip(sample_question_model):
    zip_bytes = ChallengePackageExporter.export_zip(sample_question_model, sample_question_model.test_cases)
    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 100

    # Read back ZIP
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "problem.md" in namelist
        assert "editorial.md" in namelist
        assert "solution.py" in namelist
        assert "input/input00.txt" in namelist
        assert "output/output00.txt" in namelist
        assert "metadata.json" in namelist
