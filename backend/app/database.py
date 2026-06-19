import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

is_sqlite = "sqlite" in settings.DATABASE_URL

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_size=20 if not is_sqlite else 10,
    max_overflow=40 if not is_sqlite else 20,
    pool_pre_ping=True,
    pool_recycle=300 if not is_sqlite else -1,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        return True
    except Exception:
        return False


def init_db():
    retries = 3
    for attempt in range(retries):
        try:
            if is_sqlite:
                import re
                match = re.search(r'sqlite:///(.+)', settings.DATABASE_URL)
                if match:
                    db_path = match.group(1)
                    db_dir = os.path.dirname(db_path)
                    if db_dir and not os.path.exists(db_dir):
                        os.makedirs(db_dir, exist_ok=True)

            Base.metadata.create_all(bind=engine)

            if is_sqlite:
                with engine.connect() as conn:
                    conn.execute(text("PRAGMA journal_mode=WAL"))
                    conn.execute(text("PRAGMA synchronous=NORMAL"))
                    conn.execute(text("PRAGMA cache_size=-64000"))
                    conn.commit()
            return
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                raise e
