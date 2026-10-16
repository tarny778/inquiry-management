from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    職員番号: str = Field(
        min_length=1,
        max_length=20,
    )
    パスワード: str = Field(
        min_length=1,
        max_length=128,
    )