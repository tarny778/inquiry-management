
import os
from getpass import getpass

import argon2
import psycopg


EXPECTED_DATABASE = "inquiry_management_e2e"

STAFF = [
    ("J0001", "情シス太郎"),
    ("J0002", "情シス次郎"),
    ("T0001", "山田太郎"),
]


def get_database_url():
    url = os.getenv("E2E_DATABASE_URL")

    if not url:
        raise RuntimeError("E2E_DATABASE_URL が設定されていません。")

    return url


def validate_database(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        database_name = cur.fetchone()[0]

    if database_name != EXPECTED_DATABASE:
        raise RuntimeError(
            f"接続先が違います: {database_name}"
        )


def prompt_password():
    while True:
        password = getpass("E2Eテスト用パスワード: ")
        confirmation = getpass("確認のため再入力: ")

        if not password:
            print("パスワードは空にできません。")
            continue

        if len(password) > 128:
            print("パスワードは128文字以内にしてください。")
            continue

        if password != confirmation:
            print("パスワードが一致しません。")
            continue

        return password


def main():
    database_url = get_database_url()
    password = prompt_password()
    hasher = argon2.PasswordHasher()

    with psycopg.connect(database_url) as conn:
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