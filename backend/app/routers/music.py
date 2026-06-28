import mimetypes
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AUDIO_DIR = BASE_DIR / "static" / "music"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def save_audio_file(file: UploadFile) -> str:
    filename = Path(file.filename).name
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    if not safe_name:
        safe_name = "track"
    target = AUDIO_DIR / f"{uuid4().hex}_{safe_name}"
    with target.open("wb") as buffer:
        buffer.write(file.file.read())
    return f"/static/music/{target.name}"


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
    title: str = Form(...),
    artist: str = Form(...),
    album: str | None = Form(None),
    genre: str | None = Form(None),
    duration: int | None = Form(0),
    url: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    file_url = url or ""
    if file:
        file_url = save_audio_file(file)

    song = schemas.SongCreate(
        title=title,
        artist=artist,
        album=album or "",
        genre=genre or "",
        url=file_url,
        duration=duration or 0,
    )
    return crud.create_song(db, song)


@router.get("/songs/{song_id}", response_model=schemas.Song)
def get_song(song_id: int, db: Session = Depends(get_db)):
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


@router.put("/songs/{song_id}", response_model=schemas.Song)
def update_song(song_id: int, song: schemas.SongUpdate, db: Session = Depends(get_db)):
    db_song = crud.update_song(db, song_id, song)
    if not db_song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Песня не найдена")
    return db_song


@router.delete("/songs/{song_id}", response_model=schemas.Song)
def delete_song(song_id: int, db: Session = Depends(get_db)):
    db_song = crud.delete_song(db, song_id)
    if not db_song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Песня не найдена")
    return db_song


@router.get("/playlists", response_model=List[schemas.Playlist])
def list_playlists(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.get_playlists(db, skip=skip, limit=limit)


@router.post("/playlists", response_model=schemas.Playlist)
def create_playlist(playlist: schemas.PlaylistCreate, db: Session = Depends(get_db)):
    return crud.create_playlist(db, playlist)


@router.get("/playlists/{playlist_id}", response_model=schemas.Playlist)
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    db_playlist = crud.get_playlist(db, playlist_id)
    if not db_playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Плейлист не найден")
    return db_playlist


@router.put("/playlists/{playlist_id}", response_model=schemas.Playlist)
def update_playlist(playlist_id: int, playlist: schemas.PlaylistUpdate, db: Session = Depends(get_db)):
    db_playlist = crud.update_playlist(db, playlist_id, playlist)
    if not db_playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Плейлист не найден")
    return db_playlist


@router.delete("/playlists/{playlist_id}", response_model=schemas.Playlist)
def delete_playlist(playlist_id: int, db: Session = Depends(get_db)):
    db_playlist = crud.delete_playlist(db, playlist_id)
    if not db_playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Плейлист не найден")
    return db_playlist
