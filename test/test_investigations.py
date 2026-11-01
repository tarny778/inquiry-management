from config import settings

import psycopg
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

import pytest
import main


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


# テスト用データを作成



@pytest.fixture
def investigation_search_test_data():
    """調査一覧APIのテストデータを作成し、終了後に削除する。"""

    inquiry_numbers = []
    investigation_numbers = []
    link_numbers = []

    try:
        # 1. 問い合わせを3件登録する
        for title in [
            "調査一覧APIテスト-A",
            "調査一覧APIテスト-B",
            "調査一覧APIテスト-C",
        ]:
            response = client.post(
                "/api/inquiries",
                json={
                    "問い合わせ職員番号": "T0001",
                    "受付経路": "電話",
                    "問い合わせ分類": "分類A",
                    "件名": title,
                    "緊急度": 2,
                    "受付時の処理": 2,
                    "問い合わせ詳細": "調査一覧APIの自動テスト用",
                    "受信日時": None,
                },
            )

            assert response.status_code == 200, response.text
            inquiry_numbers.append(
                response.json()["問い合わせ番号"]
            )

        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                # 問い合わせAの問い合わせ者をJ0001にする
                # 3件とも対応担当者をJ0001にする
                cur.execute(
                    '''
                    UPDATE "問い合わせ"
                    SET
                        "問い合わせ職員番号" = %s,
                        "対応担当者" = %s,
                        "引き受け日時" = CURRENT_TIMESTAMP
                    WHERE "問い合わせ番号" = %s
                    ''',
                    ("J0001", "J0001", inquiry_numbers[0]),
                )

                cur.execute(
                    '''
                    UPDATE "問い合わせ"
                    SET
                        "対応担当者" = %s,
                        "引き受け日時" = CURRENT_TIMESTAMP
                    WHERE "問い合わせ番号" IN (%s, %s)
                    ''',
                    ("J0001", inquiry_numbers[1], inquiry_numbers[2]),
                )

                # 2. 調査を2件登録する
                cur.execute(
                    '''
                    INSERT INTO "調査" (
                        "調査の名称"
                    )
                    VALUES (%s)
                    RETURNING "調査番号"
                    ''',
                    ("調査一覧APIテスト-複数問い合わせ",),
                )
                investigation_numbers.append(cur.fetchone()[0])

                cur.execute(
                    '''
                    INSERT INTO "調査" (
                        "調査の名称"
                    )
                    VALUES (%s)
                    RETURNING "調査番号"
                    ''',
                    ("調査一覧APIテスト-単一問い合わせ",),
                )
                investigation_numbers.append(cur.fetchone()[0])

                # 3. 調査と問い合わせを関連付ける
                # 1件目の調査に問い合わせA・Bを関連付ける
                for inquiry_number in inquiry_numbers[:2]:
                    cur.execute(
                        '''
                        INSERT INTO "問い合わせ調査" (
                            "調査番号",
                            "問い合わせ番号"
                        )
                        VALUES (%s, %s)
                        RETURNING "問い合わせ調査番号"
                        ''',
                        (
                            investigation_numbers[0],
                            inquiry_number,
                        ),
                    )
                    link_numbers.append(cur.fetchone()[0])

                # 2件目の調査に問い合わせCを関連付ける
                cur.execute(
                    '''
                    INSERT INTO "問い合わせ調査" (
                        "調査番号",
                        "問い合わせ番号"
                    )
                    VALUES (%s, %s)
                    RETURNING "問い合わせ調査番号"
                    ''',
                    (
                        investigation_numbers[1],
                        inquiry_numbers[2],
                    ),
                )
                link_numbers.append(cur.fetchone()[0])

        yield {
            "inquiry_numbers": inquiry_numbers,
            "investigation_numbers": investigation_numbers,
        }

    finally:
        # 4. 関連レコードから順番に削除する
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                if link_numbers:
                    cur.execute(
                        '''
                        DELETE FROM "問い合わせ調査"
                        WHERE "問い合わせ調査番号" = ANY(%s)
                        ''',
                        (link_numbers,),
                    )

                if investigation_numbers:
                    cur.execute(
                        '''
                        DELETE FROM "調査"
                        WHERE "調査番号" = ANY(%s)
                        ''',
                        (investigation_numbers,),
                    )

                if inquiry_numbers:
                    cur.execute(
                        '''
                        DELETE FROM "問い合わせ"
                        WHERE "問い合わせ番号" = ANY(%s)
                        ''',
                        (inquiry_numbers,),
                    )

