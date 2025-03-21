from __future__ import annotations
from sqlalchemy import VARCHAR, Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint, text
from sqlalchemy.orm import relationship
from app.database.database import Base

class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    priority = Column(Integer, nullable=False)
    complete = Column(Boolean, server_default=text("0"))
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    finished_at = Column(DateTime(timezone=True), nullable=True)

    owner_id = Column(VARCHAR(36), ForeignKey("users.id"), nullable=False)
    # Use string-based relationship
    owner = relationship("User", back_populates="todos")

    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 5", name="priority_range"),
    )