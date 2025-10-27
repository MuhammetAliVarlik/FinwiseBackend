# app/schemas/prompt.py
from pydantic import BaseModel

class PromptBase(BaseModel):
    text: str

class PromptCreate(PromptBase):
    user_id: int

class Prompt(PromptBase):
    id: int
    user_id: int
    class Config:
        orm_mode = True
