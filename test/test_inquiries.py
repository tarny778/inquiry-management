import os

os.environ["DATABASE_NAME"] = "inquiry_management_test"

import psycopg
from fastapi.testclient import TestClient
from main import app
import main
import pytest


client = TestClient(app)

# ここからfixture

@pytest.fixture
def pending_inquiry_number():
    """テスト用の未引き受け問い合わせを作成し、終了後に削除する。"""
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
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

@pytest.fixture
def completion_test_inquiries():
    """未引き受け・対応中・対応完了の問い合わせを用意する。"""
    inquiry_numbers = []

    for _ in range(3):
        response = client.post(
            "/api/inquiries",
            json={
                "問い合わせ職員番号": "T0001",
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
            for investigation_id in created_investigation_ids:
                cur.execute(
                    """
                    DELETE FROM "問い合わせ問題調査"
                    WHERE "問題調査番号" = %s
                    """,
                    (investigation_id,),
                )

            for investigation_id in created_investigation_ids:
                cur.execute(
                    """
                    DELETE FROM "問題調査"
                    WHERE "問題調査番号" = %s
                    """,
                    (investigation_id,),
                )

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

@pytest.fixture
def unlinked_investigation_factory():
    """関連付け前の問題調査を作成し、テスト後に削除する。"""
    created_investigation_numbers = []

    def create_investigation(state=1):
        with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO "問題調査" (
                        "問題調査の名称や仮説",
                        "問題調査状態"
                    )
                    VALUES (%s, %s)
                    RETURNING "問題調査番号"
                    """,
                    ("テスト用の問題調査", state),
                )
                investigation_number = cur.fetchone()[0]

        created_investigation_numbers.append(investigation_number)
        return investigation_number

    yield create_investigation

    # APIが作成した関連レコードを先に削除する
    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            for investigation_number in created_investigation_numbers:
                cur.execute(
                    """
                    DELETE FROM "問い合わせ問題調査"
                    WHERE "問題調査番号" = %s
                    """,
                    (investigation_number,),
                )

            for investigation_number in created_investigation_numbers:
                cur.execute(
                    """
                    DELETE FROM "問題調査"
                    WHERE "問題調査番号" = %s
                    """,
                    (investigation_number,),
                )

ORIGINAL_GET_CURRENT_USER = main.get_current_user


@pytest.fixture(autouse=True)
def _default_test_user(monkeypatch):
    """各テストの初期操作者を設定する。"""
    user = main.CurrentUser(
        職員番号="J0001",
        氏名="テスト職員",
        所属="情報システム課",
    )
    monkeypatch.setitem(
        app.dependency_overrides,
        ORIGINAL_GET_CURRENT_USER,
        lambda: user,
    )


def _set_test_user(monkeypatch, staff_number="J0001"):
    """テストで操作者を切り替える。"""
    user = main.CurrentUser(
        職員番号=staff_number,
        氏名="テスト職員",
        所属="情報システム課",
    )
    monkeypatch.setitem(
        app.dependency_overrides,
        ORIGINAL_GET_CURRENT_USER,
        lambda: user,
    )

def _make_second_in_progress_inquiry(completion_test_inquiries):
    """引き受け待ちのテスト問い合わせを、対応中に変更する。"""
    inquiry_number = completion_test_inquiries["pending"]

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = 'J0001',
                    "引き受け日時" = CURRENT_TIMESTAMP,
                    "対応完了日時" = NULL
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )

    return inquiry_number


@pytest.fixture
def bulk_created_investigation_cleanup():
    """一括APIのテストで作成した問題調査を後片付けする。"""
    investigation_numbers = []

    def register(investigation_number):
        investigation_numbers.append(investigation_number)

    yield register

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            for investigation_number in investigation_numbers:
                cur.execute(
                    """
                    DELETE FROM "問い合わせ問題調査"
                    WHERE "問題調査番号" = %s
                    """,
                    (investigation_number,),
                )

            for investigation_number in investigation_numbers:
                cur.execute(
                    """
                    DELETE FROM "問題調査"
                    WHERE "問題調査番号" = %s
                    """,
                    (investigation_number,),
                )

@pytest.fixture
def detail_test_investigation_links(detail_test_inquiries):
    """詳細取得API用に、問題調査との関連付けを作成する。"""
    inquiry_number = detail_test_inquiries["pending"]
    investigation_numbers = []

    try:
        with psycopg.connect(
            "dbname=inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                # 問題調査を2件作成
                for name in [
                    "詳細APIテスト用調査A",
                    "詳細APIテスト用調査B",
                ]:
                    cur.execute(
                        '''
                        INSERT INTO "問題調査" (
                            "問題調査の名称や仮説"
                        )
                        VALUES (%s)
                        RETURNING "問題調査番号"
                        ''',
                        (name,),
                    )
                    investigation_number = cur.fetchone()[0]
                    investigation_numbers.append(
                        investigation_number
                    )

                    # 問い合わせと問題調査を関連付ける
                    cur.execute(
                        '''
                        INSERT INTO "問い合わせ問題調査" (
                            "問題調査番号",
                            "問い合わせ番号"
                        )
                        VALUES (%s, %s)
                        ''',
                        (
                            investigation_number,
                            inquiry_number,
                        ),
                    )

        yield {
            "問い合わせ番号": inquiry_number,
            "問題調査番号一覧": investigation_numbers,
        }

    finally:
        # 関連レコードを先に削除し、その後に問題調査を削除
        with psycopg.connect(
            "dbname=inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    DELETE FROM "問い合わせ問題調査"
                    WHERE "問い合わせ番号" = %s
                      AND "問題調査番号" = ANY(%s)
                    ''',
                    (
                        inquiry_number,
                        investigation_numbers,
                    ),
                )

                cur.execute(
                    '''
                    DELETE FROM "問題調査"
                    WHERE "問題調査番号" = ANY(%s)
                    ''',
                    (investigation_numbers,),
                )

#新規作成テスト
def test_create_inquiry_invalid_urgency(monkeypatch):
    _set_test_user(monkeypatch, "J0001")
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
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

def test_create_inquiry_unknown_staff(monkeypatch):
    _set_test_user(monkeypatch, "J0001")
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T9999",
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
        "指定された問い合わせ職員は登録されていません"
    )


def test_create_inquiry_invalid_receptionist(monkeypatch):
    _set_test_user(monkeypatch, "T0001")
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
            "受付経路": "電話",
            "問い合わせ分類": "分類A",
            "件名": "受付担当者の異常系テスト",
            "緊急度": 2,
            "受付時の処理": 2,
            "問い合わせ詳細": "自動テストです",
            "受信日時": None,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "操作者が情シス職員として登録されていません"
    )


def test_create_inquiry_success(monkeypatch):
    inquiry_number = None
    _set_test_user(monkeypatch, "J0001")
    try:
        response = client.post(
            "/api/inquiries",
            json={
                "問い合わせ職員番号": "T0001",
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


#個別引き受けテスト
def test_accept_inquiry_success(pending_inquiry_number,monkeypatch):
    _set_test_user(monkeypatch, "J0001")
    response = client.post(
        f"/api/inquiries/{pending_inquiry_number}/accept",
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


def test_accept_inquiry_unknown_number(monkeypatch):
    _set_test_user(monkeypatch, "J0001")
    response = client.post(
        "/api/inquiries/999999999/accept",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "指定された問い合わせが見つかりません。"
    )


def test_accept_inquiry_invalid_staff(pending_inquiry_number,monkeypatch):
    _set_test_user(monkeypatch, "T0001")

    # 操作前の状態を取得
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
            before = cur.fetchone()

    response = client.post(
        f"/api/inquiries/{pending_inquiry_number}/accept",
    )

    # 操作後の状態を取得
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
            after = cur.fetchone()

    assert after == before

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "操作者が情シス職員として登録されていません"
    )


def test_accept_already_accepted_inquiry(pending_inquiry_number,monkeypatch):
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
    _set_test_user(monkeypatch, "J0001")
    response = client.post(
        f"/api/inquiries/{pending_inquiry_number}/accept",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "この問い合わせは引き受けできない状態です"
    )


def test_accept_completed_inquiry(pending_inquiry_number,monkeypatch):
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

    _set_test_user(monkeypatch, "J0001")
    response = client.post(
        f"/api/inquiries/{pending_inquiry_number}/accept",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "この問い合わせは引き受けできない状態です"
    )

#一括引き受けテスト
def create_pending_inquiry_for_bulk_test():
    """一括引き受けテスト用の問い合わせを1件作成する。"""
    response = client.post(
        "/api/inquiries",
        json={
            "問い合わせ職員番号": "T0001",
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


def test_bulk_accept_inquiries_success(monkeypatch,pending_inquiry_number):
    """未引き受けの問い合わせを複数件まとめて引き受けられる。"""
    second_number = create_pending_inquiry_for_bulk_test()
    inquiry_numbers = [pending_inquiry_number, second_number]
    _set_test_user(monkeypatch, "J0001")
    try:
        response = client.post(
            "/api/inquiries/bulk-accept",
            json={
                "問い合わせ番号一覧": inquiry_numbers
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


def test_bulk_accept_rejects_all_if_one_already_accepted(monkeypatch,
    pending_inquiry_number,
):
    """1件でも引き受け済みなら、全件を更新しない。"""
    second_number = create_pending_inquiry_for_bulk_test()
    inquiry_numbers = [pending_inquiry_number, second_number]
    _set_test_user(monkeypatch, "J0001")

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
                "問い合わせ番号一覧": inquiry_numbers
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



def test_bulk_accept_rejects_all_if_number_missing(monkeypatch,
    pending_inquiry_number,
):
    """存在しない問い合わせ番号が含まれていたら全件更新しない。"""
    _set_test_user(monkeypatch, "J0001")
    response = client.post(
        "/api/inquiries/bulk-accept",
        json={
            "問い合わせ番号一覧": [
                pending_inquiry_number,
                999999999,
            ]
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


def test_bulk_accept_rejects_duplicate_numbers(monkeypatch,
    pending_inquiry_number,
):
    """問い合わせ番号の重複を拒否し、DBを変更しない。"""
    _set_test_user(monkeypatch, "J0001")
    response = client.post(
        "/api/inquiries/bulk-accept",
        json={
            "問い合わせ番号一覧": [
                pending_inquiry_number,
                pending_inquiry_number,
            ]
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

def test_bulk_accept_rejects_general_staff(
    monkeypatch,
    pending_inquiry_number,
):
    """一般職員による一括引き受けを拒否し、DBを変更しない。"""
    _set_test_user(monkeypatch, "T0001")

    # 操作前の状態を取得
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
            before = cur.fetchone()

    response = client.post(
        "/api/inquiries/bulk-accept",
        json={
            "問い合わせ番号一覧": [pending_inquiry_number]
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "操作者が情シス職員として登録されていません"
    )

    # 操作後の状態を取得
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
            after = cur.fetchone()

    assert after == before

# =========================================================
# 個別対応完了APIのテスト
# =========================================================


def test_complete_inquiry_success(
    completion_test_inquiries,
    monkeypatch,
):
    """対応担当者本人は対応完了できる。"""
    _set_test_user(monkeypatch, staff_number="J0001")

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
    _set_test_user(monkeypatch, staff_number="J0002")

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
        "指定された問い合わせが見つかりません。"
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
    _set_test_user(monkeypatch, staff_number="J0001")

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

    _set_test_user(monkeypatch, staff_number="J0001")

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

#一括完了
def test_bulk_complete_inquiries_success(
    bulk_completion_test_inquiries,
    monkeypatch,
):
    """対応中の問い合わせ2件を一括で対応完了できる。"""

    # 操作者をJ0001に設定
    _set_test_user(monkeypatch, staff_number="J0001")

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

    _set_test_user(monkeypatch, staff_number="J0001")

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

    _set_test_user(monkeypatch, staff_number="J0001")

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

    _set_test_user(monkeypatch, staff_number="J0001")

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

    _set_test_user(monkeypatch, staff_number="J0001")

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

    _set_test_user(monkeypatch, staff_number="J0001")

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

    _set_test_user(monkeypatch, staff_number="J0001")

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

    _set_test_user(monkeypatch, staff_number="J0001")

    response = client.post(
        "/api/inquiries/bulk-complete",
        json={"問い合わせ番号一覧": []},
    )

    assert response.status_code == 422


# =========================================================
# 個別再開APIのテスト
# =========================================================


def test_reopen_inquiry_success(
    completion_test_inquiries,
    monkeypatch,
):
    """対応担当者本人が期限内に問い合わせを再開できる。"""

    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["completed"]

    # 再開前の対応担当者・引き受け日時を取得
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )
            before = cur.fetchone()

    assert before is not None
    assert before[0] == "J0001"
    assert before[1] is not None
    assert before[2] is not None

    response = client.post(
        f"/api/inquiries/{inquiry_number}/reopen"
    )

    assert response.status_code == 200
    assert response.json()["問い合わせ番号"] == inquiry_number

    # 再開後の状態を確認
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    "対応担当者",
                    "引き受け日時",
                    "対応完了日時"
                FROM "問い合わせ"
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )
            after = cur.fetchone()

    assert after is not None
    assert after[0] == before[0]
    assert after[1] == before[1]
    assert after[2] is None


def test_reopen_inquiry_forbidden_for_other_handler(
    completion_test_inquiries,
    monkeypatch,
):
    """別の対応担当者は問い合わせを再開できない。"""

    _set_test_user(monkeypatch, staff_number="J0002")

    inquiry_number = completion_test_inquiries["completed"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/reopen"
    )

    assert response.status_code == 403

    # 対応完了状態が維持されていること
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
    assert row[0] is not None


def test_reopen_inquiry_conflict_when_not_completed(
    completion_test_inquiries,
    monkeypatch,
):
    """対応完了していない問い合わせは再開できない。"""

    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["in_progress"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/reopen"
    )

    assert response.status_code == 409

    # 対応中の状態が維持されていること
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


def test_reopen_inquiry_conflict_when_pending(
    completion_test_inquiries,
    monkeypatch,
):
    """引き受け待ちの問い合わせは再開できない。"""

    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["pending"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/reopen"
    )

    assert response.status_code == 409


def test_reopen_inquiry_not_found(monkeypatch):
    """存在しない問い合わせ番号の場合、404を返す。"""

    _set_test_user(monkeypatch, staff_number="J0001")

    response = client.post(
        "/api/inquiries/999999999/reopen"
    )

    assert response.status_code == 404


def test_reopen_inquiry_conflict_when_expired(
    completion_test_inquiries,
    monkeypatch,
):
    """対応完了から7日以上経過した問い合わせは再開できない。"""

    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["completed"]

    # 対応完了日時を8日前に設定
    with psycopg.connect(
        dbname="inquiry_management_test"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET "対応完了日時" = NOW() - INTERVAL '8 days'
                WHERE "問い合わせ番号" = %s
                """,
                (inquiry_number,),
            )

    response = client.post(
        f"/api/inquiries/{inquiry_number}/reopen"
    )

    assert response.status_code == 409

    # 対応完了状態が維持されていること
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
    assert row[0] is not None

#新規問題調査へ個別関連付け
def test_create_investigation_success(
    completion_test_inquiries,
    monkeypatch,
):
    """対応中の問い合わせに問題調査を作成し、関連付ける。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["in_progress"]
    investigation_number = None
    inquiry_investigation_number = None

    try:
        response = client.post(
            f"/api/inquiries/{inquiry_number}/investigations",
            json={
                "問題調査の名称や仮説": "ネットワーク接続の不具合",
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert data["問い合わせ番号"] == inquiry_number
        assert data["問題調査の名称や仮説"] == "ネットワーク接続の不具合"
        assert "問題調査番号" in data
        assert "問い合わせ問題調査番号" in data

        investigation_number = data["問題調査番号"]
        inquiry_investigation_number = data["問い合わせ問題調査番号"]

        # 問題調査が初期状態1で登録されたことを確認
        with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        "問題調査の名称や仮説",
                        "問題調査状態"
                    FROM "問題調査"
                    WHERE "問題調査番号" = %s
                    """,
                    (investigation_number,),
                )
                investigation = cur.fetchone()

                assert investigation == (
                    "ネットワーク接続の不具合",
                    1,
                )

                # 問い合わせとの関連レコードが初期状態1で登録されたことを確認
                cur.execute(
                    """
                    SELECT
                        "問題調査番号",
                        "問い合わせ番号",
                        "問い合わせ問題調査状態"
                    FROM "問い合わせ問題調査"
                    WHERE "問い合わせ問題調査番号" = %s
                    """,
                    (inquiry_investigation_number,),
                )
                relation = cur.fetchone()

                assert relation == (
                    investigation_number,
                    inquiry_number,
                    1,
                )

    finally:
        # テストで作成したデータを削除
        with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
            with conn.cursor() as cur:
                if inquiry_investigation_number is not None:
                    cur.execute(
                        """
                        DELETE FROM "問い合わせ問題調査"
                        WHERE "問い合わせ問題調査番号" = %s
                        """,
                        (inquiry_investigation_number,),
                    )

                if investigation_number is not None:
                    cur.execute(
                        """
                        DELETE FROM "問題調査"
                        WHERE "問題調査番号" = %s
                        """,
                        (investigation_number,),
                    )


