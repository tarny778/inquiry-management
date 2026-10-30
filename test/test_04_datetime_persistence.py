"""タイムゾーン付き日時の更新・DB保存・API返却を確認する。"""

import os
from datetime import datetime, timezone

os.environ["DATABASE_NAME"] = "inquiry_management_test"

import psycopg
import pytest
from fastapi.testclient import TestClient

import main
from main import app


DATABASE_NAME = "inquiry_management_test"
ORIGINAL_GET_CURRENT_USER = main.get_current_user
INQUIRY_TIMESTAMP_INPUT = "2026-07-08T14:25:36+09:00"
INVESTIGATION_TIMESTAMP_INPUT = "2026-07-09T09:15:00+09:00"


# --- Fixtures ---


@pytest.fixture
def client():
    """日時更新テスト用HTTPクライアントを提供する。"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def logged_in_it_staff(monkeypatch):
    """問い合わせ・調査の更新を行う職員J0001として認証する。"""
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
def editable_inquiry(client):
    """受付担当者J0001が編集可能な未引き受け問い合わせを作る。"""
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
            "受付経路": "メール",
            "問い合わせ分類": "分類A",
            "件名": "日時保存テスト用問い合わせ",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "日時更新後の保存値を確認する",
            "受信日時": "2026-07-01T10:00:00+09:00",
        },
    )
    assert response.status_code == 200, response.text
    inquiry_number = response.json()["問い合わせ番号"]

    yield inquiry_number

    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM "問い合わせ" WHERE "問い合わせ番号" = %s',
                (inquiry_number,),
            )


@pytest.fixture
def editable_investigation(client):
    """J0001担当の問い合わせに関連する、編集中状態の調査を作る。"""
    inquiry_response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
            "受付経路": "電話",
            "問い合わせ分類": "分類A",
            "件名": "調査日時保存テスト用問い合わせ",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "調査予定日時の保存値を確認する",
            "受信日時": None,
        },
    )
    assert inquiry_response.status_code == 200, inquiry_response.text
    inquiry_number = inquiry_response.json()["問い合わせ番号"]

    investigation_number = None
    try:
        with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    UPDATE "問い合わせ"
                    SET "対応担当者" = 'J0001',
                        "引き受け日時" = CURRENT_TIMESTAMP
                    WHERE "問い合わせ番号" = %s
                    ''',
                    (inquiry_number,),
                )
                cur.execute(
                    '''
                    INSERT INTO "調査" ("調査の名称")
                    VALUES (%s)
                    RETURNING "調査番号"
                    ''',
                    ("調査日時保存テスト",),
                )
                investigation_number = cur.fetchone()[0]
                cur.execute(
                    '''
                    INSERT INTO "問い合わせ調査" (
                        "調査番号", "問い合わせ番号"
                    ) VALUES (%s, %s)
                    ''',
                    (investigation_number, inquiry_number),
                )

        yield investigation_number
    finally:
        with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
            with conn.cursor() as cur:
                if investigation_number is not None:
                    cur.execute(
                        'DELETE FROM "問い合わせ調査" WHERE "調査番号" = %s',
                        (investigation_number,),
                    )
                    cur.execute(
                        'DELETE FROM "調査" WHERE "調査番号" = %s',
                        (investigation_number,),
                    )
                cur.execute(
                    'DELETE FROM "問い合わせ" WHERE "問い合わせ番号" = %s',
                    (inquiry_number,),
                )


# --- Tests ---


def test_updated_inquiry_datetime_round_trips_as_same_instant(
    client,
    editable_inquiry,
):
    """問い合わせ更新後、DBと詳細APIで同じ時点の日時を保持する。"""
    update_response = client.put(
        f"/api/inquiries/{editable_inquiry}",
        json={
            "問い合わせ職員番号": "T0001",
            "受付経路": "メール",
            "問い合わせ分類": "分類A",
            "件名": "日時保存テスト用問い合わせ",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "日時更新後の保存値を確認する",
            "受信日時": INQUIRY_TIMESTAMP_INPUT,
        },
    )
    assert update_response.status_code == 200, update_response.text

    expected_instant = datetime.fromisoformat(
        INQUIRY_TIMESTAMP_INPUT
    ).astimezone(timezone.utc)

    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT "受信日時" FROM "問い合わせ" WHERE "問い合わせ番号" = %s',
                (editable_inquiry,),
            )
            stored_instant = cur.fetchone()[0]

    assert stored_instant.tzinfo is not None
    assert stored_instant == expected_instant

    detail_response = client.get(f"/api/inquiries/{editable_inquiry}")
    assert detail_response.status_code == 200, detail_response.text
    returned_instant = datetime.fromisoformat(
        detail_response.json()["受信日時"]
    )
    assert returned_instant.tzinfo is not None
    assert returned_instant.astimezone(timezone.utc) == expected_instant


def test_updated_investigation_datetime_round_trips_as_same_instant(
    client,
    editable_investigation,
):
    """調査予定日時の更新後、DBとAPIが同じ時点を返す。"""
    update_response = client.patch(
        f"/api/investigations/{editable_investigation}",
        json={"対応案策定予定日時": INVESTIGATION_TIMESTAMP_INPUT},
    )
    assert update_response.status_code == 200, update_response.text

    expected_instant = datetime.fromisoformat(
        INVESTIGATION_TIMESTAMP_INPUT
    ).astimezone(timezone.utc)

    with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT "対応案策定予定日時" FROM "調査" WHERE "調査番号" = %s',
                (editable_investigation,),
            )
            stored_instant = cur.fetchone()[0]

    assert stored_instant.tzinfo is not None
    assert stored_instant == expected_instant

    returned_instant = datetime.fromisoformat(
        update_response.json()["対応案策定予定日時"]
    )
    assert returned_instant.tzinfo is not None
    assert returned_instant.astimezone(timezone.utc) == expected_instant
