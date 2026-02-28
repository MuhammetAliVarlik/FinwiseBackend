from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class PromptBase(BaseModel):
    text: str

class PromptCreate(PromptBase):
    user_id: int

class Prompt(PromptBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)

class PredictionResponse(BaseModel):
    """
    Strict Schema for the LLM's Neuro-Symbolic Output.
    """
    model_config = ConfigDict(populate_by_name=True)

    symbol: str = Field(..., description="The ticker symbol analyzed")
    
    # NEW: Specific Signal Enum Constraint
    signal: str = Field(..., description="Must be exactly BULLISH, BEARISH, or NEUTRAL")
    
    # NEW: Integer confidence 0-100 instead of Float 0-1
    confidence: int = Field(..., ge=0, le=100, description="Confidence score between 0 and 100")
    
    reasoning: str = Field(..., min_length=10, description="Chain of thought narrative explaining the prediction")
    
    # RESTORED: Critical Field for Phase 3 (Shadow Mode Analysis)
    divergence_reasoning: Optional[str] = Field(
        None, 
        description="Specific explanation if Neuro context (News) overrides Symbolic trend (Price)."
    )