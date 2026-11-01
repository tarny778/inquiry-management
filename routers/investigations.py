from fastapi import Depends,APIRouter, Query, Path, HTTPException
import psycopg
from psycopg import sql
from schemas.schemas_investigations import InvestigationUpdate
import main
from config import settings
from schemas.string_normalization import blank_string_to_none
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# 調査の検索・一覧取得
@router.get("/api/investigations")
def search_investigations_api(
    調査番号: int | None = Query(default=None, ge=1),
    調査の名称: str | None = None,
    調査状態: int | None = Query(default=None, ge=1, le=3),
    問い合わせ職員番号: str | None = None,
    問い合わせ番号: int | None = Query(default=None, ge=1),
    問い合わせ状態: str | None = Query(
        default=None,
        pattern="^(引き受け待ち|対応中|対応完了)$",
    ),
    対応担当者職員番号: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: main.CurrentUser = Depends(main.get_current_user),
):
    # 空白のみの文字列検索条件は、指定なし（None）として扱う。
    調査の名称 = blank_string_to_none(調査の名称)
    問い合わせ職員番号 = blank_string_to_none(問い合わせ職員番号)
    対応担当者職員番号 = blank_string_to_none(対応担当者職員番号)

    # ログイン中の職員を取得
    操作者職員番号 = current_user.職員番号

    # 検索条件を組み立てる
    conditions = []
    params = []

    if 調査番号 is not None:
        conditions.append('q."調査番号" = %s')
        params.append(調査番号)

    if 調査の名称 and 調査の名称.strip():
        conditions.append(
            'q."調査の名称" LIKE %s'
        )
        params.append(f"%{調査の名称.strip()}%")

    if 調査状態 is not None:
        conditions.append('q."調査状態" = %s')
        params.append(調査状態)

    # 問い合わせ番号で検索
    if 問い合わせ番号 is not None:
        conditions.append(
            '''
            EXISTS (
                SELECT 1
                FROM "問い合わせ調査" ik
                JOIN "問い合わせ" i
                    ON i."問い合わせ番号" = ik."問い合わせ番号"
                WHERE ik."調査番号" = q."調査番号"
                AND i."問い合わせ番号" = %s
            )
            '''
        )
        params.append(問い合わせ番号)
    
    # 問い合わせ者の職員番号・問い合わせ状態で検索
    if 問い合わせ職員番号 or 問い合わせ状態 is not None:
        inquiry_conditions = [
            'ik."調査番号" = q."調査番号"',
            'i."問い合わせ番号" = ik."問い合わせ番号"',
        ]
        inquiry_params = []

        if 問い合わせ職員番号:
            inquiry_conditions.append(
                'i."問い合わせ職員番号" = %s'
            )
            inquiry_params.append(問い合わせ職員番号)

        if 問い合わせ状態 == "対応中":
            inquiry_conditions.append(
                '''
                i."引き受け日時" IS NOT NULL
                AND i."対応完了日時" IS NULL
                '''
            )
        elif 問い合わせ状態 == "対応完了":
            inquiry_conditions.append(
                'i."対応完了日時" IS NOT NULL'
            )
        elif 問い合わせ状態 == "引き受け待ち":
            inquiry_conditions.append(
                '''
                i."引き受け日時" IS NULL
                AND i."対応完了日時" IS NULL
                '''
            )

        conditions.append(
            '''
            EXISTS (
                SELECT 1
                FROM "問い合わせ調査" ik
                JOIN "問い合わせ" i
                    ON i."問い合わせ番号" = ik."問い合わせ番号"
                WHERE
            '''
            + " AND ".join(inquiry_conditions)
            + ")"
        )
        params.extend(inquiry_params)

    # 対応担当者の職員番号で検索
    if 対応担当者職員番号:
        conditions.append(
            '''
            EXISTS (
                SELECT 1
                FROM "問い合わせ調査" ik
                JOIN "問い合わせ" i
                    ON i."問い合わせ番号" = ik."問い合わせ番号"
                WHERE ik."調査番号" = q."調査番号"
                  AND i."対応担当者" = %s
            )
            '''
        )
        params.append(対応担当者職員番号)

    # WHERE句を組み立てる
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # ページ番号から取得開始位置を計算
    offset = (page - 1) * page_size

    # データベースから総件数と一覧データを取得
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:

            # 検索結果の総件数を取得
            cur.execute(
                f'''
                SELECT COUNT(*)
                FROM "調査" q
                {where_clause}
                ''',
                params,
            )
            total = cur.fetchone()[0]

            # 調査の一覧を取得
            cur.execute(
                f'''
                SELECT
                    q."調査番号",
                    q."調査の名称",
                    q."調査状態",

                    -- 関連する問い合わせの対応担当者職員番号
                    (
                        SELECT s."職員番号"
                        FROM "問い合わせ調査" ik
                        JOIN "問い合わせ" i
                            ON i."問い合わせ番号" = ik."問い合わせ番号"
                        JOIN "職員" s
                            ON s."職員番号" = i."対応担当者"
                        WHERE ik."調査番号" = q."調査番号"
                        ORDER BY i."問い合わせ番号"
                        LIMIT 1
                    ) AS "対応担当者職員番号",

                    -- 関連する問い合わせの件数
                    (
                        SELECT COUNT(DISTINCT ik."問い合わせ番号")
                        FROM "問い合わせ調査" ik
                        WHERE ik."調査番号" = q."調査番号"
                    ) AS "関連問い合わせ件数",

                    -- 操作者自身の問い合わせが含まれるか
                    EXISTS (
                        SELECT 1
                        FROM "問い合わせ調査" ik
                        JOIN "問い合わせ" i
                            ON i."問い合わせ番号" = ik."問い合わせ番号"
                        WHERE ik."調査番号" = q."調査番号"
                          AND i."問い合わせ職員番号" = %s
                    ) AS "自分の問い合わせを含む"

                FROM "調査" q
                {where_clause}
                ORDER BY
                    q."調査開始日時" DESC,
                    q."調査番号" DESC
                LIMIT %s OFFSET %s
                ''',
                [操作者職員番号] + params + [page_size, offset],
            )

            rows = cur.fetchall()

    # 各行をレスポンス用の辞書に変換
    columns = [
        "調査番号",
        "調査の名称",
        "調査状態",
        "対応担当者職員番号",
        "関連問い合わせ件数",
        "自分の問い合わせを含む",
    ]

    items = [
        dict(zip(columns, row))
        for row in rows
    ]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


