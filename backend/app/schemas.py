from typing import List, Optional

from pydantic import BaseModel


class OrmBaseModel(BaseModel):
    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(OrmBaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = ""


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None


class SongBase(BaseModel):
    title: str
    artist: str
    album: Optional[str] = ""
    genre: Optional[str] = ""
    genre_id: Optional[int] = None
    url: Optional[str] = ""
    cover_url: Optional[str] = ""
    duration: Optional[int] = 0
    plays_count: Optional[int] = 0
    uploader_id: Optional[int] = None


class SongCreate(SongBase):
    pass


class SongUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    genre_id: Optional[int] = None
    url: Optional[str] = None
    cover_url: Optional[str] = None
    duration: Optional[int] = None
    plays_count: Optional[int] = None


class Song(OrmBaseModel):
    id: int
    title: str
    artist: str
    album: Optional[str] = ""
    genre: Optional[str] = ""
    genre_id: Optional[int] = None
    url: Optional[str] = ""
    cover_url: Optional[str] = ""
    duration: Optional[int] = 0
    plays_count: Optional[int] = 0
    uploader_id: Optional[int] = None


class SongImportError(BaseModel):
    filename: str
    error: str


class SongImportResponse(BaseModel):
    imported: List[Song] = []
    errors: List[SongImportError] = []
    created: int = 0
    failed: int = 0


class GenreBase(BaseModel):
    title: str
    description: Optional[str] = ""
    cover_url: Optional[str] = ""


class GenreCreate(GenreBase):
    pass


class GenreUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None


class GenreResponse(GenreBase, OrmBaseModel):
    id: int


class GenreWithSongs(GenreResponse):
    songs: List[Song] = []
    songs_count: int = 0

    class Config:
        orm_mode = True


class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = ""
    cover_url: Optional[str] = ""


class PlaylistCreate(PlaylistBase):
    song_ids: Optional[List[int]] = None
    is_public: Optional[bool] = True


class PlaylistListItem(PlaylistBase, OrmBaseModel):
    id: int
    is_public: Optional[bool] = True
    likes_count: int = 0
    songs: List[Song] = []


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    song_ids: Optional[List[int]] = None
    is_public: Optional[bool] = None


class Playlist(PlaylistBase, OrmBaseModel):
    id: int
    songs: List[Song] = []
    is_public: Optional[bool] = True
    owner_id: Optional[int] = None
    likes_count: int = 0


class SearchResults(BaseModel):
    songs: List[Song] = []
    playlists: List[PlaylistListItem] = []

    class Config:
        orm_mode = True
