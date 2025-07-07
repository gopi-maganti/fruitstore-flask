from typing import Optional

from pydantic import BaseModel, conint


class OrderValidation(BaseModel):
    cart_ids: Optional[list[conint(ge=1)]] = None