def test_create_investigation_pending_inquiry_conflict(
    completion_test_inquiries,
    monkeypatch,
):
    """引き受け待ちの問い合わせには作成できない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["pending"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations",
        json={
            "問題調査の名称や仮説": "テスト用の仮説",
        },
    )

    assert response.status_code == 409


def test_create_investigation_completed_inquiry_conflict(
    completion_test_inquiries,
    monkeypatch,
):
    """対応完了の問い合わせには作成できない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["completed"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations",
        json={
            "問題調査の名称や仮説": "テスト用の仮説",
        },
    )

    assert response.status_code == 409


def test_create_investigation_inquiry_not_found(monkeypatch):
    """存在しない問い合わせ番号は404になる。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    response = client.post(
        "/api/inquiries/999999999/investigations",
        json={
            "問題調査の名称や仮説": "テスト用の仮説",
        },
    )

    assert response.status_code == 404


def test_create_investigation_forbidden_for_other_handler(
    completion_test_inquiries,
    monkeypatch,
):
    """別の職員は対応担当者の問い合わせに問題調査を作成できない。"""
    _set_test_user(monkeypatch, staff_number="J0002")

    inquiry_number = completion_test_inquiries["in_progress"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations",
        json={
            "問題調査の名称や仮説": "テスト用の仮説",
        },
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "name",
    [
        "",
        "   ",
        "あ" * 31,
    ],
)
def test_create_investigation_invalid_name(
    completion_test_inquiries,
    monkeypatch,
    name,
):
    """名称や仮説が空、空白だけ、31文字以上の場合は422になる。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["in_progress"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations",
        json={
            "問題調査の名称や仮説": name,
        },
    )

    assert response.status_code == 422

