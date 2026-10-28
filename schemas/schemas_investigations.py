
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.string_normalization import blank_string_to_none
from schemas.datetime_utils import require_aware_datetime


class InvestigationUpdate(BaseModel):
    """調査編集APIの入力スキーマ。"""

    model_config = ConfigDict(extra="forbid")

    調査の名称: str | None = Field(
        default=None,
        max_length=30,
    )
    原因仮説: str | None = Field(default=None, max_length=1000, alias="原因・仮説")
    情シス側での対応: str | None = Field(default=None, max_length=1000)
    問い合わせ者側で必要な対応: str | None = Field(
        default=None,
        max_length=1000,
    )
    対応案策定予定日時: datetime | None = None
    進捗更新の次回更新予定日時: datetime | None = None

    @field_validator("調査の名称", mode="before")
    @classmethod
    def reject_blank_name(cls, value):
        value = blank_string_to_none(value)
        if value is None:
            raise ValueError("調査の名称は空文字列・空白のみ・nullにできません。")
        return value

    @field_validator(
        "原因仮説",
        "情シス側での対応",
        "問い合わせ者側で必要な対応",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value):
        return blank_string_to_none(value)

    @field_validator(
        "対応案策定予定日時",
        "進捗更新の次回更新予定日時",
    )
    @classmethod
    def require_timezone(cls, value):
        return require_aware_datetime(value)
