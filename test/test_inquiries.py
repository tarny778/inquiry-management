import os

os.environ["DATABASE_NAME"] = "inquiry_management_test"

import psycopg
from fastapi.testclient import TestClient
from main import app
import main
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


def build_inquiry_update_payload(
    inquiry_number,
    editor_staff_number="J0001",
    **overrides,
):
    """詳細取得APIの値を使って編集リクエストを作る。"""
    response = client.get(f"/api/inquiries/{inquiry_number}")
    assert response.status_code == 200, response.text

    inquiry = response.json()

    payload = {
        "編集者職員番号": editor_staff_number,
        "問い合わせ当時の所属": inquiry["問い合わせ当時の所属"],
        "受付経路": inquiry["受付経路"],
        "問い合わせ分類": inquiry["問い合わせ分類"],
        "件名": inquiry["件名"],
        "緊急度": inquiry["緊急度"],
        "受付時の処理": inquiry["受付時の処理"],
        "問い合わせ詳細": inquiry["問い合わせ詳細"],
        "受信日時": inquiry["受信日時"],
    }

    payload.update(overrides)
    return payload


def test_update_pending_inquiry_success(pending_inquiry_number):
    """受付担当者本人は未引き受けの問い合わせを編集できる。"""
    payload = build_inquiry_update_payload(
        pending_inquiry_number,
        件名="編集APIテスト-件名変更",
        問い合わせ詳細="編集APIで変更した詳細",
    )

    response = client.put(
        f"/api/inquiries/{pending_inquiry_number}",
        json=payload,
    )

    assert response.status_code == 200, response.text

    result = response.json()
    assert result["問い合わせ番号"] == pending_inquiry_number

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "件名", "問い合わせ詳細",
                       "引き受け日時", "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry_number,),
            )
            inquiry = cur.fetchone()

    assert inquiry is not None
    assert inquiry[0] == "編集APIテスト-件名変更"
    assert inquiry[1] == "編集APIで変更した詳細"
    assert inquiry[2] is None
    assert inquiry[3] is None


def test_update_pending_inquiry_to_immediate_resolution(
    pending_inquiry_number,
):
    """要調査から即時解決に変更すると対応完了日時が設定される。"""
    payload = build_inquiry_update_payload(
        pending_inquiry_number,
        受付時の処理=1,
    )

    response = client.put(
        f"/api/inquiries/{pending_inquiry_number}",
        json=payload,
    )

    assert response.status_code == 200, response.text

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "受付時の処理", "引き受け日時",
                       "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry_number,),
            )
            inquiry = cur.fetchone()

    assert inquiry is not None
    assert inquiry[0] == 1
    assert inquiry[1] is None
    assert inquiry[2] is not None


def test_update_in_progress_inquiry_success(
    pending_inquiry_number,
):
    """対応担当者本人は対応中の問い合わせを編集できる。"""
    # J0002を対応担当者として設定する
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

    payload = build_inquiry_update_payload(
        pending_inquiry_number,
        editor_staff_number="J0002",
        件名="編集APIテスト-対応中の編集",
    )

    response = client.put(
        f"/api/inquiries/{pending_inquiry_number}",
        json=payload,
    )

    assert response.status_code == 200, response.text

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "件名", "受付時の処理",
                       "引き受け日時", "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry_number,),
            )
            inquiry = cur.fetchone()

    assert inquiry is not None
    assert inquiry[0] == "編集APIテスト-対応中の編集"
    assert inquiry[1] == 2
    assert inquiry[2] is not None
    assert inquiry[3] is None


def test_update_in_progress_cannot_change_initial_handling(
    pending_inquiry_number,
):
    """対応中に受付時の処理を変更すると、更新全体が拒否される。"""
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

    payload = build_inquiry_update_payload(
        pending_inquiry_number,
        editor_staff_number="J0002",
        件名="変更されてはいけない件名",
        受付時の処理=1,
    )

    response = client.put(
        f"/api/inquiries/{pending_inquiry_number}",
        json=payload,
    )

    assert response.status_code == 409

    # 件名も受付時の処理も変更されていないことを確認する
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "件名", "受付時の処理", "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry_number,),
            )
            inquiry = cur.fetchone()

    assert inquiry is not None
    assert inquiry[0] == "引き受けAPIテスト用問い合わせ"
    assert inquiry[1] == 2
    assert inquiry[2] is None