#既存調査へ個別関連付け
def test_link_existing_investigation_success(
    completion_test_inquiries,
    pending_inquiry_number,
    inquiry_problem_investigation_factory,
    monkeypatch,
):
    """対応中の問い合わせに調査中の問題調査を関連付けられる。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    # 既存の関連付けを持つ問い合わせ
    existing_inquiry_number = completion_test_inquiries["in_progress"]

    # 追加対象の問い合わせ
    inquiry_number = pending_inquiry_number

    # 追加対象の問い合わせをJ0001の対応中にする
    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = %s,
                    "引き受け日時" = NOW(),
                    "対応完了日時" = NULL
                WHERE "問い合わせ番号" = %s
                """,
                ("J0001", inquiry_number),
            )

    # 問題調査と最初の関連付けを作成
    relation_id = inquiry_problem_investigation_factory(
        existing_inquiry_number,
        state=1,
    )

    # 関連レコード番号から問題調査番号を取得
    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問題調査番号"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ問題調査番号" = %s
                """,
                (relation_id,),
            )
            investigation_number = cur.fetchone()[0]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations/"
        f"{investigation_number}"
    )

    assert response.status_code == 200

    data = response.json()
    assert data["問い合わせ番号"] == inquiry_number
    assert data["問題調査番号"] == investigation_number
    assert "問い合わせ問題調査番号" in data

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    "問題調査番号",
                    "問い合わせ番号",
                    "問い合わせ問題調査状態"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ問題調査番号" = %s
                """,
                (data["問い合わせ問題調査番号"],),
            )
            relation = cur.fetchone()

    assert relation == (investigation_number, inquiry_number, 1)


