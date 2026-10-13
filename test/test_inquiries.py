import os

os.environ["DATABASE_NAME"] = "inquiry_management_test"

import psycopg
from fastapi.testclient import TestClient

from main import app

import pytest

client = TestClient(app)


def test_create_inquiry_invalid_urgency():
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
            "受付担当者": "J0001",
            "受付経路": "電話",
            "問い合わせ分類": "分類A",
            "件名": "緊急度の異常系テスト",
            "緊急度": 4,
            "受付時の処理": 2,
            "問い合わせ詳細": "自動テストです",
            "受信日時": None,
        },
    )

    assert response.status_code == 422
    assert "緊急度は1、2、3のいずれかを指定してください" in (
        response.json()["detail"][0]["msg"]
    )

def test_create_inquiry_unknown_staff():
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T9999",
            "受付担当者": "J0001",
            "受付経路": "電話",
            "問い合わせ分類": "分類A",
            "件名": "存在しない職員のテスト",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "自動テストです",
            "受信日時": None,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "指定された問い合わせ職員番号は登録されていません"
    )


def test_create_inquiry_invalid_receptionist():
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
            "受付担当者": "T0001",
            "受付経路": "電話",
            "問い合わせ分類": "分類A",
            "件名": "受付担当者の異常系テスト",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "自動テストです",
            "受信日時": None,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "受付担当者が情シス職員として登録されていません"
    )


