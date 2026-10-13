import os

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "inquiry_management",
)

from datetime import datetime

import psycopg
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
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

app = FastAPI()


class InquiryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    問い合わせ職員番号: str = Field(min_length=1, max_length=20)
    受付担当者: str = Field(min_length=1, max_length=20)

    受付経路: str
    問い合わせ分類: str = Field(min_length=1, max_length=30)
    件名: str = Field(min_length=1, max_length=100)
    緊急度: int
    受付時の処理: int
    問い合わせ詳細: str | None = Field(default=None, max_length=1000)
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


class InquiryAccept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    対応担当者: str = Field(min_length=1, max_length=20)



@app.post("/api/inquiries")
def create_inquiry_api(request: InquiryCreate):

    # 1. 問い合わせ職員の存在確認と所属の取得
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "職員番号", "氏名", "所属"
                FROM "職員"
                WHERE "職員番号" = %s
                ''',
                (request.問い合わせ職員番号,)
            )

            staff = cur.fetchone()

    if staff is None:
        raise HTTPException(
            status_code=400,
            detail="指定された問い合わせ職員番号は登録されていません"
        )

    # 2. 問い合わせ当時の所属を取得
    問い合わせ当時の所属 = staff[2]

    if (
        問い合わせ当時の所属 is None
        or len(問い合わせ当時の所属) > 30
    ):
        raise HTTPException(
            status_code=400,
            detail="問い合わせ職員の所属が不正です"
        )

    # 3. 受付担当者の取得
    # 開発中はPOSTリクエストから取得する
    受付担当者職員番号 = request.受付担当者

    
    # 4. 受付担当者の存在確認と所属確認
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "職員番号", "所属"
                FROM "職員"
                WHERE "職員番号" = %s
                ''',
                (受付担当者職員番号,)
            )
            staff = cur.fetchone()

    if staff is None:
        raise HTTPException(
            status_code=400,
            detail="指定された受付担当者は登録されていません"
        )

    受付担当者所属 = staff[1]

    if 受付担当者所属 != "情報システム課":
        raise HTTPException(
            status_code=400,
            detail="受付担当者が情シス職員として登録されていません"
        )


    # 5. 日時を決定
    now = datetime.now()

    # 受信日時
    if request.受付経路 == "電話":
        received_at = now
    else:
        received_at = request.受信日時

    # 登録日時
    registered_at = now

    # 対応完了日時
    if request.受付時の処理 in (1, 3):
        completed_at = now
    else:
        completed_at = None

    # 引き受け日時：受付時点では未引き受け
    accepted_at = None

    # 問い合わせを登録
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "問い合わせ" (
                    "問い合わせ職員番号",
                    "問い合わせ当時の所属",
                    "受付経路",
                    "問い合わせ分類",
                    "件名",
                    "緊急度",
                    "受付時の処理",
                    "問い合わせ詳細",
                    "受付担当者",
                    "対応担当者",
                    "受信日時",
                    "登録日時",
                    "引き受け日時",
                    "対応完了日時"
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING "問い合わせ番号"
                ''',
                (
                    request.問い合わせ職員番号,
                    問い合わせ当時の所属,
                    request.受付経路,
                    request.問い合わせ分類,
                    request.件名,
                    request.緊急度,
                    request.受付時の処理,
                    request.問い合わせ詳細,
                    受付担当者職員番号,
                    None,  # 対応担当者：引き受け時に設定
                    received_at,
                    registered_at,
                    accepted_at,
                    completed_at
                )
            )

            inquiry_number = cur.fetchone()[0]

    return {
        "message": "問い合わせを登録しました",
        "問い合わせ番号": inquiry_number
    }


@app.post("/api/inquiries/{inquiry_number}/accept")
def accept_inquiry_api(
    inquiry_number: int,
    request: InquiryAccept,
):
    # 1. 対応担当者の存在確認と所属確認
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "職員番号", "所属"
                FROM "職員"
                WHERE "職員番号" = %s
                ''',
                (request.対応担当者,),
            )
            staff = cur.fetchone()

    if staff is None:
        raise HTTPException(
            status_code=400,
            detail="指定された対応担当者は登録されていません",
        )

    if staff[1] != "情報システム課":
        raise HTTPException(
            status_code=400,
            detail="対応担当者が情シス職員として登録されていません",
        )

    # 2. 引き受け日時を決定
    accepted_at = datetime.now()

    # 3. 未引き受け・未完了の場合だけ更新
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = %s,
                    "引き受け日時" = %s
                WHERE
                    "問い合わせ番号" = %s
                    AND "引き受け日時" IS NULL
                    AND "対応完了日時" IS NULL
                RETURNING "問い合わせ番号", "引き受け日時"
                ''',
                (
                    request.対応担当者,
                    accepted_at,
                    inquiry_number,
                ),
            )
            inquiry = cur.fetchone()

            # 4. 更新できなかった理由を確認
            if inquiry is None:
                cur.execute(
                    '''
                    SELECT 1
                    FROM "問い合わせ"
                    WHERE "問い合わせ番号" = %s
                    ''',
                    (inquiry_number,),
                )
                exists = cur.fetchone()

                if exists is None:
                    raise HTTPException(
                        status_code=404,
                        detail="指定された問い合わせは存在しません",
                    )

                raise HTTPException(
                    status_code=409,
                    detail="この問い合わせは引き受けできない状態です",
                )

    return {
        "message": "問い合わせを引き受けました",
        "問い合わせ番号": inquiry[0],
        "対応担当者": request.対応担当者,
        "引き受け日時": inquiry[1],
    }




@app.get("/api/staff/{staff_number}")
def get_staff(staff_number: str):
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "職員番号", "氏名", "所属"
                FROM "職員"
                WHERE "職員番号" = %s
                ''',
                (staff_number,)
            )

            staff = cur.fetchone()

    if staff is None:
        return {"message": "職員が見つかりません"}

    return {
        "職員番号": staff[0],
        "氏名": staff[1],
        "所属": staff[2],
    }









@app.get("/", response_class=HTMLResponse)
def inquiry_form():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>問い合わせ登録</title>
    </head>
    <body>
        <h1>問い合わせ登録</h1>

        <form action="/inquiries" method="post">
            <p>
                件名<br>
                <input type="text" name="title">
            </p>

            <p>
                会社名<br>
                <input type="text" name="company">
            </p>

            <p>
                内容<br>
                <textarea name="content"></textarea>
            </p>

            <button type="submit">登録する</button>
        </form>
    </body>
    </html>
    """


@app.post("/inquiries", response_class=HTMLResponse)
def create_inquiry(
    title: str = Form(...),
    company: str = Form(...),
    content: str = Form(...),
):
    return f"""
    <h1>問い合わせを登録しました</h1>

    <p><strong>件名：</strong>{title}</p>
    <p><strong>会社名：</strong>{company}</p>
    <p><strong>内容：</strong>{content}</p>

    <a href="/">戻る</a>
    """