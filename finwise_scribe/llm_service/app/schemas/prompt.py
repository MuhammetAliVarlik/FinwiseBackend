from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

# ==========================================
# EXISTING SCHEMAS (Database Models)
# ==========================================
class PromptBase(BaseModel):
    text: str

class PromptCreate(PromptBase):
    user_id: int

class Prompt(PromptBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# NEW SCHEMAS (Neuro-Symbolic Validation)
# ==========================================
class PredictionResponse(BaseModel):
    """
    Strict Schema for the LLM's Neuro-Symbolic Output.
    Enforces that the model outputs valid JSON with a confidence score and reasoning.
    """
    model_config = ConfigDict(populate_by_name=True)

    symbol: str = Field(..., description="The ticker symbol analyzed")
    
    # Enforce the Token Format: P_[ACTION]_V_[VOLATILITY]
    prediction: str = Field(..., pattern=r"^P_[A-Z]+_V_[A-Z]+$", description="The predicted composite token")
    
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    
    reasoning: str = Field(..., min_length=10, description="The 'Why' behind the prediction")
    
    # Critical Field for Phase 3 (Shadow Mode Analysis)
    divergence_reasoning: Optional[str] = Field(
        None, 
        description="Specific explanation if Neuro context (News) overrides Symbolic trend (Price)."
    )