# 調査の詳細取得
@router.get("/api/investigations/{investigation_id}")
def get_investigation_api(
    investigation_id: int = Path(ge=1),
    current_user: main.CurrentUser = Depends(main.get_current_user),
):
    # ログイン中の職員を取得
    操作者職員番号 = current_user.職員番号

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:

            # 1. 調査そのものの詳細を取得
            cur.execute(
                '''
                SELECT
                    "調査番号",
                    "調査の名称",
                    "原因・仮説",
                    "情シス側での対応",
                    "問い合わせ者側で必要な対応",
                    "調査状態",
                    "調査開始日時",
                    "対応案策定予定日時",
                    "進捗更新の次回更新予定日時",
                    "リアクション要求日時",
                    "調査断念日時",
                    "最新移行先の調査番号"
                FROM "調査"
                WHERE "調査番号" = %s
                ''',
                (investigation_id,),
            )

            row = cur.fetchone()

            # 調査が存在しない場合
            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された調査が見つかりません。",
                )

            columns = [
                "調査番号",
                "調査の名称",
                "原因・仮説",
                "情シス側での対応",
                "問い合わせ者側で必要な対応",
                "調査状態",
                "調査開始日時",
                "対応案策定予定日時",
                "進捗更新の次回更新予定日時",
                "リアクション要求日時",
                "調査断念日時",
                "最新移行先の調査番号",
            ]

            investigation = dict(zip(columns, row))

            # 2. 関連する問い合わせ調査を取得
            cur.execute(
                '''
                SELECT
                    ik."問い合わせ調査番号",
                    ik."問い合わせ番号",
                    requester."氏名" AS "問い合わせ者氏名",
                    handler."氏名" AS "対応担当者氏名",
                    ik."問い合わせ調査状態",
                    ik."調査開始日時",
                    ik."断念日時",
                    ik."リアクション被要求日時",
                    ik."リアクション日時",
                    ik."リアクション内容",
                    ik."NGでの移行先調査番号",
                    i."問い合わせ職員番号",
                    i."対応担当者"
                FROM "問い合わせ調査" ik
                JOIN "問い合わせ" i
                    ON i."問い合わせ番号" = ik."問い合わせ番号"
                JOIN "職員" requester
                    ON requester."職員番号" = i."問い合わせ職員番号"
                LEFT JOIN "職員" handler
                    ON handler."職員番号" = i."対応担当者"
                WHERE ik."調査番号" = %s
                ORDER BY ik."問い合わせ調査番号"
                ''',
                (investigation_id,),
            )

            rows = cur.fetchall()

    columns = [
        "問い合わせ調査番号",
        "問い合わせ番号",
        "問い合わせ者氏名",
        "対応担当者氏名",
        "問い合わせ調査状態",
        "調査開始日時",
        "断念日時",
        "リアクション被要求日時",
        "リアクション日時",
        "リアクション内容",
        "NGでの移行先調査番号",
        "問い合わせ職員番号",
        "対応担当者職員番号",
    ]

    related_inquiries = [
        dict(zip(columns, row))
        for row in rows
    ]

    # 操作者自身の問い合わせが含まれるか
    investigation["自分の問い合わせを含む"] = any(
        item["問い合わせ職員番号"] == 操作者職員番号
        for item in related_inquiries
    )

    return {
        **investigation,
        "関連する問い合わせ調査": related_inquiries,
    }


