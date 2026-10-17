
import os

os.environ["DATABASE_NAME"] = "inquiry_management_test"

import hashlib
import secrets

import argon2
import psycopg
import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app, base_url="https://testserver")
password_hasher = argon2.PasswordHasher()

TEST_STAFF_NUMBER = "J0001"
TEST_PASSWORD = "AuthTest-Password-2026!"


@pytest.fixture
def auth_account():
    """ログインテスト用アカウントを作成し、終了後に削除する。"""

    password_hash = password_hasher.hash(TEST_PASSWORD)

    try:
        with psycopg.connect(
            "dbname=inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    INSERT INTO "職員認証情報" (
                        "職員番号",
                        "パスワードハッシュ",
                        "ログイン可否"
                    )
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT ("職員番号")
                    DO UPDATE SET
                        "パスワードハッシュ" = EXCLUDED."パスワードハッシュ",
                        "ログイン可否" = TRUE
                    ''',
                    (TEST_STAFF_NUMBER, password_hash),
                )

        yield

    finally:
        with psycopg.connect(
            "dbname=inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    DELETE FROM "ログインセッション"
                    WHERE "職員番号" = %s
                    ''',
                    (TEST_STAFF_NUMBER,),
                )
                cur.execute(
                    '''
                    DELETE FROM "職員認証情報"
                    WHERE "職員番号" = %s
                    ''',
                    (TEST_STAFF_NUMBER,),
                )

@pytest.fixture
def auth_test_inquiry(auth_account):
    """詳細APIの認証テスト用問い合わせを作成し、終了後に削除する。"""

    with psycopg.connect("dbname=inquiry_management_test") as conn:
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
                    "受信日時"
                )
                VALUES (
                    'T0001',
                    '総務課',
                    '電話',
                    '分類A',
                    '認証テスト用問い合わせ',
                    2,
                    2,
                    '詳細APIの認証テスト',
                    %s,
                    CURRENT_TIMESTAMP
                )
                RETURNING "問い合わせ番号"
                ''',
                (TEST_STAFF_NUMBER,),
            )
            inquiry_number = cur.fetchone()[0]

    yield inquiry_number

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                DELETE FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (inquiry_number,),
            )

#ログインのテスト
def test_login_success(auth_account):
    """正しい職員番号とパスワードでログインできる。"""

    response = client.post(
        "/api/auth/login",
        json={
            "職員番号": TEST_STAFF_NUMBER,
            "パスワード": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["職員番号"] == TEST_STAFF_NUMBER
    assert response.json()["message"] == "ログインしました。"

    session_id = response.cookies.get("session_id")
    assert session_id

    session_hash = hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()

    with psycopg.connect(
        "dbname=inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT
                    "セッションIDハッシュ",
                    "無操作期限",
                    "絶対有効期限",
                    "失効日時"
                FROM "ログインセッション"
                WHERE "職員番号" = %s
                ''',
                (TEST_STAFF_NUMBER,),
            )
            session = cur.fetchone()

    assert session is not None
    assert session[0] == session_hash
    assert session[1] <= session[2]
    assert session[3] is None

    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_login_wrong_password(auth_account):
    """パスワードが違う場合は認証を拒否する。"""

    response = client.post(
        "/api/auth/login",
        json={
            "職員番号": TEST_STAFF_NUMBER,
            "パスワード": "Wrong-Password-2026!",
        },
    )

    assert response.status_code == 401


def test_login_unknown_staff():
    """存在しない職員番号は認証を拒否する。"""

    response = client.post(
        "/api/auth/login",
        json={
            "職員番号": "UNKNOWN-STAFF",
            "パスワード": "AuthTest-Password-2026!",
        },
    )

    assert response.status_code == 401


def test_login_disabled_account(auth_account):
    """ログイン禁止アカウントは認証を拒否する。"""

    with psycopg.connect(
        "dbname=inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "職員認証情報"
                SET "ログイン可否" = FALSE
                WHERE "職員番号" = %s
                ''',
                (TEST_STAFF_NUMBER,),
            )

    response = client.post(
        "/api/auth/login",
        json={
            "職員番号": TEST_STAFF_NUMBER,
            "パスワード": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401


def test_login_invalid_request():
    """入力制約に違反するリクエストは拒否する。"""

    response = client.post(
        "/api/auth/login",
        json={
            "職員番号": "",
            "パスワード": "password",
        },
    )

    assert response.status_code == 422

#ログアウトのテスト
def test_logout_revokes_session_and_deletes_cookie(auth_account):
    """ログアウトするとセッションが失効し、Cookieが削除される。"""

    # 先にログインする。
    login_response = client.post(
        "/api/auth/login",
        json={
            "職員番号": TEST_STAFF_NUMBER,
            "パスワード": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    session_id = login_response.cookies.get("session_id")
    assert session_id is not None

    session_hash = hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()

    # Cookieを明示的に渡してログアウトする。
    logout_response = client.post(
        "/api/auth/logout",
        cookies={"session_id": session_id},
    )

    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "ログアウトしました。"

    # DBに失効日時が記録されたことを確認する。
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "失効日時"
                FROM "ログインセッション"
                WHERE "セッションIDハッシュ" = %s
                ''',
                (session_hash,),
            )
            row = cur.fetchone()

    assert row is not None
    assert row[0] is not None

    # Cookie削除のレスポンスが返されたことを確認する。
    set_cookie = logout_response.headers.get("set-cookie", "")
    assert "session_id=" in set_cookie
    assert "max-age=0" in set_cookie.lower()


def test_logout_without_cookie_succeeds():
    """CookieがなくてもログアウトAPIは成功する。"""

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "ログアウトしました。"

#ログイン状態、セッション有無によるテスト
def test_inquiry_list_requires_authentication():
    """未ログインでは問い合わせ一覧APIを利用できない。"""

    response = client.get("/api/inquiries")

    assert response.status_code == 401


def test_inquiry_list_with_authenticated_session(auth_account):
    """ログイン済みなら問い合わせ一覧APIを利用できる。"""

    login_response = client.post(
        "/api/auth/login",
        json={
            "職員番号": TEST_STAFF_NUMBER,
            "パスワード": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    response = client.get(
        "/api/inquiries",
        params={"初期条件": 1},
    )

    assert response.status_code == 200


def test_inquiry_detail_requires_authentication(auth_test_inquiry):
    """未ログインでは問い合わせ詳細APIを利用できない。"""

    response = client.get(
        f"/api/inquiries/{auth_test_inquiry}"
    )

    assert response.status_code == 401


def test_inquiry_detail_with_authenticated_session(
    auth_test_inquiry,
    auth_account,
):
    """ログイン済みなら問い合わせ詳細APIを利用できる。"""

    login_response = client.post(
        "/api/auth/login",
        json={
            "職員番号": TEST_STAFF_NUMBER,
            "パスワード": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    response = client.get(
        f"/api/inquiries/{auth_test_inquiry}"
    )

    assert response.status_code == 200