@pytest.fixture
def ok_ng_test_data():
    """OK・NG回答APIのテストデータを作成し、終了後に削除する。"""

    inquiry_number = None
    investigation_number = None
    relation_id = None
    extra_investigation_numbers = []

    try:
        # 1. 問い合わせを登録
        response = client.post(
            "/api/inquiries",
            json={
                "問い合わせ職員番号": "T0001",
                "受付経路": "電話",
                "問い合わせ分類": "分類A",
                "件名": "OK・NG回答APIテスト",
                "緊急度": 2,
                "受付時の処理": 2,
                "問い合わせ詳細": "OK・NG回答APIのテスト用",
                "受信日時": None,
            },
        )
        assert response.status_code == 200, response.text
        inquiry_number = response.json()["問い合わせ番号"]

        # 2. リアクション要求済みの調査を登録
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO "調査" (
                        "調査の名称",
                        "調査状態"
                    )
                    VALUES (%s, 2)
                    RETURNING "調査番号"
                    """,
                    ("OK・NG回答APIテスト用の調査",),
                )
                investigation_number = cur.fetchone()[0]

                # 3. リアクション待ちの関連レコードを登録
                cur.execute(
                    """
                    INSERT INTO "問い合わせ調査" (
                        "調査番号",
                        "問い合わせ番号",
                        "問い合わせ調査状態"
                    )
                    VALUES (%s, %s, 3)
                    RETURNING "問い合わせ調査番号"
                    """,
                    (investigation_number, inquiry_number),
                )
                relation_id = cur.fetchone()[0]

        yield {
            "inquiry_number": inquiry_number,
            "investigation_number": investigation_number,
            "relation_id": relation_id,
            "extra_investigation_numbers": extra_investigation_numbers,
        }

    finally:
        # 4. テストで作成された調査番号を収集して削除
        if inquiry_number is not None:
            with psycopg.connect(
                settings.database_url
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT DISTINCT "調査番号"
                        FROM "問い合わせ調査"
                        WHERE "問い合わせ番号" = %s
                        """,
                        (inquiry_number,),
                    )
                    linked_numbers = [
                        row[0] for row in cur.fetchall()
                    ]

                    investigation_numbers = list(
                        dict.fromkeys(
                            linked_numbers
                            + extra_investigation_numbers
                            + (
                                [investigation_number]
                                if investigation_number is not None
                                else []
                            )
                        )
                    )

                    # 自己参照の移行先を解除
                    if investigation_numbers:
                        cur.execute(
                            """
                            UPDATE "調査"
                            SET "最新移行先の調査番号" = NULL
                            WHERE "調査番号" = ANY(%s)
                            """,
                            (investigation_numbers,),
                        )

                    # 問い合わせに紐づく関連レコードをすべて削除
                    cur.execute(
                        """
                        DELETE FROM "問い合わせ調査"
                        WHERE "問い合わせ番号" = %s
                        """,
                        (inquiry_number,),
                    )

                    # NGで作成された移行先を含めて削除
                    if investigation_numbers:
                        cur.execute(
                            """
                            DELETE FROM "調査"
                            WHERE "調査番号" = ANY(%s)
                            """,
                            (investigation_numbers,),
                        )

                    cur.execute(
                        """
                        DELETE FROM "問い合わせ"
                        WHERE "問い合わせ番号" = %s
                        """,
                        (inquiry_number,),
                    )

#調査の検索一覧取得のテスト
def test_search_investigations_response(
    investigation_search_test_data,
):
    """調査一覧APIが必要な情報を返すことを確認する。"""

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.get(
        "/api/investigations",
        params={"調査番号": investigation_number},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["調査番号"] == investigation_number
    assert item["調査の名称"] == (
        "調査一覧APIテスト-複数問い合わせ"
    )
    assert item["調査状態"] == 1
    assert item["対応担当者職員番号"] is not None
    assert item["関連問い合わせ件数"] == 2
    assert item["自分の問い合わせを含む"] is True


def test_search_investigations_not_own_inquiry(
    investigation_search_test_data,
):
    """自分の問い合わせが関連していない場合はfalseになることを確認する。"""

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][1]
    )

    response = client.get(
        "/api/investigations",
        params={"調査番号": investigation_number},
    )

    assert response.status_code == 200, response.text

    item = response.json()["items"][0]

    assert item["関連問い合わせ件数"] == 1
    assert item["自分の問い合わせを含む"] is False


def test_search_investigations_by_requester_number(
    investigation_search_test_data,
):
    """問い合わせ者の職員番号で調査を絞り込めることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"問い合わせ職員番号": "T0001"},
    )

    assert response.status_code == 200, response.text

    returned_numbers = {
        item["調査番号"]
        for item in response.json()["items"]
    }

    assert set(
        investigation_search_test_data["investigation_numbers"]
    ).issubset(returned_numbers)


def test_search_investigations_by_handler_number(
    investigation_search_test_data,
):
    """対応担当者の職員番号で調査を絞り込めることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"対応担当者職員番号": "J0001"},
    )

    assert response.status_code == 200, response.text

    returned_numbers = {
        item["調査番号"]
        for item in response.json()["items"]
    }

    assert set(
        investigation_search_test_data["investigation_numbers"]
    ).issubset(returned_numbers)

def test_search_investigations_by_name(
    investigation_search_test_data,
):
    """調査の名称で部分一致検索できることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"調査の名称": "複数問い合わせ"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["調査番号"] == (
        investigation_search_test_data["investigation_numbers"][0]
    )


def test_search_investigations_by_status(
    investigation_search_test_data,
):
    """調査状態で検索できることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"調査状態": 1},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total"] >= 2

    assert all(
        item["調査状態"] == 1
        for item in data["items"]
    )