# 調査の編集
@router.patch("/api/investigations/{investigation_id}")
def update_investigation_api(
    body: InvestigationUpdate,
    investigation_id: int = Path(ge=1),
    current_user: main.CurrentUser = Depends(main.get_current_user),
):
    # ログイン中の職員を取得
    操作者職員番号 = current_user.職員番号

    # スキーマで許可された、実際に送信された項目だけを取得
    update_data = body.model_dump(exclude_unset=True, by_alias=True)

    # 空のPATCHリクエストは拒否
    if not update_data:
        raise HTTPException(
            status_code=422,
            detail="更新する項目を1つ以上指定してください。",
        )

    # 更新可能なDBカラムを限定する
    column_mapping = {
        "調査の名称": "調査の名称",
        "原因・仮説": "原因・仮説",
        "情シス側での対応": "情シス側での対応",
        "問い合わせ者側で必要な対応": "問い合わせ者側で必要な対応",
        "対応案策定予定日時": "対応案策定予定日時",
        "進捗更新の次回更新予定日時": "進捗更新の次回更新予定日時",
    }

    # 更新対象カラムと値を組み立てる
    set_clause = sql.SQL(", ").join(
        sql.SQL("{} = %s").format(sql.Identifier(column_mapping[field]))
        for field in update_data
    )
    values = list(update_data.values())

    # 管理項目を含む、更新後の調査を返す
    returning_columns = [
        "調査番号",
        "調査の名称",
        "原因・仮説",
        "情シス側での対応",
        "問い合わせ者側で必要な対応",
        "調査状態",
        "調査開始日時",
        "対応案策定予定日時",
        "進捗更新の次回更新予定日時",
        "リアクション要求日時",
        "調査断念日時",
        "最新移行先の調査番号",
    ]

    returning_clause = sql.SQL(", ").join(
        sql.Identifier(column) for column in returning_columns
    )

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # 対象行をロックし、存在・権限・状態を確認
            cur.execute(
                '''
                SELECT
                    q."調査状態",
                    EXISTS (
                        SELECT 1
                        FROM "問い合わせ調査" ik
                        WHERE ik."調査番号" = q."調査番号"
                    )
                    AND NOT EXISTS (
                        SELECT 1
                        FROM "問い合わせ調査" ik
                        JOIN "問い合わせ" i
                            ON i."問い合わせ番号" = ik."問い合わせ番号"
                        WHERE ik."調査番号" = q."調査番号"
                          AND i."対応担当者" IS DISTINCT FROM %s
                    ) AS 編集権限あり
                FROM "調査" q
                WHERE q."調査番号" = %s
                FOR UPDATE OF q
                ''',
                (操作者職員番号, investigation_id),
            )

            row = cur.fetchone()

            # 調査が存在しない場合
            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された調査が見つかりません。",
                )

            調査状態 = row[0]
            編集権限あり = row[1]

            # 関連する問い合わせの対応担当者でなければ拒否
            if not 編集権限あり:
                raise HTTPException(
                    status_code=403,
                    detail="関連する問い合わせの対応担当者本人だけが編集できます。",
                )

            # 調査中の調査だけ編集可能
            if 調査状態 != 1:
                raise HTTPException(
                    status_code=409,
                    detail="調査中の調査だけ編集できます。",
                )


            # 更新を実行
            cur.execute(
                sql.SQL(
                    '''
                    UPDATE "調査"
                    SET {}
                    WHERE "調査番号" = %s
                    RETURNING {}
                    '''
                ).format(set_clause, returning_clause),
                values + [investigation_id],
            )

            updated_row = cur.fetchone()

            updated_investigation = dict(
                zip(returning_columns, updated_row)
            )

    return updated_investigation



