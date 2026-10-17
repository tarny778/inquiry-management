
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# このポートフォリオで使用する問い合わせ分類
ALLOWED_INQUIRY_CATEGORIES = {
    # 要件定義で決めた分類名を追加する
    "分類A",
    "分類B",
    "分類C",
}

#型チェッククラス
class InquiryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    問い合わせ職員番号: str = Field(min_length=1, max_length=20)

    受付経路: str
    問い合わせ分類: str = Field(min_length=1, max_length=30)
    件名: str = Field(min_length=1, max_length=100)
    緊急度: int
    受付時の処理: int
    問い合わせ詳細: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )
    受信日時: datetime | None = None

    @field_validator("受付経路")
    @classmethod
    def validate_受付経路(cls, value):
        if value not in {"電話", "メール", "フォーム"}:
            raise ValueError("受付経路が不正です")
        return value

    @field_validator("緊急度")
    @classmethod
    def validate_緊急度(cls, value):
        if value not in {1, 2, 3}:
            raise ValueError("緊急度は1、2、3のいずれかを指定してください")
        return value

    @field_validator("問い合わせ分類")
    @classmethod
    def validate_問い合わせ分類(cls, value):
        if value not in ALLOWED_INQUIRY_CATEGORIES:
            raise ValueError("問い合わせ分類が不正です")
        return value

    @field_validator("受付時の処理")
    @classmethod
    def validate_受付時の処理(cls, value):
        if value not in {1, 2, 3}:
            raise ValueError("受付時の処理は1、2、3のいずれかを指定してください")
        return value

    @model_validator(mode="after")
    def validate_receipt_datetime(self):
        if (
            self.受付経路 in {"メール", "フォーム"}
            and self.受信日時 is None
        ):
            raise ValueError(
                "メール・フォームの場合、受信日時は必須です"
            )

        if (
            self.受付経路 == "電話"
            and self.受信日時 is not None
        ):
            raise ValueError(
                "電話の場合、受信日時は指定できません"
            )

        return self


class InquiryBulkAccept(BaseModel):
    model_config = ConfigDict(extra="forbid")
    問い合わせ番号一覧: list[int] = Field(min_length=1)


class InquiryBulkComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    問い合わせ番号一覧: list[int] = Field(min_length=1)


class InvestigationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    問題調査の名称や仮説: str = Field(
        min_length=1,
        max_length=30,
    )

    @field_validator("問題調査の名称や仮説")
    @classmethod
    def validate_問題調査の名称や仮説(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "問題調査の名称や仮説は空白だけでは登録できません"
            )

        return value

class BulkInvestigationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    問い合わせ番号一覧: list[int] = Field(min_length=1)

    問題調査の名称や仮説: str = Field(
        min_length=1,
        max_length=30,
    )

    @field_validator("問い合わせ番号一覧")
    @classmethod
    def validate_問い合わせ番号一覧(cls, value):
        if any(number < 1 for number in value):
            raise ValueError(
                "問い合わせ番号は1以上で指定してください"
            )

        if len(value) != len(set(value)):
            raise ValueError(
                "問い合わせ番号を重複して指定できません"
            )

        return value

    @field_validator("問題調査の名称や仮説")
    @classmethod
    def validate_問題調査の名称や仮説(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "問題調査の名称や仮説は空白だけでは登録できません"
            )

        return value

class BulkLinkInvestigation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    問い合わせ番号一覧: list[int] = Field(min_length=1)
    問題調査番号: int = Field(ge=1)

    @field_validator("問い合わせ番号一覧")
    @classmethod
    def validate_問い合わせ番号一覧(cls, value):
        if any(number < 1 for number in value):
            raise ValueError(
                "問い合わせ番号は1以上で指定してください"
            )

        if len(value) != len(set(value)):
            raise ValueError(
                "問い合わせ番号を重複して指定できません"
            )

        return value

class InquiryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    問い合わせ当時の所属: str = Field(min_length=1, max_length=30)
    受付経路: str
    問い合わせ分類: str = Field(min_length=1, max_length=30)
    件名: str = Field(min_length=1, max_length=100)
    緊急度: int
    受付時の処理: int
    問い合わせ詳細: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )
    受信日時: datetime

    @field_validator("受付経路")
    @classmethod
    def validate_受付経路(cls, value):
        if value not in {"電話", "メール", "フォーム"}:
            raise ValueError("受付経路が不正です")
        return value

    @field_validator("緊急度")
    @classmethod
    def validate_緊急度(cls, value):
        if value not in {1, 2, 3}:
            raise ValueError("緊急度は1、2、3のいずれかを指定してください")
        return value

    @field_validator("問い合わせ分類")
    @classmethod
    def validate_問い合わせ分類(cls, value):
        if value not in ALLOWED_INQUIRY_CATEGORIES:
            raise ValueError("問い合わせ分類が不正です")
        return value

    @field_validator("受付時の処理")
    @classmethod
    def validate_受付時の処理(cls, value):
        if value not in {1, 2, 3}:
            raise ValueError("受付時の処理は1、2、3のいずれかを指定してください")
        return value

    @model_validator(mode="after")
    def validate_receipt_datetime(self):
        if self.受信日時 is None:
            raise ValueError("受信日時は必須です")

        return self


class InquirySearch(BaseModel):
    """問い合わせ一覧・検索APIのクエリパラメータ。"""

    model_config = ConfigDict(extra="forbid")

    初期条件: int = Field(ge=1, le=2)

    問い合わせ番号: int | None = Field(default=None, ge=1)
    問い合わせ職員番号: str | None = Field(
        default=None, min_length=1, max_length=20
    )
    問い合わせ当時の所属: str | None = Field(
        default=None, min_length=1, max_length=30
    )

    受付経路: list[str] | None = None
    問い合わせ分類: str | None = Field(
        default=None, min_length=1, max_length=30
    )
    件名: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    緊急度: int | None = None
    受付担当者: str | None = Field(
        default=None, min_length=1, max_length=20
    )
    対応担当者: str | None = Field(
        default=None, min_length=1, max_length=20
    )
    状態: list[str] | None = None

    受信日時開始: datetime | None = None
    受信日時終了: datetime | None = None

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

    @field_validator("受付経路")
    @classmethod
    def validate_受付経路(cls, value):
        if value is not None and not set(value) <= {
            "電話", "メール", "フォーム"
        }:
            raise ValueError("受付経路の指定が不正です")
        return value

    @field_validator("問い合わせ分類")
    @classmethod
    def validate_問い合わせ分類(cls, value):
        if (
            value is not None
            and value not in ALLOWED_INQUIRY_CATEGORIES
        ):
            raise ValueError("問い合わせ分類が不正です")
        return value

    @field_validator("緊急度")
    @classmethod
    def validate_緊急度(cls, value):
        if value is not None and value not in {1, 2, 3}:
            raise ValueError("緊急度は1、2、3のいずれかを指定してください")
        return value

    @field_validator("状態")
    @classmethod
    def validate_状態(cls, value):
        allowed = {"引き受け待ち", "対応中", "対応完了"}
        if value is not None and not set(value) <= allowed:
            raise ValueError("状態の指定が不正です")
        return value

    @model_validator(mode="after")
    def validate_受信日時(self):
        if (
            self.受信日時開始 is not None
            and self.受信日時終了 is not None
            and self.受信日時開始 > self.受信日時終了
        ):
            raise ValueError(
                "受信日時開始は受信日時終了以前にしてください"
            )
        return self
