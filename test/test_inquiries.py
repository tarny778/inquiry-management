import os

os.environ["DATABASE_NAME"] = "inquiry_management_test"

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