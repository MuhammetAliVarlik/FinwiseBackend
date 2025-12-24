# app/schemas/response.py
from pydantic import BaseModel, ConfigDict

class ResponseBase(BaseModel):
    text: str

class ResponseCreate(ResponseBase):
    prompt_id: int

class Response(ResponseBase):
    id: int
    prompt_id: int
    model_config = ConfigDict(from_attributes=True)
