from datetime import datetime

import main
import psycopg
from fastapi import APIRouter, HTTPException, Path, Query

from schemas.inquiries import (
    ALLOWED_INQUIRY_CATEGORIES,
    InquiryCreate,
    InquiryBulkAccept,
    InquiryBulkComplete,
    InvestigationCreate,
    BulkInvestigationCreate,
    BulkLinkInvestigation,
    InquiryUpdate,
)

DATABASE_NAME = main.DATABASE_NAME

router = APIRouter()


#新規作成api
@router.post("/api/inquiries")
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
    # ログイン中の職員を受付担当者とする
    current_user = main.get_current_user()
    受付担当者職員番号 = current_user.職員番号

    
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

#個別引き受け
@router.post("/api/inquiries/{inquiry_number}/accept")
def accept_inquiry_api(
    inquiry_number: int = Path(ge=1),
):
    # ログイン中の職員を受付担当者とする
    current_user = main.get_current_user()
    操作者職員番号 = current_user.職員番号
    # 1. 操作者の存在確認と所属確認
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "職員番号", "所属"
                FROM "職員"
                WHERE "職員番号" = %s
                ''',
                (操作者職員番号,),
            )
            staff = cur.fetchone()

    if staff is None:
        raise HTTPException(
            status_code=400,
            detail="指定された操作者は登録されていません",
        )

    if staff[1] != "情報システム課":
        raise HTTPException(
            status_code=400,
            detail="操作者が情シス職員として登録されていません",
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
                    操作者職員番号,
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
        "対応担当者": 操作者職員番号,
        "引き受け日時": inquiry[1],
    }

#一括引き受け
@router.post("/api/inquiries/bulk-accept")
def accept_inquiries_bulk_api(request: InquiryBulkAccept):
    # ログイン中の職員を対応担当者とする
    current_user = main.get_current_user()
    操作者職員番号 = current_user.職員番号

    # 1. 操作者の存在確認と所属確認
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "職員番号", "所属"
                FROM "職員"
                WHERE "職員番号" = %s
                ''',
                (操作者職員番号,),
            )
            staff = cur.fetchone()

            if staff is None:
                raise HTTPException(
                    status_code=400,
                    detail="指定された操作者は登録されていません",
                )

            if staff[1] != "情報システム課":
                raise HTTPException(
                    status_code=400,
                    detail="操作者が情シス職員として登録されていません",
                )

            # 2. 問い合わせ番号の重複を確認
            inquiry_numbers = request.問い合わせ番号一覧

            if len(inquiry_numbers) != len(set(inquiry_numbers)):
                raise HTTPException(
                    status_code=400,
                    detail="問い合わせ番号が重複しています",
                )

            # 3. 全件をロックして状態を確認
            cur.execute(
                '''
                SELECT
                    "問い合わせ番号",
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                ORDER BY "問い合わせ番号"
                FOR UPDATE
                ''',
                (inquiry_numbers,),
            )
            inquiries = cur.fetchall()

            # 4. 指定された番号がすべて存在するか確認
            found_numbers = {row[0] for row in inquiries}
            missing_numbers = [
                number
                for number in inquiry_numbers
                if number not in found_numbers
            ]

            if missing_numbers:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": "指定された問い合わせが存在しません",
                        "問い合わせ番号一覧": missing_numbers,
                    },
                )

            # 5. 全件が引き受け可能か確認
            invalid_numbers = [
                row[0]
                for row in inquiries
                if (
                    row[1] is not None
                    or row[2] is not None
                    or row[3] is not None
                )
            ]

            if invalid_numbers:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "引き受けできない状態の問い合わせが含まれています",
                        "問い合わせ番号一覧": invalid_numbers,
                    },
                )

            # 6. 全件を更新
            accepted_at = datetime.now()

            cur.execute(
                '''
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = %s,
                    "引き受け日時" = %s
                WHERE "問い合わせ番号" = ANY(%s)
                RETURNING "問い合わせ番号"
                ''',
                (
                    操作者職員番号,
                    accepted_at,
                    inquiry_numbers,
                ),
            )

            updated_numbers = sorted(
                row[0] for row in cur.fetchall()
            )

    return {
        "message": "問い合わせを一括で引き受けました",
        "対応担当者": 操作者職員番号,
        "問い合わせ番号一覧": updated_numbers,
        "引き受け日時": accepted_at,
    }

