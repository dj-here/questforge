import pytest
from backend.app.models import Question, QuestionStatus

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "QuestForge"

def test_metrics_endpoint(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "questions_total" in data
    assert "generation_jobs_total" in data

def test_create_generation_job_sync(client, auth_headers):
    payload = {
        "topic": "String Manipulation",
        "subtopic": "Prefix Matching",
        "difficulty": "Medium",
        "question_type": "coding",
        "languages": ["python", "java"],
        "count": 1,
        "auto_publish": False
    }
    res = client.post("/generation-jobs?sync=true", json=payload, headers=auth_headers)
    assert res.status_code == 201
    job = res.json()
    assert job["id"].startswith("job_")
    assert job["status"] == "completed"
    assert job["progress"] == 100.0
    assert len(job["questions"]) == 1

def test_get_generation_job(client, auth_headers):
    res = client.post("/generation-jobs", json={"topic": "Graphs", "count": 1}, headers=auth_headers)
    assert res.status_code == 201
    job_id = res.json()["id"]

    res_get = client.get(f"/generation-jobs/{job_id}", headers=auth_headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == job_id

def test_list_and_filter_questions(client, auth_headers):
    res = client.get("/questions?topic=Arrays", headers=auth_headers)
    assert res.status_code == 200
    questions = res.json()
    assert len(questions) >= 1
    assert all("Arrays" in q["topic"] for q in questions)

def test_get_question_by_id(client, auth_headers):
    list_res = client.get("/questions", headers=auth_headers)
    qid = list_res.json()[0]["id"]

    res = client.get(f"/questions/{qid}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == qid

def test_patch_question(client, auth_headers):
    list_res = client.get("/questions", headers=auth_headers)
    qid = list_res.json()[0]["id"]

    patch_res = client.patch(f"/questions/{qid}", json={"title": "Updated Custom Title"}, headers=auth_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Custom Title"

def test_approve_question(client, auth_headers):
    list_res = client.get("/questions", headers=auth_headers)
    qid = list_res.json()[0]["id"]

    res = client.post(f"/questions/{qid}/approve", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == QuestionStatus.APPROVED.value

def test_reject_question(client, auth_headers):
    list_res = client.get("/questions", headers=auth_headers)
    qid = list_res.json()[0]["id"]

    res = client.post(f"/questions/{qid}/reject?reason=Ambiguous+constraints", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == QuestionStatus.REJECTED.value

def test_publish_question_dry_run(client, auth_headers):
    list_res = client.get("/questions", headers=auth_headers)
    qid = list_res.json()[0]["id"]

    # First approve it
    client.post(f"/questions/{qid}/approve", headers=auth_headers)

    res = client.post(f"/questions/{qid}/publish", json={"dry_run": True}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["remote_id"].startswith("hr_q_")

def test_bulk_publish_dry_run(client, auth_headers):
    list_res = client.get("/questions", headers=auth_headers)
    qids = [q["id"] for q in list_res.json()[:2]]

    res = client.post("/publish/bulk", json={"question_ids": qids, "dry_run": True}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == len(qids)
    assert data["published"] == len(qids)
    assert data["failed"] == 0

def test_export_question_zip(client, auth_headers):
    list_res = client.get("/questions", headers=auth_headers)
    qid = list_res.json()[0]["id"]

    res = client.get(f"/questions/{qid}/export", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    assert len(res.content) > 50
