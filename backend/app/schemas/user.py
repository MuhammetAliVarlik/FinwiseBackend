from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserOut(UserBase):
    id: int
    
    # FIXED: Pydantic V2 Configuration
    model_config = ConfigDict(from_attributes=True)