"""実セッションの境界と保護APIの認証を確認するテスト。"""

import hashlib
import os

os.environ["DATABASE_NAME"] = "inquiry_management_test"

import argon2
import psycopg
import pytest
from fastapi.testclient import TestClient

import main
from main import app


TEST_STAFF_NUMBER = "J0002"
TEST_PASSWORD = "Auth-Boundary-Test-2026!"
ORIGINAL_GET_CURRENT_USER = main.get_current_user


# --- Fixtures ---


@pytest.fixture
def client():
    """Cookieをテスト間で共有しないHTTPクライアントを提供する。"""
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client


@pytest.fixture
def auth_account():
    """テスト用ログイン情報を一時設定し、終了後に元の状態へ戻す。"""
    password_hash = argon2.PasswordHasher().hash(TEST_PASSWORD)

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "パスワードハッシュ", "ログイン可否",
                       "作成日時", "更新日時", "パスワード更新日時"
                FROM "職員認証情報"
                WHERE "職員番号" = %s
                ''',
                (TEST_STAFF_NUMBER,),
            )
            previous_account = cur.fetchone()

            cur.execute(
                '''
                INSERT INTO "職員認証情報" (
                    "職員番号", "パスワードハッシュ", "ログイン可否"
                )
                VALUES (%s, %s, TRUE)
                ON CONFLICT ("職員番号") DO UPDATE SET
                    "パスワードハッシュ" = EXCLUDED."パスワードハッシュ",
                    "ログイン可否" = TRUE
                ''',
                (TEST_STAFF_NUMBER, password_hash),
            )

    created_session_hashes = []

    try:
        yield {
            "session_hashes": created_session_hashes,
        }
    finally:
        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                if created_session_hashes:
                    cur.execute(
                        '''
                        DELETE FROM "ログインセッション"
                        WHERE "セッションIDハッシュ" = ANY(%s)
                        ''',
                        (created_session_hashes,),
                    )

                if previous_account is None:
                    cur.execute(
                        '''
                        DELETE FROM "職員認証情報"
                        WHERE "職員番号" = %s
                        ''',
                        (TEST_STAFF_NUMBER,),
                    )
                else:
                    cur.execute(
                        '''
                        UPDATE "職員認証情報"
                        SET "パスワードハッシュ" = %s,
                            "ログイン可否" = %s,
                            "作成日時" = %s,
                            "更新日時" = %s,
                            "パスワード更新日時" = %s
                        WHERE "職員番号" = %s
                        ''',
                        (*previous_account, TEST_STAFF_NUMBER),
                    )


@pytest.fixture
def login_as_test_staff(client, auth_account):
    """実際のログインAPIを通してセッションCookieを発行する。"""

    def login():
        response = client.post(
            "/api/auth/login",
            json={
                "職員番号": TEST_STAFF_NUMBER,
                "パスワード": TEST_PASSWORD,
            },
        )
        assert response.status_code == 200, response.text

        session_id = response.cookies.get("session_id")
        assert session_id
        auth_account["session_hashes"].append(
            hashlib.sha256(session_id.encode("utf-8")).hexdigest()
        )
        return session_id

    return login


# --- Tests ---


def test_unknown_session_id_is_rejected(client):
    """DBに存在しないセッションIDでは保護APIを利用できない。"""
    response = client.get(
        "/api/auth/me",
        cookies={"session_id": "not-a-valid-session-id"},
    )

    assert response.status_code == 401


def test_revoked_session_is_rejected(
    client,
    login_as_test_staff,
):
    """ログアウトで失効したセッションは、その後のアクセスを拒否する。"""
    session_id = login_as_test_staff()

    logout_response = client.post(
        "/api/auth/logout",
        cookies={"session_id": session_id},
    )
    assert logout_response.status_code == 200

    response = client.get(
        "/api/auth/me",
        cookies={"session_id": session_id},
    )

    assert response.status_code == 401


@pytest.mark.parametrize("expired_limit", ["idle", "absolute"])
def test_expired_session_limit_is_rejected(
    client,
    login_as_test_staff,
    auth_account,
    expired_limit,
):
    """無操作期限と絶対有効期限を個別に過去へ移すと拒否される。"""
    session_id = login_as_test_staff()
    session_hash = hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            if expired_limit == "idle":
                cur.execute(
                    '''
                    UPDATE "ログインセッション"
                    SET "無操作期限" = CURRENT_TIMESTAMP - INTERVAL '1 second'
                    WHERE "セッションIDハッシュ" = %s
                    ''',
                    (session_hash,),
                )
            else:
                # CHECK制約を保つため、無操作期限も絶対期限より前にする。
                cur.execute(
                    '''
                    UPDATE "ログインセッション"
                    SET "無操作期限" = CURRENT_TIMESTAMP - INTERVAL '2 seconds',
                        "絶対有効期限" = CURRENT_TIMESTAMP - INTERVAL '1 second'
                    WHERE "セッションIDハッシュ" = %s
                    ''',
                    (session_hash,),
                )

    response = client.get(
        "/api/auth/me",
        cookies={"session_id": session_id},
    )

    assert response.status_code == 401


def test_investigation_search_requires_real_session(client):
    """調査一覧APIもCookie認証なしでは利用できない。"""
    # 他の調査APIテストが依存関係を上書きするため、ここでは実認証に戻す。
    app.dependency_overrides.pop(ORIGINAL_GET_CURRENT_USER, None)

    response = client.get("/api/investigations")

    assert response.status_code == 401
