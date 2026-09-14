from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import datetime


# ─── PRODUCT SCHEMAS ─────────────────────────────────────────────
class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Product display name")
    category: str = Field(default="Other", max_length=100, description="Product category (Shoes, Apparel, Accessories, Other)")
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="Price in KSh")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    image_url: Optional[str] = Field(None, max_length=500, description="Image URL or path")
    in_stock: bool = Field(True, description="Whether product is in stock")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    description: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)
    in_stock: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ─── USER & AUTH SCHEMAS ─────────────────────────────────────────
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserBase(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, max_length=255, description="Valid email address")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72, description="Password must be between 8 and 72 characters")
    role: Optional[str] = Field("customer", pattern="^(customer|admin)$")


class UserLogin(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, max_length=255)
    password: str = Field(..., min_length=1, max_length=72)



class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None