def test_search_investigations_pagination(
    investigation_search_test_data,
):
    """ページ番号とページサイズがレスポンスに反映されることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"page": 1, "page_size": 1},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 1
    assert len(data["items"]) == 1
    assert data["total"] >= 2

def test_search_investigations_with_multiple_conditions(
    investigation_search_test_data,
):
    """状態と対応担当者を組み合わせて検索できることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={
            "調査状態": 1,
            "対応担当者職員番号": "J0001",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    returned_numbers = {
        item["調査番号"]
        for item in data["items"]
    }

    expected_numbers = set(
        investigation_search_test_data["investigation_numbers"]
    )

    assert expected_numbers.issubset(returned_numbers)

    assert all(
        item["調査状態"] == 1
        for item in data["items"]
    )


def test_search_investigations_second_page(
    investigation_search_test_data,
):
    """2ページ目で1ページ目とは異なる調査を取得できることを確認する。"""

    first_response = client.get(
        "/api/investigations",
        params={"page": 1, "page_size": 1},
    )

    second_response = client.get(
        "/api/investigations",
        params={"page": 2, "page_size": 1},
    )

    assert first_response.status_code == 200, first_response.text
    assert second_response.status_code == 200, second_response.text

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["total"] >= 2
    assert len(first_data["items"]) == 1
    assert len(second_data["items"]) == 1

    assert (
        first_data["items"][0]["調査番号"]
        != second_data["items"][0]["調査番号"]
    )


def test_search_investigations_rejects_page_zero(
    investigation_search_test_data,
):
    """ページ番号0が拒否されることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"page": 0},
    )

    assert response.status_code == 422


def test_search_investigations_rejects_page_size_over_limit(
    investigation_search_test_data,
):
    """ページサイズ101が拒否されることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"page_size": 101},
    )

    assert response.status_code == 422


def test_search_investigations_rejects_invalid_status(
    investigation_search_test_data,
):
    """定義されていない調査状態4が拒否されることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"調査状態": 4},
    )

    assert response.status_code == 422



# =========================================================
# 調査詳細取得APIのテスト
# =========================================================


# 正常に調査の詳細と関連一覧を取得できる
def test_get_investigation_response(investigation_search_test_data):
    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.get(
        f"/api/investigations/{investigation_number}"
    )

    assert response.status_code == 200

    data = response.json()

    # 調査そのものの情報
    assert data["調査番号"] == investigation_number
    assert "調査の名称" in data
    assert "原因・仮説" in data
    assert "情シス側での対応" in data
    assert "問い合わせ者側で必要な対応" in data
    assert "調査状態" in data
    assert "調査開始日時" in data
    assert "対応案策定予定日時" in data
    assert "進捗更新の次回更新予定日時" in data
    assert "リアクション要求日時" in data
    assert "調査断念日時" in data
    assert "最新移行先の調査番号" in data

    # 関連一覧と操作者自身の問い合わせの有無
    assert "関連する問い合わせ調査" in data
    assert isinstance(data["関連する問い合わせ調査"], list)
    assert data["自分の問い合わせを含む"] is True


# 関連する問い合わせ調査が複数件返る
def test_get_investigation_with_multiple_related_inquiries(
    investigation_search_test_data,
):
    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.get(
        f"/api/investigations/{investigation_number}"
    )

    assert response.status_code == 200

    related = response.json()["関連する問い合わせ調査"]

    # フィクスチャでは、この調査に2件を関連付けている
    assert len(related) == 2

    # それぞれの問い合わせ調査の情報が返る
    assert len({
        item["問い合わせ調査番号"]
        for item in related
    }) == 2

    assert len({
        item["問い合わせ番号"]
        for item in related
    }) == 2

    for item in related:
        assert "問い合わせ者氏名" in item
        assert "対応担当者氏名" in item
        assert "問い合わせ調査状態" in item
        assert "リアクション内容" in item
        assert "NGでの移行先調査番号" in item


# 存在しない調査番号では404を返す
def test_get_investigation_not_found():
    response = client.get("/api/investigations/999999999")

    assert response.status_code == 404


# 関連する問い合わせ調査がなくても詳細を取得できる
def test_get_investigation_without_related_inquiries():
    # 関連レコードを持たない調査をテスト用に作成
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "調査" (
                    "調査の名称"
                )
                VALUES (%s)
                RETURNING "調査番号"
                ''',
                ("詳細取得APIテスト-関連なし",),
            )

            investigation_number = cur.fetchone()[0]

    try:
        response = client.get(
            f"/api/investigations/{investigation_number}"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["調査番号"] == investigation_number
        assert data["関連する問い合わせ調査"] == []
        assert data["自分の問い合わせを含む"] is False

    finally:
        # このテストで作成した調査を削除
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    DELETE FROM "調査"
                    WHERE "調査番号" = %s
                    ''',
                    (investigation_number,),
                )


# 調査の編集テスト
def test_update_investigation_success(
    investigation_search_test_data,
    monkeypatch,
):
    """関連問い合わせの対応担当者は調査を編集できる。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={
            "調査の名称": "編集後の調査名",
            "原因・仮説": "編集後の原因",
        },
    )

    assert response.status_code == 200, response.text

    result = response.json()
    assert result["調査番号"] == investigation_number
    assert result["調査の名称"] == "編集後の調査名"
    assert result["原因・仮説"] == "編集後の原因"


