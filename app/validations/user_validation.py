from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserValidation(BaseModel):
    name: str
    email: EmailStr
    phone_number: str = Field(..., description="Must be a 10-digit phone number")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError(
                "Improper phone number length. Please enter exactly 10 digits."
            )
        return v