#個別完了
@router.post("/api/inquiries/{inquiry_number}/complete")
def complete_inquiry_api(
    inquiry_number: int = Path(ge=1),
):
    # 1. 操作者を取得（認証導入前の仮実装）
    current_user = main.get_current_user()

    with psycopg.connect(dbname=DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            # 2. 問い合わせを取得し、同時更新を防ぐ
            cur.execute(
                """
                SELECT
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

            handler, accepted_at, completed_at = row

            # 3. 対応中の問い合わせか確認
            if accepted_at is None:
                raise HTTPException(
                    status_code=409,
                    detail="未引き受けの問い合わせは対応完了できません。",
                )

            if completed_at is not None:
                raise HTTPException(
                    status_code=409,
                    detail="すでに対応完了した問い合わせです。",
                )

            # 4. 対応担当者本人か確認
            if current_user.職員番号 != handler:
                raise HTTPException(
                    status_code=403,
                    detail="対応担当者本人だけが対応完了できます。",
                )

            # 5. 未完了の調査が残っていないか確認
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM "問い合わせ問題調査"
                    WHERE "問い合わせ番号" = %s
                      AND "問い合わせ問題調査状態" IN (1, 3)
                )
                """,
                (inquiry_number,),
            )
            has_unfinished_problem = cur.fetchone()[0]

            if has_unfinished_problem:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "調査中またはリアクション待ちの"
                        "問い合わせ問題が残っているため、"
                        "対応完了できません。"
                    ),
                )

            # 6. 対応完了日時を記録
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET "対応完了日時" = NOW()
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )

    return {
        "message": "問い合わせを対応完了しました。",
        "問い合わせ番号": inquiry_number,
    }