def test_update_investigation_forbidden_for_other_handler(
    investigation_search_test_data,
    monkeypatch,
):
    """関連問い合わせの対応担当者でない職員は編集できない。"""
    _set_test_user(monkeypatch, "J0002")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={
            "調査の名称": "変更してはいけない名称",
        },
    )

    assert response.status_code == 403


# 関連する問い合わせがない調査は編集できない
def test_update_investigation_without_related_inquiries(
    monkeypatch,
):
    """関連する問い合わせがない調査は編集できない。"""
    _set_test_user(monkeypatch, "J0001")

    # 関連レコードを持たない調査を作成
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "調査" (
                    "調査の名称"
                )
                VALUES (%s)
                RETURNING "調査番号"
                ''',
                ("編集権限テスト-関連なし",),
            )
            investigation_number = cur.fetchone()[0]

    try:
        response = client.patch(
            f"/api/investigations/{investigation_number}",
            json={
                "調査の名称": "変更してはいけない名称",
            },
        )

        assert response.status_code == 403

    finally:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    DELETE FROM "調査"
                    WHERE "調査番号" = %s
                    ''',
                    (investigation_number,),
                )


# 存在しない調査番号の編集は404を返す
def test_update_investigation_not_found(monkeypatch):
    """存在しない調査は編集できない。"""
    _set_test_user(monkeypatch, "J0001")

    response = client.patch(
        "/api/investigations/999999999",
        json={
            "調査の名称": "存在しない調査",
        },
    )

    assert response.status_code == 404


# 調査中ではない調査は編集できない
@pytest.mark.parametrize("state", [2, 3])
def test_update_investigation_not_editable_state(
    investigation_search_test_data,
    monkeypatch,
    state,
):
    """状態が2または3の調査は編集できない。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    # テスト対象の調査を指定した状態に変更
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "調査"
                SET "調査状態" = %s
                WHERE "調査番号" = %s
                ''',
                (state, investigation_number),
            )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={
            "調査の名称": "変更してはいけない名称",
        },
    )

    assert response.status_code == 409


# 調査編集APIの入力値検証テスト

def test_update_investigation_empty_body_returns_422(
    investigation_search_test_data,
    monkeypatch,
):
    """変更項目がないリクエストは拒否する。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={},
    )

    assert response.status_code == 422


def test_update_investigation_null_name_returns_422(
    investigation_search_test_data,
    monkeypatch,
):
    """名称にnullを指定したリクエストは拒否する。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={"調査の名称": None},
    )

    assert response.status_code == 422


def test_update_investigation_extra_field_returns_422(
    investigation_search_test_data,
    monkeypatch,
):
    """編集対象外の項目を指定したリクエストは拒否する。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={
            "調査の名称": "入力検証テスト",
            "調査状態": 3,
        },
    )

    assert response.status_code == 422


def test_update_investigation_name_over_max_length_returns_422(
    investigation_search_test_data,
    monkeypatch,
):
    """名称が最大文字数を超えた場合は拒否する。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={"調査の名称": "あ" * 31},
    )

    assert response.status_code == 422


def test_update_investigation_invalid_datetime_returns_422(
    investigation_search_test_data,
    monkeypatch,
):
    """不正な日時形式は拒否する。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={"対応案策定予定日時": "これは日時ではありません"},
    )

    assert response.status_code == 422


def test_update_investigation_preserves_omitted_fields(
    investigation_search_test_data,
    monkeypatch,
):
    """指定していない項目は更新前の値を維持する。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    # 更新前の値を設定
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "調査"
                SET
                    "調査の名称" = %s,
                    "原因・仮説" = %s,
                    "情シス側での対応" = %s
                WHERE "調査番号" = %s
                ''',
                (
                    "更新前の名称",
                    "更新前の原因",
                    "更新前の対応",
                    investigation_number,
                ),
            )

    # 原因だけを更新
    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={"原因・仮説": "更新後の原因"},
    )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["調査の名称"] == "更新前の名称"
    assert result["原因・仮説"] == "更新後の原因"
    assert result["情シス側での対応"] == "更新前の対応"


def test_update_investigation_forbidden_when_handlers_differ(
    investigation_search_test_data,
    monkeypatch,
):
    """関連問い合わせの対応担当者が一致しない場合は編集できない。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )
    inquiry_numbers = (
        investigation_search_test_data["inquiry_numbers"]
    )

    # 関連する問い合わせのうち1件を別の担当者に変更
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問い合わせ"
                SET "対応担当者" = %s
                WHERE "問い合わせ番号" = %s
                ''',
                ("J0002", inquiry_numbers[1]),
            )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={"調査の名称": "変更してはいけない名称"},
    )

    assert response.status_code == 403


# 調査の断念APIテスト

def test_abandon_investigation_success(
    investigation_search_test_data,
    monkeypatch,
):
    """関連レコードをすべて状態2にして、調査を断念できる。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.post(
        f"/api/investigations/{investigation_number}/abandon"
    )

    assert response.status_code == 200, response.text

    result = response.json()
    assert result["調査番号"] == investigation_number
    assert result["調査状態"] == 3
    assert result["調査断念日時"] is not None

    # 調査本体の状態を確認
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "調査状態", "調査断念日時"
                FROM "調査"
                WHERE "調査番号" = %s
                ''',
                (investigation_number,),
            )
            investigation_row = cur.fetchone()

            assert investigation_row[0] == 3
            assert investigation_row[1] is not None

            # 関連する問い合わせ調査がすべて状態2であることを確認
            cur.execute(
                '''
                SELECT COUNT(*)
                FROM "問い合わせ調査"
                WHERE "調査番号" = %s
                  AND "問い合わせ調査状態" <> 2
                ''',
                (investigation_number,),
            )
            not_state_2_count = cur.fetchone()[0]

            assert not_state_2_count == 0


