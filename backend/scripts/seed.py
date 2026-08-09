"""Seed script: create tables, a demo user and a demo trip (mock itinerary)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta

import json

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import TripCreate
from app.services import ai_service


def main() -> None:
    init_db()
    db = SessionLocal()

    email = "demo@tripai.cn"
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password("demo123456"),
            nickname="演示用户",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"已创建演示账号: {email} / demo123456")
    else:
        print(f"演示账号已存在: {email}")

    if db.query(Trip).filter(Trip.user_id == user.id).count() == 0:
        req = TripCreate(
            destination="上海",
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=16),
            travelers=2,
            budget=3000,
            pace="适中",
            interests=["美食", "人文历史"],
        )
        trip_data = req.model_dump(exclude={"title"})
        trip_data["interests"] = json.dumps(trip_data["interests"], ensure_ascii=False)
        trip = Trip(
            user_id=user.id,
            title=f"上海 3天旅行计划",
            **trip_data,
            status="draft",
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)

        result = ai_service.generate_itinerary(req)
        ai_service.save_itinerary(db, trip, result, city_hint=req.destination)
        trip.status = "generated"
        db.commit()
        print(f"已创建演示行程: {trip.title}")
    else:
        print("演示行程已存在")

    db.close()


if __name__ == "__main__":
    main()
