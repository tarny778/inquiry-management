
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import argon2
import psycopg
from fastapi import APIRouter, HTTPException, Request, Response

import main
from schemas.schemas_auth import LoginRequest


router = APIRouter(prefix="/api/auth", tags=["認証"])

# セッションの有効期間
IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TIMEOUT = timedelta(hours=12)

# Cookie名
SESSION_COOKIE_NAME = "session_id"

# Argon2によるパスワード検証
password_hasher = argon2.PasswordHasher()


def authenticate_session(request: Request) -> main.CurrentUser:
    """Cookieのセッションを検証し、ログイン中の職員を返す。"""

    # CookieからセッションIDを取得する。
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="ログインが必要です。",
        )

    # DBにはハッシュしか保存していないため、同じ方法で変換する。
    session_hash = hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()

    now = datetime.now(timezone.utc)

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT
                    ls."職員番号",
                    s."氏名",
                    s."所属",
                    ls."絶対有効期限"
                FROM "ログインセッション" AS ls
                JOIN "職員認証情報" AS a
                  ON a."職員番号" = ls."職員番号"
                JOIN "職員" AS s
                  ON s."職員番号" = ls."職員番号"
                WHERE ls."セッションIDハッシュ" = %s
                  AND ls."失効日時" IS NULL
                  AND ls."無操作期限" > %s
                  AND ls."絶対有効期限" > %s
                  AND a."ログイン可否" = TRUE
                FOR UPDATE OF ls
                ''',
                (session_hash, now, now),
            )

            session = cur.fetchone()

            if session is None:
                raise HTTPException(
                    status_code=401,
                    detail="セッションが無効です。再度ログインしてください。",
                )

            staff_number, name, department, absolute_expiry = session

            # 無操作期限は延長するが、絶対有効期限は延長しない。
            new_idle_expiry = min(
                now + IDLE_TIMEOUT,
                absolute_expiry,
            )

            cur.execute(
                '''
                UPDATE "ログインセッション"
                SET
                    "無操作期限" = %s,
                    "最終利用日時" = %s
                WHERE "セッションIDハッシュ" = %s
                ''',
                (
                    new_idle_expiry,
                    now,
                    session_hash,
                ),
            )

    return main.CurrentUser(
        職員番号=staff_number,
        氏名=name,
        所属=department,
    )



@router.post("/login")
def login(
    request: LoginRequest,
    response: Response,
):
    """職員番号とパスワードで認証し、セッションを発行する。"""

    with psycopg.connect(
        dbname=main.DATABASE_NAME
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT
                    a."パスワードハッシュ",
                    a."ログイン可否",
                    s."氏名",
                    s."所属"
                FROM "職員認証情報" AS a
                JOIN "職員" AS s
                  ON s."職員番号" = a."職員番号"
                WHERE a."職員番号" = %s
                ''',
                (request.職員番号,),
            )
            account = cur.fetchone()

    # アカウントが存在しない場合も、ログイン不可の場合も
    # 利用者には同じエラーを返す。
    if account is None:
        raise HTTPException(
            status_code=401,
            detail="職員番号またはパスワードが正しくありません。",
        )

    password_hash, login_allowed, name, department = account

    if not login_allowed:
        raise HTTPException(
            status_code=401,
            detail="職員番号またはパスワードが正しくありません。",
        )

    try:
        password_hasher.verify(
            password_hash,
            request.パスワード,
        )
    except (argon2.exceptions.VerifyMismatchError,
            argon2.exceptions.VerificationError):
        raise HTTPException(
            status_code=401,
            detail="職員番号またはパスワードが正しくありません。",
        )

    # 認証成功。ランダムなセッションIDを発行する。
    session_id = secrets.token_urlsafe(32)

    # DBにはセッションIDそのものではなくハッシュを保存する。
    session_hash = hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()

    now = datetime.now(timezone.utc)
    idle_expiry = now + IDLE_TIMEOUT
    absolute_expiry = now + ABSOLUTE_TIMEOUT

    with psycopg.connect(
        dbname=main.DATABASE_NAME
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "ログインセッション" (
                    "セッションIDハッシュ",
                    "職員番号",
                    "作成日時",
                    "無操作期限",
                    "絶対有効期限",
                    "最終利用日時"
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ''',
                (
                    session_hash,
                    request.職員番号,
                    now,
                    idle_expiry,
                    absolute_expiry,
                    now,
                ),
            )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax",
        max_age=int(ABSOLUTE_TIMEOUT.total_seconds()),
        path="/",
    )

    return {
        "message": "ログインしました。",
        "職員番号": request.職員番号,
        "氏名": name,
        "所属": department,
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
):
    """セッションを失効させ、Cookieを削除する。"""

    # CookieからセッションIDを取得する。
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_id:
        # DBに保存しているハッシュ値を計算する。
        session_hash = hashlib.sha256(
            session_id.encode("utf-8")
        ).hexdigest()

        now = datetime.now(timezone.utc)

        # セッションを削除せず、失効日時を記録する。
        with psycopg.connect(
            dbname=main.DATABASE_NAME
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    UPDATE "ログインセッション"
                    SET "失効日時" = %s
                    WHERE "セッションIDハッシュ" = %s
                      AND "失効日時" IS NULL
                    ''',
                    (now, session_hash),
                )

    # Cookieがない場合や、すでに失効している場合も
    # ブラウザ側のCookie削除を試みる。
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax",
    )

    return {
        "message": "ログアウトしました。",
    }

