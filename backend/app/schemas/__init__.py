from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# --- Auth Schemas ---
class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, description="User email address")
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime

# --- LLM Strict Generation Schema ---
class ReferenceSolutionSchema(BaseModel):
    python: str = Field(description="Production-grade Python 3 solution with complete imports and stdio handling")
    c: Optional[str] = Field(default=None, description="Idiomatic standard C (C11) solution with complete stdio handling")
    cpp: Optional[str] = Field(default=None, description="Modern C++ solution with fast I/O")
    java: Optional[str] = Field(default=None, description="Idiomatic Java solution class Solution with main")
    sql: Optional[str] = Field(default=None, description="Standard SQL query for database tasks")

class GeneratedQuestionSchema(BaseModel):
    title: str = Field(description="Clear, engaging problem title")
    story: str = Field(description="Rich narrative or clean problem description")
    input_format: str = Field(description="Specification of input format from stdin")
    output_format: str = Field(description="Specification of output format to stdout")
    constraints: str = Field(description="Bounds and mathematical constraints")
    sample_inputs: List[str] = Field(min_length=1, description="List of sample input strings")
    sample_outputs: List[str] = Field(min_length=1, description="List of expected sample outputs")
    explanation: str = Field(description="Explanation of sample cases")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    difficulty: str = Field(description="Easy, Medium, or Hard")
    time_limit: float = Field(default=2.0, description="Time limit in seconds")
    memory_limit: int = Field(default=256, description="Memory limit in MB")
    reference_solution: ReferenceSolutionSchema
    brute_force_solution: str = Field(description="Simpler brute-force implementation to verify small cases against")
    test_case_generator_code: str = Field(description="Executable Python script that prints input cases delimited or standard")
    editorial: str = Field(description="Comprehensive pedagogical explanation of the algorithm, complexities, and pitfalls")

# --- Critic Schema ---
class CriticScoreDetail(BaseModel):
    clarity: float = Field(ge=1.0, le=10.0, description="Clarity and readability of problem statement")
    originality: float = Field(ge=1.0, le=10.0, description="Novelty and absence of direct copycat boilerplate")
    difficulty_match: float = Field(ge=1.0, le=10.0, description="Alignment with chosen difficulty tier")
    unambiguity: float = Field(ge=1.0, le=10.0, description="Precision of constraints, edge cases, and I/O format")

class CriticResultSchema(BaseModel):
    scores: CriticScoreDetail
    overall_score: float = Field(ge=1.0, le=10.0)
    passed: bool
    critique: str
    suggested_improvements: List[str] = Field(default_factory=list)

# --- Test Case Schemas ---
class TestCaseBase(BaseModel):
    __test__ = False
    input_data: str
    output_data: str
    is_sample: bool = False
    is_hidden: bool = True
    score: float = 5.0
    explanation: Optional[str] = None

class TestCaseResponse(TestCaseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_id: str
    created_at: datetime

# --- Verification Schemas ---
class VerificationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    attempt_number: int
    stage: str
    passed: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_time_ms: Optional[float] = None
    memory_used_kb: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime

# --- Question Schemas ---
class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    story: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    constraints: Optional[str] = None
    sample_inputs: Optional[List[str]] = None
    sample_outputs: Optional[List[str]] = None
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: Optional[str] = None
    time_limit: Optional[float] = None
    memory_limit: Optional[int] = None
    reference_solution: Optional[Dict[str, str]] = None
    editorial: Optional[str] = None
    status: Optional[str] = None

class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    job_id: Optional[str] = None
    title: str
    topic: str
    subtopic: Optional[str] = None
    difficulty: str
    question_type: str
    story: str
    input_format: str
    output_format: str
    constraints: str
    sample_inputs: List[str]
    sample_outputs: List[str]
    explanation: Optional[str] = None
    tags: List[str]
    time_limit: float
    memory_limit: int
    reference_solution: Dict[str, Any]
    brute_force_solution: Optional[str] = None
    test_case_generator_code: Optional[str] = None
    editorial: Optional[str] = None
    status: str
    critic_score: Optional[float] = None
    critic_feedback: Optional[Dict[str, Any]] = None
    remote_hackerrank_id: Optional[str] = None
    hackerrank_url: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    test_cases: List[TestCaseResponse] = []
    verification_logs: List[VerificationLogResponse] = []

# --- Job Schemas ---
class GenerationJobCreate(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100, description="e.g. Arrays, Dynamic Programming, Graphs")
    subtopic: Optional[str] = Field(default=None, max_length=100, description="e.g. Two Pointers, Shortest Paths")
    difficulty: str = Field(default="Medium", description="Easy, Medium, Hard, or Custom")
    question_type: str = Field(default="coding", description="coding, MCQ, SQL, debugging, output-prediction")
    languages: List[str] = Field(default=["python", "java", "cpp"])
    count: int = Field(default=1, ge=1, le=10, description="Number of questions to generate")
    auto_publish: bool = Field(default=False, description="Automatically publish to HackerRank on passing all checks")

class GenerationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    topic: str
    subtopic: Optional[str] = None
    difficulty: str
    question_type: str
    languages: List[str]
    count: int
    auto_publish: bool
    status: str
    progress: float
    current_stage: str
    stage_history: List[Dict[str, Any]]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse] = []

# --- HackerRank Publish Schemas ---
class PublishRequest(BaseModel):
    test_id: Optional[str] = Field(default=None, description="Optional existing HackerRank test ID to attach to")
    dry_run: Optional[bool] = Field(default=None, description="Simulate without external API call")

class BulkPublishRequest(BaseModel):
    question_ids: List[str]
    test_id: Optional[str] = None
    dry_run: Optional[bool] = None

class PublishResultItem(BaseModel):
    question_id: str
    success: bool
    remote_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None

class PublishResponse(BaseModel):
    results: List[PublishResultItem]
    total: int
    published: int
    failed: int
