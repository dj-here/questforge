from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

raw_url = settings.effective_db_url
# In dev/testing if DATABASE_URL was inherited from another project's PostgreSQL, fallback or normalize
if raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {}
if raw_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    raw_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
