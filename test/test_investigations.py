import os

os.environ["DATABASE_NAME"] = "inquiry_management_test"

import psycopg
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


import main


def _set_test_user(monkeypatch, staff_number="J0001"):
    """テストで操作者を切り替える。"""
    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda: main.CurrentUser(
            職員番号=staff_number,
            氏名="テスト職員",
            所属="情報システム課",
        ),
    )



# テスト用データを作成
import pytest


@pytest.fixture
def investigation_search_test_data():
    """問題調査一覧APIのテストデータを作成し、終了後に削除する。"""

    inquiry_numbers = []
    investigation_numbers = []
    link_numbers = []

    try:
        # 1. 問い合わせを3件登録する
        for title in [
            "問題調査一覧APIテスト-A",
            "問題調査一覧APIテスト-B",
            "問題調査一覧APIテスト-C",
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
                    "問い合わせ詳細": "問題調査一覧APIの自動テスト用",
                    "受信日時": None,
                },
            )

            assert response.status_code == 200, response.text
            inquiry_numbers.append(
                response.json()["問い合わせ番号"]
            )

        with psycopg.connect("dbname=inquiry_management_test") as conn:
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

                # 2. 問題調査を2件登録する
                cur.execute(
                    '''
                    INSERT INTO "問題調査" (
                        "問題調査の名称や仮説"
                    )
                    VALUES (%s)
                    RETURNING "問題調査番号"
                    ''',
                    ("問題調査一覧APIテスト-複数問い合わせ",),
                )
                investigation_numbers.append(cur.fetchone()[0])

                cur.execute(
                    '''
                    INSERT INTO "問題調査" (
                        "問題調査の名称や仮説"
                    )
                    VALUES (%s)
                    RETURNING "問題調査番号"
                    ''',
                    ("問題調査一覧APIテスト-単一問い合わせ",),
                )
                investigation_numbers.append(cur.fetchone()[0])

                # 3. 問題調査と問い合わせを関連付ける
                # 1件目の問題調査に問い合わせA・Bを関連付ける
                for inquiry_number in inquiry_numbers[:2]:
                    cur.execute(
                        '''
                        INSERT INTO "問い合わせ問題調査" (
                            "問題調査番号",
                            "問い合わせ番号"
                        )
                        VALUES (%s, %s)
                        RETURNING "問い合わせ問題調査番号"
                        ''',
                        (
                            investigation_numbers[0],
                            inquiry_number,
                        ),
                    )
                    link_numbers.append(cur.fetchone()[0])

                # 2件目の問題調査に問い合わせCを関連付ける
                cur.execute(
                    '''
                    INSERT INTO "問い合わせ問題調査" (
                        "問題調査番号",
                        "問い合わせ番号"
                    )
                    VALUES (%s, %s)
                    RETURNING "問い合わせ問題調査番号"
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
        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                if link_numbers:
                    cur.execute(
                        '''
                        DELETE FROM "問い合わせ問題調査"
                        WHERE "問い合わせ問題調査番号" = ANY(%s)
                        ''',
                        (link_numbers,),
                    )

                if investigation_numbers:
                    cur.execute(
                        '''
                        DELETE FROM "問題調査"
                        WHERE "問題調査番号" = ANY(%s)
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


#問題調査の検索一覧取得のテスト
def test_search_investigations_response(
    investigation_search_test_data,
):
    """問題調査一覧APIが必要な情報を返すことを確認する。"""

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.get(
        "/api/investigations",
        params={"問題調査番号": investigation_number},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["問題調査番号"] == investigation_number
    assert item["問題調査の名称や仮説"] == (
        "問題調査一覧APIテスト-複数問い合わせ"
    )
    assert item["問題調査状態"] == 1
    assert item["対応担当者職員氏名"] is not None
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
        params={"問題調査番号": investigation_number},
    )

    assert response.status_code == 200, response.text

    item = response.json()["items"][0]

    assert item["関連問い合わせ件数"] == 1
    assert item["自分の問い合わせを含む"] is False


def test_search_investigations_by_requester_number(
    investigation_search_test_data,
):
    """問い合わせ者の職員番号で問題調査を絞り込めることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"問い合わせ職員番号": "T0001"},
    )

    assert response.status_code == 200, response.text

    returned_numbers = {
        item["問題調査番号"]
        for item in response.json()["items"]
    }

    assert set(
        investigation_search_test_data["investigation_numbers"]
    ).issubset(returned_numbers)


def test_search_investigations_by_handler_number(
    investigation_search_test_data,
):
    """対応担当者の職員番号で問題調査を絞り込めることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"対応担当者職員番号": "J0001"},
    )

    assert response.status_code == 200, response.text

    returned_numbers = {
        item["問題調査番号"]
        for item in response.json()["items"]
    }

    assert set(
        investigation_search_test_data["investigation_numbers"]
    ).issubset(returned_numbers)