#一括完了
@router.post("/api/inquiries/bulk-complete")
def complete_inquiries_bulk_api(
    request: InquiryBulkComplete,
):
    # 1. 操作者を取得
    current_user = main.get_current_user()

    inquiry_numbers = request.問い合わせ番号一覧

    # 2. 問い合わせ番号の重複を確認
    if len(inquiry_numbers) != len(set(inquiry_numbers)):
        raise HTTPException(
            status_code=400,
            detail="問い合わせ番号が重複しています。",
        )

    with psycopg.connect(dbname=DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            # 3. 全件をロックして状態を確認
            cur.execute(
                """
                SELECT
                    "問い合わせ番号",
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                ORDER BY "問い合わせ番号"
                FOR UPDATE
                """,
                (inquiry_numbers,),
            )
            inquiries = cur.fetchall()

            # 4. 指定された番号がすべて存在するか確認
            found_numbers = {row[0] for row in inquiries}
            missing_numbers = [
                number
                for number in inquiry_numbers
                if number not in found_numbers
            ]

            if missing_numbers:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": "指定された問い合わせが存在しません。",
                        "問い合わせ番号一覧": missing_numbers,
                    },
                )

            # 5. 全件が対応中か確認
            invalid_state_numbers = [
                row[0]
                for row in inquiries
                if row[2] is None or row[3] is not None
            ]

            if invalid_state_numbers:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "対応中ではない問い合わせが含まれています。",
                        "問い合わせ番号一覧": invalid_state_numbers,
                    },
                )

            # 6. 全件の対応担当者が操作者本人か確認
            unauthorized_numbers = [
                row[0]
                for row in inquiries
                if row[1] != current_user.職員番号
            ]

            if unauthorized_numbers:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": "対応担当者本人ではない問い合わせが含まれています。",
                        "問い合わせ番号一覧": unauthorized_numbers,
                    },
                )

            # 7. 未完了の調査が残っていないか全件確認
            cur.execute(
                """
                SELECT DISTINCT "問い合わせ番号"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ番号" = ANY(%s)
                  AND "問い合わせ問題調査状態" IN (1, 3)
                ORDER BY "問い合わせ番号"
                """,
                (inquiry_numbers,),
            )
            unfinished_numbers = [
                row[0] for row in cur.fetchall()
            ]

            if unfinished_numbers:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": (
                            "調査中またはリアクション待ちの"
                            "問い合わせ問題が残っています。"
                        ),
                        "問い合わせ番号一覧": unfinished_numbers,
                    },
                )

            # 8. 全件の検証に成功した場合のみ更新
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET "対応完了日時" = NOW()
                WHERE "問い合わせ番号" = ANY(%s)
                RETURNING "問い合わせ番号"
                """,
                (inquiry_numbers,),
            )

            updated_numbers = sorted(
                row[0] for row in cur.fetchall()
            )

    return {
        "message": "問い合わせを一括で対応完了しました。",
        "問い合わせ番号一覧": updated_numbers,
    }

#個別再開
@router.post("/api/inquiries/{inquiry_number}/reopen")
def reopen_inquiry_api(
    inquiry_number: int = Path(ge=1),
):
    # 1. 操作者を取得
    current_user = main.get_current_user()

    with psycopg.connect(dbname=DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            # 2. 問い合わせをロックして現在の状態を取得
            cur.execute(
                """
                SELECT
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                FOR UPDATE
                """,
                (inquiry_number,),
            )
            inquiry = cur.fetchone()

            # 3. 問い合わせの存在確認
            if inquiry is None:
                raise HTTPException(
                    status_code=404,
                    detail="問い合わせが存在しません。",
                )

            handler, accepted_at, completed_at = inquiry

            # 4. 対応完了済みか確認
            if completed_at is None:
                raise HTTPException(
                    status_code=409,
                    detail="対応完了していない問い合わせは再開できません。",
                )

            # 5. 対応担当者本人か確認
            if handler != current_user.職員番号:
                raise HTTPException(
                    status_code=403,
                    detail="対応担当者本人だけが問い合わせを再開できます。",
                )

            # 6. 再開可能期間を確認
            # 対応完了日時から7日後ちょうども期限切れとする
            cur.execute(
                """
                SELECT
                    clock_timestamp()
                    >= %s + INTERVAL '7 days'
                """,
                (completed_at,),
            )
            reopen_expired = cur.fetchone()[0]

            if reopen_expired:
                raise HTTPException(
                    status_code=409,
                    detail="再開可能期間（対応完了から7日以内）を過ぎています。",
                )

            # 7. 対応完了日時だけをNULLに戻す
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET "対応完了日時" = NULL
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )

    return {
        "message": "問い合わせを再開しました。",
        "問い合わせ番号": inquiry_number,
    }

#新規調査へ個別関連付け
@router.post("/api/inquiries/{inquiry_number}/investigations")
def create_investigation_api(
    request: InvestigationCreate,
    inquiry_number: int = Path(ge=1),
):
    # 1. 操作者を取得
    current_user = main.get_current_user()

    # 2. 問い合わせの状態と対応担当者を確認
    with psycopg.connect(dbname=DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                FOR UPDATE
                """,
                (inquiry_number,),
            )

            inquiry = cur.fetchone()

            # 3. 問い合わせの存在確認
            if inquiry is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせが存在しません。",
                )

            handler, accepted_at, completed_at = inquiry

            # 4. 対応中であることを確認
            if accepted_at is None or completed_at is not None:
                raise HTTPException(
                    status_code=409,
                    detail="対応中の問い合わせだけ問題調査を作成できます。",
                )

            # 5. 対応担当者本人であることを確認
            if handler != current_user.職員番号:
                raise HTTPException(
                    status_code=403,
                    detail="対応担当者本人だけが問題調査を作成できます。",
                )

            # 6. 問題調査を新規作成
            cur.execute(
                """
                INSERT INTO "問題調査" (
                    "問題調査の名称や仮説"
                )
                VALUES (%s)
                RETURNING "問題調査番号"
                """,
                (request.問題調査の名称や仮説,),
            )

            investigation_number = cur.fetchone()[0]

            # 7. 問い合わせと問題調査を関連付ける
            cur.execute(
                """
                INSERT INTO "問い合わせ問題調査" (
                    "問題調査番号",
                    "問い合わせ番号"
                )
                VALUES (%s, %s)
                RETURNING "問い合わせ問題調査番号"
                """,
                (
                    investigation_number,
                    inquiry_number,
                ),
            )

            inquiry_investigation_number = cur.fetchone()[0]

    # 8. 作成結果を返す
    return {
        "message": "問題調査を作成し、問い合わせに関連付けました。",
        "問い合わせ番号": inquiry_number,
        "問題調査番号": investigation_number,
        "問い合わせ問題調査番号": inquiry_investigation_number,
        "問題調査の名称や仮説": request.問題調査の名称や仮説,
    }