# 調査の断念
@router.post("/api/investigations/{investigation_id}/abandon")
def abandon_investigation_api(
    investigation_id: int = Path(ge=1),
    current_user: main.CurrentUser = Depends(main.get_current_user),
):
    # ログイン中の職員を取得
    操作者職員番号 = current_user.職員番号

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # 対象の調査をロックし、存在・権限・状態を確認
            cur.execute(
                '''
                SELECT
                    q."調査状態",
                    EXISTS (
                        SELECT 1
                        FROM "問い合わせ調査" ik
                        WHERE ik."調査番号" = q."調査番号"
                    )
                    AND NOT EXISTS (
                        SELECT 1
                        FROM "問い合わせ調査" ik
                        JOIN "問い合わせ" i
                            ON i."問い合わせ番号" = ik."問い合わせ番号"
                        WHERE ik."調査番号" = q."調査番号"
                          AND i."対応担当者" IS DISTINCT FROM %s
                    ) AS 編集権限あり
                FROM "調査" q
                WHERE q."調査番号" = %s
                FOR UPDATE OF q
                ''',
                (操作者職員番号, investigation_id),
            )

            row = cur.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された調査が見つかりません。",
                )

            調査状態 = row[0]
            編集権限あり = row[1]

            if not 編集権限あり:
                raise HTTPException(
                    status_code=403,
                    detail="関連する問い合わせの対応担当者本人だけが断念できます。",
                )

            if 調査状態 != 1:
                raise HTTPException(
                    status_code=409,
                    detail="調査中の調査だけ断念できます。",
                )

            # 関連する問い合わせ調査に状態1・2以外が存在しないか検証
            cur.execute(
                '''
                SELECT NOT EXISTS (
                    SELECT 1
                    FROM "問い合わせ調査"
                    WHERE "調査番号" = %s
                    AND "問い合わせ調査状態" NOT IN (1, 2)
                )
                ''',
                (investigation_id,),
            )

            関連レコード整合性あり = cur.fetchone()[0]

            if not 関連レコード整合性あり:
                logger.error(
                    "調査の断念処理でデータ整合性エラー: "
                    "調査番号=%s",
                    investigation_id,
                )
                raise HTTPException(
                    status_code=500,
                    detail="データ整合性エラーが発生しました。",
                )


            # 関連する問い合わせ調査のうち、
            # 状態1（調査中）のレコードをすべて状態2（個別断念）にする
            cur.execute(
                '''
                UPDATE "問い合わせ調査"
                SET "問い合わせ調査状態" = 2
                WHERE "調査番号" = %s
                  AND "問い合わせ調査状態" = 1
                ''',
                (investigation_id,),
            )

            # 調査本体を状態3（調査断念）にし、断念日時を記録
            cur.execute(
                '''
                UPDATE "調査"
                SET
                    "調査状態" = 3,
                    "調査断念日時" = CURRENT_TIMESTAMP
                WHERE "調査番号" = %s
                RETURNING
                    "調査番号",
                    "調査の名称",
                    "調査状態",
                    "調査断念日時"
                ''',
                (investigation_id,),
            )

            updated_row = cur.fetchone()

            result = {
                "調査番号": updated_row[0],
                "調査の名称": updated_row[1],
                "調査状態": updated_row[2],
                "調査断念日時": updated_row[3],
            }

    # ここまで正常に到達した場合だけ、トランザクションが確定する
    return result


