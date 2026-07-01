from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from .database import Base

playlist_song = Table(
    "playlist_song",
    Base.metadata,
    Column("playlist_id", Integer, ForeignKey("playlists.id"), primary_key=True),
    Column("song_id", Integer, ForeignKey("songs.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    auth_token = Column(String, unique=True, index=True, nullable=True)
    avatar_url = Column(String, default="")


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    album = Column(String, default="")
    genre = Column(String, default="")
    genre_id = Column(Integer, ForeignKey("genres.id"), nullable=True)
    url = Column(String, default="")
    cover_url = Column(String, default="")
    duration = Column(Integer, default=0)
    plays_count = Column(Integer, default=0)

    genre_detail = relationship("Genre", back_populates="songs")
    playlists = relationship("Playlist", secondary=playlist_song, back_populates="songs")


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, default="")
    cover_url = Column(String, default="")

    songs = relationship("Song", back_populates="genre_detail")


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, default="")
    cover_url = Column(String, default="")

    songs = relationship("Song", secondary=playlist_song, back_populates="playlists")
