import os
from pathlib import Path

from dotenv import load_dotenv
import pytest
import psycopg


# プロジェクトのルートディレクトリ
ROOT_DIR = Path(__file__).resolve().parents[1]

# テスト専用の環境設定ファイル
TEST_ENV_FILE = ROOT_DIR / ".env.test"

STAFF = [
    ("J0001", "情シス太郎", "情報システム課"),
    ("J0002", "情シス次郎", "情報システム課"),
    ("T0001", "山田太郎", "総務課"),
]


# .env.test が存在しなければテストを開始しない
if not TEST_ENV_FILE.is_file():
    raise RuntimeError(
        ".env.test が見つかりません。"
        "テスト環境の設定を確認してください。"
    )


# テスト用の環境変数を読み込む
load_dotenv(TEST_ENV_FILE, override=True)


# APP_ENV が test でなければテストを開始しない
if os.environ.get("APP_ENV") != "test":
    raise RuntimeError(
        "テスト実行時の APP_ENV は test である必要があります。"
    )


# config.py の設定読み込みとDB名の検証を実行する
from config import settings


if settings.app_env != "test":
    raise RuntimeError(
        "テスト環境の設定が正しく読み込まれていません。"
    )

@pytest.fixture(scope="session", autouse=True)
def seed_staff():
    # テスト用DB以外には、絶対に書き込まない
    assert settings.app_env == "test", "APP_ENVがtestではありません"

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            for number, name, dept in STAFF:
                cur.execute(
                    """
                    INSERT INTO "職員" ("職員番号", "氏名", "所属")
                    VALUES (%s, %s, %s)
                    ON CONFLICT ("職員番号") DO NOTHING
                    """,
                     (number, name, dept),
                )