# app/schemas/prompt.py
from pydantic import BaseModel, ConfigDict

class PromptBase(BaseModel):
    text: str

class PromptCreate(PromptBase):
    user_id: int

class Prompt(PromptBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)
