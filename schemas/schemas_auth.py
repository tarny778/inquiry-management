from pydantic import BaseModel, Field, field_validator

from schemas.string_normalization import blank_string_to_none


class LoginRequest(BaseModel):
    職員番号: str = Field(
        min_length=1,
        max_length=20,
    )
    パスワード: str = Field(
        min_length=1,
        max_length=128,
    )

    @field_validator("職員番号", "パスワード", mode="before")
    @classmethod
    def reject_blank_credentials(cls, value):
        return blank_string_to_none(value)