def test_link_investigation_pending_inquiry_returns_409(
    completion_test_inquiries,
    unlinked_investigation_factory,
    monkeypatch,
):
    """引き受け待ちの問い合わせには関連付けできない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["pending"]
    investigation_number = unlinked_investigation_factory(state=1)

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations/"
        f"{investigation_number}"
    )

    assert response.status_code == 409


def test_link_investigation_completed_inquiry_returns_409(
    completion_test_inquiries,
    unlinked_investigation_factory,
    monkeypatch,
):
    """対応完了の問い合わせには関連付けできない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["completed"]
    investigation_number = unlinked_investigation_factory(state=1)

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations/"
        f"{investigation_number}"
    )

    assert response.status_code == 409


def test_link_investigation_nonexistent_inquiry_returns_404(
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
    monkeypatch,
):
    """存在しない問い合わせには関連付けできない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    # 既存の関連付けを持つ問い合わせ
    existing_inquiry_number = completion_test_inquiries["in_progress"]
    # 問題調査と最初の関連付けを作成
    relation_id = inquiry_problem_investigation_factory(
        existing_inquiry_number,
        state=1,
    )
    # 関連レコード番号から問題調査番号を取得
    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問題調査番号"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ問題調査番号" = %s
                """,
                (relation_id,),
            )
            investigation_number = cur.fetchone()[0]


    response = client.post(
        f"/api/inquiries/999999999/investigations/"
        f"{investigation_number}"
    )

    assert response.status_code == 404


def test_link_investigation_nonexistent_investigation_returns_404(
    completion_test_inquiries,
    monkeypatch,
):
    """存在しない問題調査は関連付けできない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["in_progress"]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations/999999999"
    )

    assert response.status_code == 404


def test_link_investigation_other_handler_returns_403(
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
    monkeypatch,
):
    """対応担当者本人以外は関連付けできない。"""
    _set_test_user(monkeypatch, staff_number="J0002")


    inquiry_number = completion_test_inquiries["in_progress"]

    #既存の問い合わせ問題調査を作成
    existing_inquiry_number = completion_test_inquiries["pending"]
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
                    ("J0001", existing_inquiry_number),
                )
    # 問題調査と最初の関連付けを作成
    relation_id = inquiry_problem_investigation_factory(
        existing_inquiry_number,
        state=1,
    )
    # 関連レコード番号から問題調査番号を取得
    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問題調査番号"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ問題調査番号" = %s
                """,
                (relation_id,),
            )
            investigation_number = cur.fetchone()[0]

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations/"
        f"{investigation_number}"
    )

    assert response.status_code == 403


@pytest.mark.parametrize("state", [2, 3])
def test_link_investigation_non_active_state_returns_409(
    completion_test_inquiries,
    unlinked_investigation_factory,
    monkeypatch,
    state,
):
    """調査中以外の問題調査は関連付けできない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["in_progress"]
    investigation_number = unlinked_investigation_factory(state=state)

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations/"
        f"{investigation_number}"
    )

    assert response.status_code == 409

def test_link_investigation_duplicate_returns_409(
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
    monkeypatch,
):
    """同じ問い合わせと問題調査の組み合わせを二重登録できない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["in_progress"]

    # 問題調査と最初の関連付けを作成
    relation_id = inquiry_problem_investigation_factory(
        inquiry_number,
        state=1,
    )

    # 関連レコード番号から問題調査番号を取得
    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問題調査番号"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ問題調査番号" = %s
                """,
                (relation_id,),
            )
            investigation_number = cur.fetchone()[0]

    url = (
        f"/api/inquiries/{inquiry_number}/investigations/"
        f"{investigation_number}"
    )

    # すでに関連付け済みなので、重複登録は拒否される
    response = client.post(url)
    assert response.status_code == 409

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ番号" = %s
                  AND "問題調査番号" = %s
                """,
                (inquiry_number, investigation_number),
            )
            count = cur.fetchone()[0]

    assert count == 1

def test_link_investigation_existing_inquiry_other_handler_returns_403(
    completion_test_inquiries,
    pending_inquiry_number,
    inquiry_problem_investigation_factory,
    monkeypatch,
):
    """既存の関連付け先の対応担当者が異なる場合は追加できない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    # 既存の関連付け先はJ0002の対応中にする
    existing_inquiry_number = completion_test_inquiries["in_progress"]

    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET "対応担当者" = %s
                WHERE "問い合わせ番号" = %s
                """,
                ("J0002", existing_inquiry_number),
            )

    # 既存の関連付けを持つ問題調査を作成
    relation_id = inquiry_problem_investigation_factory(
        existing_inquiry_number,
        state=1,
    )

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問題調査番号"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ問題調査番号" = %s
                """,
                (relation_id,),
            )
            investigation_number = cur.fetchone()[0]

    # 追加対象はJ0001の対応中にする
    inquiry_number = pending_inquiry_number

    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET
                    "対応担当者" = %s,
                    "引き受け日時" = NOW(),
                    "対応完了日時" = NULL
                WHERE "問い合わせ番号" = %s
                """,
                ("J0001", inquiry_number),
            )

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations/"
        f"{investigation_number}"
    )

    assert response.status_code == 403

