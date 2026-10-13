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
