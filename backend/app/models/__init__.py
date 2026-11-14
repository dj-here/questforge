import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"

class QuestionStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW_READY = "review_ready"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.REVIEWER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class DifficultyRubric(Base):
    __tablename__ = "difficulty_rubrics"

    id = Column(Integer, primary_key=True, index=True)
    difficulty = Column(String(50), unique=True, nullable=False)  # Easy, Medium, Hard, Custom
    max_solution_lines = Column(Integer, default=25)
    time_complexity_target = Column(String(100), default="O(n)")
    concepts_count = Column(Integer, default=1)
    constraints_guideline = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(64), primary_key=True, index=True)
    topic = Column(String(100), nullable=False)
    subtopic = Column(String(100), nullable=True)
    difficulty = Column(String(50), default="Medium", nullable=False)
    question_type = Column(String(50), default="coding", nullable=False)
    languages = Column(JSON, default=lambda: ["python", "java", "cpp"])
    count = Column(Integer, default=1, nullable=False)
    auto_publish = Column(Boolean, default=False, nullable=False)
    
    status = Column(String(50), default=JobStatus.PENDING.value, nullable=False)
    progress = Column(Float, default=0.0)  # 0.0 - 100.0
    current_stage = Column(String(50), default="queued")
    stage_history = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    questions = relationship("Question", back_populates="job", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("generation_jobs.id"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    subtopic = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=False, index=True)
    question_type = Column(String(50), default="coding", nullable=False)
    
    story = Column(Text, nullable=False)  # Problem description / context
    input_format = Column(Text, nullable=False)
    output_format = Column(Text, nullable=False)
    constraints = Column(Text, nullable=False)
    
    sample_inputs = Column(JSON, default=list)
    sample_outputs = Column(JSON, default=list)
    explanation = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    
    time_limit = Column(Float, default=2.0)  # seconds
    memory_limit = Column(Integer, default=256)  # MB
    
    reference_solution = Column(JSON, default=dict)  # {"python": "...", "java": "...", "cpp": "..."}
    brute_force_solution = Column(Text, nullable=True)
    test_case_generator_code = Column(Text, nullable=True)
    editorial = Column(Text, nullable=True)
    
    status = Column(String(50), default=QuestionStatus.REVIEW_READY.value, nullable=False, index=True)
    
    # Critic & Quality
    critic_score = Column(Float, nullable=True)
    critic_feedback = Column(JSON, default=dict)
    
    # Dedup embedding
    embedding = Column(JSON, nullable=True)
    
    # HackerRank Sync
    remote_hackerrank_id = Column(String(100), nullable=True, index=True)
    hackerrank_url = Column(String(500), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    job = relationship("GenerationJob", back_populates="questions")
    test_cases = relationship("TestCase", back_populates="question", cascade="all, delete-orphan")
    verification_logs = relationship("VerificationLog", back_populates="question", cascade="all, delete-orphan")
    audit_trails = relationship("AuditTrail", back_populates="question", cascade="all, delete-orphan")

class TestCase(Base):
    __tablename__ = "test_cases"
    __test__ = False

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String(64), ForeignKey("questions.id"), nullable=False, index=True)
    
    input_data = Column(Text, nullable=False)
    output_data = Column(Text, nullable=False)
    is_sample = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=True)
    score = Column(Float, default=5.0)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    question = relationship("Question", back_populates="test_cases")

class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String(64), ForeignKey("questions.id"), nullable=False, index=True)
    
    attempt_number = Column(Integer, default=1)
    stage = Column(String(50), nullable=False)  # generator, reference_solution, brute_force
    passed = Column(Boolean, default=False)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    memory_used_kb = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    question = relationship("Question", back_populates="verification_logs")

class AuditTrail(Base):
    __tablename__ = "audit_trails"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String(64), ForeignKey("questions.id"), nullable=True, index=True)
    
    action = Column(String(100), nullable=False)
    actor = Column(String(100), default="system")
    prompt_snapshot = Column(Text, nullable=True)
    raw_llm_response = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    question = relationship("Question", back_populates="audit_trails")