# 既存調査へ個別関連付け
@router.post(
    "/api/inquiries/{inquiry_number}/investigations/{investigation_number}"
)
def link_existing_investigation_api(
    inquiry_number: int = Path(ge=1),
    investigation_number: int = Path(ge=1),
):
    current_user = main.get_current_user()

    with psycopg.connect(dbname=DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            # 1. 問題調査を先にロックし、状態を確認する
            cur.execute(
                """
                SELECT "問題調査状態"
                FROM "問題調査"
                WHERE "問題調査番号" = %s
                FOR UPDATE
                """,
                (investigation_number,),
            )
            investigation = cur.fetchone()

            if investigation is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問題調査が存在しません。",
                )

            if investigation[0] != 1:
                raise HTTPException(
                    status_code=409,
                    detail="調査中の問題調査だけ関連付けできます。",
                )

            # 2. 対象の問い合わせを取得し、ロックする
            cur.execute(
                """
                SELECT
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                FOR UPDATE
                """,
                (inquiry_number,),
            )
            inquiry = cur.fetchone()

            if inquiry is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせが存在しません。",
                )

            handler, accepted_at, completed_at = inquiry

            if accepted_at is None or completed_at is not None:
                raise HTTPException(
                    status_code=409,
                    detail="対応中の問い合わせだけ関連付けできます。",
                )

            if handler != current_user.職員番号:
                raise HTTPException(
                    status_code=403,
                    detail="対応担当者本人だけが関連付けできます。",
                )

            # 3. 既存の関連問い合わせを取得する
            cur.execute(
                """
                SELECT i."問い合わせ番号", i."対応担当者"
                FROM "問い合わせ問題調査" AS r
                JOIN "問い合わせ" AS i
                  ON i."問い合わせ番号" = r."問い合わせ番号"
                WHERE r."問題調査番号" = %s
                ORDER BY i."問い合わせ番号"
                FOR UPDATE OF i
                """,
                (investigation_number,),
            )
            related_inquiries = cur.fetchall()

            if not related_inquiries:
                raise HTTPException(
                    status_code=409,
                    detail="既存の関連付けがない問題調査には追加できません。",
                )

            # 4. 既存の関連問い合わせの対応担当者が
            #    全員、操作者と一致することを確認する
            for related_number, related_handler in related_inquiries:
                if related_handler != current_user.職員番号:
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            "既存の関連問い合わせの対応担当者と"
                            "一致しないため、関連付けできません。"
                        ),
                    )

            # 5. 同じ組み合わせの二重登録を防ぐ
            cur.execute(
                """
                SELECT 1
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ番号" = %s
                  AND "問題調査番号" = %s
                """,
                (inquiry_number, investigation_number),
            )

            if cur.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="この問い合わせには、すでに関連付けられています。",
                )

            # 6. 関連レコードだけを追加する
            cur.execute(
                """
                INSERT INTO "問い合わせ問題調査" (
                    "問題調査番号",
                    "問い合わせ番号"
                )
                VALUES (%s, %s)
                RETURNING "問い合わせ問題調査番号"
                """,
                (investigation_number, inquiry_number),
            )

            relation_number = cur.fetchone()[0]

    return {
        "message": "既存の問題調査を問い合わせに関連付けました。",
        "問い合わせ番号": inquiry_number,
        "問題調査番号": investigation_number,
        "問い合わせ問題調査番号": relation_number,
    }