# 調査のリアクション要求
@router.post(
    "/api/investigations/{investigation_id}/request-reaction"
)
def request_reaction_investigation_api(
    investigation_id: int = Path(ge=1),
    current_user: main.CurrentUser = Depends(main.get_current_user),
):
    # ログイン中の職員を取得
    操作者職員番号 = current_user.職員番号

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # 対象の調査をロックし、存在・権限・状態を確認
            cur.execute(
                '''
                SELECT
                    q."調査状態",
                    EXISTS (
                        SELECT 1
                        FROM "問い合わせ調査" ik
                        WHERE ik."調査番号" = q."調査番号"
                    )
                    AND NOT EXISTS (
                        SELECT 1
                        FROM "問い合わせ調査" ik
                        JOIN "問い合わせ" i
                            ON i."問い合わせ番号" = ik."問い合わせ番号"
                        WHERE ik."調査番号" = q."調査番号"
                          AND i."対応担当者" IS DISTINCT FROM %s
                    ) AS 編集権限あり
                FROM "調査" q
                WHERE q."調査番号" = %s
                FOR UPDATE OF q
                ''',
                (操作者職員番号, investigation_id),
            )

            row = cur.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された調査が見つかりません。",
                )

            調査状態 = row[0]
            編集権限あり = row[1]

            if not 編集権限あり:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "関連する問い合わせの対応担当者本人だけが"
                        "リアクション要求できます。"
                    ),
                )

            if 調査状態 != 1:
                raise HTTPException(
                    status_code=409,
                    detail="調査中の調査だけリアクション要求できます。",
                )

            # 要求前の整合性チェック：
            # 関連する問い合わせ調査に状態1・2以外が存在しないか検証
            cur.execute(
                '''
                SELECT NOT EXISTS (
                    SELECT 1
                    FROM "問い合わせ調査"
                    WHERE "調査番号" = %s
                    AND "問い合わせ調査状態" NOT IN (1, 2)
                )
                ''',
                (investigation_id,),
            )

            関連レコード整合性あり = cur.fetchone()[0]

            if not 関連レコード整合性あり:
                logger.error(
                    "リアクション依頼処理でデータ整合性エラー: "
                    "調査番号=%s",
                    investigation_id,
                )
                raise HTTPException(
                    status_code=500,
                    detail="データ整合性エラーが発生しました。",
                )


            # 関連レコードの状態1を状態3（リアクション待ち）に変更
            # 状態2（個別断念）はそのまま維持する
            cur.execute(
                '''
                UPDATE "問い合わせ調査"
                SET "問い合わせ調査状態" = 3
                WHERE "調査番号" = %s
                  AND "問い合わせ調査状態" = 1
                ''',
                (investigation_id,),
            )

            # 調査本体を状態2にし、リクエスト要求日時を記録
            cur.execute(
                '''
                UPDATE "調査"
                SET
                    "調査状態" = 2,
                    "リアクション要求日時" = CURRENT_TIMESTAMP
                WHERE "調査番号" = %s
                RETURNING
                    "調査番号",
                    "調査の名称",
                    "調査状態",
                    "リアクション要求日時"
                ''',
                (investigation_id,),
            )

            updated_row = cur.fetchone()

            # 更新後の整合性チェック：
            # 関連レコードは状態2（個別断念）または
            # 状態3（リアクション待ち）でなければならない
            cur.execute(
                '''
                SELECT NOT EXISTS (
                    SELECT 1
                    FROM "問い合わせ調査"
                    WHERE "調査番号" = %s
                      AND "問い合わせ調査状態" NOT IN (2, 3)
                )
                ''',
                (investigation_id,),
            )

            更新後の整合性あり = cur.fetchone()[0]

            if not 更新後の整合性あり:
                logger.error(
                    "調査の断念処理でデータ整合性エラー: "
                    "調査番号=%s",
                    investigation_id,
                ),                
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "サーバー内部でエラーが発生しました。"
                        "時間をおいて再度お試しください。"
                        "解決しない場合は、システム管理者にお問い合わせください。"
                    ),
                )

            result = {
                "調査番号": updated_row[0],
                "調査の名称": updated_row[1],
                "調査状態": updated_row[2],
                "リアクション要求日時": updated_row[3],
            }

    # すべて成功した場合にのみトランザクションが確定する
    return result