def test_link_investigation_without_existing_relation_returns_409(
    completion_test_inquiries,
    unlinked_investigation_factory,
    monkeypatch,
):
    """既存の関連付けがない問題調査には追加できない。"""
    _set_test_user(monkeypatch, staff_number="J0001")

    inquiry_number = completion_test_inquiries["in_progress"]

    # 問題調査は作成するが、関連付けは作成しない
    investigation_number = unlinked_investigation_factory(state=1)

    response = client.post(
        f"/api/inquiries/{inquiry_number}/investigations/"
        f"{investigation_number}"
    )

    assert response.status_code == 409

#新規調査へ一括関連付け
def test_bulk_create_investigation_success(
    completion_test_inquiries,
    bulk_created_investigation_cleanup,
    monkeypatch,
):
    """複数の対応中問い合わせに、新しい問題調査を関連付けられる。"""
    _set_test_user(monkeypatch)

    inquiry1 = completion_test_inquiries["in_progress"]
    inquiry2 = _make_second_in_progress_inquiry(
        completion_test_inquiries
    )

    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [inquiry1, inquiry2],
            "問題調査の名称や仮説": "一括登録の正常系テスト",
        },
    )

    assert response.status_code == 200
    data = response.json()

    investigation_number = data["問題調査番号"]
    bulk_created_investigation_cleanup(investigation_number)

    assert data["関連付け件数"] == 2
    assert len(data["関連付け一覧"]) == 2

    assert {
        item["問い合わせ番号"]
        for item in data["関連付け一覧"]
    } == {inquiry1, inquiry2}

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    "問題調査の名称や仮説",
                    "問題調査状態"
                FROM "問題調査"
                WHERE "問題調査番号" = %s
                """,
                (investigation_number,),
            )
            investigation = cur.fetchone()

            cur.execute(
                """
                SELECT COUNT(*)
                FROM "問い合わせ問題調査"
                WHERE "問題調査番号" = %s
                """,
                (investigation_number,),
            )
            relation_count = cur.fetchone()[0]

    assert investigation == ("一括登録の正常系テスト", 1)
    assert relation_count == 2

def test_bulk_create_investigation_single_inquiry_success(
    completion_test_inquiries,
    bulk_created_investigation_cleanup,
    monkeypatch,
):
    """問い合わせを1件だけ指定しても一括APIを利用できる。"""
    _set_test_user(monkeypatch)

    inquiry_number = completion_test_inquiries["in_progress"]

    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [inquiry_number],
            "問題調査の名称や仮説": "1件選択の正常系テスト",
        },
    )

    assert response.status_code == 200
    data = response.json()

    bulk_created_investigation_cleanup(data["問題調査番号"])

    assert data["関連付け件数"] == 1
    assert len(data["関連付け一覧"]) == 1
    assert (
        data["関連付け一覧"][0]["問い合わせ番号"]
        == inquiry_number
    )

def test_bulk_create_investigation_missing_inquiry_returns_404(
    completion_test_inquiries,
    monkeypatch,
):
    """存在しない問い合わせが含まれていたら登録しない。"""
    _set_test_user(monkeypatch)

    inquiry_number = completion_test_inquiries["in_progress"]
    name = "一括登録の存在確認テスト"

    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [
                inquiry_number,
                999999999,
            ],
            "問題調査の名称や仮説": name,
        },
    )

    assert response.status_code == 404

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM "問題調査"
                WHERE "問題調査の名称や仮説" = %s
                """,
                (name,),
            )
            assert cur.fetchone()[0] == 0

def test_bulk_create_investigation_pending_inquiry_returns_409(
    completion_test_inquiries,
    monkeypatch,
):
    """引き受け待ちの問い合わせが混ざっていたら全件拒否する。"""
    _set_test_user(monkeypatch)

    inquiry1 = completion_test_inquiries["in_progress"]
    inquiry2 = completion_test_inquiries["pending"]
    name = "一括登録の状態確認テスト"

    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [inquiry1, inquiry2],
            "問題調査の名称や仮説": name,
        },
    )

    assert response.status_code == 409

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM "問題調査"
                WHERE "問題調査の名称や仮説" = %s
                """,
                (name,),
            )
            assert cur.fetchone()[0] == 0

def test_bulk_create_investigation_completed_inquiry_returns_409(
    completion_test_inquiries,
    monkeypatch,
):
    """対応完了の問い合わせが指定された場合は拒否する。"""
    _set_test_user(monkeypatch)

    inquiry_number = completion_test_inquiries["in_progress"]
    completed_number = completion_test_inquiries["completed"]

    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [
                inquiry_number,
                completed_number,
            ],
            "問題調査の名称や仮説": "一括登録の完了状態テスト",
        },
    )

    assert response.status_code == 409

def test_bulk_create_investigation_other_handler_returns_403(
    completion_test_inquiries,
    monkeypatch,
):
    """対応担当者本人でない場合は拒否する。"""
    _set_test_user(monkeypatch, staff_number="J0002")

    inquiry_number = completion_test_inquiries["in_progress"]

    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [inquiry_number],
            "問題調査の名称や仮説": "一括登録の権限テスト",
        },
    )

    assert response.status_code == 403

def test_bulk_create_investigation_empty_list_returns_422():
    """問い合わせ番号が1件も指定されていなければ拒否する。"""
    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [],
            "問題調査の名称や仮説": "空リストのテスト",
        },
    )

    assert response.status_code == 422

def test_bulk_create_investigation_duplicate_numbers_returns_422():
    """同じ問い合わせ番号を重複指定できない。"""
    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [101, 101],
            "問題調査の名称や仮説": "重複番号のテスト",
        },
    )

    assert response.status_code == 422

def test_bulk_create_investigation_invalid_number_returns_422():
    """1未満の問い合わせ番号は受け付けない。"""
    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [0],
            "問題調査の名称や仮説": "番号範囲のテスト",
        },
    )

    assert response.status_code == 422

@pytest.mark.parametrize(
    "name",
    [
        "",
        "   ",
        "あ" * 31,
    ],
)
def test_bulk_create_investigation_invalid_name_returns_422(name):
    """名称や仮説が空、空白のみ、31文字以上なら拒否する。"""
    response = client.post(
        "/api/inquiries/bulk-investigations",
        json={
            "問い合わせ番号一覧": [101],
            "問題調査の名称や仮説": name,
        },
    )

    assert response.status_code == 422

# =========================================================
# 既存の問題調査を複数の問い合わせに関連付けるAPIのテスト
# =========================================================

def _get_bulk_link_relation_count(
    investigation_number,
    inquiry_numbers,
):
    """指定した問題調査と問い合わせの関連付け件数を取得する。"""
    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM "問い合わせ問題調査"
                WHERE "問題調査番号" = %s
                  AND "問い合わせ番号" = ANY(%s)
                """,
                (investigation_number, inquiry_numbers),
            )
            return cur.fetchone()[0]


