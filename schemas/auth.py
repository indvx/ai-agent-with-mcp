from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo


class RegisterRequest(BaseModel):
    """Registration payload enforcing password complexity and matching confirmation."""
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)
    password_confirmation: str = Field(min_length=8)

    @field_validator("password")
    def password_complexity(cls, v):
        # Require uppercase, lowercase, digit, and special symbol
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("password_confirmation")
    def password_match(cls, v, info: ValidationInfo):
        # Ensure password and confirmation match exactly
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    """User credentials payload for authentication."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Payload containing the refresh token used to generate a new access token."""
    refresh_token: str


class LoginResponse(BaseModel):
    """Successful authentication response containing JWT access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenResponse(BaseModel):
    """Response returning a refreshed access token."""
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic status response returning a confirmation message."""
    message: str
