from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Analysis, Facility, OccupancyLog, Upload, User
from app.services.congestion import calculate_congestion


def _demo_image(path: Path, title: str, color: tuple[int, int, int]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1200, 720), color)
    draw = ImageDraw.Draw(image)
    for row in range(3):
        for col in range(8):
            x = 120 + col * 120
            y = 260 + row * 95
            draw.rectangle((x, y, x + 74, y + 48), fill=(245, 248, 250), outline=(45, 55, 72), width=2)
    draw.text((80, 80), title, fill=(255, 255, 255))
    image.save(path)


def seed() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        if not db.scalar(select(User).where(User.email == settings.seed_admin_email)):
            db.add(User(email=settings.seed_admin_email, password_hash=hash_password(settings.seed_admin_password), role="admin"))

        facilities = [
            ("Central Library Reading Hall", "Library", "Main Campus 2F", 84, "Quiet study area with long tables and window seating.", (24, 67, 90)),
            ("Engineering Study Lounge", "Study Room", "Engineering Building B1", 48, "Flexible collaboration lounge used heavily during project weeks.", (60, 83, 64)),
            ("North Cafe Commons", "Cafe", "Student Center 1F", 72, "Cafe seating area connected to the main student concourse.", (104, 76, 57)),
        ]
        for index, (name, ftype, location, seats, description, color) in enumerate(facilities):
            facility = db.scalar(select(Facility).where(Facility.name == name))
            image_path = settings.storage_dir / "uploads" / f"seed-facility-{index + 1}.jpg"
            _demo_image(image_path, name, color)
            if not facility:
                facility = Facility(
                    name=name,
                    type=ftype,
                    location=location,
                    total_seats=seats,
                    description=description,
                    image_url=f"{settings.public_base_url}/media/uploads/{image_path.name}",
                )
                db.add(facility)
                db.flush()
            if not facility.analyses:
                for day in range(5, -1, -1):
                    for hour, people in [(9, 12 + index * 4 + day), (13, 28 + index * 8 + day), (18, 20 + index * 6 + day)]:
                        upload = Upload(facility_id=facility.id, file_path=str(image_path), original_filename=image_path.name)
                        db.add(upload)
                        db.flush()
                        congestion = calculate_congestion(people, seats)
                        timestamp = datetime.utcnow() - timedelta(days=day)
                        timestamp = timestamp.replace(hour=hour, minute=15, second=0, microsecond=0)
                        analysis = Analysis(
                            facility_id=facility.id,
                            upload_id=upload.id,
                            people_count=congestion.people_count,
                            occupied_seats=congestion.occupied_seats,
                            available_seats=congestion.available_seats,
                            occupancy_rate=congestion.occupancy_rate,
                            congestion_level=congestion.congestion_level,
                            congestion_score=congestion.congestion_score,
                            annotated_image_path=str(image_path),
                            created_at=timestamp,
                        )
                        db.add(analysis)
                        db.flush()
                        db.add(
                            OccupancyLog(
                                facility_id=facility.id,
                                analysis_id=analysis.id,
                                timestamp=timestamp,
                                people_count=analysis.people_count,
                                occupied_seats=analysis.occupied_seats,
                                available_seats=analysis.available_seats,
                                occupancy_rate=analysis.occupancy_rate,
                                congestion_score=analysis.congestion_score,
                                congestion_level=analysis.congestion_level,
                            )
                        )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()