def test_bulk_link_existing_investigation_success(
    monkeypatch,
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
):
    """複数の対応中問い合わせに既存の問題調査を関連付けできる。"""
    _set_test_user(monkeypatch, "J0001")

    existing_number = completion_test_inquiries["in_progress"]

    # 一括APIの対象となる問い合わせを2件作成
    first_number = create_pending_inquiry_for_bulk_test()
    second_number = create_pending_inquiry_for_bulk_test()
    inquiry_numbers = [first_number, second_number]

    try:
        # 既存の関連付け先となる問題調査を作成
        relation_id = inquiry_problem_investigation_factory(
            existing_number,
            state=1,
        )

        with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT "問題調査番号"
                    FROM "問い合わせ問題調査"
                    WHERE "問い合わせ問題調査番号" = %s
                    """,
                    (relation_id,),
                )
                investigation_number = cur.fetchone()[0]

        # 追加対象をJ0001の対応中に変更
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
                    ("J0001", inquiry_numbers),
                )

        response = client.post(
            "/api/inquiries/bulk-link-investigation",
            json={
                "問い合わせ番号一覧": inquiry_numbers,
                "問題調査番号": investigation_number,
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["問題調査番号"] == investigation_number
        assert response.json()["関連付け件数"] == 2
        assert {
            item["問い合わせ番号"]
            for item in response.json()["関連付け一覧"]
        } == set(inquiry_numbers)

        assert _get_bulk_link_relation_count(
            investigation_number,
            inquiry_numbers,
        ) == 2

    finally:
        # 問い合わせ問題調査の関連レコードを先に削除
        with psycopg.connect(
            dbname="inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM "問い合わせ問題調査"
                    WHERE "問い合わせ番号" = ANY(%s)
                    """,
                    (inquiry_numbers,),
                )

        # その後、問い合わせ本体を削除
        delete_inquiries_for_bulk_test(inquiry_numbers)

