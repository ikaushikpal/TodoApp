from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional, Annotated
import re

# Regex patterns
USERNAME_REGEX = r"^[a-zA-Z0-9_-]+$"
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
PHONE_NUMBER_REGEX = r"^\d{6,12}$"
COUNTRY_CODE_REGEX = r"^\+\d{1,4}$"


def strip_whitespace(v: str) -> str:
    """Strip leading and trailing whitespace from a string."""
    return v.strip() if isinstance(v, str) else v


class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=20, examples=["john_doe123"])]
    email: EmailStr = Field(examples=["johndoe@example.com"])
    first_name: Annotated[str, Field(min_length=2, max_length=100, examples=["John"])]
    last_name: Annotated[str, Field(min_length=2, max_length=100, examples=["Doe"])]
    country_code: Annotated[str, Field(min_length=2, max_length=5, examples=["+91"])]
    phone_number: Annotated[str, Field(min_length=6, max_length=12, examples=["9876543210"])]
    password: Annotated[str, Field(min_length=8, examples=["StrongP@ss1"])]

    @field_validator('username', 'first_name', 'last_name', 'country_code', 'phone_number', 'password')
    @classmethod
    def strip_and_validate(cls, v):
        v = strip_whitespace(v)
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(USERNAME_REGEX, v):
            raise ValueError('Username must contain only letters, numbers, underscores, and hyphens')
        return v

    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v):
        if not re.match(COUNTRY_CODE_REGEX, v):
            raise ValueError('Country Code must contain + and following 1-4 digits')
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        if not re.match(PHONE_NUMBER_REGEX, v):
            raise ValueError('Phone number must contain only digits and be 6-12 characters long')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError('Password must be at least 8 characters and contain uppercase, lowercase, number, and special character')
        return v


class UserUpdate(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=20, examples=["john_doe123"])]
    first_name: Annotated[str, Field(min_length=2, max_length=100, examples=["John"])]
    last_name: Annotated[str, Field(min_length=2, max_length=100, examples=["Doe"])]
    country_code: Annotated[str, Field(min_length=2, max_length=5, examples=["+91"])]
    phone_number: Annotated[str, Field(min_length=6, max_length=12, examples=["9876543210"])]

    @field_validator('username', 'first_name', 'last_name', 'country_code', 'phone_number')
    @classmethod
    def strip_and_validate(cls, v):
        v = strip_whitespace(v)
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(USERNAME_REGEX, v):
            raise ValueError('Username must contain only letters, numbers, underscores, and hyphens')
        return v

    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v):
        if not re.match(COUNTRY_CODE_REGEX, v):
            raise ValueError('Country Code must contain + and following 1-4 digits')
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        if not re.match(PHONE_NUMBER_REGEX, v):
            raise ValueError('Phone number must contain only digits and be 6-12 characters long')
        return v


class UserResponse(BaseModel):
    id: Annotated[str, Field(min_length=36, max_length=36, examples=["550e8400-e29b-41d4-a716-446655440000"])]
    username: str = Field(examples=["john_doe123"])
    first_name: str = Field(examples=["John"])
    last_name: str = Field(examples=["Doe"])
    country_code: str = Field(examples=["+91"])
    phone_number: str = Field(examples=["9876543210"])
    role: str = Field(examples=["USER"])
    is_active: bool = Field(examples=[True])
    created_at: datetime = Field(examples=["2025-03-16T10:00:00Z"])

    model_config = {"from_attributes": True}  # Replaces Config class for ORM compatibility


class PasswordUpdate(BaseModel):
    password: Annotated[str, Field(min_length=8, examples=["StrongP@ss1"])]

    @field_validator('password')
    @classmethod
    def strip_and_validate(cls, v):
        v = strip_whitespace(v)
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError('Password must be at least 8 characters and contain uppercase, lowercase, number, and special character')
        return v


class RoleUpdate(BaseModel):
    role: str = Field(examples=["ADMIN"])
    is_active: bool = Field(examples=[True])



class AuthRequest(BaseModel):
    email: EmailStr = Field(examples=["johndoe@example.com"])
    password: Annotated[str, Field(min_length=8, examples=["StrongP@ss1"])]