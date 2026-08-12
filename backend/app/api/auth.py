from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.models.trip import Trip, TripExpense
from app.schemas.user import (
    Token,
    UserCreate,
    UserLogin,
    UserOut,
    UserStatsOut,
    UserUpdate,
)
from app.schemas.preference import UserPreferenceOut, UserPreferenceUpdate
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(
        access_token=create_access_token(str(user.id)),
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    return Token(
        access_token=create_access_token(str(user.id)),
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/me/stats", response_model=UserStatsOut)
def me_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserStatsOut:
    trips = db.query(Trip).filter(Trip.user_id == current_user.id).all()
    trip_ids = [trip.id for trip in trips]
    total_budget = round(sum(trip.budget for trip in trips), 2)
    total_places = sum(len(trip.schedules) for trip in trips)
    total_spent = 0.0
    if trip_ids:
        total_spent = (
            db.query(func.coalesce(func.sum(TripExpense.amount), 0))
            .filter(TripExpense.trip_id.in_(trip_ids))
            .scalar()
            or 0
        )
    member_days = max((date.today() - current_user.created_at.date()).days, 0)
    return UserStatsOut(
        trip_count=len(trips),
        total_budget=total_budget,
        total_spent=round(float(total_spent), 2),
        total_places=total_places,
        member_days=member_days,
    )


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    current_user.nickname = payload.nickname.strip()
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/preferences", response_model=UserPreferenceOut)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPreferenceOut:
    from app.services import preference_service

    return preference_service.to_out(db, current_user.id)


@router.put("/me/preferences", response_model=UserPreferenceOut)
def update_preferences(
    payload: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPreferenceOut:
    from app.services import preference_service

    result = preference_service.update_lists(
        db,
        current_user.id,
        payload.favorite_places,
        payload.avoid_places,
    )
    db.commit()
    return result


@router.delete("/me/preferences", status_code=204)
def clear_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    from app.services import preference_service

    preference_service.clear(db, current_user.id)
    db.commit()
