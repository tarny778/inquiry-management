"""E2Eテスト用の職員データと認証情報を登録するスクリプト。

実行内容:
  1. 職員テーブルに、E2E用の職員を登録する(既に存在する場合は変更しない)
  2. 環境変数 E2E_TEST_PASSWORD のパスワードをハッシュ化し、
     職員認証情報に登録する(既に存在する場合は、パスワードを更新する)

何度実行しても安全に動くようにしてある。
"""

import os
import sys
from pathlib import Path

import argon2
import psycopg
from dotenv import load_dotenv

# プロジェクトルートをPythonの検索対象に追加
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# プロジェクトルートの .env.e2e を読み込む
load_dotenv(ROOT_DIR / ".env.e2e", override=True)

from config import settings

EXPECTED_DATABASE = "inquiry_management_e2e"

# (職員番号, 氏名, 所属)
# ※所属は例です。実際の値に合わせて修正してください。
STAFF = [
    ("J0001", "情シス太郎", "情報システム課"),
    ("J0002", "情シス次郎", "情報システム課"),
    ("T0001", "山田太郎", "総務課"),
]


def validate_database(conn):
    """接続先が、E2E用のDBであることを確認する。"""
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        database_name = cur.fetchone()[0]

    if database_name != EXPECTED_DATABASE:
        raise RuntimeError(f"接続先が違います: {database_name}")


def main():
    if settings.app_env != "e2e":
        raise RuntimeError(
            "APP_ENV が e2e ではありません。処理を中止します。"
        )

    password = os.environ.get("E2E_TEST_PASSWORD")

    if not password:
        raise RuntimeError("E2E_TEST_PASSWORD が設定されていません。")

    if len(password) > 128:
        raise RuntimeError(
            "E2E_TEST_PASSWORD は128文字以内にしてください。"
        )

    hasher = argon2.PasswordHasher()

    with psycopg.connect(settings.database_url) as conn:
        validate_database(conn)

        with conn.cursor() as cur:
            # 既存の認証情報を確認
            cur.execute(
                'SELECT "職員番号", "ログイン可否" FROM "職員認証情報"'
            )
            accounts = {row[0]: row[1] for row in cur.fetchall()}

            # ログイン不可のアカウントは変更しない
            for staff_number, _, _ in STAFF:
                if staff_number in accounts and not accounts[staff_number]:
                    raise RuntimeError(
                        f"{staff_number} はログイン不可に設定されています。"
                    )

            # 1. 職員を登録(既にある場合は変更しない)
            for staff_number, staff_name, department in STAFF:
                cur.execute(
                    """
                    INSERT INTO "職員" ("職員番号", "氏名", "所属")
                    VALUES (%s, %s, %s)
                    ON CONFLICT ("職員番号") DO NOTHING
                    """,
                    (staff_number, staff_name, department),
                )

            # 2. 全員に、同じパスワードを設定
            for staff_number, staff_name, _ in STAFF:
                password_hash = hasher.hash(password)

                cur.execute(
                    """
                    INSERT INTO "職員認証情報" (
                        "職員番号",
                        "パスワードハッシュ"
                    )
                    VALUES (%s, %s)
                    ON CONFLICT ("職員番号")
                    DO UPDATE SET
                        "パスワードハッシュ" = EXCLUDED."パスワードハッシュ",
                        "更新日時" = CURRENT_TIMESTAMP,
                        "パスワード更新日時" = CURRENT_TIMESTAMP
                    """,
                    (staff_number, password_hash),
                )

                if staff_number in accounts:
                    print(f"{staff_number} {staff_name}: パスワードを更新しました")
                else:
                    print(f"{staff_number} {staff_name}: 登録しました")

    print("E2E用3アカウントの登録が完了しました。")


if __name__ == "__main__":
    main()