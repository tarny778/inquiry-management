
-- 問い合わせ管理Webアプリ
-- 初期マイグレーション
--
-- 現在のDB構造を新規DBに構築するためのDDL。
-- 既存DBに対しては、構造が一致していることを確認したうえで
-- マイグレーション履歴に初期バージョンを登録する。
--
-- migrate:up

-- =========================================================
-- 1. 職員
-- =========================================================

CREATE TABLE "職員" (
    "職員番号" VARCHAR(20) PRIMARY KEY,
    "氏名" VARCHAR(30) NOT NULL,
    "所属" VARCHAR(30) NOT NULL
);


-- =========================================================
-- 2. 職員認証情報
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
-- 3. ログインセッション
-- =========================================================

CREATE TABLE "ログインセッション" (
    "セッションIDハッシュ" VARCHAR(64) PRIMARY KEY,
    "職員番号" VARCHAR(20) NOT NULL,
    "作成日時" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "無操作期限" TIMESTAMPTZ NOT NULL,
    "絶対有効期限" TIMESTAMPTZ NOT NULL,
    "最終利用日時" TIMESTAMPTZ,
    "失効日時" TIMESTAMPTZ,

    CONSTRAINT "ck_ログインセッション_期限"
        CHECK ("無操作期限" <= "絶対有効期限"),

    CONSTRAINT "fk_ログインセッション_職員認証情報"
        FOREIGN KEY ("職員番号")
        REFERENCES "職員認証情報" ("職員番号")
        ON DELETE CASCADE
);

CREATE INDEX "idx_ログインセッション_職員番号"
    ON "ログインセッション" ("職員番号");


-- =========================================================
-- 4. 問い合わせ
-- =========================================================

CREATE TABLE "問い合わせ" (
    "問い合わせ番号" INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "問い合わせ職員番号" VARCHAR(20),
    "問い合わせ当時の所属" VARCHAR(30) NOT NULL,
    "受付経路" VARCHAR(20) NOT NULL,
    "問い合わせ分類" VARCHAR(30) NOT NULL,
    "件名" VARCHAR(100) NOT NULL,
    "緊急度" INTEGER NOT NULL
        CHECK ("緊急度" IN (1, 2, 3)),
    "受付時の処理" INTEGER NOT NULL
        CHECK ("受付時の処理" IN (1, 2, 3)),
    "問い合わせ詳細" VARCHAR(1000),
    "受付担当者" VARCHAR(20),
    "対応担当者" VARCHAR(20),
    "受信日時" TIMESTAMPTZ NOT NULL,
    "登録日時" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "引き受け日時" TIMESTAMPTZ,
    "対応完了日時" TIMESTAMPTZ,

    CONSTRAINT "fk_問い合わせ_問い合わせ職員"
        FOREIGN KEY ("問い合わせ職員番号")
        REFERENCES "職員" ("職員番号")
        ON DELETE SET NULL,

    CONSTRAINT "fk_問い合わせ_受付担当者"
        FOREIGN KEY ("受付担当者")
        REFERENCES "職員" ("職員番号")
        ON DELETE SET NULL,

    CONSTRAINT "fk_問い合わせ_対応担当者"
        FOREIGN KEY ("対応担当者")
        REFERENCES "職員" ("職員番号")
        ON DELETE SET NULL
);


-- =========================================================
-- 5. 調査
-- =========================================================

CREATE TABLE "調査" (
    "調査番号" INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "調査の名称" VARCHAR(30) NOT NULL,
    "原因・仮説" VARCHAR(1000),
    "情シス側での対応" VARCHAR(1000),
    "問い合わせ者側で必要な対応" VARCHAR(1000),
    "調査状態" INTEGER NOT NULL DEFAULT 1
        CHECK ("調査状態" IN (1, 2, 3)),
    "調査開始日時" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "対応案策定予定日時" TIMESTAMPTZ,
    "進捗更新の次回更新予定日時" TIMESTAMPTZ,
    "リアクション要求日時" TIMESTAMPTZ,
    "調査断念日時" TIMESTAMPTZ,
    "最新移行先の調査番号" INTEGER,

    CONSTRAINT "fk_調査_最新移行先"
        FOREIGN KEY ("最新移行先の調査番号")
        REFERENCES "調査" ("調査番号")
);


-- =========================================================
-- 6. 問い合わせ調査
-- =========================================================

CREATE TABLE "問い合わせ調査" (
    "問い合わせ調査番号" INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "調査番号" INTEGER NOT NULL,
    "問い合わせ番号" INTEGER NOT NULL,
    "問い合わせ調査状態" INTEGER NOT NULL DEFAULT 1
        CHECK ("問い合わせ調査状態" IN (1, 2, 3, 4, 5)),
    "調査開始日時" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "断念日時" TIMESTAMPTZ,
    "リアクション被要求日時" TIMESTAMPTZ,
    "リアクション日時" TIMESTAMPTZ,
    "リアクション内容" INTEGER
        CHECK ("リアクション内容" IN (1, 2)),
    "NGでの移行先調査番号" INTEGER,

    CONSTRAINT "fk_問い合わせ調査_調査"
        FOREIGN KEY ("調査番号")
        REFERENCES "調査" ("調査番号"),

    CONSTRAINT "fk_問い合わせ調査_問い合わせ"
        FOREIGN KEY ("問い合わせ番号")
        REFERENCES "問い合わせ" ("問い合わせ番号"),

    CONSTRAINT "fk_問い合わせ調査_NG移行先"
        FOREIGN KEY ("NGでの移行先調査番号")
        REFERENCES "調査" ("調査番号"),

    CONSTRAINT "uq_問い合わせ調査_問い合わせ_調査"
        UNIQUE ("問い合わせ番号", "調査番号"),

    CONSTRAINT "ck_問い合わせ調査_NG移行先は別調査"
        CHECK (
            "NGでの移行先調査番号" IS NULL
            OR "NGでの移行先調査番号" <> "調査番号"
        )
);


-- migrate:down

-- 初期マイグレーションは既存DBの構造を登録する基準点でもある。
-- 誤って rollback した場合のテーブル・データ消失を防ぐため、
-- このマイグレーションは取り消し不可とする。
DO $$
BEGIN
    RAISE EXCEPTION
        '初期マイグレーションは取り消せません。';
END
$$;