def test_update_inquiry_by_unauthorized_staff(
    pending_inquiry_number,
):
    """受付担当者でも対応担当者でもない職員は編集できない。"""
    payload = build_inquiry_update_payload(
        pending_inquiry_number,
        editor_staff_number="J0002",
        件名="変更されてはいけない件名",
    )

    response = client.put(
        f"/api/inquiries/{pending_inquiry_number}",
        json=payload,
    )

    assert response.status_code == 403

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "件名"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry_number,),
            )
            inquiry = cur.fetchone()

    assert inquiry is not None
    assert inquiry[0] == "引き受けAPIテスト用問い合わせ"


def test_update_completed_inquiry_rejected(
    pending_inquiry_number,
):
    """対応完了済みの問い合わせは編集できない。"""
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

    payload = build_inquiry_update_payload(
        pending_inquiry_number,
        件名="変更されてはいけない件名",
    )

    response = client.put(
        f"/api/inquiries/{pending_inquiry_number}",
        json=payload,
    )

    assert response.status_code == 409

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "件名", "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                ''',
                (pending_inquiry_number,),
            )
            inquiry = cur.fetchone()

    assert inquiry is not None
    assert inquiry[0] == "引き受けAPIテスト用問い合わせ"
    assert inquiry[1] is not None


def test_update_inquiry_unknown_number(pending_inquiry_number):
    """存在しない問い合わせ番号では404になる。"""
    payload = build_inquiry_update_payload(
        pending_inquiry_number,
    )

    response = client.put(
        "/api/inquiries/999999999",
        json=payload,
    )

    assert response.status_code == 404


def create_pending_inquiry_for_bulk_test():
    """一括引き受けテスト用の問い合わせを1件作成する。"""
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
            "受付担当者": "J0001",
            "受付経路": "電話",
            "問い合わせ分類": "分類A",
            "件名": "一括引き受けAPIテスト用問い合わせ",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "一括引き受けテスト用データ",
            "受信日時": None,
        },
    )

    assert response.status_code == 200, response.text
    return response.json()["問い合わせ番号"]


def delete_inquiries_for_bulk_test(inquiry_numbers):
    """一括引き受けテストで作成した問い合わせを削除する。"""
    if not inquiry_numbers:
        return

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                DELETE FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                ''',
                (inquiry_numbers,),
            )


def test_bulk_accept_inquiries_success(pending_inquiry_number):
    """未引き受けの問い合わせを複数件まとめて引き受けられる。"""
    second_number = create_pending_inquiry_for_bulk_test()
    inquiry_numbers = [pending_inquiry_number, second_number]

    try:
        response = client.post(
            "/api/inquiries/bulk-accept",
            json={
                "対応担当者": "J0001",
                "問い合わせ番号一覧": inquiry_numbers,
            },
        )

        assert response.status_code == 200, response.text

        result = response.json()
        assert result["対応担当者"] == "J0001"
        assert sorted(result["問い合わせ番号一覧"]) == sorted(
            inquiry_numbers
        )

        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    SELECT "問い合わせ番号", "対応担当者",
                           "引き受け日時", "対応完了日時"
                    FROM "問い合わせ"
                    WHERE "問い合わせ番号" = ANY(%s)
                    ''',
                    (inquiry_numbers,),
                )
                inquiries = cur.fetchall()

        assert len(inquiries) == 2

        for inquiry in inquiries:
            assert inquiry[1] == "J0001"
            assert inquiry[2] is not None
            assert inquiry[3] is None

    finally:
        delete_inquiries_for_bulk_test([second_number])


def test_bulk_accept_rejects_all_if_one_already_accepted(
    pending_inquiry_number,
):
    """1件でも引き受け済みなら、全件を更新しない。"""
    second_number = create_pending_inquiry_for_bulk_test()
    inquiry_numbers = [pending_inquiry_number, second_number]

    try:
        # 2件目を先に引き受け済みにする
        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    UPDATE "問い合わせ"
                    SET "対応担当者" = %s,
                        "引き受け日時" = NOW()
                    WHERE "問い合わせ番号" = %s
                    ''',
                    ("J0002", second_number),
                )

        response = client.post(
            "/api/inquiries/bulk-accept",
            json={
                "対応担当者": "J0001",
                "問い合わせ番号一覧": inquiry_numbers,
            },
        )

        assert response.status_code == 409

        # 1件目も更新されていないことを確認
        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    SELECT
                        "問い合わせ番号",
                        "対応担当者",
                        "引き受け日時"
                    FROM "問い合わせ"
                    WHERE "問い合わせ番号" = ANY(%s)
                    ''',
                    (inquiry_numbers,),
                )
                inquiries = cur.fetchall()

        assert len(inquiries) == 2

        # 問い合わせ番号をキーにして結果を対応づける
        inquiry_by_number = {
            number: (handler, accepted_at)
            for number, handler, accepted_at in inquiries
        }

        # 1件目は未引き受けのまま
        assert inquiry_by_number[pending_inquiry_number] == (None, None)

        # 2件目は、事前に設定した引き受け状態のまま
        assert inquiry_by_number[second_number][0] == "J0002"
        assert inquiry_by_number[second_number][1] is not None

    finally:
        delete_inquiries_for_bulk_test([second_number])



