from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class VisitHistory(Base):
    __tablename__ = "visit_history"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="check_visit_history_rating"),
        Index("idx_visit_history_user_date", "user_id", "visited_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id"), nullable=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="visits")
    place = relationship("Place", back_populates="visits")
