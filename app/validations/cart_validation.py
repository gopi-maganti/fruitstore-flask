from typing import Optional

from pydantic import BaseModel, conint


class CartAddValidation(BaseModel):
    user_id: Optional[int] = -1
    fruit_id: conint(ge=1)
    quantity: conint(ge=1)


class CartUpdateValidation(BaseModel):
    quantity: conint(ge=1)