def test_bulk_accept_rejects_all_if_number_missing(
    pending_inquiry_number,
):
    """存在しない問い合わせ番号が含まれていたら全件更新しない。"""
    response = client.post(
        "/api/inquiries/bulk-accept",
        json={
            "対応担当者": "J0001",
            "問い合わせ番号一覧": [
                pending_inquiry_number,
                999999999,
            ],
        },
    )

    assert response.status_code == 404

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
    assert inquiry[0] is None
    assert inquiry[1] is None


def test_bulk_accept_rejects_duplicate_numbers(
    pending_inquiry_number,
):
    """問い合わせ番号の重複を拒否し、DBを変更しない。"""
    response = client.post(
        "/api/inquiries/bulk-accept",
        json={
            "対応担当者": "J0001",
            "問い合わせ番号一覧": [
                pending_inquiry_number,
                pending_inquiry_number,
            ],
        },
    )

    assert response.status_code == 400

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
    assert inquiry[0] is None
    assert inquiry[1] is None


# =========================================================
# 対応完了APIのテスト
# =========================================================

@pytest.fixture
def completion_test_inquiries():
    """未引き受け・対応中・対応完了の問い合わせを用意する。"""
    inquiry_numbers = []

    for _ in range(3):
        response = client.post(
            "/api/inquiries",
            json={
                "問い合わせ職員番号": "T0001",
                "受付担当者": "J0001",
                "受付経路": "電話",
                "問い合わせ分類": "分類A",
                "件名": "テスト問い合わせ",
                "緊急度": 2,
                "受付時の処理": 2,
                "受信日時": None,
            },
        )
        assert response.status_code == 200
        inquiry_numbers.append(response.json()["問い合わせ番号"])

    pending_number, in_progress_number, completed_number = inquiry_numbers

    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            # 対応中の問い合わせを作成
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = %s,
                    "引き受け日時" = NOW(),
                    "対応完了日時" = NULL
                WHERE "問い合わせ番号" = %s
                """,
                ("J0001", in_progress_number),
            )

            # 対応完了済みの問い合わせを作成
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = %s,
                    "引き受け日時" = NOW(),
                    "対応完了日時" = NOW()
                WHERE "問い合わせ番号" = %s
                """,
                ("J0001", completed_number),
            )

    yield {
        "pending": pending_number,
        "in_progress": in_progress_number,
        "completed": completed_number,
    }

    # テストデータを削除
    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            for inquiry_number in inquiry_numbers:
                cur.execute(
                    """
                    DELETE FROM "問い合わせ"
                    WHERE "問い合わせ番号" = %s
                    """,
                    (inquiry_number,),
                )

