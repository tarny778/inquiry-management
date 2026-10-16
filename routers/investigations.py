from fastapi import APIRouter, Query, Path, HTTPException
import psycopg
import main

DATABASE_NAME = main.DATABASE_NAME

router = APIRouter()


# 問題調査の検索・一覧取得
@router.get("/api/investigations")
def search_investigations_api(
    問題調査番号: int | None = Query(default=None, ge=1),
    問題調査の名称や仮説: str | None = None,
    問題調査状態: int | None = Query(default=None, ge=1, le=3),
    問い合わせ職員番号: str | None = None,
    問い合わせ者氏名: str | None = None,
    対応担当者職員番号: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    # ログイン中の職員を取得
    current_user = main.get_current_user()
    操作者職員番号 = current_user.職員番号

    # 検索条件を組み立てる
    conditions = []
    params = []

    if 問題調査番号 is not None:
        conditions.append('q."問題調査番号" = %s')
        params.append(問題調査番号)

    if 問題調査の名称や仮説 and 問題調査の名称や仮説.strip():
        conditions.append(
            'q."問題調査の名称や仮説" LIKE %s'
        )
        params.append(f"%{問題調査の名称や仮説.strip()}%")

    if 問題調査状態 is not None:
        conditions.append('q."問題調査状態" = %s')
        params.append(問題調査状態)

    # 問い合わせ者の職員番号で検索
    if 問い合わせ職員番号:
        conditions.append(
            '''
            EXISTS (
                SELECT 1
                FROM "問い合わせ問題調査" ik
                JOIN "問い合わせ" i
                    ON i."問い合わせ番号" = ik."問い合わせ番号"
                WHERE ik."問題調査番号" = q."問題調査番号"
                  AND i."問い合わせ職員番号" = %s
            )
            '''
        )
        params.append(問い合わせ職員番号)

    # 問い合わせ者の氏名で部分一致検索
    if 問い合わせ者氏名 and 問い合わせ者氏名.strip():
        conditions.append(
            '''
            EXISTS (
                SELECT 1
                FROM "問い合わせ問題調査" ik
                JOIN "問い合わせ" i
                    ON i."問い合わせ番号" = ik."問い合わせ番号"
                JOIN "職員" s
                    ON s."職員番号" = i."問い合わせ職員番号"
                WHERE ik."問題調査番号" = q."問題調査番号"
                  AND s."氏名" LIKE %s
            )
            '''
        )
        params.append(f"%{問い合わせ者氏名.strip()}%")

    # 対応担当者の職員番号で検索
    if 対応担当者職員番号:
        conditions.append(
            '''
            EXISTS (
                SELECT 1
                FROM "問い合わせ問題調査" ik
                JOIN "問い合わせ" i
                    ON i."問い合わせ番号" = ik."問い合わせ番号"
                WHERE ik."問題調査番号" = q."問題調査番号"
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
    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:

            # 検索結果の総件数を取得
            cur.execute(
                f'''
                SELECT COUNT(*)
                FROM "問題調査" q
                {where_clause}
                ''',
                params,
            )
            total = cur.fetchone()[0]

            # 問題調査の一覧を取得
            cur.execute(
                f'''
                SELECT
                    q."問題調査番号",
                    q."問題調査の名称や仮説",
                    q."問題調査状態",

                    -- 関連する問い合わせの対応担当者氏名
                    (
                        SELECT s."氏名"
                        FROM "問い合わせ問題調査" ik
                        JOIN "問い合わせ" i
                            ON i."問い合わせ番号" = ik."問い合わせ番号"
                        JOIN "職員" s
                            ON s."職員番号" = i."対応担当者"
                        WHERE ik."問題調査番号" = q."問題調査番号"
                        ORDER BY i."問い合わせ番号"
                        LIMIT 1
                    ) AS "対応担当者職員氏名",

                    -- 関連する問い合わせの件数
                    (
                        SELECT COUNT(DISTINCT ik."問い合わせ番号")
                        FROM "問い合わせ問題調査" ik
                        WHERE ik."問題調査番号" = q."問題調査番号"
                    ) AS "関連問い合わせ件数",

                    -- 操作者自身の問い合わせが含まれるか
                    EXISTS (
                        SELECT 1
                        FROM "問い合わせ問題調査" ik
                        JOIN "問い合わせ" i
                            ON i."問い合わせ番号" = ik."問い合わせ番号"
                        WHERE ik."問題調査番号" = q."問題調査番号"
                          AND i."問い合わせ職員番号" = %s
                    ) AS "自分の問い合わせを含む"

                FROM "問題調査" q
                {where_clause}
                ORDER BY
                    q."調査開始日時" DESC,
                    q."問題調査番号" DESC
                LIMIT %s OFFSET %s
                ''',
                [操作者職員番号] + params + [page_size, offset],
            )

            rows = cur.fetchall()

    # 各行をレスポンス用の辞書に変換
    columns = [
        "問題調査番号",
        "問題調査の名称や仮説",
        "問題調査状態",
        "対応担当者職員氏名",
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


# 問題調査の詳細取得
@router.get("/api/investigations/{investigation_id}")
def get_investigation_api(
    investigation_id: int = Path(ge=1),
):
    # ログイン中の職員を取得
    current_user = main.get_current_user()
    操作者職員番号 = current_user.職員番号

    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:

            # 1. 問題調査そのものの詳細を取得
            cur.execute(
                '''
                SELECT
                    "問題調査番号",
                    "問題調査の名称や仮説",
                    "問題の原因",
                    "情シス側での対応",
                    "問い合わせ者側で必要な対応",
                    "問題調査状態",
                    "調査開始日時",
                    "対応案策定予定日時",
                    "進捗更新の次回更新予定日時",
                    "リアクション要求日時",
                    "問題調査断念日時",
                    "最新移行先の問題調査番号"
                FROM "問題調査"
                WHERE "問題調査番号" = %s
                ''',
                (investigation_id,),
            )

            row = cur.fetchone()

            # 問題調査が存在しない場合
            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="指定された問題調査が見つかりません。",
                )

            columns = [
                "問題調査番号",
                "問題調査の名称や仮説",
                "問題の原因",
                "情シス側での対応",
                "問い合わせ者側で必要な対応",
                "問題調査状態",
                "調査開始日時",
                "対応案策定予定日時",
                "進捗更新の次回更新予定日時",
                "リアクション要求日時",
                "問題調査断念日時",
                "最新移行先の問題調査番号",
            ]

            investigation = dict(zip(columns, row))

            # 2. 関連する問い合わせ問題調査を取得
            cur.execute(
                '''
                SELECT
                    ik."問い合わせ問題調査番号",
                    ik."問い合わせ番号",
                    requester."氏名" AS "問い合わせ者氏名",
                    handler."氏名" AS "対応担当者氏名",
                    ik."問い合わせ問題調査状態",
                    ik."調査開始日時",
                    ik."断念日時",
                    ik."リアクション被要求日時",
                    ik."リアクション日時",
                    ik."リアクション内容",
                    ik."NGでの移行先問題調査番号",
                    i."問い合わせ職員番号",
                    i."対応担当者"
                FROM "問い合わせ問題調査" ik
                JOIN "問い合わせ" i
                    ON i."問い合わせ番号" = ik."問い合わせ番号"
                JOIN "職員" requester
                    ON requester."職員番号" = i."問い合わせ職員番号"
                LEFT JOIN "職員" handler
                    ON handler."職員番号" = i."対応担当者"
                WHERE ik."問題調査番号" = %s
                ORDER BY ik."問い合わせ問題調査番号"
                ''',
                (investigation_id,),
            )

            rows = cur.fetchall()

    columns = [
        "問い合わせ問題調査番号",
        "問い合わせ番号",
        "問い合わせ者氏名",
        "対応担当者氏名",
        "問い合わせ問題調査状態",
        "調査開始日時",
        "断念日時",
        "リアクション被要求日時",
        "リアクション日時",
        "リアクション内容",
        "NGでの移行先問題調査番号",
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
        "関連する問い合わせ問題調査": related_inquiries,
    }