#新規調査へ一括関連付け
@router.post("/api/inquiries/bulk-investigations")
def bulk_create_investigation_api(
    request: BulkInvestigationCreate,
):
    current_user = main.get_current_user()
    inquiry_numbers = request.問い合わせ番号一覧

    with psycopg.connect(dbname=DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            # 1. 対象の問い合わせを取得してロックする
            cur.execute(
                """
                SELECT
                    "問い合わせ番号",
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                ORDER BY "問い合わせ番号"
                FOR UPDATE
                """,
                (inquiry_numbers,),
            )

            inquiries = cur.fetchall()

            # 2. 指定された問い合わせがすべて存在するか確認
            if len(inquiries) != len(inquiry_numbers):
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせの中に存在しないものがあります。",
                )

            # 3. すべての問い合わせの状態を確認
            for (
                inquiry_number,
                handler,
                accepted_at,
                completed_at,
            ) in inquiries:
                if accepted_at is None or completed_at is not None:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"問い合わせ番号 {inquiry_number} は"
                            "対応中ではありません。"
                        ),
                    )

            # 4. すべての問い合わせの対応担当者を確認
            for inquiry_number, handler, _, _ in inquiries:
                if handler != current_user.職員番号:
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            f"問い合わせ番号 {inquiry_number} は"
                            "対応担当者本人ではありません。"
                        ),
                    )

            # 5. 新しい問題調査を1件作成
            cur.execute(
                """
                INSERT INTO "問題調査" (
                    "問題調査の名称や仮説"
                )
                VALUES (%s)
                RETURNING "問題調査番号"
                """,
                (request.問題調査の名称や仮説,),
            )

            investigation_number = cur.fetchone()[0]

            # 6. すべての問い合わせに関連レコードを作成
            relations = []

            for inquiry_number in inquiry_numbers:
                cur.execute(
                    """
                    INSERT INTO "問い合わせ問題調査" (
                        "問題調査番号",
                        "問い合わせ番号"
                    )
                    VALUES (%s, %s)
                    RETURNING "問い合わせ問題調査番号"
                    """,
                    (investigation_number, inquiry_number),
                )

                relation_number = cur.fetchone()[0]

                relations.append(
                    {
                        "問い合わせ番号": inquiry_number,
                        "問い合わせ問題調査番号": relation_number,
                    }
                )

    return {
        "message": (
            "問題調査を作成し、複数の問い合わせに関連付けました。"
        ),
        "問題調査番号": investigation_number,
        "問題調査の名称や仮説": request.問題調査の名称や仮説,
        "関連付け件数": len(relations),
        "関連付け一覧": relations,
    }

