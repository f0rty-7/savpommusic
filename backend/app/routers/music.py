import mimetypes
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db

router = APIRouter()


@router.post("/auth/register", response_model=schemas.TokenResponse)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь уже существует")

    user = models.User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        auth_token=create_access_token(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": user.auth_token, "token_type": "bearer"}


@router.post("/auth/login", response_model=schemas.TokenResponse)
def login_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")

    user.auth_token = create_access_token()
    db.commit()
    db.refresh(user)
    return {"access_token": user.auth_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user



@router.put("/auth/me", response_model=schemas.UserResponse)
async def update_me(
    username: str | None = Form(None),
    password: str | None = Form(None),
    avatar: UploadFile | None = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    avatar_url_value = current_user.avatar_url or ""
    if avatar:
        avatar_url_value = save_cover_file(avatar)

    update = schemas.UserUpdate(username=username, password=password, avatar_url=avatar_url_value)
    user = crud.update_user_profile(db, current_user.id, update)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AUDIO_DIR = BASE_DIR / "static" / "music"
COVER_DIR = BASE_DIR / "static" / "covers"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
COVER_DIR.mkdir(parents=True, exist_ok=True)


def save_audio_file(file: UploadFile) -> str:
    filename = Path(file.filename).name
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    if not safe_name:
        safe_name = "track"
    target = AUDIO_DIR / f"{uuid4().hex}_{safe_name}"
    with target.open("wb") as buffer:
        buffer.write(file.file.read())
    return f"/static/music/{target.name}"


def save_cover_file(file: UploadFile) -> str:
    filename = Path(file.filename).name
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    if not safe_name:
        safe_name = "cover"
    target = COVER_DIR / f"{uuid4().hex}_{safe_name}"
    with target.open("wb") as buffer:
        buffer.write(file.file.read())
    return f"/static/covers/{target.name}"


def parse_song_ids(song_ids: str | List[str] | None) -> list[int] | None:
    if song_ids is None:
        return None
    if isinstance(song_ids, list):
        values: list[str] = []
        for item in song_ids:
            if item is None:
                continue
            if isinstance(item, int):
                values.append(str(item))
            else:
                item_text = str(item).strip()
                if not item_text:
                    continue
                values.extend(part.strip() for part in item_text.split(",") if part.strip())
        return [int(value) for value in values]
    if isinstance(song_ids, str):
        cleaned = song_ids.strip()
        if not cleaned:
            return None
        return [int(part.strip()) for part in cleaned.split(",") if part.strip()]
    return None


@router.get("/songs", response_model=List[schemas.Song])
def list_songs(
    search: str | None = Query(None, description="Искать по названию, артисту или альбому"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return crud.get_songs(db, skip=skip, limit=limit, search=search)


@router.post("/songs", response_model=schemas.Song)
async def add_song(
    current_user: models.User = Depends(get_current_user),
    title: str = Form(...),
    artist: str = Form(...),
    album: str | None = Form(None),
    genre: str | None = Form(None),
    genre_id: int | None = Form(None),
    duration: int | None = Form(0),
    url: str | None = Form(None),
    cover_url: str | None = Form(None),
    file: UploadFile | None = File(None),
    cover: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    file_url = url or ""
    if file:
        file_url = save_audio_file(file)

    cover_url_value = cover_url or ""
    if cover:
        cover_url_value = save_cover_file(cover)

    genre_value = genre or ""
    if genre_id:
        db_genre = crud.get_genre(db, genre_id)
        if db_genre:
            genre_value = db_genre.title

    song = schemas.SongCreate(
        title=title,
        artist=artist,
        album=album or "",
        genre=genre_value,
        genre_id=genre_id,
        url=file_url,
        cover_url=cover_url_value,
        duration=duration or 0,
    )
    return crud.create_song(db, song)


@router.get("/songs/popular", response_model=List[schemas.Song])
def popular_songs(limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_popular_songs(db, limit=limit)


@router.get("/genres", response_model=List[schemas.GenreResponse])
def list_genres(db: Session = Depends(get_db)):
    return crud.get_genres(db)


@router.post("/genres", response_model=schemas.GenreResponse)
def create_genre(
    current_user: models.User = Depends(get_current_user),
    title: str = Form(...),
    description: str | None = Form(None),
    cover_url: str | None = Form(None),
    cover: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    cover_url_value = cover_url or ""
    if cover:
        cover_url_value = save_cover_file(cover)

    genre = schemas.GenreCreate(
        title=title,
        description=description or "",
        cover_url=cover_url_value,
    )
    return crud.create_genre(db, genre)


@router.get("/genres/{genre_id}", response_model=schemas.GenreWithSongs)
def get_genre(
    genre_id: int,
    db: Session = Depends(get_db),
):
    db_genre = crud.get_genre(db, genre_id)
    if not db_genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Жанр не найден")
    setattr(db_genre, "songs_count", len(db_genre.songs or []))
    return db_genre


@router.put("/genres/{genre_id}", response_model=schemas.GenreResponse)
def update_genre(
    genre_id: int,
    current_user: models.User = Depends(get_current_user),
    title: str | None = Form(None),
    description: str | None = Form(None),
    cover_url: str | None = Form(None),
    cover: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    db_genre = crud.get_genre(db, genre_id)
    if not db_genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Жанр не найден")

    cover_url_value = cover_url if cover_url is not None else db_genre.cover_url
    if cover:
        cover_url_value = save_cover_file(cover)

    genre_update = schemas.GenreUpdate(
        title=title,
        description=description,
        cover_url=cover_url_value,
    )
    return crud.update_genre(db, genre_id, genre_update)


@router.delete("/genres/{genre_id}", response_model=schemas.GenreResponse)
def delete_genre(
    genre_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_genre = crud.delete_genre(db, genre_id)
    if not db_genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Жанр не найден")
    return db_genre


@router.get("/songs/genre/{genre_name}", response_model=List[schemas.Song])
def songs_by_genre(
    genre_name: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return crud.get_songs_by_genre(db, genre_name, skip=skip, limit=limit)


@router.get("/songs/{song_id}", response_model=schemas.Song)
def get_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_song = crud.get_song(db, song_id)
    if not db_song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Песня не найдена")
    return db_song


@router.get("/songs/{song_id}/stream")
def stream_song(song_id: int, db: Session = Depends(get_db)):
    db_song = crud.get_song(db, song_id)
    if not db_song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Песня не найдена")

    media_url = (db_song.url or "").strip()
    if not media_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="У песни нет аудиофайла")

    if media_url.startswith(("http://", "https://")):
        return RedirectResponse(url=media_url)

    candidate = (BASE_DIR / media_url.lstrip("/")).resolve()
    try:
        candidate.relative_to(BASE_DIR)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недопустимый путь к аудио") from exc

    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Аудиофайл не найден")

    media_type, _ = mimetypes.guess_type(str(candidate))
    return FileResponse(candidate, media_type=media_type or "audio/mpeg")


@router.post("/songs/{song_id}/play", response_model=schemas.Song)
def play_song(song_id: int, db: Session = Depends(get_db)):
    db_song = crud.increment_song_plays(db, song_id)
    if not db_song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Песня не найдена")
    return db_song


@router.put("/songs/{song_id}", response_model=schemas.Song)
def update_song(
    song_id: int,
    song: schemas.SongUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_song = crud.update_song(db, song_id, song)
    if not db_song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Песня не найдена")
    return db_song


@router.delete("/songs/{song_id}", response_model=schemas.Song)
def delete_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_song = crud.delete_song(db, song_id)
    if not db_song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Песня не найдена")
    return db_song


@router.get("/playlists", response_model=List[schemas.PlaylistListItem])
def list_playlists(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return crud.get_playlists(db, skip=skip, limit=limit)


@router.post("/playlists", response_model=schemas.Playlist)
def create_playlist(
    current_user: models.User = Depends(get_current_user),
    name: str = Form(...),
    description: str | None = Form(None),
    cover_url: str | None = Form(None),
    song_ids: str | List[str] | None = Form(None),
    cover: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    cover_url_value = cover_url or ""
    if cover:
        cover_url_value = save_cover_file(cover)

    playlist_data = schemas.PlaylistCreate(
        name=name,
        description=description or "",
        cover_url=cover_url_value,
        song_ids=parse_song_ids(song_ids),
    )
    return crud.create_playlist(db, playlist_data)


@router.get("/playlists/{playlist_id}", response_model=schemas.Playlist)
def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
):
    db_playlist = crud.get_playlist(db, playlist_id)
    if not db_playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Плейлист не найден")
    return db_playlist


@router.put("/playlists/{playlist_id}", response_model=schemas.Playlist)
def update_playlist(
    playlist_id: int,
    current_user: models.User = Depends(get_current_user),
    name: str | None = Form(None),
    description: str | None = Form(None),
    cover_url: str | None = Form(None),
    song_ids: str | List[str] | None = Form(None),
    cover: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    db_playlist = crud.get_playlist(db, playlist_id)
    if not db_playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Плейлист не найден")

    cover_url_value = cover_url if cover_url is not None else db_playlist.cover_url
    if cover:
        cover_url_value = save_cover_file(cover)

    playlist_update = schemas.PlaylistUpdate(
        name=name,
        description=description,
        cover_url=cover_url_value,
        song_ids=parse_song_ids(song_ids),
    )
    db_playlist = crud.update_playlist(db, playlist_id, playlist_update)
    if not db_playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Плейлист не найден")
    return db_playlist


@router.delete("/playlists/{playlist_id}", response_model=schemas.Playlist)
def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_playlist = crud.delete_playlist(db, playlist_id)
    if not db_playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Плейлист не найден")
    return db_playlist
