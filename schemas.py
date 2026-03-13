from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List


# User Schemas
class UserBase(BaseModel):
    full_name: Optional[str] = None
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# NGO Schemas
class NGOBase(BaseModel):
    name: str
    description: str
    image_url: Optional[str] = None


class NGO(NGOBase):
    id: int

    class Config:
        from_attributes = True


# Lawyer Schemas
class LawyerBase(BaseModel):
    name: str
    quote: str
    image_url: Optional[str] = None


class Lawyer(LawyerBase):
    id: int

    class Config:
        from_attributes = True


# Appointment Schemas
class AppointmentBase(BaseModel):
    user_id: Optional[int] = None
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    appointment_type: str
    provider_name: Optional[str] = None
    appointment_date: date
    purpose: Optional[str] = None
    status: Optional[str] = "Pending"


class AppointmentCreate(AppointmentBase):
    pass


class Appointment(AppointmentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
