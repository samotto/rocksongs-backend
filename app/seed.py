import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import get_settings
from app.database import SessionLocal
from app.models import LookupList, LookupListItem, Song, User


settings = get_settings()


def load_seed_data() -> list[dict]:
    seed_path = Path(__file__).resolve().parent.parent / "data" / "seed_songs.json"
    with seed_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def ensure_admin_user(db: Session) -> User:
    admin_email = settings.seed_admin_email.strip().lower()
    admin = db.query(User).filter(func.lower(User.email) == admin_email).first()
    if admin:
        # If the seed address was registered before initial seeding, promote it
        # and establish the seed password once. Later password changes survive
        # normal application restarts because an existing admin is left alone.
        needs_promotion = admin.role != "Admin"
        if needs_promotion:
            admin.role = "Admin"
        if needs_promotion or settings.seed_admin_force_password_reset:
            admin.password_hash = hash_password(settings.seed_admin_password)
        if admin.last_logon_time is None:
            admin.last_logon_time = datetime.now(timezone.utc)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    admin = User(
        name="Sam Otto" if admin_email == "sam@overturegroup.com" else admin_email.split("@", 1)[0],
        email=admin_email,
        role="Admin",
        password_hash=hash_password(settings.seed_admin_password),
        google_id=None,
        create_time=datetime.now(timezone.utc),
        last_logon_time=datetime.now(timezone.utc),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def seed_songs(db: Session, admin_user: User) -> int:
    songs = load_seed_data()
    inserted_count = 0

    for item in songs:
        exists = (
            db.query(Song)
            .filter(Song.artist == item["artist"], Song.song == item["song"])
            .first()
        )
        if exists:
            continue

        now = datetime.now(timezone.utc)
        song = Song(
            artist=item["artist"],
            album=item.get("album"),
            song=item["song"],
            overplayed=item.get("overplayed", False),
            create_time=now,
            update_time=now,
            create_id=admin_user.id,
            update_id=admin_user.id,
        )
        db.add(song)
        inserted_count += 1

    db.commit()
    return inserted_count


def seed_role_lookup_list(db: Session, admin_user: User) -> int:
    lookup_list = db.query(LookupList).filter(func.lower(LookupList.list_name) == "role").first()
    now = datetime.now(timezone.utc)
    if not lookup_list:
        lookup_list = LookupList(
            list_name="Role",
            description="Application user roles",
            sort_mode="Alphabetical",
            default_item_value=None,
            active=True,
            create_time=now,
            update_time=now,
            create_id=admin_user.id,
            update_id=admin_user.id,
        )
        db.add(lookup_list)
        db.flush()
    else:
        lookup_list.sort_mode = "Alphabetical"
        lookup_list.update_time = now
        lookup_list.update_id = admin_user.id
        db.add(lookup_list)

    inserted_count = 0
    for value in ("Admin", "Basic", "Pending"):
        existing = (
            db.query(LookupListItem)
            .filter(
                LookupListItem.list_id == lookup_list.id,
                LookupListItem.list_item_value == value,
            )
            .first()
        )
        if existing:
            existing.list_item_text = value
            existing.sequence = 0
            existing.active = True
            existing.update_time = now
            existing.update_id = admin_user.id
            db.add(existing)
        else:
            db.add(LookupListItem(
                list_id=lookup_list.id,
                list_item_value=value,
                list_item_text=value,
                sequence=0,
                active=True,
                create_time=now,
                update_time=now,
                create_id=admin_user.id,
                update_id=admin_user.id,
            ))
            inserted_count += 1
    db.flush()
    lookup_list.default_item_value = "Basic"
    lookup_list.update_time = now
    lookup_list.update_id = admin_user.id
    db.add(lookup_list)
    db.commit()
    return inserted_count


def run_seed() -> None:
    db = SessionLocal()
    try:
        admin_user = ensure_admin_user(db)
        inserted_roles = seed_role_lookup_list(db, admin_user)
        inserted = seed_songs(db, admin_user)
        print(f"Seed complete. Inserted {inserted_roles} role values and {inserted} songs.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
