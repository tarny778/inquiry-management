"""問い合わせ一覧の個別検索条件・組み合わせ・日時境界を確認する。"""

import os

os.environ["DATABASE_NAME"] = "inquiry_management_test"

import psycopg
import pytest
from fastapi.testclient import TestClient

import main
from main import app


DATABASE_NAME = "inquiry_management_test"
ORIGINAL_GET_CURRENT_USER = main.get_current_user
TEST_INQUIRIES = [
    {
        "key": "before_start",
        "subject": "検索境界-開始前",
        "urgency": 1,
        "receptionist": "J0001",
        "handler": "J0001",
        "received_at": "2026-06-01T09:59:00+09:00",
    },
    {
        "key": "at_start",
        "subject": "検索境界-開始時刻",
        "urgency": 2,
        "receptionist": "J0002",
        "handler": "J0001",
        "received_at": "2026-06-01T10:00:00+09:00",
    },
    {
        "key": "at_end",
        "subject": "検索境界-終了時刻",
        "urgency": 2,
        "receptionist": "J0001",
        "handler": "J0002",
        "received_at": "2026-06-01T11:00:00+09:00",
    },
    {
        "key": "after_end",
        "subject": "検索境界-終了後",
        "urgency": 3,
        "receptionist": "J0002",
        "handler": "J0002",
        "received_at": "2026-06-01T11:01:00+09:00",
    },
    {
        "key": "combined_only",
        "subject": "検索境界-複合条件のみ",
        "urgency": 2,
        "receptionist": "J0001",
        "handler": "J0001",
        "received_at": "2026-06-01T11:30:00+09:00",
    },
]


# --- Fixtures ---


@pytest.fixture
def client():
    """検索テスト用HTTPクライアントを提供する。"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def logged_in_it_staff(monkeypatch):
    """検索APIの認証依存を、テスト用の情シス職員に置き換える。"""
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
def search_inquiries(client):
    """検索条件ごとに値が異なる問い合わせを作成し、終了後に削除する。"""
    inquiry_numbers = {}

    try:
        for item in TEST_INQUIRIES:
            response = client.post(
                "/api/inquiries",
                json={
                    "問い合わせ職員番号": "T0001",
                    "受付経路": "メール",
                    "問い合わせ分類": "分類A",
                    "件名": item["subject"],
                    "緊急度": item["urgency"],
                    "受付時の処理": 2,
                    "問い合わせ詳細": "検索条件テスト用データ",
                    "受信日時": item["received_at"],
                },
            )
            assert response.status_code == 200, response.text
            inquiry_numbers[item["key"]] = response.json()["問い合わせ番号"]

        with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
            with conn.cursor() as cur:
                for item in TEST_INQUIRIES:
                    inquiry_number = inquiry_numbers[item["key"]]
                    cur.execute(
                        '''
                        UPDATE "問い合わせ"
                        SET "受付担当者" = %s,
                            "対応担当者" = %s,
                            "引き受け日時" = CURRENT_TIMESTAMP
                        WHERE "問い合わせ番号" = %s
                        ''',
                        (
                            item["receptionist"],
                            item["handler"],
                            inquiry_number,
                        ),
                    )

        yield inquiry_numbers
    finally:
        if inquiry_numbers:
            with psycopg.connect(f"dbname={DATABASE_NAME}") as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        '''
                        DELETE FROM "問い合わせ"
                        WHERE "問い合わせ番号" = ANY(%s)
                        ''',
                        (list(inquiry_numbers.values()),),
                    )


# --- Tests ---


def test_search_inquiries_by_urgency(client, search_inquiries):
    """緊急度で検索すると、その値に該当する問い合わせだけが返る。"""
    response = client.get(
        "/api/inquiries",
        params={"初期条件": 2, "緊急度": 2},
    )

    assert response.status_code == 200, response.text
    actual = {
        item["問い合わせ番号"] for item in response.json()["items"]
    }
    expected = {
        search_inquiries[key]
        for key in ("at_start", "at_end", "combined_only")
    }
    assert actual == expected


def test_search_inquiries_by_receptionist(client, search_inquiries):
    """受付担当者で検索すると、担当者が一致する問い合わせだけが返る。"""
    response = client.get(
        "/api/inquiries",
        params={"初期条件": 2, "受付担当者": "J0001"},
    )

    assert response.status_code == 200, response.text
    actual = {
        item["問い合わせ番号"] for item in response.json()["items"]
    }
    expected = {
        search_inquiries[key]
        for key in ("before_start", "at_end", "combined_only")
    }
    assert actual == expected


def test_search_inquiries_by_handler(client, search_inquiries):
    """対応担当者で検索すると、担当者が一致する問い合わせだけが返る。"""
    response = client.get(
        "/api/inquiries",
        params={"初期条件": 2, "対応担当者": "J0001"},
    )

    assert response.status_code == 200, response.text
    actual = {
        item["問い合わせ番号"] for item in response.json()["items"]
    }
    expected = {
        search_inquiries[key]
        for key in ("before_start", "at_start", "combined_only")
    }
    assert actual == expected


def test_search_inquiries_date_range_includes_both_boundaries(
    client,
    search_inquiries,
):
    """受信日時範囲は開始・終了と同時刻の問い合わせを含める。"""
    response = client.get(
        "/api/inquiries",
        params={
            "初期条件": 2,
            "受信日時開始": "2026-06-01T10:00:00+09:00",
            "受信日時終了": "2026-06-01T11:00:00+09:00",
        },
    )

    assert response.status_code == 200, response.text
    actual = {
        item["問い合わせ番号"] for item in response.json()["items"]
    }
    expected = {
        search_inquiries["at_start"],
        search_inquiries["at_end"],
    }
    assert actual == expected


def test_search_inquiries_combined_filters_are_all_applied(
    client,
    search_inquiries,
):
    """緊急度・受付担当者・対応担当者の複合条件はANDで絞り込む。"""
    response = client.get(
        "/api/inquiries",
        params={
            "初期条件": 2,
            "緊急度": 2,
            "受付担当者": "J0001",
            "対応担当者": "J0001",
        },
    )

    assert response.status_code == 200, response.text
    actual = {
        item["問い合わせ番号"] for item in response.json()["items"]
    }
    assert actual == {search_inquiries["combined_only"]}
