import os

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "inquiry_management",
)

from datetime import datetime

import psycopg
from fastapi import FastAPI, HTTPException, Path, Query
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

class InquiryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    編集者職員番号: str = Field(min_length=1, max_length=20)

    問い合わせ当時の所属: str = Field(min_length=1, max_length=30)
    受付経路: str
    問い合わせ分類: str = Field(min_length=1, max_length=30)
    件名: str = Field(min_length=1, max_length=100)
    緊急度: int
    受付時の処理: int
    問い合わせ詳細: str | None = Field(default=None, max_length=1000)
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
    request: InquiryAccept,
    inquiry_number: int = Path(ge=1),
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


@app.put("/api/inquiries/{inquiry_number}")
def update_inquiry_api(
    request: InquiryUpdate,
    inquiry_number: int = Path(ge=1),
):
    with psycopg.connect(dbname=DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            # 1. 現在の問い合わせ状態を取得し、更新中の競合を防ぐ
            cur.execute(
                """
                SELECT
                    "受付時の処理",
                    "受付担当者",
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                FOR UPDATE
                """,
                (inquiry_number,),
            )

            row = cur.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせが存在しません。",
                )

            (
                current_handling,
                receptionist,
                handler,
                accepted_at,
                completed_at,
            ) = row

            # 2. 現在の状態を判定し、編集権限を確認
            if completed_at is not None:
                raise HTTPException(
                    status_code=409,
                    detail="対応完了した問い合わせは編集できません。",
                )

            if accepted_at is None:
                # 未引き受け：受付担当者本人だけ編集可能
                if request.編集者職員番号 != receptionist:
                    raise HTTPException(
                        status_code=403,
                        detail="未引き受けの問い合わせは受付担当者本人だけが編集できます。",
                    )

                # 未引き受けの問い合わせは、受付時の処理が要調査であることを前提とする
                if current_handling != 2:
                    raise HTTPException(
                        status_code=409,
                        detail="問い合わせの状態と受付時の処理が一致していません。",
                    )

                # 即時解決（1）または他部署へ引き継ぎ（3）なら完了扱いにする
                if request.受付時の処理 in (1, 3):
                    new_completed_at = datetime.now()
                else:
                    new_completed_at = None

            else:
                # 対応中：現在の対応担当者本人だけ編集可能
                if request.編集者職員番号 != handler:
                    raise HTTPException(
                        status_code=403,
                        detail="対応中の問い合わせは対応担当者本人だけが編集できます。",
                    )

                # 対応中は受付時の処理を変更できない
                if request.受付時の処理 != current_handling:
                    raise HTTPException(
                        status_code=409,
                        detail="対応中の問い合わせでは受付時の処理を変更できません。",
                    )

                new_completed_at = None

            # 3. 編集可能な項目を更新
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET
                    "問い合わせ当時の所属" = %s,
                    "受付経路" = %s,
                    "問い合わせ分類" = %s,
                    "件名" = %s,
                    "緊急度" = %s,
                    "受付時の処理" = %s,
                    "問い合わせ詳細" = %s,
                    "受信日時" = %s,
                    "対応完了日時" = %s
                WHERE "問い合わせ番号" = %s
                """,
                (
                    request.問い合わせ当時の所属,
                    request.受付経路,
                    request.問い合わせ分類,
                    request.件名,
                    request.緊急度,
                    request.受付時の処理,
                    request.問い合わせ詳細,
                    request.受信日時,
                    new_completed_at,
                    inquiry_number,
                ),
            )

    return {
        "message": "問い合わせを更新しました。",
        "問い合わせ番号": inquiry_number,
    }





@app.get("/api/inquiries")
def search_inquiries_api(
    問い合わせ番号: int | None = Query(default=None, ge=1),
    件名: str | None = Query(default=None, min_length=1, max_length=100),
    問い合わせ分類: str | None = Query(default=None,  min_length=1, max_length=30),
    状態: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    # 1. 状態の指定値を確認
    allowed_statuses = {
        "引き受け待ち",
        "対応中",
        "対応完了",
    }

    if 状態 is not None and 状態 not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="状態の指定が不正です",
        )
    if 問い合わせ分類 is not None:
        if 問い合わせ分類 not in ALLOWED_INQUIRY_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail="問い合わせ分類が不正です",
            )

    # 2. 検索条件を組み立てる
    conditions = []
    params = []

    if 問い合わせ番号 is not None:
        conditions.append(
            '"問い合わせ番号" = %s'
        )
        params.append(問い合わせ番号)

    if 件名 is not None:
        conditions.append(
            '"件名" ILIKE %s'
        )
        params.append(f"%{件名}%")

    if 問い合わせ分類 is not None:
        conditions.append(
            '"問い合わせ分類" = %s'
        )
        params.append(問い合わせ分類)

    # 状態は日時カラムから判定する
    if 状態 == "引き受け待ち":
        conditions.append(
            '"引き受け日時" IS NULL '
            'AND "対応完了日時" IS NULL'
        )
    elif 状態 == "対応中":
        conditions.append(
            '"引き受け日時" IS NOT NULL '
            'AND "対応完了日時" IS NULL'
        )
    elif 状態 == "対応完了":
        conditions.append(
            '"対応完了日時" IS NOT NULL'
        )

    where_sql = ""
    if conditions:
        where_sql = "WHERE " + " AND ".join(conditions)

    # 3. 総件数と検索結果を取得する
    offset = (page - 1) * page_size

    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            # 検索条件に合致する総件数
            cur.execute(
                f'''
                SELECT COUNT(*)
                FROM "問い合わせ"
                {where_sql}
                ''',
                tuple(params),
            )
            total = cur.fetchone()[0]

            # 検索結果を受信日時の新しい順で取得
            cur.execute(
                f'''
                SELECT
                    "問い合わせ番号",
                    "件名",
                    "問い合わせ分類",
                    "受信日時",
                    CASE
                        WHEN "対応完了日時" IS NOT NULL
                            THEN '対応完了'
                        WHEN "引き受け日時" IS NOT NULL
                            THEN '対応中'
                        ELSE '引き受け待ち'
                    END AS "状態"
                FROM "問い合わせ"
                {where_sql}
                ORDER BY
                    "受信日時" DESC,
                    "問い合わせ番号" DESC
                LIMIT %s
                OFFSET %s
                ''',
                tuple(params) + (page_size, offset),
            )

            rows = cur.fetchall()

    # 4. APIレスポンスを作成する
    items = [
        {
            "問い合わせ番号": row[0],
            "件名": row[1],
            "問い合わせ分類": row[2],
            "受信日時": row[3],
            "状態": row[4],
        }
        for row in rows
    ]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@app.get("/api/inquiries/{inquiry_number}")
def get_inquiry_api(
    inquiry_number: int = Path(ge=1),
):
    print(f"詳細取得APIのDB: {DATABASE_NAME}")

    # 1. 指定された問い合わせを取得する
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT
                    "問い合わせ番号",
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
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (inquiry_number,),
            )

            row = cur.fetchone()

    # 2. 該当する問い合わせが存在しない場合
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="問い合わせが見つかりません",
        )

    # 3. 問い合わせ状態を判定する
    if row[14] is not None:
        状態 = "対応完了"
    elif row[13] is not None:
        状態 = "対応中"
    else:
        状態 = "引き受け待ち"

    # 4. APIレスポンスを作成する
    return {
        "問い合わせ番号": row[0],
        "問い合わせ職員番号": row[1],
        "問い合わせ当時の所属": row[2],
        "受付経路": row[3],
        "問い合わせ分類": row[4],
        "件名": row[5],
        "緊急度": row[6],
        "受付時の処理": row[7],
        "問い合わせ詳細": row[8],
        "受付担当者": row[9],
        "対応担当者": row[10],
        "受信日時": row[11],
        "登録日時": row[12],
        "引き受け日時": row[13],
        "対応完了日時": row[14],
        "状態": 状態,
    }



