import time
import random
import uuid
import logging
from typing import Optional, Dict, Any, List
import httpx

from backend.app.config import settings
from backend.app.models import Question, TestCase
from backend.app.integrations.hackerrank.mapper import question_to_hackerrank_payload

logger = logging.getLogger(__name__)

class HackerRankAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

class HackerRankClient:
    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        dry_run: Optional[bool] = None
    ):
        self.token = token or settings.HACKERRANK_API_TOKEN
        self.base_url = (base_url or settings.HACKERRANK_BASE_URL).rstrip("/")
        self.dry_run = dry_run if dry_run is not None else settings.HACKERRANK_DRY_RUN

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _request_with_retry(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 4
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        delay = 1.0

        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=20.0) as client:
                    resp = client.request(
                        method=method,
                        url=url,
                        headers=self._headers(),
                        json=json_data,
                        params=params
                    )
                    
                    # If rate limited (429) or server error (5xx), back off and retry
                    if resp.status_code == 429 or resp.status_code >= 500:
                        if attempt == max_retries - 1:
                            raise HackerRankAPIError(
                                f"HackerRank API error {resp.status_code} after {max_retries} retries",
                                status_code=resp.status_code,
                                response_body=resp.text
                            )
                        jitter = random.uniform(0.1, 0.5)
                        time.sleep(delay + jitter)
                        delay *= 2
                        continue

                    if resp.status_code not in (200, 201, 204):
                        raise HackerRankAPIError(
                            f"HackerRank API returned {resp.status_code}: {resp.text}",
                            status_code=resp.status_code,
                            response_body=resp.text
                        )

                    return resp.json() if resp.status_code != 204 else {"status": "success"}

            except httpx.RequestError as e:
                if attempt == max_retries - 1:
                    raise HackerRankAPIError(f"HackerRank network request failed: {str(e)}")
                time.sleep(delay)
                delay *= 2

        raise HackerRankAPIError("Request failed unexpectedly")

    def create_question(
        self,
        question: Question,
        test_cases: List[TestCase],
        test_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates question on HackerRank or updates if remote ID exists (idempotency)."""
        if self.dry_run:
            simulated_id = f"hr_q_{uuid.uuid4().hex[:10]}"
            logger.info(f"[DRY-RUN] Simulated creating question '{question.title}' -> remote_id={simulated_id}")
            return {
                "id": simulated_id,
                "name": question.title,
                "url": f"https://www.hackerrank.com/work/questions/{simulated_id}",
                "status": "published_dry_run",
                "test_cases_count": len(test_cases)
            }

        payload = question_to_hackerrank_payload(question, test_cases)
        
        # If question already has remote_hackerrank_id, use update for idempotency
        if question.remote_hackerrank_id:
            return self.update_question(question.remote_hackerrank_id, question, test_cases)

        result = self._request_with_retry("POST", "/tests/questions", json_data=payload)
        remote_id = str(result.get("id") or result.get("data", {}).get("id"))

        # Optionally add to existing test
        if test_id and remote_id:
            try:
                self.add_to_test(remote_id, test_id)
            except Exception as e:
                logger.warning(f"Created question {remote_id} but failed to attach to test {test_id}: {e}")

        return {
            "id": remote_id,
            "name": question.title,
            "url": f"https://www.hackerrank.com/work/questions/{remote_id}",
            "status": "published",
            "raw": result
        }

    def update_question(
        self,
        remote_id: str,
        question: Question,
        test_cases: List[TestCase]
    ) -> Dict[str, Any]:
        if self.dry_run:
            logger.info(f"[DRY-RUN] Simulated updating remote question {remote_id}")
            return {
                "id": remote_id,
                "name": question.title,
                "url": f"https://www.hackerrank.com/work/questions/{remote_id}",
                "status": "updated_dry_run"
            }

        payload = question_to_hackerrank_payload(question, test_cases)
        result = self._request_with_retry("PUT", f"/tests/questions/{remote_id}", json_data=payload)
        return {
            "id": remote_id,
            "name": question.title,
            "url": f"https://www.hackerrank.com/work/questions/{remote_id}",
            "status": "updated",
            "raw": result
        }

    def get_question(self, remote_id: str) -> Dict[str, Any]:
        if self.dry_run:
            return {
                "id": remote_id,
                "name": "Simulated Remote Question",
                "status": "active"
            }
        return self._request_with_retry("GET", f"/tests/questions/{remote_id}")

    def list_questions(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        if self.dry_run:
            return {
                "total": 3,
                "questions": [
                    {"id": "hr_q_mock1", "name": "Array Sum Query", "difficulty": "easy"},
                    {"id": "hr_q_mock2", "name": "Dynamic Substring Match", "difficulty": "medium"},
                    {"id": "hr_q_mock3", "name": "Network Flow Maximizer", "difficulty": "hard"}
                ]
            }
        return self._request_with_retry("GET", "/tests/questions", params={"limit": limit, "offset": offset})

    def delete_question(self, remote_id: str) -> bool:
        if self.dry_run:
            logger.info(f"[DRY-RUN] Simulated deleting question {remote_id}")
            return True
        self._request_with_retry("DELETE", f"/tests/questions/{remote_id}")
        return True

    def add_to_test(self, question_id: str, test_id: str) -> bool:
        if self.dry_run:
            logger.info(f"[DRY-RUN] Simulated adding question {question_id} to test {test_id}")
            return True
        self._request_with_retry("POST", f"/tests/{test_id}/questions", json_data={"question_id": question_id})
        return True