def test_abandon_investigation_forbidden_for_other_handler(
    investigation_search_test_data,
    monkeypatch,
):
    """対応担当者でない職員は断念できない。"""
    _set_test_user(monkeypatch, "J0002")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.post(
        f"/api/investigations/{investigation_number}/abandon"
    )

    assert response.status_code == 403


def test_abandon_investigation_without_related_inquiries(
    monkeypatch,
):
    """関連する問い合わせがない調査は断念できない。"""
    _set_test_user(monkeypatch, "J0001")

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "調査" (
                    "調査の名称"
                )
                VALUES (%s)
                RETURNING "調査番号"
                ''',
                ("断念APIテスト-関連なし",),
            )
            investigation_number = cur.fetchone()[0]

    try:
        response = client.post(
            f"/api/investigations/{investigation_number}/abandon"
        )

        assert response.status_code == 403

    finally:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    DELETE FROM "調査"
                    WHERE "調査番号" = %s
                    ''',
                    (investigation_number,),
                )


def test_abandon_investigation_not_found(monkeypatch):
    """存在しない調査は断念できない。"""
    _set_test_user(monkeypatch, "J0001")

    response = client.post(
        "/api/investigations/999999999/abandon"
    )

    assert response.status_code == 404


@pytest.mark.parametrize("state", [2, 3])
def test_abandon_investigation_invalid_state(
    investigation_search_test_data,
    monkeypatch,
    state,
):
    """調査の状態が2または3なら断念できない。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "調査"
                SET "調査状態" = %s
                WHERE "調査番号" = %s
                ''',
                (state, investigation_number),
            )

    response = client.post(
        f"/api/investigations/{investigation_number}/abandon"
    )

    assert response.status_code == 409


def test_abandon_investigation_detects_inconsistent_related_state(
    investigation_search_test_data,
    monkeypatch,
):
    """
    関連レコードに状態3があれば整合性エラーを返し、
    調査本体と関連レコードの更新をロールバックする。
    """
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )
    inquiry_number = (
        investigation_search_test_data["inquiry_numbers"][0]
    )

    # 本来は状態1または2のはずの関連レコードに、
    # 設計上想定しない状態3を意図的に設定する
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問い合わせ調査"
                SET "問い合わせ調査状態" = 3
                WHERE "調査番号" = %s
                  AND "問い合わせ番号" = %s
                ''',
                (investigation_number, inquiry_number),
            )
            assert cur.rowcount == 1

    response = client.post(
        f"/api/investigations/{investigation_number}/abandon"
    )

    assert response.status_code == 500
    assert "データ整合性エラー" in response.json()["detail"]

    # 調査本体が状態1のまま、断念日時も未設定であることを確認
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "調査状態", "調査断念日時"
                FROM "調査"
                WHERE "調査番号" = %s
                ''',
                (investigation_number,),
            )
            investigation_row = cur.fetchone()

            assert investigation_row[0] == 1
            assert investigation_row[1] is None

            # 関連レコードも、API実行前の状態に戻っていることを確認
            cur.execute(
                '''
                SELECT "問い合わせ番号", "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "調査番号" = %s
                ORDER BY "問い合わせ番号"
                ''',
                (investigation_number,),
            )
            related_rows = cur.fetchall()

            states_by_inquiry = {
                row[0]: row[1] for row in related_rows
            }

            assert states_by_inquiry[inquiry_number] == 3

            # もう一方の関連レコードも、状態1のまま戻っている
            other_inquiry_number = next(
                number
                for number in investigation_search_test_data["inquiry_numbers"]
                if number != inquiry_number
            )
            assert states_by_inquiry[other_inquiry_number] == 1


# 調査のリアクション要求APIテスト

def test_request_reaction_investigation_success(
    investigation_search_test_data,
    monkeypatch,
):
    """状態1を3に変更し、状態2は維持して要求できる。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )
    inquiry_numbers = (
        investigation_search_test_data["inquiry_numbers"]
    )

    # 事前に1件を個別断念（状態2）にしておく
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問い合わせ調査"
                SET "問い合わせ調査状態" = 2
                WHERE "調査番号" = %s
                  AND "問い合わせ番号" = %s
                ''',
                (investigation_number, inquiry_numbers[0]),
            )
            assert cur.rowcount == 1

    response = client.post(
        f"/api/investigations/{investigation_number}/request-reaction"
    )

    assert response.status_code == 200, response.text

    result = response.json()
    assert result["調査番号"] == investigation_number
    assert result["調査状態"] == 2
    assert result["リアクション要求日時"] is not None

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # 調査本体が状態2になったことを確認
            cur.execute(
                '''
                SELECT "調査状態", "リアクション要求日時"
                FROM "調査"
                WHERE "調査番号" = %s
                ''',
                (investigation_number,),
            )
            investigation_row = cur.fetchone()

            assert investigation_row[0] == 2
            assert investigation_row[1] is not None

            # 状態1だったレコードは3、状態2だったレコードは2のまま
            cur.execute(
                '''
                SELECT "問い合わせ番号", "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "調査番号" = %s
                ''',
                (investigation_number,),
            )
            states_by_inquiry = {
                row[0]: row[1] for row in cur.fetchall()
            }

            assert states_by_inquiry[inquiry_numbers[0]] == 2
            assert states_by_inquiry[inquiry_numbers[1]] == 3

            # 更新後、状態2・3以外のレコードが存在しないことを確認
            cur.execute(
                '''
                SELECT COUNT(*)
                FROM "問い合わせ調査"
                WHERE "調査番号" = %s
                  AND "問い合わせ調査状態" NOT IN (2, 3)
                ''',
                (investigation_number,),
            )
            assert cur.fetchone()[0] == 0


def test_request_reaction_investigation_forbidden_for_other_handler(
    investigation_search_test_data,
    monkeypatch,
):
    """関連する問い合わせの対応担当者でなければ要求できない。"""
    _set_test_user(monkeypatch, "J0002")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.post(
        f"/api/investigations/{investigation_number}/request-reaction"
    )

    assert response.status_code == 403


def test_request_reaction_investigation_without_related_inquiries(
    monkeypatch,
):
    """関連する問い合わせがない調査は要求できない。"""
    _set_test_user(monkeypatch, "J0001")

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "調査" (
                    "調査の名称"
                )
                VALUES (%s)
                RETURNING "調査番号"
                ''',
                ("要求APIテスト-関連なし",),
            )
            investigation_number = cur.fetchone()[0]

    try:
        response = client.post(
            f"/api/investigations/{investigation_number}/request-reaction"
        )

        assert response.status_code == 403

    finally:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    DELETE FROM "調査"
                    WHERE "調査番号" = %s
                    ''',
                    (investigation_number,),
                )


def test_request_reaction_investigation_not_found(monkeypatch):
    """存在しない調査は要求できない。"""
    _set_test_user(monkeypatch, "J0001")

    response = client.post(
        "/api/investigations/999999999/request-reaction"
    )

    assert response.status_code == 404


@pytest.mark.parametrize("state", [2, 3])
def test_request_reaction_investigation_invalid_state(
    investigation_search_test_data,
    monkeypatch,
    state,
):
    """調査本体が状態1以外なら要求できない。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "調査"
                SET "調査状態" = %s
                WHERE "調査番号" = %s
                ''',
                (state, investigation_number),
            )

    response = client.post(
        f"/api/investigations/{investigation_number}/request-reaction"
    )

    assert response.status_code == 409