def test_create_inquiry_success():
    inquiry_number = None

    try:
        response = client.post(
            "/api/inquiries",
            json={
                "問い合わせ職員番号": "T0001",
                "受付担当者": "J0001",
                "受付経路": "電話",
                "問い合わせ分類": "分類A",
                "件名": "正常系テスト用問い合わせ",
                "緊急度": 2,
                "受付時の処理": 2,
                "問い合わせ詳細": "自動テストで登録したデータです",
                "受信日時": None,
            },
        )
        
        assert response.status_code == 200

        result = response.json()
        assert result["message"] == "問い合わせを登録しました"
        assert "問い合わせ番号" in result

        inquiry_number = result["問い合わせ番号"]

        # テスト用DBに実際に保存されたか確認する
        with psycopg.connect(
            "dbname=inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    SELECT
                        "問い合わせ職員番号",
                        "件名",
                        "受付担当者",
                        "引き受け日時",
                        "対応完了日時"
                    FROM "問い合わせ"
                    WHERE "問い合わせ番号" = %s
                    ''',
                    (inquiry_number,),
                )
                inquiry = cur.fetchone()

        assert inquiry is not None
        assert inquiry[0] == "T0001"
        assert inquiry[1] == "正常系テスト用問い合わせ"
        assert inquiry[2] == "J0001"
        assert inquiry[3] is None
        assert inquiry[4] is None

    finally:
        # テストで登録したデータを削除して後片付けする
        if inquiry_number is not None:
            with psycopg.connect(
                "dbname=inquiry_management_test"
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        '''
                        DELETE FROM "問い合わせ"
                        WHERE "問い合わせ番号" = %s
                        ''',
                        (inquiry_number,),
                    )


@pytest.fixture
def pending_inquiry_number():
    """テスト用の未引き受け問い合わせを作成し、終了後に削除する。"""
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
            "受付担当者": "J0001",
            "受付経路": "電話",
            "問い合わせ分類": "分類A",
            "件名": "引き受けAPIテスト用問い合わせ",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "自動テスト用データ",
            "受信日時": None,
        },
    )

    assert response.status_code == 200, response.text
    inquiry_number = response.json()["問い合わせ番号"]

    yield inquiry_number

    # テスト終了後にデータを削除する
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                DELETE FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (inquiry_number,),
            )


def test_accept_inquiry_success(pending_inquiry_number):
    response = client.post(
        f"/api/inquiries/{pending_inquiry_number}/accept",
        json={"対応担当者": "J0001"},
    )

    assert response.status_code == 200

    result = response.json()
    assert result["message"] == "問い合わせを引き受けました"
    assert result["問い合わせ番号"] == pending_inquiry_number
    assert result["対応担当者"] == "J0001"
    assert result["引き受け日時"] is not None

    # DBにも更新結果が保存されたことを確認する
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "対応担当者", "引き受け日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry_number,),
            )
            inquiry = cur.fetchone()

    assert inquiry is not None
    assert inquiry[0] == "J0001"
    assert inquiry[1] is not None


def test_accept_inquiry_unknown_number():
    response = client.post(
        "/api/inquiries/999999999/accept",
        json={"対応担当者": "J0001"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "指定された問い合わせは存在しません"
    )


def test_accept_inquiry_invalid_staff(pending_inquiry_number):
    response = client.post(
        f"/api/inquiries/{pending_inquiry_number}/accept",
        json={"対応担当者": "T0001"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "対応担当者が情シス職員として登録されていません"
    )


def test_accept_already_accepted_inquiry(pending_inquiry_number):
    # あらかじめ別の情シス職員が引き受けた状態にする
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = %s,
                    "引き受け日時" = NOW()
                WHERE "問い合わせ番号" = %s
                ''',
                ("J0002", pending_inquiry_number),
            )

    response = client.post(
        f"/api/inquiries/{pending_inquiry_number}/accept",
        json={"対応担当者": "J0001"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "この問い合わせは引き受けできない状態です"
    )


def test_accept_completed_inquiry(pending_inquiry_number):
    # あらかじめ対応完了済みの状態にする
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問い合わせ"
                SET "対応完了日時" = NOW()
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry_number,),
            )

    response = client.post(
        f"/api/inquiries/{pending_inquiry_number}/accept",
        json={"対応担当者": "J0001"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "この問い合わせは引き受けできない状態です"
    )


@pytest.fixture
def search_test_inquiries():
    """検索API用の問い合わせ3件を作成し、終了後に削除する。"""
    inquiry_numbers = []

    test_cases = [
        ("検索APIテスト-引き受け待ち", "pending"),
        ("検索APIテスト-対応中", "in_progress"),
        ("検索APIテスト-対応完了", "completed"),
    ]

    try:
        # 1. 問い合わせを3件登録する
        for title, state in test_cases:
            response = client.post(
                "/api/inquiries",
                json={
                    "問い合わせ職員番号": "T0001",
                    "受付担当者": "J0001",
                    "受付経路": "電話",
                    "問い合わせ分類": "分類A",
                    "件名": title,
                    "緊急度": 2,
                    "受付時の処理": 2,
                    "問い合わせ詳細": "検索APIの自動テスト用",
                    "受信日時": None,
                },
            )

            assert response.status_code == 200, response.text

            inquiry_number = response.json()["問い合わせ番号"]
            inquiry_numbers.append(inquiry_number)

        # 2. 2件目を対応中、3件目を対応完了にする
        with psycopg.connect(
            "dbname=inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    UPDATE "問い合わせ"
                    SET
                        "対応担当者" = %s,
                        "引き受け日時" = NOW()
                    WHERE "問い合わせ番号" = %s
                    ''',
                    ("J0001", inquiry_numbers[1]),
                )

                cur.execute(
                    '''
                    UPDATE "問い合わせ"
                    SET "対応完了日時" = NOW()
                    WHERE "問い合わせ番号" = %s
                    ''',
                    (inquiry_numbers[2],),
                )

        yield {
            state: number
            for (_, state), number in zip(
                test_cases, inquiry_numbers
            )
        }

    finally:
        # 3. テストで作成したデータを削除する
        with psycopg.connect(
            "dbname=inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                for inquiry_number in inquiry_numbers:
                    cur.execute(
                        '''
                        DELETE FROM "問い合わせ"
                        WHERE "問い合わせ番号" = %s
                        ''',
                        (inquiry_number,),
                    )


def test_search_inquiries_without_conditions():
    response = client.get("/api/inquiries")

    assert response.status_code == 200

    result = response.json()
    assert set(result.keys()) == {
        "items", "page", "page_size", "total"
    }
    assert result["page"] == 1
    assert result["page_size"] == 50
    assert result["total"] >= len(result["items"])

    # 受信日時の降順、同日時なら問い合わせ番号の降順
    items = result["items"]
    actual_order = [
        (item["受信日時"], item["問い合わせ番号"])
        for item in items
    ]
    assert actual_order == sorted(actual_order, reverse=True)


def test_search_inquiries_by_number(search_test_inquiries):
    inquiry_number = search_test_inquiries["pending"]

    response = client.get(
        "/api/inquiries",
        params={"問い合わせ番号": inquiry_number},
    )

    assert response.status_code == 200

    result = response.json()
    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["問い合わせ番号"] == inquiry_number


def test_search_inquiries_by_partial_subject(search_test_inquiries):
    response = client.get(
        "/api/inquiries",
        params={"件名": "検索APIテスト-引き受け待ち"},
    )

    assert response.status_code == 200

    result = response.json()
    assert result["total"] == 1
    assert result["items"][0]["件名"] == "検索APIテスト-引き受け待ち"


def test_search_inquiries_by_category(search_test_inquiries):
    response = client.get(
        "/api/inquiries",
        params={"問い合わせ分類": "分類A"},
    )

    assert response.status_code == 200

    result = response.json()
    assert result["total"] >= 3
    assert all(
        item["問い合わせ分類"] == "分類A"
        for item in result["items"]
    )


def test_search_inquiries_by_status(search_test_inquiries):
    expected_states = {
        "引き受け待ち": "pending",
        "対応中": "in_progress",
        "対応完了": "completed",
    }

    for status, state_key in expected_states.items():
        inquiry_number = search_test_inquiries[state_key]

        response = client.get(
            "/api/inquiries",
            params={"状態": status},
        )

        assert response.status_code == 200

        result = response.json()
        matching_items = [
            item for item in result["items"]
            if item["問い合わせ番号"] == inquiry_number
        ]

        assert len(matching_items) == 1
        assert matching_items[0]["状態"] == status


def test_search_inquiries_pagination(search_test_inquiries):
    params = {
        "件名": "検索APIテスト-",
        "page": 1,
        "page_size": 2,
    }

    response_page1 = client.get(
        "/api/inquiries",
        params=params,
    )

    assert response_page1.status_code == 200
    result_page1 = response_page1.json()

    assert result_page1["total"] == 3
    assert result_page1["page"] == 1
    assert result_page1["page_size"] == 2
    assert len(result_page1["items"]) == 2

    params["page"] = 2

    response_page2 = client.get(
        "/api/inquiries",
        params=params,
    )

    assert response_page2.status_code == 200
    result_page2 = response_page2.json()

    assert result_page2["total"] == 3
    assert result_page2["page"] == 2
    assert len(result_page2["items"]) == 1

    # 1ページ目と2ページ目に重複がないこと
    page1_numbers = {
        item["問い合わせ番号"]
        for item in result_page1["items"]
    }
    page2_numbers = {
        item["問い合わせ番号"]
        for item in result_page2["items"]
    }
    assert page1_numbers.isdisjoint(page2_numbers)


def test_search_inquiries_invalid_status():
    response = client.get(
        "/api/inquiries",
        params={"状態": "存在しない状態"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "状態の指定が不正です"


def test_search_inquiries_invalid_page():
    response = client.get(
        "/api/inquiries",
        params={"page": 0},
    )

    assert response.status_code == 422


@pytest.fixture
def detail_test_inquiries():
    """詳細取得API用の問い合わせ3件を作成し、終了後に削除する。"""
    inquiry_numbers = []

    test_cases = [
        ("詳細APIテスト-引き受け待ち", "pending"),
        ("詳細APIテスト-対応中", "in_progress"),
        ("詳細APIテスト-対応完了", "completed"),
    ]

    try:
        # 1. テスト用の問い合わせを3件登録する
        for title, state in test_cases:
            response = client.post(
                "/api/inquiries",
                json={
                    "問い合わせ職員番号": "T0001",
                    "受付担当者": "J0001",
                    "受付経路": "電話",
                    "問い合わせ分類": "分類A",
                    "件名": title,
                    "緊急度": 2,
                    "受付時の処理": 2,
                    "問い合わせ詳細": "詳細取得APIの自動テスト用",
                    "受信日時": None,
                },
            )

            assert response.status_code == 200, response.text

            inquiry_number = response.json()["問い合わせ番号"]
            inquiry_numbers.append(inquiry_number)

        # 2. 2件目を対応中、3件目を対応完了にする
        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    UPDATE "問い合わせ"
                    SET
                        "対応担当者" = %s,
                        "引き受け日時" = NOW()
                    WHERE "問い合わせ番号" = %s
                    ''',
                    ("J0001", inquiry_numbers[1]),
                )

                cur.execute(
                    '''
                    UPDATE "問い合わせ"
                    SET "対応完了日時" = NOW()
                    WHERE "問い合わせ番号" = %s
                    ''',
                    (inquiry_numbers[2],),
                )

        yield {
            state: number
            for (_, state), number in zip(test_cases, inquiry_numbers)
        }

    finally:
        # 3. テストで作成した問い合わせを削除する
        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                for inquiry_number in inquiry_numbers:
                    cur.execute(
                        '''
                        DELETE FROM "問い合わせ"
                        WHERE "問い合わせ番号" = %s
                        ''',
                        (inquiry_number,),
                    )


def test_get_inquiry_success(detail_test_inquiries):
    """存在する問い合わせの詳細を取得できる。"""
    inquiry_number = detail_test_inquiries["pending"]

    response = client.get(f"/api/inquiries/{inquiry_number}")

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["問い合わせ番号"] == inquiry_number
    assert result["問い合わせ職員番号"] == "T0001"
    assert result["問い合わせ分類"] == "分類A"
    assert result["件名"] == "詳細APIテスト-引き受け待ち"
    assert result["問い合わせ詳細"] == "詳細取得APIの自動テスト用"
    assert result["状態"] == "引き受け待ち"


def test_get_inquiry_unknown_number():
    """存在しない問い合わせ番号では404になる。"""
    response = client.get("/api/inquiries/999999999")

    assert response.status_code == 404


def test_get_inquiry_status(detail_test_inquiries):
    """日時に応じた問い合わせ状態を取得できる。"""
    expected_statuses = {
        "pending": "引き受け待ち",
        "in_progress": "対応中",
        "completed": "対応完了",
    }

    for state, expected_status in expected_statuses.items():
        inquiry_number = detail_test_inquiries[state]

        response = client.get(f"/api/inquiries/{inquiry_number}")

        assert response.status_code == 200
        assert response.json()["状態"] == expected_status



