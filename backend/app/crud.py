from sqlalchemy.orm import Session

from . import models, schemas


def get_song(db: Session, song_id: int):
    return db.query(models.Song).filter(models.Song.id == song_id).first()


def get_songs(db: Session, skip: int = 0, limit: int = 50, search: str | None = None):
    query = db.query(models.Song)
    if search:
        search_text = f"%{search}%"
        query = query.filter(
            models.Song.title.ilike(search_text)
            | models.Song.artist.ilike(search_text)
            | models.Song.album.ilike(search_text)
        )
    return query.offset(skip).limit(limit).all()


def create_song(db: Session, song: schemas.SongCreate):
    db_song = models.Song(**song.dict())
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song


def update_song(db: Session, song_id: int, song_update: schemas.SongUpdate):
    db_song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not db_song:
        return None
    for field, value in song_update.dict(exclude_unset=True).items():
        setattr(db_song, field, value)
    db.commit()
    db.refresh(db_song)
    return db_song


def delete_song(db: Session, song_id: int):
    db_song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not db_song:
        return None
    db.delete(db_song)
    db.commit()
    return db_song


def get_playlist(db: Session, playlist_id: int):
    return db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()


def get_playlists(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.Playlist).offset(skip).limit(limit).all()


def create_playlist(db: Session, playlist: schemas.PlaylistCreate):
    songs = []
    if playlist.song_ids:
        songs = db.query(models.Song).filter(models.Song.id.in_(playlist.song_ids)).all()

    db_playlist = models.Playlist(name=playlist.name, description=playlist.description)
    db_playlist.songs = songs
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)
    return db_playlist


def update_playlist(db: Session, playlist_id: int, playlist_update: schemas.PlaylistUpdate):
    db_playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not db_playlist:
        return None

    update_data = playlist_update.dict(exclude_unset=True)
    if "song_ids" in update_data:
        song_ids = update_data.pop("song_ids")
        db_playlist.songs = []
        if song_ids is not None:
            db_playlist.songs = db.query(models.Song).filter(models.Song.id.in_(song_ids)).all()

    for field, value in update_data.items():
        setattr(db_playlist, field, value)

    db.commit()
    db.refresh(db_playlist)
    return db_playlist


def delete_playlist(db: Session, playlist_id: int):
    db_playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not db_playlist:
        return None
    db.delete(db_playlist)
    db.commit()
    return db_playlist