@pytest.mark.parametrize("related_state", [3, 4, 5])
def test_request_reaction_investigation_detects_inconsistent_related_state(
    investigation_search_test_data,
    monkeypatch,
    related_state,
):
    """
    調査が状態1なのに、関連レコードが状態1・2以外なら
    整合性エラーを返し、更新を行わない。
    """
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )
    inquiry_number = (
        investigation_search_test_data["inquiry_numbers"][0]
    )

    # 設計上想定しない関連レコードの状態を意図的に設定
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問い合わせ調査"
                SET "問い合わせ調査状態" = %s
                WHERE "調査番号" = %s
                  AND "問い合わせ番号" = %s
                ''',
                (related_state, investigation_number, inquiry_number),
            )
            assert cur.rowcount == 1

    response = client.post(
        f"/api/investigations/{investigation_number}/request-reaction"
    )

    assert response.status_code == 500
    assert "データ整合性エラー" in response.json()["detail"]

    # 調査本体は更新されていないことを確認
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "調査状態", "リアクション要求日時"
                FROM "調査"
                WHERE "調査番号" = %s
                ''',
                (investigation_number,),
            )
            investigation_row = cur.fetchone()

            assert investigation_row[0] == 1
            assert investigation_row[1] is None

            # 異常な関連レコードの状態もそのまま保持されている
            cur.execute(
                '''
                SELECT "問い合わせ番号", "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "調査番号" = %s
                ''',
                (investigation_number,),
            )
            states_by_inquiry = {
                row[0]: row[1] for row in cur.fetchall()
            }

            assert states_by_inquiry[inquiry_number] == related_state

            # もう一方の正常な状態1も更新されていない
            other_inquiry_number = next(
                number
                for number in investigation_search_test_data["inquiry_numbers"]
                if number != inquiry_number
            )
            assert states_by_inquiry[other_inquiry_number] == 1


# 問い合わせ調査の個別断念APIのテスト

