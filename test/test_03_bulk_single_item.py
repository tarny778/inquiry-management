"""一括引き受け・一括完了APIの1件指定を確認する。"""

from config import settings

import psycopg
import pytest
from fastapi.testclient import TestClient

import main
from main import app


ORIGINAL_GET_CURRENT_USER = main.get_current_user


# --- Fixtures ---


@pytest.fixture
def client():
    """一括APIテスト用HTTPクライアントを提供する。"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def logged_in_it_staff(monkeypatch):
    """一括操作の操作者を情シス職員J0001として認証する。"""
    user = main.CurrentUser(
        職員番号="J0001",
        氏名="テスト情シス職員",
        所属="情報システム課",
    )
    monkeypatch.setitem(
        app.dependency_overrides,
        ORIGINAL_GET_CURRENT_USER,
        lambda: user,
    )


@pytest.fixture
def pending_inquiry(client):
    """引き受け待ち問い合わせを作り、終了後に削除する。"""
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
            "受付経路": "電話",
            "問い合わせ分類": "分類A",
            "件名": "一括APIの1件引き受けテスト",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "1件指定の状態更新を確認する",
            "受信日時": None,
        },
    )
    assert response.status_code == 200, response.text
    inquiry_number = response.json()["問い合わせ番号"]

    yield inquiry_number

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM "問い合わせ" WHERE "問い合わせ番号" = %s',
                (inquiry_number,),
            )


@pytest.fixture
def in_progress_inquiry(client, pending_inquiry):
    """完了操作用に、テスト問い合わせをJ0001の対応中へ設定する。"""
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問い合わせ"
                SET "対応担当者" = 'J0001',
                    "引き受け日時" = CURRENT_TIMESTAMP
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry,),
            )

    yield pending_inquiry


# --- Tests ---


def test_bulk_accept_one_inquiry_updates_that_record(
    client,
    pending_inquiry,
):
    """一括引き受けAPIに番号を1件だけ渡しても、担当と日時を設定する。"""
    response = client.post(
        "/api/inquiries/bulk-accept",
        json={"問い合わせ番号一覧": [pending_inquiry]},
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["対応担当者"] == "J0001"
    assert result["問い合わせ番号一覧"] == [pending_inquiry]

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "対応担当者", "引き受け日時", "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry,),
            )
            handler, accepted_at, completed_at = cur.fetchone()

    assert handler == "J0001"
    assert accepted_at is not None
    assert accepted_at.tzinfo is not None
    assert completed_at is None


def test_bulk_complete_one_inquiry_updates_that_record(
    client,
    in_progress_inquiry,
):
    """一括完了APIに番号を1件だけ渡しても、完了日時を設定する。"""
    response = client.post(
        "/api/inquiries/bulk-complete",
        json={"問い合わせ番号一覧": [in_progress_inquiry]},
    )

    assert response.status_code == 200, response.text
    assert response.json()["問い合わせ番号一覧"] == [in_progress_inquiry]

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "対応担当者", "引き受け日時", "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (in_progress_inquiry,),
            )
            handler, accepted_at, completed_at = cur.fetchone()

    assert handler == "J0001"
    assert accepted_at is not None
    assert completed_at is not None
    assert completed_at.tzinfo is not None