def test_search_investigations_by_name(
    investigation_search_test_data,
):
    """問題調査の名称や仮説で部分一致検索できることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"問題調査の名称や仮説": "複数問い合わせ"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["問題調査番号"] == (
        investigation_search_test_data["investigation_numbers"][0]
    )


def test_search_investigations_by_status(
    investigation_search_test_data,
):
    """問題調査状態で検索できることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"問題調査状態": 1},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total"] >= 2

    assert all(
        item["問題調査状態"] == 1
        for item in data["items"]
    )


def test_search_investigations_by_requester_name(
    investigation_search_test_data,
):
    """問い合わせ者の氏名で部分一致検索できることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"問い合わせ者氏名": "情シス太郎"},
    )

    assert response.status_code == 200, response.text

    returned_numbers = {
        item["問題調査番号"]
        for item in response.json()["items"]
    }

    assert (
        investigation_search_test_data["investigation_numbers"][0]
        in returned_numbers
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
            "問題調査状態": 1,
            "対応担当者職員番号": "J0001",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    returned_numbers = {
        item["問題調査番号"]
        for item in data["items"]
    }

    expected_numbers = set(
        investigation_search_test_data["investigation_numbers"]
    )

    assert expected_numbers.issubset(returned_numbers)

    assert all(
        item["問題調査状態"] == 1
        for item in data["items"]
    )


def test_search_investigations_second_page(
    investigation_search_test_data,
):
    """2ページ目で1ページ目とは異なる問題調査を取得できることを確認する。"""

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
        first_data["items"][0]["問題調査番号"]
        != second_data["items"][0]["問題調査番号"]
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
    """定義されていない問題調査状態4が拒否されることを確認する。"""

    response = client.get(
        "/api/investigations",
        params={"問題調査状態": 4},
    )

    assert response.status_code == 422



# =========================================================
# 問題調査詳細取得APIのテスト
# =========================================================


# 正常に問題調査の詳細と関連一覧を取得できる
def test_get_investigation_response(investigation_search_test_data):
    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.get(
        f"/api/investigations/{investigation_number}"
    )

    assert response.status_code == 200

    data = response.json()

    # 問題調査そのものの情報
    assert data["問題調査番号"] == investigation_number
    assert "問題調査の名称や仮説" in data
    assert "問題の原因" in data
    assert "情シス側での対応" in data
    assert "問い合わせ者側で必要な対応" in data
    assert "問題調査状態" in data
    assert "調査開始日時" in data
    assert "対応案策定予定日時" in data
    assert "進捗更新の次回更新予定日時" in data
    assert "リアクション要求日時" in data
    assert "問題調査断念日時" in data
    assert "最新移行先の問題調査番号" in data

    # 関連一覧と操作者自身の問い合わせの有無
    assert "関連する問い合わせ問題調査" in data
    assert isinstance(data["関連する問い合わせ問題調査"], list)
    assert data["自分の問い合わせを含む"] is True


# 関連する問い合わせ問題調査が複数件返る
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

    related = response.json()["関連する問い合わせ問題調査"]

    # フィクスチャでは、この問題調査に2件を関連付けている
    assert len(related) == 2

    # それぞれの問い合わせ問題調査の情報が返る
    assert len({
        item["問い合わせ問題調査番号"]
        for item in related
    }) == 2

    assert len({
        item["問い合わせ番号"]
        for item in related
    }) == 2

    for item in related:
        assert "問い合わせ者氏名" in item
        assert "対応担当者氏名" in item
        assert "問い合わせ問題調査状態" in item
        assert "リアクション内容" in item
        assert "NGでの移行先問題調査番号" in item


# 存在しない問題調査番号では404を返す
def test_get_investigation_not_found():
    response = client.get("/api/investigations/999999999")

    assert response.status_code == 404


# 関連する問い合わせ問題調査がなくても詳細を取得できる
def test_get_investigation_without_related_inquiries():
    # 関連レコードを持たない問題調査をテスト用に作成
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "問題調査" (
                    "問題調査の名称や仮説"
                )
                VALUES (%s)
                RETURNING "問題調査番号"
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

        assert data["問題調査番号"] == investigation_number
        assert data["関連する問い合わせ問題調査"] == []
        assert data["自分の問い合わせを含む"] is False

    finally:
        # このテストで作成した問題調査を削除
        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    DELETE FROM "問題調査"
                    WHERE "問題調査番号" = %s
                    ''',
                    (investigation_number,),
                )


# 問題調査の編集テスト
def test_update_investigation_success(
    investigation_search_test_data,
    monkeypatch,
):
    """関連問い合わせの対応担当者は問題調査を編集できる。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={
            "問題調査の名称や仮説": "編集後の問題調査名",
            "問題の原因": "編集後の原因",
        },
    )

    assert response.status_code == 200, response.text

    result = response.json()
    assert result["問題調査番号"] == investigation_number
    assert result["問題調査の名称や仮説"] == "編集後の問題調査名"
    assert result["問題の原因"] == "編集後の原因"


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
            "問題調査の名称や仮説": "変更してはいけない名称",
        },
    )

    assert response.status_code == 403