def _get_relation_id(investigation_number, inquiry_number):
    """調査番号と問い合わせ番号から関連レコード番号を取得する。"""
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問い合わせ調査番号"
                FROM "問い合わせ調査"
                WHERE "調査番号" = %s
                  AND "問い合わせ番号" = %s
                """,
                (investigation_number, inquiry_number),
            )
            row = cur.fetchone()

    assert row is not None
    return row[0]


def test_abandon_inquiry_problem_investigation_success(
    investigation_search_test_data,
    monkeypatch,
):
    """対応担当者が調査中の関連レコードを個別断念できる。"""
    _set_test_user(monkeypatch, "J0001")

    data = investigation_search_test_data
    investigation_number = data["investigation_numbers"][0]
    inquiry_number = data["inquiry_numbers"][0]
    other_inquiry_number = data["inquiry_numbers"][1]

    relation_id = _get_relation_id(
        investigation_number, inquiry_number
    )
    other_relation_id = _get_relation_id(
        investigation_number, other_inquiry_number
    )

    response = client.post(
        f"/api/investigations/relations/{relation_id}/abandon"
    )

    assert response.status_code == 200, response.text

    result = response.json()
    assert result["問い合わせ調査番号"] == relation_id
    assert result["問い合わせ番号"] == inquiry_number
    assert result["調査番号"] == investigation_number
    assert result["問い合わせ調査状態"] == 2

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )
            target_state = cur.fetchone()[0]

            cur.execute(
                """
                SELECT "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (other_relation_id,),
            )
            other_state = cur.fetchone()[0]

            cur.execute(
                """
                SELECT "調査状態"
                FROM "調査"
                WHERE "調査番号" = %s
                """,
                (investigation_number,),
            )
            parent_state = cur.fetchone()[0]

    assert target_state == 2
    assert other_state == 1
    assert parent_state == 1


def test_abandon_inquiry_problem_investigation_other_handler_returns_403(
    investigation_search_test_data,
    monkeypatch,
):
    """別の職員は個別断念できない。"""
    _set_test_user(monkeypatch, "J0001")

    data = investigation_search_test_data
    investigation_number = data["investigation_numbers"][0]
    inquiry_number = data["inquiry_numbers"][0]
    relation_id = _get_relation_id(
        investigation_number, inquiry_number
    )

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ"
                SET "対応担当者" = %s
                WHERE "問い合わせ番号" = %s
                """,
                ("J0002", inquiry_number),
            )

    response = client.post(
        f"/api/investigations/relations/{relation_id}/abandon"
    )

    assert response.status_code == 403

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )
            assert cur.fetchone()[0] == 1


def test_abandon_inquiry_problem_investigation_parent_not_in_progress_returns_409(
    investigation_search_test_data,
    monkeypatch,
):
    """親の調査が調査中でなければ個別断念できない。"""
    _set_test_user(monkeypatch, "J0001")

    data = investigation_search_test_data
    investigation_number = data["investigation_numbers"][0]
    inquiry_number = data["inquiry_numbers"][0]
    relation_id = _get_relation_id(
        investigation_number, inquiry_number
    )

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "調査"
                SET "調査状態" = 2
                WHERE "調査番号" = %s
                """,
                (investigation_number,),
            )

    response = client.post(
        f"/api/investigations/relations/{relation_id}/abandon"
    )

    assert response.status_code == 409

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )
            assert cur.fetchone()[0] == 1


def test_abandon_inquiry_problem_investigation_relation_not_in_progress_returns_409(
    investigation_search_test_data,
    monkeypatch,
):
    """関連レコードが調査中でなければ個別断念できない。"""
    _set_test_user(monkeypatch, "J0001")

    data = investigation_search_test_data
    investigation_number = data["investigation_numbers"][0]
    inquiry_number = data["inquiry_numbers"][0]
    relation_id = _get_relation_id(
        investigation_number, inquiry_number
    )

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ調査"
                SET "問い合わせ調査状態" = 3
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )

    response = client.post(
        f"/api/investigations/relations/{relation_id}/abandon"
    )

    assert response.status_code == 409

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )
            assert cur.fetchone()[0] == 3


def test_abandon_inquiry_problem_investigation_not_found_returns_404(
    monkeypatch,
):
    """存在しない関連レコード番号は404になる。"""
    _set_test_user(monkeypatch, "J0001")

    response = client.post(
        "/api/investigations/relations/999999999/abandon"
    )

    assert response.status_code == 404

# 問い合わせ調査のOK回答APIテスト
def test_ok_investigation_relation_success(
    monkeypatch,
    ok_ng_test_data,
):
    """問い合わせ者本人がリアクション待ちの調査にOKと回答できる。"""
    _set_test_user(monkeypatch, "T0001")

    inquiry_number = ok_ng_test_data["inquiry_number"]
    relation_id = ok_ng_test_data["relation_id"]

    response = client.post(
        f"/api/investigations/relations/{relation_id}/ok"
    )

    assert response.status_code == 200, response.text

    result = response.json()
    assert result["問い合わせ調査番号"] == relation_id
    assert result["問い合わせ番号"] == inquiry_number
    assert result["問い合わせ調査状態"] == 4

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "問い合わせ調査状態"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )
            assert cur.fetchone()[0] == 4



def test_ok_investigation_relation_forbidden(
    monkeypatch,
    ok_ng_test_data,
):
    """問い合わせ者本人以外はリアクション待ちの調査にOKと回答不可。"""
    _set_test_user(monkeypatch, "J0001")

    inquiry_number = ok_ng_test_data["inquiry_number"]
    relation_id = ok_ng_test_data["relation_id"]

    response = client.post(
        f"/api/investigations/relations/{relation_id}/ok"
    )

    assert response.status_code == 403


