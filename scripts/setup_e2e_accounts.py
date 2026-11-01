
from pathlib import Path
import os

import argon2
import psycopg
from dotenv import load_dotenv

# プロジェクトルートの .env.e2e を読み込む
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env.e2e", override=True)

from config import settings

EXPECTED_DATABASE = "inquiry_management_e2e"

STAFF = [
    ("J0001", "情シス太郎"),
    ("J0002", "情シス次郎"),
    ("T0001", "山田太郎"),
]

def validate_database(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        database_name = cur.fetchone()[0]

    if database_name != EXPECTED_DATABASE:
        raise RuntimeError(
            f"接続先が違います: {database_name}"
        )

def main():
    if settings.app_env != "e2e":
        raise RuntimeError(
            "APP_ENV が e2e ではありません。処理を中止します。"
        )

    password = os.environ.get("E2E_TEST_PASSWORD")

    if not password:
        raise RuntimeError(
            "E2E_TEST_PASSWORD が設定されていません。"
        )

    if len(password) > 128:
        raise RuntimeError(
            "E2E_TEST_PASSWORD は128文字以内にしてください。"
        )
    hasher = argon2.PasswordHasher()

    with psycopg.connect(settings.database_url) as conn:
        validate_database(conn)

        with conn.cursor() as cur:
            # 対象職員が職員マスタに存在することを確認
            cur.execute('SELECT "職員番号" FROM "職員"')
            existing_staff = {
                row[0] for row in cur.fetchall()
            }

            for staff_number, _ in STAFF:
                if staff_number not in existing_staff:
                    raise RuntimeError(
                        f"職員テーブルに {staff_number} がありません。"
                    )

            # 既存の認証情報を確認
            cur.execute(
                'SELECT "職員番号", "ログイン可否" '
                'FROM "職員認証情報"'
            )

            accounts = {
                row[0]: row[1]
                for row in cur.fetchall()
            }

            # ログイン不可のアカウントは変更しない
            for staff_number, _ in STAFF:
                if (
                    staff_number in accounts
                    and not accounts[staff_number]
                ):
                    raise RuntimeError(
                        f"{staff_number} はログイン不可に設定されています。"
                    )

            # 3人に同じパスワードを設定
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
                        "パスワードハッシュ" = EXCLUDED."パスワードハッシュ"
                    ''',
                    (staff_number, password_hash),
                )

                if staff_number in accounts:
                    print(f"{staff_number} {staff_name}: パスワードを更新しました")
                else:
                    print(f"{staff_number} {staff_name}: 登録しました")

    print("E2E用3アカウントのパスワード統一が完了しました。")


if __name__ == "__main__":
    main()