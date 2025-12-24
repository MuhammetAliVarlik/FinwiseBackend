from pydantic import BaseModel, ConfigDict
from datetime import datetime

class StockBase(BaseModel):
    symbol: str
    company_name: str
    price: float
    currency: str
    last_updated: datetime

    # FIXED: Pydantic V2 Configuration
    model_config = ConfigDict(from_attributes=True)