# 関連する問い合わせがない問題調査は編集できない
def test_update_investigation_without_related_inquiries(
    monkeypatch,
):
    """関連する問い合わせがない問題調査は編集できない。"""
    _set_test_user(monkeypatch, "J0001")

    # 関連レコードを持たない問題調査を作成
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "問題調査" (
                    "問題調査の名称や仮説"
                )
                VALUES (%s)
                RETURNING "問題調査番号"
                ''',
                ("編集権限テスト-関連なし",),
            )
            investigation_number = cur.fetchone()[0]

    try:
        response = client.patch(
            f"/api/investigations/{investigation_number}",
            json={
                "問題調査の名称や仮説": "変更してはいけない名称",
            },
        )

        assert response.status_code == 403

    finally:
        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    DELETE FROM "問題調査"
                    WHERE "問題調査番号" = %s
                    ''',
                    (investigation_number,),
                )


# 存在しない問題調査番号の編集は404を返す
def test_update_investigation_not_found(monkeypatch):
    """存在しない問題調査は編集できない。"""
    _set_test_user(monkeypatch, "J0001")

    response = client.patch(
        "/api/investigations/999999999",
        json={
            "問題調査の名称や仮説": "存在しない問題調査",
        },
    )

    assert response.status_code == 404


# 調査中ではない問題調査は編集できない
@pytest.mark.parametrize("state", [2, 3])
def test_update_investigation_not_editable_state(
    investigation_search_test_data,
    monkeypatch,
    state,
):
    """状態が2または3の問題調査は編集できない。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    # テスト対象の問題調査を指定した状態に変更
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問題調査"
                SET "問題調査状態" = %s
                WHERE "問題調査番号" = %s
                ''',
                (state, investigation_number),
            )

    response = client.patch(
        f"/api/investigations/{investigation_number}",
        json={
            "問題調査の名称や仮説": "変更してはいけない名称",
        },
    )

    assert response.status_code == 409


# 問題調査編集APIの入力値検証テスト

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
        json={"問題調査の名称や仮説": None},
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
            "問題調査の名称や仮説": "入力検証テスト",
            "問題調査状態": 3,
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
        json={"問題調査の名称や仮説": "あ" * 31},
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
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問題調査"
                SET
                    "問題調査の名称や仮説" = %s,
                    "問題の原因" = %s,
                    "情シス側での対応" = %s
                WHERE "問題調査番号" = %s
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
        json={"問題の原因": "更新後の原因"},
    )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["問題調査の名称や仮説"] == "更新前の名称"
    assert result["問題の原因"] == "更新後の原因"
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
    with psycopg.connect("dbname=inquiry_management_test") as conn:
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
        json={"問題調査の名称や仮説": "変更してはいけない名称"},
    )

    assert response.status_code == 403


# 問題調査の断念APIテスト

def test_abandon_investigation_success(
    investigation_search_test_data,
    monkeypatch,
):
    """関連レコードをすべて状態2にして、問題調査を断念できる。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    response = client.post(
        f"/api/investigations/{investigation_number}/abandon"
    )

    assert response.status_code == 200, response.text

    result = response.json()
    assert result["問題調査番号"] == investigation_number
    assert result["問題調査状態"] == 3
    assert result["問題調査断念日時"] is not None

    # 問題調査本体の状態を確認
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "問題調査状態", "問題調査断念日時"
                FROM "問題調査"
                WHERE "問題調査番号" = %s
                ''',
                (investigation_number,),
            )
            investigation_row = cur.fetchone()

            assert investigation_row[0] == 3
            assert investigation_row[1] is not None

            # 関連する問い合わせ問題調査がすべて状態2であることを確認
            cur.execute(
                '''
                SELECT COUNT(*)
                FROM "問い合わせ問題調査"
                WHERE "問題調査番号" = %s
                  AND "問い合わせ問題調査状態" <> 2
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
    """関連する問い合わせがない問題調査は断念できない。"""
    _set_test_user(monkeypatch, "J0001")

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "問題調査" (
                    "問題調査の名称や仮説"
                )
                VALUES (%s)
                RETURNING "問題調査番号"
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
        with psycopg.connect("dbname=inquiry_management_test") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    DELETE FROM "問題調査"
                    WHERE "問題調査番号" = %s
                    ''',
                    (investigation_number,),
                )


def test_abandon_investigation_not_found(monkeypatch):
    """存在しない問題調査は断念できない。"""
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
    """問題調査の状態が2または3なら断念できない。"""
    _set_test_user(monkeypatch, "J0001")

    investigation_number = (
        investigation_search_test_data["investigation_numbers"][0]
    )

    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問題調査"
                SET "問題調査状態" = %s
                WHERE "問題調査番号" = %s
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
    問題調査本体と関連レコードの更新をロールバックする。
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
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE "問い合わせ問題調査"
                SET "問い合わせ問題調査状態" = 3
                WHERE "問題調査番号" = %s
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

    # 問題調査本体が状態1のまま、断念日時も未設定であることを確認
    with psycopg.connect("dbname=inquiry_management_test") as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "問題調査状態", "問題調査断念日時"
                FROM "問題調査"
                WHERE "問題調査番号" = %s
                ''',
                (investigation_number,),
            )
            investigation_row = cur.fetchone()

            assert investigation_row[0] == 1
            assert investigation_row[1] is None

            # 関連レコードも、API実行前の状態に戻っていることを確認
            cur.execute(
                '''
                SELECT "問い合わせ番号", "問い合わせ問題調査状態"
                FROM "問い合わせ問題調査"
                WHERE "問題調査番号" = %s
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

