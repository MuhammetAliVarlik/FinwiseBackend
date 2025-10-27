# app/schemas/response.py
from pydantic import BaseModel

class ResponseBase(BaseModel):
    text: str

class ResponseCreate(ResponseBase):
    prompt_id: int

class Response(ResponseBase):
    id: int
    prompt_id: int
    class Config:
        orm_mode = True