@pytest.fixture
def inquiry_problem_investigation_factory():
    """問い合わせ問題調査を作成するテスト用ファクトリ。"""
    created_investigation_ids = []
    created_relation_ids = []

    def create(inquiry_number, state):
        with psycopg.connect(
            dbname="inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                # 1. 問題調査を作成
                cur.execute(
                    """
                    INSERT INTO "問題調査" (
                        "問題調査の名称や仮説"
                    )
                    VALUES (%s)
                    RETURNING "問題調査番号"
                    """,
                    ("テスト用の調査",),
                )
                investigation_id = cur.fetchone()[0]
                created_investigation_ids.append(investigation_id)

                # 2. 問い合わせ問題調査を作成
                cur.execute(
                    """
                    INSERT INTO "問い合わせ問題調査" (
                        "問題調査番号",
                        "問い合わせ番号",
                        "問い合わせ問題調査状態"
                    )
                    VALUES (%s, %s, %s)
                    RETURNING "問い合わせ問題調査番号"
                    """,
                    (
                        investigation_id,
                        inquiry_number,
                        state,
                    ),
                )
                relation_id = cur.fetchone()[0]
                created_relation_ids.append(relation_id)

        return relation_id

    yield create

    # 外部キー制約があるため、関連レコードから先に削除
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            for relation_id in created_relation_ids:
                cur.execute(
                    """
                    DELETE FROM "問い合わせ問題調査"
                    WHERE "問い合わせ問題調査番号" = %s
                    """,
                    (relation_id,),
                )

            for investigation_id in created_investigation_ids:
                cur.execute(
                    """
                    DELETE FROM "問題調査"
                    WHERE "問題調査番号" = %s
                    """,
                    (investigation_id,),
                )

def test_complete_inquiry_success(
    completion_test_inquiries,
    monkeypatch,
):
    """対応担当者本人は対応完了できる。"""
    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0001",
            氏名="情シス太郎",
            所属="情報システム課",
        ),
    )

    inquiry_number = completion_test_inquiries["in_progress"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/complete"
    )

    assert response.status_code == 200
    assert response.json()["問い合わせ番号"] == inquiry_number
    assert response.json()["message"] == "問い合わせを対応完了しました。"

    # DBに対応完了日時が記録されたことを確認
    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )
            row = cur.fetchone()

    assert row is not None
    assert row[0] is not None


def test_complete_inquiry_forbidden_for_other_user(
    completion_test_inquiries,
    monkeypatch,
):
    """対応担当者以外は対応完了できない。"""
    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0002",
            氏名="情シス次郎",
            所属="情報システム課",
        ),
    )

    inquiry_number = completion_test_inquiries["in_progress"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/complete"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "対応担当者本人だけが対応完了できます。"
    )


def test_complete_inquiry_conflict_when_not_accepted(
    completion_test_inquiries,
):
    """未引き受けの問い合わせは対応完了できない。"""
    inquiry_number = completion_test_inquiries["pending"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/complete"
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "未引き受けの問い合わせは対応完了できません。"
    )


def test_complete_inquiry_conflict_when_already_completed(
    completion_test_inquiries,
):
    """対応完了済みの問い合わせは再度完了できない。"""
    inquiry_number = completion_test_inquiries["completed"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/complete"
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "すでに対応完了した問い合わせです。"
    )


def test_complete_inquiry_not_found():
    """存在しない問い合わせ番号では404になる。"""
    response = client.post(
        "/api/inquiries/999999999/complete"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "指定された問い合わせが存在しません。"
    )

@pytest.mark.parametrize(
    ("state", "expected_status"),
    [
        (1, 409),  # 調査中：拒否
        (2, 200),  # 断念：許可
        (3, 409),  # リアクション待ち：拒否
        (4, 200),  # OK：許可
        (5, 200),  # NG・移行済み：許可
    ],
)
def test_complete_inquiry_by_inquiry_problem_investigation_state(
    monkeypatch,
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
    state,
    expected_status,
):
    """関連する問い合わせ問題調査の状態によって完了可否が決まる。"""
    inquiry_number = completion_test_inquiries["in_progress"]

    # 対応担当者を J0001 に設定
    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: type(
            "TestUser",
            (),
            {"職員番号": "J0001"},
        )(),
    )

    # 対象の問い合わせに指定状態の調査を紐づける
    inquiry_problem_investigation_factory(
        inquiry_number,
        state,
    )

    response = client.post(
        f"/api/inquiries/{inquiry_number}/complete"
    )

    assert response.status_code == expected_status

@pytest.mark.parametrize(
    "unfinished_state",
    [1, 3],
)
def test_complete_inquiry_rejected_when_any_investigation_is_unfinished(
    monkeypatch,
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
    unfinished_state,
):
    """完了可能な調査と未完了の調査が混在しても、完了を拒否する。"""
    inquiry_number = completion_test_inquiries["in_progress"]

    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: type(
            "TestUser",
            (),
            {"職員番号": "J0001"},
        )(),
    )

    # OKになった調査
    inquiry_problem_investigation_factory(
        inquiry_number,
        4,
    )

    # 調査中、またはリアクション待ちの調査
    inquiry_problem_investigation_factory(
        inquiry_number,
        unfinished_state,
    )

    response = client.post(
        f"/api/inquiries/{inquiry_number}/complete"
    )

    assert response.status_code == 409


