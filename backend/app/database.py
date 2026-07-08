import os

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./music.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info('songs')"))
            columns = [row[1] for row in result.fetchall()]
            if "plays_count" not in columns:
                conn.execute(text("ALTER TABLE songs ADD COLUMN plays_count INTEGER DEFAULT 0"))
            if "cover_url" not in columns:
                conn.execute(text("ALTER TABLE songs ADD COLUMN cover_url TEXT DEFAULT ''"))
            if "genre_id" not in columns:
                conn.execute(text("ALTER TABLE songs ADD COLUMN genre_id INTEGER NULL"))
            if "uploader_id" not in columns:
                conn.execute(text("ALTER TABLE songs ADD COLUMN uploader_id INTEGER NULL"))
            conn.commit()
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info('playlists')"))
            columns = [row[1] for row in result.fetchall()]
            if "cover_url" not in columns:
                conn.execute(text("ALTER TABLE playlists ADD COLUMN cover_url TEXT DEFAULT ''"))
            if "is_public" not in columns:
                conn.execute(text("ALTER TABLE playlists ADD COLUMN is_public INTEGER DEFAULT 1"))
            if "owner_id" not in columns:
                conn.execute(text("ALTER TABLE playlists ADD COLUMN owner_id INTEGER NULL"))
            conn.commit()
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info('users')"))
            columns = [row[1] for row in result.fetchall()]
            if "avatar_url" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url TEXT DEFAULT ''"))
            conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
