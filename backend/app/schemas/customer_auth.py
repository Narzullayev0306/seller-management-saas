from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerRegisterRequest(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=30)


class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class CustomerRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class CustomerLogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class CustomerTokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CustomerMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str | None = None
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    phone: str | None = None
    address: str | None = None
    is_active: bool = True


class CustomerProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=300)
    current_password: str | None = Field(default=None, min_length=1)
    password: str | None = Field(default=None, min_length=8, max_length=128)
