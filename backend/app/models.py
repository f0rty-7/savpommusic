from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from .database import Base

playlist_song = Table(
    "playlist_song",
    Base.metadata,
    Column("playlist_id", Integer, ForeignKey("playlists.id"), primary_key=True),
    Column("song_id", Integer, ForeignKey("songs.id"), primary_key=True),
)


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    album = Column(String, default="")
    genre = Column(String, default="")
    url = Column(String, default="")
    duration = Column(Integer, default=0)

    playlists = relationship("Playlist", secondary=playlist_song, back_populates="songs")


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, default="")

    songs = relationship("Song", secondary=playlist_song, back_populates="playlists")