# 問い合わせ調査の個別断念
@router.post(
    "/api/investigations/relations/{relation_id}/abandon"
)
def abandon_inquiry_problem_investigation_api(
    relation_id: int = Path(ge=1),
    current_user: main.CurrentUser = Depends(main.get_current_user),
):
    """問い合わせ調査を個別断念にする。"""

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # 1. 親の調査番号を取得する
            # この段階ではロックせず、親を特定するために使う
            cur.execute(
                """
                SELECT "調査番号"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )
            row = cur.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせ調査が見つかりません。",
                )

            investigation_id = row[0]

            # 2. 親を先にロックする
            cur.execute(
                """
                SELECT "調査状態"
                FROM "調査"
                WHERE "調査番号" = %s
                FOR UPDATE
                """,
                (investigation_id,),
            )
            parent = cur.fetchone()

            if parent is None:
                raise HTTPException(
                    status_code=404,
                    detail="関連する調査が存在しません。",
                )

            if parent[0] != 1:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "調査中の調査に関連する"
                        "問い合わせ調査のみ個別断念できます。"
                    ),
                )

            # 3. 親のロックを保持したまま対象の関連レコードをロック
            cur.execute(
                """
                SELECT
                    "問い合わせ番号",
                    "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                  AND "調査番号" = %s
                FOR UPDATE
                """,
                (relation_id, investigation_id),
            )
            relation = cur.fetchone()

            if relation is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせ調査が見つかりません。",
                )

            inquiry_number, relation_state = relation

            # 4. 問い合わせの対応担当者を確認
            cur.execute(
                """
                SELECT "対応担当者"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )
            inquiry = cur.fetchone()

            if inquiry is None:
                raise HTTPException(
                    status_code=404,
                    detail="関連する問い合わせが見つかりません。",
                )

            if inquiry[0] != current_user.職員番号:
                raise HTTPException(
                    status_code=403,
                    detail="関連する問い合わせの対応担当者本人だけが個別断念できます。",
                )

            if relation_state != 1:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "調査中の問い合わせ調査のみ"
                        "個別断念できます。"
                    ),
                )

                        # 5. 対象の関連レコードだけを個別断念にする
            cur.execute(
                """
                UPDATE "問い合わせ調査"
                SET
                    "問い合わせ調査状態" = 2,
                    "断念日時" = CURRENT_TIMESTAMP
                WHERE "問い合わせ調査番号" = %s
                RETURNING
                    "問い合わせ調査番号",
                    "問い合わせ番号",
                    "調査番号",
                    "問い合わせ調査状態",
                    "断念日時"
                """,
                (relation_id,),
            )
            updated = cur.fetchone()

            result = {
                "問い合わせ調査番号": updated[0],
                "問い合わせ番号": updated[1],
                "調査番号": updated[2],
                "問い合わせ調査状態": updated[3],
                "断念日時": updated[4],
                "message": "問い合わせ調査を個別断念にしました。",
            }

    return result

# 問い合わせ調査のOK回答
@router.post(
    "/api/investigations/relations/{relation_id}/ok"
)
def ok_inquiry_problem_investigation_api(
    relation_id: int = Path(ge=1),
    current_user: main.CurrentUser = Depends(main.get_current_user),
):
    """問い合わせ調査にOKと回答する。"""

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # 1. 対象の関連レコードから旧調査番号を取得する
            cur.execute(
                """
                SELECT "調査番号"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )

            relation_ref = cur.fetchone()
            if relation_ref is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせ調査が見つかりません。",
                )

            old_investigation_id = relation_ref[0]

            # 2. 調査をロックする
            cur.execute(
                """
                SELECT
                    "調査状態",
                    "調査の名称",
                    "原因・仮説",
                    "情シス側での対応",
                    "問い合わせ者側で必要な対応",
                    "対応案策定予定日時",
                    "進捗更新の次回更新予定日時",
                    "最新移行先の調査番号"
                FROM "調査"
                WHERE "調査番号" = %s
                FOR UPDATE
                """,
                (old_investigation_id,),
            )
            investigation = cur.fetchone()

            if investigation is None:
                raise HTTPException(
                    status_code=404,
                    detail="関連する調査が見つかりません。",
                )

            # 3. 対象の子レコードをロックして取得する
            cur.execute(
                """
                SELECT
                    "問い合わせ番号",
                    "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                FOR UPDATE
                """,
                (relation_id,),
            )
            relation = cur.fetchone()

            if relation is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせ調査が見つかりません。",
                )

            inquiry_number, relation_state = relation

            # 4. 問い合わせ者本人であることを確認する
            cur.execute(
                """
                SELECT "問い合わせ職員番号"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )
            inquiry = cur.fetchone()

            if inquiry is None:
                raise HTTPException(
                    status_code=404,
                    detail="関連する問い合わせが見つかりません。",
                )

            if inquiry[0] != current_user.職員番号:
                raise HTTPException(
                    status_code=403,
                    detail="問い合わせ者本人だけがOKと回答できます。",
                )

            # 5. リアクション待ちであることを確認する
            if relation_state != 3:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "リアクション待ちの問い合わせ調査のみ"
                        "OKと回答できます。"
                    ),
                )

            # 6. 対象の子レコードにOK回答を記録する
            cur.execute(
                """
                UPDATE "問い合わせ調査"
                SET
                    "問い合わせ調査状態" = 4,
                    "リアクション内容" = 1,
                    "リアクション日時" = CURRENT_TIMESTAMP
                WHERE "問い合わせ調査番号" = %s
                RETURNING
                    "問い合わせ調査番号",
                    "問い合わせ番号",
                    "調査番号",
                    "問い合わせ調査状態",
                    "リアクション内容",
                    "リアクション日時"
                """,
                (relation_id,),
            )
            updated = cur.fetchone()

            result = {
                "問い合わせ調査番号": updated[0],
                "問い合わせ番号": updated[1],
                "調査番号": updated[2],
                "問い合わせ調査状態": updated[3],
                "リアクション内容": updated[4],
                "リアクション日時": updated[5],
                "message": "問い合わせ調査にOKと回答しました。",
            }

    return result