@pytest.fixture
def bulk_completion_test_inquiries():
    """一括対応完了APIのテスト用問い合わせを用意する。"""
    inquiry_numbers = []

    # 問い合わせを4件登録
    for _ in range(4):
        response = client.post(
            "/api/inquiries",
            json={
                "問い合わせ職員番号": "T0001",
                "受付担当者": "J0001",
                "受付経路": "電話",
                "問い合わせ分類": "分類A",
                "件名": "一括対応完了テスト",
                "緊急度": 2,
                "受付時の処理": 2,
                "受信日時": None,
            },
        )
        assert response.status_code == 200
        inquiry_numbers.append(
            response.json()["問い合わせ番号"]
        )

    pending_number = inquiry_numbers[0]
    in_progress_numbers = inquiry_numbers[1:3]
    completed_number = inquiry_numbers[3]

    # 2件を対応中、1件を対応完了にする
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = %s,
                    "引き受け日時" = NOW(),
                    "対応完了日時" = NULL
                WHERE "問い合わせ番号" = ANY(%s)
                """,
                ("J0001", in_progress_numbers),
            )

            cur.execute(
                """
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = %s,
                    "引き受け日時" = NOW(),
                    "対応完了日時" = NOW()
                WHERE "問い合わせ番号" = %s
                """,
                ("J0001", completed_number),
            )

    yield {
        "pending": pending_number,
        "in_progress": in_progress_numbers,
        "completed": completed_number,
    }

    # テストデータを削除
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            for inquiry_number in inquiry_numbers:
                cur.execute(
                    """
                    DELETE FROM "問い合わせ"
                    WHERE "問い合わせ番号" = %s
                    """,
                    (inquiry_number,),
                )


def test_bulk_complete_inquiries_success(
    bulk_completion_test_inquiries,
    monkeypatch,
):
    """対応中の問い合わせ2件を一括で対応完了できる。"""

    # 操作者をJ0001に設定
    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0001",
            氏名="情シス太郎",
            所属="情報システム課",
        ),
    )

    inquiry_numbers = (
        bulk_completion_test_inquiries["in_progress"]
    )

    # 一括対応完了APIを呼び出す
    response = client.post(
        "/api/inquiries/bulk-complete",
        json={
            "問い合わせ番号一覧": inquiry_numbers,
        },
    )

    # HTTPステータスとレスポンスを確認
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["問い合わせ番号一覧"] == sorted(
        inquiry_numbers
    )

    # DB上でも2件とも対応完了になったことを確認
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    "問い合わせ番号",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                """,
                (inquiry_numbers,),
            )
            rows = cur.fetchall()

    assert len(rows) == 2
    assert all(
        completed_at is not None
        for _, completed_at in rows
    )

# =========================================================
# 一括対応完了APIの異常系テスト
# =========================================================


def test_bulk_complete_forbidden_for_other_handler(
    bulk_completion_test_inquiries,
    monkeypatch,
):
    """別の対応担当者の問い合わせが含まれる場合、全件更新しない。"""

    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0001",
            氏名="情シス太郎",
            所属="情報システム課",
        ),
    )

    inquiry_numbers = (
        bulk_completion_test_inquiries["in_progress"]
    )
    unauthorized_number = inquiry_numbers[1]

    # 2件目だけ別の職員を対応担当者にする
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET "対応担当者" = %s
                WHERE "問い合わせ番号" = %s
                """,
                ("J0002", unauthorized_number),
            )

    response = client.post(
        "/api/inquiries/bulk-complete",
        json={"問い合わせ番号一覧": inquiry_numbers},
    )

    assert response.status_code == 403
    assert unauthorized_number in response.json()["detail"][
        "問い合わせ番号一覧"
    ]

    # 正常な問い合わせも含め、全件が未完了のままであること
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                """,
                (inquiry_numbers,),
            )
            rows = cur.fetchall()

    assert len(rows) == 2
    assert all(row[0] is None for row in rows)


