
import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values
from psycopg.conninfo import conninfo_to_dict


# プロジェクトのルートディレクトリ
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 環境ごとの設定
ENVIRONMENTS = {
    "development": {
        "file": ".env",
        "app_env": "development",
        "database": "inquiry_management_dev",
    },
    "test": {
        "file": ".env.test",
        "app_env": "test",
        "database": "inquiry_management_test",
    },
    "e2e": {
        "file": ".env.e2e",
        "app_env": "e2e",
        "database": "inquiry_management_e2e",
    },
}


def main():
    # 1. コマンドライン引数を受け取る
    parser = argparse.ArgumentParser(
        description="安全確認付きdbmate実行スクリプト"
    )

    parser.add_argument(
        "environment",
        choices=ENVIRONMENTS.keys(),
        help="実行対象の環境",
    )

    parser.add_argument(
        "command",
        choices=["status", "migrate"],
        help="dbmateのサブコマンド",
    )

    args = parser.parse_args()

    # 2. 対象環境の設定を取得
    environment = ENVIRONMENTS[args.environment]
    env_file = PROJECT_ROOT / environment["file"]

    if not env_file.is_file():
        sys.exit(f"エラー: 環境ファイルがありません: {env_file}")

    # 3. 環境ファイルを読み込む
    env_values = dotenv_values(env_file, interpolate=False)

    app_env = env_values.get("APP_ENV")
    database_url = env_values.get("DATABASE_URL")

    if not app_env or not database_url:
        sys.exit("エラー: APP_ENV または DATABASE_URL が設定されていません。")

    # 4. APP_ENVを検証
    if app_env != environment["app_env"]:
        sys.exit(
            f"エラー: APP_ENVが一致しません。"
            f"期待値={environment['app_env']}, 実際={app_env}"
        )

    # 5. DATABASE_URLからDB名を取得して検証
    try:
        connection_info = conninfo_to_dict(database_url)
    except Exception:
        sys.exit("エラー: DATABASE_URLを解析できません。")

    database_name = connection_info.get("dbname")

    if database_name != environment["database"]:
        sys.exit(
            f"エラー: 接続先DBが一致しません。"
            f"期待値={environment['database']}, 実際={database_name}"
        )

    # 6. 検証結果を表示
    print(f"環境: {app_env}")
    print(f"接続先DB: {database_name}")
    print(f"実行コマンド: dbmate {args.command}")
    print()

    # 7. migrateの場合は実行前に最終確認
    if args.command == "migrate":
        print("これから上記のDBにマイグレーションを適用します。")
        confirmation = input(
            f"実行する場合はDB名を入力してください: "
        )

        if confirmation != database_name:
            sys.exit("入力されたDB名が一致しないため、処理を中止しました。")

    # 8. dbmateに渡す環境変数を準備
    child_env = os.environ.copy()
    child_env["DATABASE_URL"] = database_url

    # 9. dbmateを実行
    try:
        result = subprocess.run(
            [
                "dbmate",
                "--env-file",
                str(env_file),
                args.command,
            ],
            cwd=PROJECT_ROOT,
            env=child_env,
            check=False,
        )
    except FileNotFoundError:
        sys.exit("エラー: dbmateが見つかりません。")

    # 10. dbmateの終了コードを引き継ぐ
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