#既存調査へ一括関連付け
@router.post("/api/inquiries/bulk-link-investigation")
def bulk_link_existing_investigation_api(
    request: BulkLinkInvestigation,
):
    current_user = main.get_current_user()
    inquiry_numbers = request.問い合わせ番号一覧
    investigation_number = request.問題調査番号

    with psycopg.connect(dbname=DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            # 1. 既存の問題調査をロックして状態を確認
            cur.execute(
                """
                SELECT "問題調査状態"
                FROM "問題調査"
                WHERE "問題調査番号" = %s
                FOR UPDATE
                """,
                (investigation_number,),
            )
            investigation = cur.fetchone()

            if investigation is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問題調査が存在しません。",
                )

            if investigation[0] != 1:
                raise HTTPException(
                    status_code=409,
                    detail="調査中の問題調査だけ関連付けできます。",
                )

            # 2. 対象の問い合わせを番号順にロック
            cur.execute(
                """
                SELECT
                    "問い合わせ番号",
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                ORDER BY "問い合わせ番号"
                FOR UPDATE
                """,
                (inquiry_numbers,),
            )
            inquiries = cur.fetchall()

            # 3. すべての問い合わせが存在するか確認
            if len(inquiries) != len(inquiry_numbers):
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせの中に存在しないものがあります。",
                )

            # 4. すべて対応中か確認
            for (
                inquiry_number,
                handler,
                accepted_at,
                completed_at,
            ) in inquiries:
                if accepted_at is None or completed_at is not None:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"問い合わせ番号 {inquiry_number} は"
                            "対応中ではありません。"
                        ),
                    )

            # 5. すべて自分が対応担当者か確認
            for inquiry_number, handler, _, _ in inquiries:
                if handler != current_user.職員番号:
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            f"問い合わせ番号 {inquiry_number} は"
                            "対応担当者本人ではありません。"
                        ),
                    )
            # 6. 既存の関連付けがあるか確認し、
            #    既存の問い合わせも自分が担当しているか確認
            cur.execute(
                """
                SELECT
                    i."問い合わせ番号",
                    i."対応担当者"
                FROM "問い合わせ問題調査" AS r
                JOIN "問い合わせ" AS i
                  ON i."問い合わせ番号" = r."問い合わせ番号"
                WHERE r."問題調査番号" = %s
                ORDER BY i."問い合わせ番号"
                FOR UPDATE OF i
                """,
                (investigation_number,),
            )
            existing_inquiries = cur.fetchall()

            if not existing_inquiries:
                raise HTTPException(
                    status_code=409,
                    detail="既存の関連付けがない問題調査には追加できません。",
                )

            for existing_number, existing_handler in existing_inquiries:
                if existing_handler != current_user.職員番号:
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            f"既存の問い合わせ番号 {existing_number} は"
                            "別の対応担当者が担当しているため、"
                            "関連付けできません。"
                        ),
                    )

            # 7. すでに関連付けられている問い合わせがないか確認
            cur.execute(
                """
                SELECT "問い合わせ番号"
                FROM "問い合わせ問題調査"
                WHERE "問題調査番号" = %s
                  AND "問い合わせ番号" = ANY(%s)
                """,
                (investigation_number, inquiry_numbers),
            )
            existing_numbers = {
                row[0] for row in cur.fetchall()
            }

            if existing_numbers:
                duplicated_number = min(existing_numbers)
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"問い合わせ番号 {duplicated_number} は"
                        "すでにこの問題調査に関連付けられています。"
                    ),
                )

            # 8. 全件の確認が済んでから関連レコードを追加
            relations = []

            for inquiry_number in inquiry_numbers:
                cur.execute(
                    """
                    INSERT INTO "問い合わせ問題調査" (
                        "問題調査番号",
                        "問い合わせ番号"
                    )
                    VALUES (%s, %s)
                    RETURNING "問い合わせ問題調査番号"
                    """,
                    (investigation_number, inquiry_number),
                )

                relation_number = cur.fetchone()[0]

                relations.append(
                    {
                        "問い合わせ番号": inquiry_number,
                        "問い合わせ問題調査番号": relation_number,
                    }
                )

    return {
        "message": "既存の問題調査を複数の問い合わせに関連付けました。",
        "問題調査番号": investigation_number,
        "関連付け件数": len(relations),
        "関連付け一覧": relations,
    }

#上書き保存
@router.put("/api/inquiries/{inquiry_number}")
def update_inquiry_api(
    request: InquiryUpdate,
    inquiry_number: int = Path(ge=1),
):
    current_user = main.get_current_user()
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
                if current_user.職員番号 != receptionist:
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
                if current_user.職員番号 != handler:
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




#検索により一覧取得
@router.get("/api/inquiries")
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

#個別の詳細取得
@router.get("/api/inquiries/{inquiry_number}")
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