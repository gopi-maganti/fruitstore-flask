from typing import List
from pydantic import BaseModel, StrictInt, StrictStr

class OrderValidation(BaseModel):
    cart_ids: List[StrictInt]
