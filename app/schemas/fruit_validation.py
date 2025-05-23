from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    HttpUrl,
    confloat,
    conint,
    constr,
    field_validator,
    validator,
)


class FruitValidation(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    description: Optional[constr(strip_whitespace=True)] = None
    color: constr(strip_whitespace=True, min_length=1)
    size: constr(strip_whitespace=True, min_length=1)
    image_url: HttpUrl
    has_seeds: Optional[bool] = False
    weight: confloat(gt=0)
    price: confloat(gt=0)
    total_quantity: conint(ge=0)
    available_quantity: Optional[conint(ge=0)] = None
    sell_by_date: datetime

    @field_validator("sell_by_date")
    def must_be_future(cls, v):
        if v <= datetime.utcnow():
            raise ValueError("sell_by_date must be a future date")
        return v
