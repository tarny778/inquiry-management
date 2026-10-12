import os

os.environ["DATABASE_NAME"] = "inquiry_management_test"

import psycopg
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_inquiry_invalid_urgency():
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
            "受付担当者": "情シス太郎",
            "受付経路": "電話",
            "問い合わせ分類": "PC",
            "件名": "緊急度の異常系テスト",
            "緊急度": 4,
            "受付時の処理": 2,
            "問い合わせ詳細": "自動テストです",
            "対応担当者": None,
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
            "受付担当者": "情シス太郎",
            "受付経路": "電話",
            "問い合わせ分類": "PC",
            "件名": "存在しない職員のテスト",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "自動テストです",
            "対応担当者": None,
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
            "受付担当者": "一般職員太郎",
            "受付経路": "電話",
            "問い合わせ分類": "PC",
            "件名": "受付担当者の異常系テスト",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "自動テストです",
            "対応担当者": None,
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
                "受付担当者": "情シス太郎",
                "受付経路": "電話",
                "問い合わせ分類": "PC",
                "件名": "正常系テスト用問い合わせ",
                "緊急度": 2,
                "受付時の処理": 2,
                "問い合わせ詳細": "自動テストで登録したデータです",
                "対応担当者": None,
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
        assert inquiry[2] == "情シス太郎"
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
