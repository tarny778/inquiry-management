"""本番(AWS)用の、デモ職員とログインアカウントを登録するスクリプト。

backend コンテナの中で実行する:
  docker compose --env-file .env.docker -f compose.prod.yaml \
      exec backend python scripts/setup_demo_accounts.py

実行内容:
  1. 職員テーブルに、デモ用の職員を登録する(既に存在する場合は変更しない)
  2. 入力されたパスワードをハッシュ化し、職員認証情報に登録する
     (既に存在する場合は、パスワードを更新する)

何度実行しても安全に動くようにしてある。
"""

from getpass import getpass
from pathlib import Path
import sys

import argon2
import psycopg

# プロジェクトルートをPythonの検索対象に追加
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import settings

EXPECTED_DATABASE = "inquiry_management"

# (職員番号, 氏名, 所属)
STAFF = [
    ("J0001", "情シス太郎", "情報システム課"),
    ("J0002", "情シス次郎", "情報システム課"),
    ("T0001", "山田太郎", "総務課"),
]


def main():
    # 接続先の安全確認
    if settings.app_env != "production":
        raise RuntimeError("APP_ENVがproductionではありません。")

    password = getpass("デモ用アカウントのパスワード: ")
    password_confirm = getpass("パスワード(確認): ")

    if not password:
        raise RuntimeError("パスワードが空です。")

    if len(password) > 128:
        raise RuntimeError("パスワードは128文字以内にしてください。")

    if password != password_confirm:
        raise RuntimeError("パスワードが一致しません。")

    hasher = argon2.PasswordHasher()

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # 実際の接続先DBを確認
            cur.execute("SELECT current_database()")
            database_name = cur.fetchone()[0]

            if database_name != EXPECTED_DATABASE:
                raise RuntimeError(f"接続先DBが違います: {database_name}")

            # 既存アカウントのログイン可否を確認
            cur.execute(
                'SELECT "職員番号", "ログイン可否" FROM "職員認証情報"'
            )
            accounts = {row[0]: row[1] for row in cur.fetchall()}

            for staff_number, _, _ in STAFF:
                if staff_number in accounts and not accounts[staff_number]:
                    raise RuntimeError(
                        f"{staff_number} はログイン不可です。"
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

            # 2. パスワードをハッシュ化して認証情報を登録
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

                print(f"{staff_number} {staff_name}: 登録しました")

    print("デモ用3アカウントの登録が完了しました。")


if __name__ == "__main__":
    main()