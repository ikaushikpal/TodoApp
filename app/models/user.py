from __future__ import annotations
import uuid
from sqlalchemy import VARCHAR, Boolean, Column, DateTime, Enum as SQLAlchemyEnum, String, UniqueConstraint, text
from sqlalchemy.orm import relationship
from app.database.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(VARCHAR(36), primary_key=True, index=True, default=generate_uuid)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    country_code = Column(String(5), nullable=False)
    phone_number = Column(String(15), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum("USER", "ADMIN", name="user_roles"), server_default="USER")
    is_active = Column(Boolean, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Use string-based relationship
    todos = relationship("Todo", back_populates="owner", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("country_code", "phone_number", name="unique_phone"),
    )
