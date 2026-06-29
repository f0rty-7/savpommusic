from typing import List, Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class SongBase(BaseModel):
    title: str
    artist: str
    album: Optional[str] = ""
    genre: Optional[str] = ""
    url: Optional[str] = ""
    cover_url: Optional[str] = ""
    duration: Optional[int] = 0
    plays_count: Optional[int] = 0


class SongCreate(SongBase):
    pass


class SongUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    url: Optional[str] = None
    cover_url: Optional[str] = None
    duration: Optional[int] = None
    plays_count: Optional[int] = None


class Song(SongBase):
    id: int

    class Config:
        orm_mode = True


class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = ""


class PlaylistCreate(PlaylistBase):
    song_ids: Optional[List[int]] = None


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    song_ids: Optional[List[int]] = None


class Playlist(PlaylistBase):
    id: int
    songs: List[Song] = []

    class Config:
        orm_mode = True
