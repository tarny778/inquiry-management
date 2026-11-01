
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict


# プロジェクト直下の .env を読み込む。
# すでにOS側に設定されている環境変数は上書きしない。
ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_FILE, override=False)


# 実行環境と接続先DBの対応
EXPECTED_DATABASES = {
    "development": "inquiry_management_dev",
    "test": "inquiry_management_test",
    "e2e": "inquiry_management_e2e",
    "production": "inquiry_management",
}


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    cors_origins: list[str]


def load_settings() -> Settings:
    # 必須環境変数を取得する。未設定なら起動時にエラーとする。
    app_env = os.environ["APP_ENV"]
    database_url = os.environ["DATABASE_URL"]
    cors_origins_value = os.environ["CORS_ORIGINS"]

    # 実行環境を検証
    if app_env not in EXPECTED_DATABASES:
        raise ValueError(
            f"APP_ENVの値が不正です: {app_env}"
        )

    # DATABASE_URLを解析
    try:
        connection_info = conninfo_to_dict(database_url)
    except Exception as exc:
        raise ValueError(
            "DATABASE_URLの形式が不正です。"
        ) from exc

    # PostgreSQLの接続先DB名を検証
    actual_database = connection_info.get("dbname")
    expected_database = EXPECTED_DATABASES[app_env]

    if actual_database != expected_database:
        raise ValueError(
            "APP_ENVとDATABASE_URLの組み合わせが不正です。"
            f" APP_ENV={app_env},"
            f" 期待するDB={expected_database},"
            f" 指定されたDB={actual_database}"
        )

    # CORS許可オリジンをリスト化
    cors_origins = [
        origin.strip()
        for origin in cors_origins_value.split(",")
        if origin.strip()
    ]

    if not cors_origins:
        raise ValueError(
            "CORS_ORIGINSを1つ以上指定してください。"
        )

    return Settings(
        app_env=app_env,
        database_url=database_url,
        cors_origins=cors_origins,
    )


# アプリ全体で共有する設定
settings = load_settings()