def test_ok_investigation_relation_invalid_state(
    monkeypatch,
    ok_ng_test_data,
):
    """relationの状態が3以外の場合は、回答不可。"""
    _set_test_user(monkeypatch, "T0001")

    relation_id = ok_ng_test_data["relation_id"]

    # リアクション待ち以外の状態に変更する
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ調査"
                SET "問い合わせ調査状態" = 1
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )


    response = client.post(
        f"/api/investigations/relations/{relation_id}/ok"
    )

    assert response.status_code == 409


def test_ok_investigation_relation_not_found(monkeypatch):
    """存在しない関連レコードは404になる。"""
    _set_test_user(monkeypatch, "T0001")

    response = client.post(
        "/api/investigations/relations/999999999/ok"
    )

    assert response.status_code == 404

# =========================================================
# 問い合わせ調査のNG回答APIテスト
# =========================================================

def test_ng_investigation_relation_reuses_latest_destination(
    monkeypatch,
    ok_ng_test_data,
):
    """最新移行先が調査中なら、その調査を再利用する。"""
    _set_test_user(monkeypatch, "T0001")

    inquiry_number = ok_ng_test_data["inquiry_number"]
    old_relation_id = ok_ng_test_data["relation_id"]

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "調査番号"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (old_relation_id,),
            )
            old_investigation_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO "調査" (
                    "調査の名称",
                    "調査状態",
                    "調査開始日時"
                )
                VALUES (%s, 1, CURRENT_TIMESTAMP)
                RETURNING "調査番号"
                """,
                ("再利用先テスト",),
            )
            destination_id = cur.fetchone()[0]
            ok_ng_test_data["extra_investigation_numbers"].append(
                destination_id
            )

            cur.execute(
                """
                UPDATE "調査"
                SET "最新移行先の調査番号" = %s
                WHERE "調査番号" = %s
                """,
                (destination_id, old_investigation_id),
            )

    response = client.post(
        f"/api/investigations/relations/{old_relation_id}/ng"
    )

    assert response.status_code == 200, response.text
    result = response.json()

    assert result["問い合わせ調査状態"] == 5
    assert result["リアクション内容"] == 2
    assert result["NGでの移行先調査番号"] == destination_id
    assert result["新しい調査番号"] == destination_id
    assert result["新しい問い合わせ調査状態"] == 1

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM "問い合わせ調査"
                WHERE "問い合わせ番号" = %s
                  AND "調査番号" = %s
                """,
                (inquiry_number, destination_id),
            )
            assert cur.fetchone()[0] >= 1


def test_ng_investigation_relation_creates_new_destination(
    monkeypatch,
    ok_ng_test_data,
):
    """最新移行先がなければ、新しい調査を作成する。"""
    _set_test_user(monkeypatch, "T0001")

    inquiry_number = ok_ng_test_data["inquiry_number"]
    old_relation_id = ok_ng_test_data["relation_id"]

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "調査番号"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (old_relation_id,),
            )
            old_investigation_id = cur.fetchone()[0]

    response = client.post(
        f"/api/investigations/relations/{old_relation_id}/ng"
    )

    assert response.status_code == 200, response.text
    result = response.json()

    new_investigation_id = result["新しい調査番号"]
    ok_ng_test_data["extra_investigation_numbers"].append(
        new_investigation_id
    )

    assert new_investigation_id != old_investigation_id
    assert result["問い合わせ調査状態"] == 5
    assert result["リアクション内容"] == 2
    assert result["NGでの移行先調査番号"] == new_investigation_id
    assert result["新しい問い合わせ調査状態"] == 1

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "最新移行先の調査番号"
                FROM "調査"
                WHERE "調査番号" = %s
                """,
                (old_investigation_id,),
            )
            assert cur.fetchone()[0] == new_investigation_id

            cur.execute(
                """
                SELECT "問い合わせ番号"
                FROM "問い合わせ調査"
                WHERE "問い合わせ調査番号" = %s
                """,
                (result["新しい問い合わせ調査番号"],),
            )
            assert cur.fetchone()[0] == inquiry_number


def test_ng_investigation_relation_forbidden(
    monkeypatch,
    ok_ng_test_data,
):
    """問い合わせ者本人以外はNGと回答できない。"""
    _set_test_user(monkeypatch, "J0001")

    relation_id = ok_ng_test_data["relation_id"]

    response = client.post(
        f"/api/investigations/relations/{relation_id}/ng"
    )

    assert response.status_code == 403


def test_ng_investigation_relation_invalid_state(
    monkeypatch,
    ok_ng_test_data,
):
    """relationの状態が3以外ならば、回答不可"""
    _set_test_user(monkeypatch, "T0001")

    relation_id = ok_ng_test_data["relation_id"]
    # リアクション待ち以外の状態に変更する
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE "問い合わせ調査"
                SET "問い合わせ調査状態" = 1
                WHERE "問い合わせ調査番号" = %s
                """,
                (relation_id,),
            )

    response = client.post(
        f"/api/investigations/relations/{relation_id}/ng"
    )

    assert response.status_code == 409