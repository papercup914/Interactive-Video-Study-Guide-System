import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv(override=False)

# For local testing if env variables are not provided, default to sqlite
# The user will inject Neon URL (postgresql://...) here later
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/data/jobs.db")

# If using PostgreSQL, connect_args shouldn't include check_same_thread
# If using SQLite, it's required for FastAPI
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True,  # Handle dropped connections gracefully
    pool_recycle=1800    # Recycle connections after 30 mins to avoid Neon DB timeout
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
