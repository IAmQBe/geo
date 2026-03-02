from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Place(Base):
    __tablename__ = "places"
    __table_args__ = (
        Index("idx_places_city_category", "city_id", "category_id"),
        Index("idx_places_rating", "rating"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    working_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    price_range: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_url_yandex: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url_2gis: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id_yandex: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_id_2gis: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    city = relationship("City", back_populates="places")
    category = relationship("Category", back_populates="places")
    photos = relationship("PlacePhoto", back_populates="place", cascade="all, delete-orphan")
    tags = relationship("PlaceTag", back_populates="place", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="place", cascade="all, delete-orphan")
    visits = relationship("VisitHistory", back_populates="place")
    reviews = relationship("PlaceReview", back_populates="place", cascade="all, delete-orphan")
    ai_recommendations = relationship(
        "AIRecommendation", back_populates="place", cascade="all, delete-orphan"
    )