# 問い合わせ調査のNG回答
@router.post(
    "/api/investigations/relations/{relation_id}/ng"
)
def ng_inquiry_problem_investigation_api(
    relation_id: int = Path(ge=1),
    current_user: main.CurrentUser = Depends(main.get_current_user),
):
    """問い合わせ調査にNGと回答し、次の調査先へ移行する。"""

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # 1. 対象の関連レコードから旧調査番号を取得する
            cur.execute(
                """
                SELECT "調査番号"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )
            relation_ref = cur.fetchone()

            if relation_ref is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせ調査が見つかりません。",
                )

            old_investigation_id = relation_ref[0]

            # 2. 旧調査をロックする
            # 最新移行先の判定・更新を直列化する
            cur.execute(
                """
                SELECT
                    "調査状態",
                    "調査の名称",
                    "原因・仮説",
                    "情シス側での対応",
                    "問い合わせ者側で必要な対応",
                    "対応案策定予定日時",
                    "進捗更新の次回更新予定日時",
                    "最新移行先の調査番号"
                FROM "調査"
                WHERE "調査番号" = %s
                FOR UPDATE
                """,
                (old_investigation_id,),
            )
            old_investigation = cur.fetchone()

            if old_investigation is None:
                raise HTTPException(
                    status_code=404,
                    detail="関連する調査が見つかりません。",
                )

            (
                old_investigation_state,
                old_name,
                old_cause,
                old_it_response,
                old_requester_response,
                old_plan_due_at,
                old_next_update_at,
                latest_destination_id,
            ) = old_investigation

            # 3. 対象の関連レコードをロックし、状態を確認する
            cur.execute(
                """
                SELECT
                    "問い合わせ番号",
                    "調査番号",
                    "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                FOR UPDATE
                """,
                (relation_id,),
            )
            relation = cur.fetchone()

            if relation is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問い合わせ調査が見つかりません。",
                )

            inquiry_number, relation_investigation_id, relation_state = (
                relation
            )

            if relation_investigation_id != old_investigation_id:
                raise HTTPException(
                    status_code=409,
                    detail="調査との関連が変更されています。",
                )

            if relation_state != 3:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "リアクション待ちの問い合わせ調査のみ"
                        "NGと回答できます。"
                    ),
                )

            # 4. 問い合わせ者本人であることを確認する
            cur.execute(
                """
                SELECT "問い合わせ職員番号"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )
            inquiry = cur.fetchone()

            if inquiry is None:
                raise HTTPException(
                    status_code=404,
                    detail="関連する問い合わせが見つかりません。",
                )

            if inquiry[0] != current_user.職員番号:
                raise HTTPException(
                    status_code=403,
                    detail="問い合わせ者本人だけがNGと回答できます。",
                )

            # 5. 最新移行先が調査中かどうかを判定する
            destination_id = None

            if latest_destination_id is not None:
                # 移行先の状態遷移とも競合しないようロックする
                cur.execute(
                    """
                    SELECT "調査状態"
                    FROM "調査"
                    WHERE "調査番号" = %s
                    FOR UPDATE
                    """,
                    (latest_destination_id,),
                )
                latest_destination = cur.fetchone()

                if (
                    latest_destination is not None
                    and latest_destination[0] == 1
                ):
                    # パターンA：調査中の最新移行先を再利用する
                    destination_id = latest_destination_id

            # 6. 再利用できる移行先がなければ新規作成する
            if destination_id is None:
                cur.execute(
                    """
                    INSERT INTO "調査" (
                        "調査の名称",
                        "原因・仮説",
                        "情シス側での対応",
                        "問い合わせ者側で必要な対応",
                        "調査状態",
                        "調査開始日時",
                        "対応案策定予定日時",
                        "進捗更新の次回更新予定日時"
                    )
                    VALUES (
                        COALESCE(%s, '名称未設定') || 'から複写',
                        %s,
                        %s,
                        %s,
                        1,
                        CURRENT_TIMESTAMP,
                        %s,
                        %s
                    )
                    RETURNING "調査番号"
                    """,
                    (
                        old_name,
                        old_cause,
                        old_it_response,
                        old_requester_response,
                        old_plan_due_at,
                        old_next_update_at,
                    ),
                )
                destination_id = cur.fetchone()[0]

                # パターンB：旧調査の最新移行先を更新する
                cur.execute(
                    """
                    UPDATE "調査"
                    SET "最新移行先の調査番号" = %s
                    WHERE "調査番号" = %s
                    """,
                    (
                        destination_id,
                        old_investigation_id,
                    ),
                )

            # 7. 旧関連レコードにNG回答と移行先を記録する
            cur.execute(
                """
                UPDATE "問い合わせ調査"
                SET
                    "問い合わせ調査状態" = 5,
                    "リアクション内容" = 2,
                    "リアクション日時" = CURRENT_TIMESTAMP,
                    "NGでの移行先調査番号" = %s
                WHERE "問い合わせ調査番号" = %s
                RETURNING
                    "問い合わせ調査番号",
                    "問い合わせ番号",
                    "調査番号",
                    "問い合わせ調査状態",
                    "リアクション内容",
                    "リアクション日時",
                    "NGでの移行先調査番号"
                """,
                (
                    destination_id,
                    relation_id,
                ),
            )
            updated_relation = cur.fetchone()


            # 8. 移行先に同じ問い合わせが関連付け済みでないか確認
            cur.execute(
                """
                SELECT "問い合わせ番号"
                FROM "問い合わせ調査"
                WHERE "調査番号" = %s
                  AND "問い合わせ番号" = %s
                """,
                (destination_id, inquiry_number),
            )
            existing_relation = cur.fetchone()

            if existing_relation is not None:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"問い合わせ番号 {inquiry_number} は"
                        "すでにこの調査に関連付けられています。"
                    ),
                )

            # 9. 問い合わせと移行先調査を新たに関連づける
            # 関連レコードの状態はDBの初期値1を使用する
            cur.execute(
                """
                INSERT INTO "問い合わせ調査" (
                    "問い合わせ番号",
                    "調査番号"
                )
                VALUES (%s, %s)
                RETURNING
                    "問い合わせ調査番号",
                    "問い合わせ番号",
                    "調査番号",
                    "問い合わせ調査状態"
                """,
                (
                    inquiry_number,
                    destination_id,
                ),
            )

            new_relation = cur.fetchone()

            result = {
                "問い合わせ調査番号": updated_relation[0],
                "問い合わせ番号": updated_relation[1],
                "調査番号": updated_relation[2],
                "問い合わせ調査状態": updated_relation[3],
                "リアクション内容": updated_relation[4],
                "リアクション日時": updated_relation[5],
                "NGでの移行先調査番号": updated_relation[6],
                "新しい調査番号": destination_id,
                "新しい問い合わせ調査番号": new_relation[0],
                "新しい問い合わせ調査状態": new_relation[3],
                "message": "NGと回答し、追加調査先へ移行しました。",
            }

    return result