def test_bulk_complete_conflict_when_already_completed(
    bulk_completion_test_inquiries,
    monkeypatch,
):
    """対応完了済みの問い合わせが混ざる場合、全件更新しない。"""

    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0001",
            氏名="情シス太郎",
            所属="情報システム課",
        ),
    )

    inquiry_numbers = (
        bulk_completion_test_inquiries["in_progress"]
    )
    completed_number = (
        bulk_completion_test_inquiries["completed"]
    )
    requested_numbers = inquiry_numbers + [completed_number]

    response = client.post(
        "/api/inquiries/bulk-complete",
        json={"問い合わせ番号一覧": requested_numbers},
    )

    assert response.status_code == 409
    assert completed_number in response.json()["detail"][
        "問い合わせ番号一覧"
    ]

    # 対応中だった2件が更新されていないこと
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                """,
                (inquiry_numbers,),
            )
            rows = cur.fetchall()

    assert len(rows) == 2
    assert all(row[0] is None for row in rows)


def test_bulk_complete_conflict_when_not_accepted(
    bulk_completion_test_inquiries,
    monkeypatch,
):
    """引き受け待ちの問い合わせが混ざる場合、全件更新しない。"""

    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0001",
            氏名="情シス太郎",
            所属="情報システム課",
        ),
    )

    inquiry_numbers = (
        bulk_completion_test_inquiries["in_progress"]
    )
    pending_number = bulk_completion_test_inquiries["pending"]
    requested_numbers = inquiry_numbers + [pending_number]

    response = client.post(
        "/api/inquiries/bulk-complete",
        json={"問い合わせ番号一覧": requested_numbers},
    )

    assert response.status_code == 409
    assert pending_number in response.json()["detail"][
        "問い合わせ番号一覧"
    ]

    # 対応中だった2件が更新されていないこと
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                """,
                (inquiry_numbers,),
            )
            rows = cur.fetchall()

    assert len(rows) == 2
    assert all(row[0] is None for row in rows)


@pytest.mark.parametrize(
    "investigation_state",
    [1, 3],
)
def test_bulk_complete_conflict_when_unfinished_investigation_exists(
    bulk_completion_test_inquiries,
    inquiry_problem_investigation_factory,
    monkeypatch,
    investigation_state,
):
    """調査中またはリアクション待ちの調査がある場合、全件更新しない。"""

    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0001",
            氏名="情シス太郎",
            所属="情報システム課",
        ),
    )

    inquiry_numbers = (
        bulk_completion_test_inquiries["in_progress"]
    )

    # 2件目に未完了の調査を関連付ける
    inquiry_problem_investigation_factory(
        inquiry_numbers[1],
        investigation_state,
    )

    response = client.post(
        "/api/inquiries/bulk-complete",
        json={"問い合わせ番号一覧": inquiry_numbers},
    )

    assert response.status_code == 409
    assert inquiry_numbers[1] in response.json()["detail"][
        "問い合わせ番号一覧"
    ]

    # 1件目も含め、両方とも未完了のままであること
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                """,
                (inquiry_numbers,),
            )
            rows = cur.fetchall()

    assert len(rows) == 2
    assert all(row[0] is None for row in rows)


def test_bulk_complete_bad_request_when_duplicate_numbers(
    bulk_completion_test_inquiries,
    monkeypatch,
):
    """問い合わせ番号が重複している場合、400を返す。"""

    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0001",
            氏名="情シス太郎",
            所属="情報システム課",
        ),
    )

    inquiry_number = (
        bulk_completion_test_inquiries["in_progress"][0]
    )

    response = client.post(
        "/api/inquiries/bulk-complete",
        json={
            "問い合わせ番号一覧": [
                inquiry_number,
                inquiry_number,
            ]
        },
    )

    assert response.status_code == 400

    # 対象が更新されていないこと
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )
            row = cur.fetchone()

    assert row is not None
    assert row[0] is None


def test_bulk_complete_not_found_when_number_does_not_exist(
    bulk_completion_test_inquiries,
    monkeypatch,
):
    """存在しない問い合わせ番号が含まれる場合、404を返す。"""

    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0001",
            氏名="情シス太郎",
            所属="情報システム課",
        ),
    )

    inquiry_numbers = (
        bulk_completion_test_inquiries["in_progress"]
    )
    nonexistent_number = 999999999
    requested_numbers = inquiry_numbers + [nonexistent_number]

    response = client.post(
        "/api/inquiries/bulk-complete",
        json={"問い合わせ番号一覧": requested_numbers},
    )

    assert response.status_code == 404
    assert nonexistent_number in response.json()["detail"][
        "問い合わせ番号一覧"
    ]

    # 存在する2件が更新されていないこと
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = ANY(%s)
                """,
                (inquiry_numbers,),
            )
            rows = cur.fetchall()

    assert len(rows) == 2
    assert all(row[0] is None for row in rows)


def test_bulk_complete_bad_request_when_number_list_is_empty(
    monkeypatch,
):
    """問い合わせ番号一覧が空の場合、422を返す。"""

    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号="J0001",
            氏名="情シス太郎",
            所属="情報システム課",
        ),
    )

    response = client.post(
        "/api/inquiries/bulk-complete",
        json={"問い合わせ番号一覧": []},
    )

    assert response.status_code == 422