def test_bulk_link_existing_investigation_single_inquiry_success(
    monkeypatch,
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
):
    """問い合わせが1件だけでも関連付けできる。"""
    _set_test_user(monkeypatch, "J0001")

    existing_number = completion_test_inquiries["in_progress"]

    # 一括APIの対象となる問い合わせを作成
    inquiry_number = create_pending_inquiry_for_bulk_test()
    inquiry_numbers = [inquiry_number]

    try:
        # 既存の関連付け先となる問題調査を作成
        relation_id = inquiry_problem_investigation_factory(
            existing_number,
            state=1,
        )

        with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT "問題調査番号"
                    FROM "問い合わせ問題調査"
                    WHERE "問い合わせ問題調査番号" = %s
                    """,
                    (relation_id,),
                )
                investigation_number = cur.fetchone()[0]

        # 追加対象をJ0001の対応中に変更
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
                    WHERE "問い合わせ番号" = %s
                    """,
                    ("J0001", inquiry_number),
                )

        response = client.post(
            "/api/inquiries/bulk-link-investigation",
            json={
                "問い合わせ番号一覧": inquiry_numbers,
                "問題調査番号": investigation_number,
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["問題調査番号"] == investigation_number
        assert response.json()["関連付け件数"] == 1
        assert {
            item["問い合わせ番号"]
            for item in response.json()["関連付け一覧"]
        } == set(inquiry_numbers)

        assert _get_bulk_link_relation_count(
            investigation_number,
            inquiry_numbers,
        ) == 1

    finally:
        # 関連レコードを先に削除
        with psycopg.connect(
            dbname="inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM "問い合わせ問題調査"
                    WHERE "問い合わせ番号" = ANY(%s)
                    """,
                    (inquiry_numbers,),
                )

        # その後、問い合わせ本体を削除
        delete_inquiries_for_bulk_test(inquiry_numbers)


def test_bulk_link_existing_investigation_not_found(
    completion_test_inquiries,
):
    """存在しない問題調査は関連付けできない。"""
    inquiry_number = completion_test_inquiries["in_progress"]

    response = client.post(
        "/api/inquiries/bulk-link-investigation",
        json={
            "問い合わせ番号一覧": [inquiry_number],
            "問題調査番号": 999999999,
        },
    )

    assert response.status_code == 404


def test_bulk_link_existing_investigation_inquiry_not_found(
    monkeypatch,
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
):
    """問い合わせが1件でも存在しなければ、1件も関連付けない。"""
    _set_test_user(monkeypatch, "J0001")

    valid_number = completion_test_inquiries["in_progress"]
    missing_number = 999999999
    #既存の問い合わせ問題調査を作成
    existing_inquiry_number = completion_test_inquiries["pending"]
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
                    ("J0001", existing_inquiry_number),
                )
    # 問題調査と最初の関連付けを作成
    relation_id = inquiry_problem_investigation_factory(
        existing_inquiry_number,
        state=1,
    )
    # 関連レコード番号から問題調査番号を取得
    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問題調査番号"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ問題調査番号" = %s
                """,
                (relation_id,),
            )
            investigation_number = cur.fetchone()[0]

    response = client.post(
        "/api/inquiries/bulk-link-investigation",
        json={
            "問い合わせ番号一覧": [valid_number, missing_number],
            "問題調査番号": investigation_number,
        },
    )

    assert response.status_code == 404
    assert _get_bulk_link_relation_count(
        investigation_number,
        [valid_number, missing_number],
    ) == 0


def test_bulk_link_existing_investigation_wrong_state(
    monkeypatch,
    completion_test_inquiries,
    unlinked_investigation_factory,
):
    """調査中以外の問題調査は関連付けできない。"""
    _set_test_user(monkeypatch, "J0001")

    inquiry_number = completion_test_inquiries["in_progress"]
    investigation_number = unlinked_investigation_factory(state=2)

    response = client.post(
        "/api/inquiries/bulk-link-investigation",
        json={
            "問い合わせ番号一覧": [inquiry_number],
            "問題調査番号": investigation_number,
        },
    )

    assert response.status_code == 409
    assert _get_bulk_link_relation_count(
        investigation_number,
        [inquiry_number],
    ) == 0


def test_bulk_link_existing_investigation_inquiry_not_in_progress(
    monkeypatch,
    completion_test_inquiries,
    unlinked_investigation_factory,
):
    """対応中でない問い合わせが含まれる場合、1件も関連付けない。"""
    _set_test_user(monkeypatch, "J0001")

    valid_number = completion_test_inquiries["in_progress"]
    pending_number = completion_test_inquiries["pending"]
    investigation_number = unlinked_investigation_factory()

    response = client.post(
        "/api/inquiries/bulk-link-investigation",
        json={
            "問い合わせ番号一覧": [valid_number, pending_number],
            "問題調査番号": investigation_number,
        },
    )

    assert response.status_code == 409
    assert _get_bulk_link_relation_count(
        investigation_number,
        [valid_number, pending_number],
    ) == 0


def test_bulk_link_existing_investigation_wrong_handler(
    monkeypatch,
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
):
    """対応担当者本人でなければ関連付けできない。"""
    _set_test_user(monkeypatch, "J0002")

    inquiry_number = completion_test_inquiries["in_progress"]
    #既存の問い合わせ問題調査を作成
    existing_inquiry_number = completion_test_inquiries["pending"]
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
                    ("J0001", existing_inquiry_number),
                )
    # 問題調査と最初の関連付けを作成
    relation_id = inquiry_problem_investigation_factory(
        existing_inquiry_number,
        state=1,
    )
    # 関連レコード番号から問題調査番号を取得
    with psycopg.connect(dbname="inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問題調査番号"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ問題調査番号" = %s
                """,
                (relation_id,),
            )
            investigation_number = cur.fetchone()[0]

    response = client.post(
        "/api/inquiries/bulk-link-investigation",
        json={
            "問い合わせ番号一覧": [inquiry_number],
            "問題調査番号": investigation_number,
        },
    )

    assert response.status_code == 403
    assert _get_bulk_link_relation_count(
        investigation_number,
        [inquiry_number],
    ) == 0

def test_bulk_link_existing_investigation_existing_inquiry_other_handler_returns_403(
    monkeypatch,
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
):
    """既存調査の関連付け済み問い合わせが別担当者なら追加できない。"""
    _set_test_user(monkeypatch, "J0001")

    existing_number = completion_test_inquiries["in_progress"]
    inquiry_number = create_pending_inquiry_for_bulk_test()
    inquiry_numbers = [inquiry_number]

    try:
        # 既存調査と、最初の関連付けを作成する
        relation_id = inquiry_problem_investigation_factory(
            existing_number,
            state=1,
        )

        with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT "問題調査番号"
                    FROM "問い合わせ問題調査"
                    WHERE "問い合わせ問題調査番号" = %s
                    """,
                    (relation_id,),
                )
                investigation_number = cur.fetchone()[0]

        # 既存の関連付け済み問い合わせを別担当者J0002に変更
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
                    ("J0002", existing_number),
                )

                # 追加対象は実行ユーザーJ0001の対応中にする
                cur.execute(
                    """
                    UPDATE "問い合わせ"
                    SET
                        "対応担当者" = %s,
                        "引き受け日時" = NOW(),
                        "対応完了日時" = NULL
                    WHERE "問い合わせ番号" = %s
                    """,
                    ("J0001", inquiry_number),
                )

        response = client.post(
            "/api/inquiries/bulk-link-investigation",
            json={
                "問い合わせ番号一覧": inquiry_numbers,
                "問題調査番号": investigation_number,
            },
        )

        assert response.status_code == 403

        # 追加対象の関連付けが作成されていないことを確認
        assert _get_bulk_link_relation_count(
            investigation_number,
            inquiry_numbers,
        ) == 0

    finally:
        # 関連レコードを先に削除してから問い合わせを削除する
        with psycopg.connect(
            dbname="inquiry_management_test"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM "問い合わせ問題調査"
                    WHERE "問い合わせ番号" = ANY(%s)
                    """,
                    (inquiry_numbers,),
                )

        delete_inquiries_for_bulk_test(inquiry_numbers)

def test_bulk_link_existing_investigation_already_linked(
    monkeypatch,
    completion_test_inquiries,
    inquiry_problem_investigation_factory,
):
    """既に関連付けられている問い合わせを再度関連付けできない。"""
    _set_test_user(monkeypatch, "J0001")

    inquiry_number = completion_test_inquiries["in_progress"]

    # テスト用ファクトリで、最初の関連付けを作成する
    relation_id = inquiry_problem_investigation_factory(
        inquiry_number,
        state=1,
    )

    with psycopg.connect(dbname=main.DATABASE_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問題調査番号"
                FROM "問い合わせ問題調査"
                WHERE "問い合わせ問題調査番号" = %s
                """,
                (relation_id,),
            )
            investigation_number = cur.fetchone()[0]

    # 同じ組み合わせを一括APIで再度指定する
    response = client.post(
        "/api/inquiries/bulk-link-investigation",
        json={
            "問い合わせ番号一覧": [inquiry_number],
            "問題調査番号": investigation_number,
        },
    )

    assert response.status_code == 409
    assert _get_bulk_link_relation_count(
        investigation_number,
        [inquiry_number],
    ) == 1


@pytest.mark.parametrize(
    "inquiry_numbers",
    [
        [],
        [0],
        [-1],
        [1, 1],
    ],
)
def test_bulk_link_existing_investigation_invalid_inquiry_numbers(
    inquiry_numbers,
):
    """問い合わせ番号一覧が空・不正・重複の場合は422。"""
    response = client.post(
        "/api/inquiries/bulk-link-investigation",
        json={
            "問い合わせ番号一覧": inquiry_numbers,
            "問題調査番号": 1,
        },
    )

    assert response.status_code == 422


#上書き保存テスト
def build_inquiry_update_payload(
    inquiry_number,
    **overrides,
):
    """詳細取得APIの値を使って編集リクエストを作る。"""
    response = client.get(f"/api/inquiries/{inquiry_number}")
    assert response.status_code == 200, response.text

    inquiry = response.json()

    payload = {
        "問い合わせ職員番号": inquiry["問い合わせ職員番号"],
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

def test_update_pending_inquiry_success(pending_inquiry_number,monkeypatch):
    """受付担当者本人は未引き受けの問い合わせを編集できる。"""
    payload = build_inquiry_update_payload(
        pending_inquiry_number,
        件名="編集APIテスト-件名変更",
        問い合わせ詳細="編集APIで変更した詳細",
    )
    _set_test_user(monkeypatch, "J0001")
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
    pending_inquiry_number,monkeypatch
):
    """要調査から即時解決に変更すると対応完了日時が設定される。"""
    payload = build_inquiry_update_payload(
        pending_inquiry_number,
        受付時の処理=1,
    )
    _set_test_user(monkeypatch, "J0001")
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
    pending_inquiry_number,monkeypatch
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
        件名="編集APIテスト-対応中の編集",
    )
    _set_test_user(monkeypatch, "J0002")
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
    pending_inquiry_number,monkeypatch
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
        件名="変更されてはいけない件名",
        受付時の処理=1,
    )
    _set_test_user(monkeypatch, "J0002")
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
    pending_inquiry_number,monkeypatch
):
    """受付担当者でも対応担当者でもない職員は編集できない。"""
    payload = build_inquiry_update_payload(
        pending_inquiry_number,
        件名="変更されてはいけない件名",
    )

    _set_test_user(monkeypatch, "J0002")
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
    pending_inquiry_number,monkeypatch
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
    _set_test_user(monkeypatch, "J0001")
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


