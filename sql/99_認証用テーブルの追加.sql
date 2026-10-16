
-- =========================================================
-- 認証テーブル追加
-- 既存の業務テーブルは削除・再作成しない。
-- =========================================================

BEGIN;

-- =========================================================
-- 1. 職員認証情報
-- アカウントを発行した職員だけ登録する。
-- =========================================================
CREATE TABLE "職員認証情報" (
    "職員番号" VARCHAR(20) PRIMARY KEY,
    "パスワードハッシュ" TEXT NOT NULL,
    "ログイン可否" BOOLEAN NOT NULL DEFAULT TRUE,
    "作成日時" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "更新日時" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "パスワード更新日時" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "fk_職員認証情報_職員"
        FOREIGN KEY ("職員番号")
        REFERENCES "職員" ("職員番号")
        ON DELETE CASCADE
);

-- =========================================================
-- 2. ログインセッション
-- セッションIDそのものではなくSHA-256ハッシュを保存する。
-- =========================================================
CREATE TABLE "ログインセッション" (
    "セッションIDハッシュ" VARCHAR(64) PRIMARY KEY,
    "職員番号" VARCHAR(20) NOT NULL,
    "作成日時" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "無操作期限" TIMESTAMPTZ NOT NULL,
    "絶対有効期限" TIMESTAMPTZ NOT NULL,
    "最終利用日時" TIMESTAMPTZ,
    "失効日時" TIMESTAMPTZ,

    CONSTRAINT "fk_ログインセッション_職員認証情報"
        FOREIGN KEY ("職員番号")
        REFERENCES "職員認証情報" ("職員番号")
        ON DELETE CASCADE,

    CONSTRAINT "ck_ログインセッション_期限"
        CHECK ("無操作期限" <= "絶対有効期限")
);

-- 職員ごとのセッション検索に使用する。
CREATE INDEX "idx_ログインセッション_職員番号"
    ON "ログインセッション" ("職員番号");

COMMIT;
