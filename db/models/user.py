from datetime import datetime

from sqlalchemy import BIGINT, Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("idx_users_telegram_id", "telegram_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BIGINT, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="ru", nullable=False)
    preferred_city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    preferred_city = relationship("City", back_populates="users")
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
    visits = relationship("VisitHistory", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("PlaceReview", back_populates="user", cascade="all, delete-orphan")
    ai_recommendations = relationship(
        "AIRecommendation", back_populates="user", cascade="all, delete-orphan"
    )
