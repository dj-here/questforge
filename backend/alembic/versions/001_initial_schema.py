"""initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-11-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )
    op.create_table(
        'difficulty_rubrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('difficulty', sa.String(length=50), nullable=False, unique=True),
        sa.Column('max_solution_lines', sa.Integer(), default=25),
        sa.Column('time_complexity_target', sa.String(length=100), default="O(n)"),
        sa.Column('concepts_count', sa.Integer(), default=1),
        sa.Column('constraints_guideline', sa.Text()),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True)
    )
    op.create_table(
        'generation_jobs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('subtopic', sa.String(length=100)),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('languages', sa.JSON()),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('auto_publish', sa.Boolean(), default=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('progress', sa.Float(), default=0.0),
        sa.Column('current_stage', sa.String(length=50)),
        sa.Column('stage_history', sa.JSON()),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )
    op.create_table(
        'questions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('job_id', sa.String(length=64), sa.ForeignKey('generation_jobs.id')),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('subtopic', sa.String(length=100)),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('story', sa.Text(), nullable=False),
        sa.Column('input_format', sa.Text(), nullable=False),
        sa.Column('output_format', sa.Text(), nullable=False),
        sa.Column('constraints', sa.Text(), nullable=False),
        sa.Column('sample_inputs', sa.JSON()),
        sa.Column('sample_outputs', sa.JSON()),
        sa.Column('explanation', sa.Text()),
        sa.Column('tags', sa.JSON()),
        sa.Column('time_limit', sa.Float(), default=2.0),
        sa.Column('memory_limit', sa.Integer(), default=256),
        sa.Column('reference_solution', sa.JSON()),
        sa.Column('brute_force_solution', sa.Text()),
        sa.Column('test_case_generator_code', sa.Text()),
        sa.Column('editorial', sa.Text()),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('critic_score', sa.Float()),
        sa.Column('critic_feedback', sa.JSON()),
        sa.Column('embedding', sa.JSON()),
        sa.Column('remote_hackerrank_id', sa.String(length=100)),
        sa.Column('hackerrank_url', sa.String(length=500)),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )
    op.create_table(
        'test_cases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.String(length=64), sa.ForeignKey('questions.id'), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=False),
        sa.Column('output_data', sa.Text(), nullable=False),
        sa.Column('is_sample', sa.Boolean(), default=False),
        sa.Column('is_hidden', sa.Boolean(), default=True),
        sa.Column('score', sa.Float(), default=5.0),
        sa.Column('explanation', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )
    op.create_table(
        'verification_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.String(length=64), sa.ForeignKey('questions.id'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), default=1),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('passed', sa.Boolean(), default=False),
        sa.Column('stdout', sa.Text()),
        sa.Column('stderr', sa.Text()),
        sa.Column('execution_time_ms', sa.Float()),
        sa.Column('memory_used_kb', sa.Float()),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )
    op.create_table(
        'audit_trails',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.String(length=64), sa.ForeignKey('questions.id')),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=100), default='system'),
        sa.Column('prompt_snapshot', sa.Text()),
        sa.Column('raw_llm_response', sa.Text()),
        sa.Column('metadata_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )

def downgrade() -> None:
    op.drop_table('audit_trails')
    op.drop_table('verification_logs')
    op.drop_table('test_cases')
    op.drop_table('questions')
    op.drop_table('generation_jobs')
    op.drop_table('difficulty_rubrics')
    op.drop_table('users')