def test_update_inquiry_unknown_number(pending_inquiry_number,monkeypatch):
    """存在しない問い合わせ番号では404になる。"""
    payload = build_inquiry_update_payload(
        pending_inquiry_number,
    )
    _set_test_user(monkeypatch, "J0001")
    response = client.put(
        "/api/inquiries/999999999",
        json=payload,
    )

    assert response.status_code == 404

#検索一覧取得のテスト
def test_search_inquiries_without_conditions(
    search_test_inquiries,
):
    """初期条件を適用しない場合、全件を検索できる。"""
    response = client.get(
        "/api/inquiries",
        params={"初期条件": 2},
    )

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 50
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_search_inquiries_by_number(search_test_inquiries):
    """問い合わせ番号で検索できる。"""
    inquiry_number = search_test_inquiries["pending"]

    response = client.get(
        "/api/inquiries",
        params={
            "初期条件": 2,
            "問い合わせ番号": inquiry_number,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["問い合わせ番号"] == inquiry_number


def test_search_inquiries_by_subject(search_test_inquiries):
    """件名の部分一致で検索できる。"""
    response = client.get(
        "/api/inquiries",
        params={
            "初期条件": 2,
            "件名": "検索APIテスト-対応中",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1


def test_search_inquiries_by_category(search_test_inquiries):
    """問い合わせ分類で検索できる。"""
    response = client.get(
        "/api/inquiries",
        params={
            "初期条件": 2,
            "問い合わせ分類": "分類A",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 3


def test_search_inquiries_by_status(search_test_inquiries):
    """問い合わせ状態で検索できる。"""
    response = client.get(
        "/api/inquiries",
        params=[
            ("初期条件", "2"),
            ("状態", "対応中"),
        ],
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1


def test_search_inquiries_pagination(search_test_inquiries):
    """ページネーションが機能する。"""
    response_page1 = client.get(
        "/api/inquiries",
        params={
            "初期条件": 2,
            "page": 1,
            "page_size": 2,
        },
    )
    response_page2 = client.get(
        "/api/inquiries",
        params={
            "初期条件": 2,
            "page": 2,
            "page_size": 2,
        },
    )

    assert response_page1.status_code == 200
    assert response_page2.status_code == 200

    page1 = response_page1.json()
    page2 = response_page2.json()

    assert page1["total"] == 3
    assert page1["page_size"] == 2
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 1

    page1_numbers = {
        item["問い合わせ番号"] for item in page1["items"]
    }
    page2_numbers = {
        item["問い合わせ番号"] for item in page2["items"]
    }

    assert page1_numbers.isdisjoint(page2_numbers)


def test_search_inquiries_invalid_status(search_test_inquiries):
    """不正な問い合わせ状態は422になる。"""
    response = client.get(
        "/api/inquiries",
        params=[
            ("初期条件", "2"),
            ("状態", "存在しない状態"),
        ],
    )

    assert response.status_code == 422


def test_search_inquiries_invalid_initial_condition():
    """不正な初期条件は422になる。"""
    response = client.get(
        "/api/inquiries",
        params={"初期条件": 3},
    )

    assert response.status_code == 422


def test_search_inquiries_missing_initial_condition():
    """初期条件を省略すると422になる。"""
    response = client.get("/api/inquiries")

    assert response.status_code == 422


def test_search_inquiries_invalid_page():
    """ページ番号が1未満の場合は422になる。"""
    response = client.get(
        "/api/inquiries",
        params={
            "初期条件": 2,
            "page": 0,
        },
    )

    assert response.status_code == 422


def test_search_initial_condition_ignores_other_conditions(
    monkeypatch,
    search_test_inquiries,
):
    """初期条件1では、ほかの検索条件を無視する。"""
    _set_test_user(monkeypatch, "T0001")

    response = client.get(
        "/api/inquiries",
        params={
            "初期条件": 1,
            "件名": "検索APIテスト-対応完了",
            "状態": "対応完了",
        },
    )

    assert response.status_code == 200
    data = response.json()

    numbers = {
        item["問い合わせ番号"] for item in data["items"]
    }

    assert search_test_inquiries["pending"] in numbers
    assert search_test_inquiries["in_progress"] in numbers
    assert search_test_inquiries["completed"] not in numbers


def test_search_initial_condition_for_it_staff(
    monkeypatch,
    search_test_inquiries,
):
    """情シス職員の初期条件では、引き受け待ちと自分の対応中を表示する。"""
    _set_test_user(monkeypatch, "J0001")

    response = client.get(
        "/api/inquiries",
        params={"初期条件": 1},
    )

    assert response.status_code == 200
    data = response.json()

    numbers = {
        item["問い合わせ番号"] for item in data["items"]
    }

    assert search_test_inquiries["pending"] in numbers
    assert search_test_inquiries["in_progress"] in numbers
    assert search_test_inquiries["completed"] not in numbers



#個別詳細取得
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
    assert "関連する問題調査番号一覧" in result
    assert isinstance(
        result["関連する問題調査番号一覧"],
        list,
    )


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

def test_get_inquiry_includes_related_investigation_numbers(
    detail_test_investigation_links,
):
    """関連する問題調査番号を一覧で取得できる。"""
    inquiry_number = (
        detail_test_investigation_links["問い合わせ番号"]
    )
    expected_numbers = (
        detail_test_investigation_links["問題調査番号一覧"]
    )

    response = client.get(
        f"/api/inquiries/{inquiry_number}"
    )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["関連する問題調査番号一覧"] == sorted(
        expected_numbers
    )


def test_get_inquiry_without_related_investigations(
    detail_test_inquiries,
):
    """関連する問題調査がない場合は空リストを返す。"""
    inquiry_number = detail_test_inquiries["pending"]

    response = client.get(
        f"/api/inquiries/{inquiry_number}"
    )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["関連する問題調査番号一覧"] == []