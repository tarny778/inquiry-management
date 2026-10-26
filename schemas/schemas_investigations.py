
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class InvestigationUpdate(BaseModel):
    """調査編集APIの入力スキーマ。"""

    model_config = ConfigDict(extra="forbid")

    調査の名称: str | None = Field(
        default=None,
        max_length=30,
    )
    原因・仮説: str | None = Field(default=None, max_length=1000)
    情シス側での対応: str | None = Field(default=None, max_length=1000)
    問い合わせ者側で必要な対応: str | None = Field(
        default=None,
        max_length=1000,
    )
    対応案策定予定日時: datetime | None = None
    進捗更新の次回更新予定日時: datetime | None = None

    @field_validator("調査の名称", mode="before")
    @classmethod
    def reject_null_name(cls, value):
        if value is None:
            raise ValueError("調査の名称はnullにできません。")
        return value
