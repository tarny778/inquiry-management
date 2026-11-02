from pathlib import Path
import sys
from getpass import getpass

import argon2
import psycopg
from dotenv import load_dotenv

# プロジェクトルートをPythonの検索対象に追加
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Docker用の環境変数を読み込む
load_dotenv(ROOT_DIR / ".env.docker", override=True)

from config import settings


EXPECTED_DATABASE = "inquiry_management_dev"

STAFF = [
    ("J0001", "情シス太郎"),
    ("J0002", "情シス次郎"),
    ("T0001", "山田太郎"),
]


def main():
    # 接続先の安全確認
    if settings.app_env != "development":
        raise RuntimeError("APP_ENVがdevelopmentではありません。")

    password = getpass("3名に設定する開発用パスワード: ")
    password_confirm = getpass("パスワード（確認）: ")

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
                raise RuntimeError(
                    f"接続先DBが違います: {database_name}"
                )

            # 職員マスタの存在確認
            cur.execute('SELECT "職員番号" FROM "職員"')
            existing_staff = {
                row[0] for row in cur.fetchall()
            }

            for staff_number, _ in STAFF:
                if staff_number not in existing_staff:
                    raise RuntimeError(
                        f"職員マスタに {staff_number} がありません。"
                    )

            # 既存アカウントのログイン可否を確認
            cur.execute(
                'SELECT "職員番号", "ログイン可否" '
                'FROM "職員認証情報"'
            )

            accounts = {
                row[0]: row[1] for row in cur.fetchall()
            }

            for staff_number, _ in STAFF:
                if (
                    staff_number in accounts
                    and not accounts[staff_number]
                ):
                    raise RuntimeError(
                        f"{staff_number} はログイン不可です。"
                    )

            # パスワードをハッシュ化して登録
            for staff_number, staff_name in STAFF:
                password_hash = hasher.hash(password)

                cur.execute(
                    '''
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
                    ''',
                    (staff_number, password_hash),
                )

                print(f"{staff_number} {staff_name}: 登録しました")

    print("Docker用3アカウントの登録が完了しました。")


if __name__ == "__main__":
    main()