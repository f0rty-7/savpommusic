from sqlalchemy.orm import Session

from . import models, schemas
from sqlalchemy import func


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


def increment_song_plays(db: Session, song_id: int):
    db_song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not db_song:
        return None
    db_song.plays_count += 1
    db.commit()
    db.refresh(db_song)
    return db_song


def get_popular_songs(db: Session, limit: int = 10):
    return db.query(models.Song).order_by(models.Song.plays_count.desc()).limit(limit).all()


def get_genres(db: Session):
    return db.query(models.Genre).order_by(models.Genre.title).all()


def get_genre(db: Session, genre_id: int):
    return db.query(models.Genre).filter(models.Genre.id == genre_id).first()


def create_genre(db: Session, genre: schemas.GenreCreate):
    db_genre = models.Genre(**genre.dict())
    db.add(db_genre)
    db.commit()
    db.refresh(db_genre)
    return db_genre


def update_genre(db: Session, genre_id: int, genre_update: schemas.GenreUpdate):
    db_genre = db.query(models.Genre).filter(models.Genre.id == genre_id).first()
    if not db_genre:
        return None
    for field, value in genre_update.dict(exclude_unset=True).items():
        setattr(db_genre, field, value)
    db.commit()
    db.refresh(db_genre)
    return db_genre


def delete_genre(db: Session, genre_id: int):
    db_genre = db.query(models.Genre).filter(models.Genre.id == genre_id).first()
    if not db_genre:
        return None
    db.delete(db_genre)
    db.commit()
    return db_genre


def get_songs_by_genre(db: Session, genre: str, skip: int = 0, limit: int = 50):
    genre_record = db.query(models.Genre).filter(models.Genre.title.ilike(genre)).first()
    query = db.query(models.Song)
    if genre_record:
        query = query.filter(models.Song.genre_id == genre_record.id)
    else:
        query = query.filter(models.Song.genre.ilike(genre))
    return query.offset(skip).limit(limit).all()


def get_playlist(db: Session, playlist_id: int):
    return db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()


def get_playlists(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.Playlist).filter(models.Playlist.is_public == 1).offset(skip).limit(limit).all()


def create_playlist(db: Session, playlist: schemas.PlaylistCreate, owner_id: int | None = None):
    songs = []
    if playlist.song_ids:
        songs = db.query(models.Song).filter(models.Song.id.in_(playlist.song_ids)).all()
    db_playlist = models.Playlist(
        name=playlist.name,
        description=playlist.description,
        cover_url=playlist.cover_url or "",
        is_public=1 if (playlist.is_public is None or playlist.is_public) else 0,
        owner_id=owner_id,
    )
    db_playlist.songs = songs
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)
    return db_playlist


def add_favorite(db: Session, user_id: int, song_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    db_song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not db_song:
        return None
    if db_song not in db_user.favorites:
        db_user.favorites.append(db_song)
        db.commit()
        db.refresh(db_user)
    return db_song


def remove_favorite(db: Session, user_id: int, song_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    db_song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not db_song:
        return None
    if db_song in db_user.favorites:
        db_user.favorites.remove(db_song)
        db.commit()
        db.refresh(db_user)
    return db_song


def get_user_favorites(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Song)
        .join(models.User.favorites)
        .filter(models.User.id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


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


def get_private_playlists(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    return (
        db.query(models.Playlist)
        .filter(models.Playlist.owner_id == user_id)
        .filter(models.Playlist.is_public == 0)
        .offset(skip)
        .limit(limit)
        .all()
    )


def add_playlist_like(db: Session, user_id: int, playlist_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    db_playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not db_playlist:
        return None
    if db_playlist not in db_user.liked_playlists:
        db_user.liked_playlists.append(db_playlist)
        db.commit()
        db.refresh(db_playlist)
    return db_playlist


def remove_playlist_like(db: Session, user_id: int, playlist_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    db_playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not db_playlist:
        return None
    if db_playlist in db_user.liked_playlists:
        db_user.liked_playlists.remove(db_playlist)
        db.commit()
        db.refresh(db_playlist)
    return db_playlist


def get_popular_playlists(db: Session, limit: int = 10):
    # return playlists ordered by number of likes desc
    q = (
        db.query(models.Playlist, func.count(models.user_playlist_like.c.user_id).label("likes"))
        .outerjoin(models.user_playlist_like, models.Playlist.id == models.user_playlist_like.c.playlist_id)
        .filter(models.Playlist.is_public == 1)
        .group_by(models.Playlist.id)
        .order_by(func.count(models.user_playlist_like.c.user_id).desc())
        .limit(limit)
    )
    results = q.all()
    playlists: list[models.Playlist] = []
    for playlist, likes in results:
        setattr(playlist, "likes_count", int(likes))
        playlists.append(playlist)
    return playlists


def get_user_playlists(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    return (
        db.query(models.Playlist)
        .filter(models.Playlist.owner_id == user_id)
        .order_by(models.Playlist.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_liked_playlists(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    # return playlists liked by user; include only public playlists or those owned by the user
    q = (
        db.query(models.Playlist)
        .join(models.user_playlist_like, models.Playlist.id == models.user_playlist_like.c.playlist_id)
        .filter(models.user_playlist_like.c.user_id == user_id)
        .filter((models.Playlist.is_public == 1) | (models.Playlist.owner_id == user_id))
        .order_by(models.Playlist.id.desc())
        .offset(skip)
        .limit(limit)
    )
    results = q.all()
    # annotate likes_count
    for p in results:
        setattr(p, "likes_count", len(getattr(p, "liked_by", []) or []))
    return results


def delete_playlist(db: Session, playlist_id: int):
    db_playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not db_playlist:
        return None
    db.delete(db_playlist)
    db.commit()
    return db_playlist


# update user profile helper
def update_user_profile(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data and update_data.get("password") is not None:
        from .auth import hash_password

        db_user.password_hash = hash_password(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user
