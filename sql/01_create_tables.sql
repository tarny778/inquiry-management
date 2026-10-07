-- 問い合わせ管理Webアプリ
-- 2026-10-07
-- DB再構築用DDL
--
-- 目的：
--   03_データベース設計.md の内容に基づき、
--   問い合わせ管理システムのテーブルを構築する。
--
-- 注意：
--   本DDLは既存テーブルを削除して再作成する。
--   開発初期段階・テスト用データベースでの利用を想定する。

-- =========================================================
-- 既存テーブル削除
-- =========================================================

DROP TABLE IF EXISTS "問い合わせ問題";
DROP TABLE IF EXISTS "対応担当者変更履歴";
DROP TABLE IF EXISTS "問い合わせ";
DROP TABLE IF EXISTS "問題";
DROP TABLE IF EXISTS "職員";


-- =========================================================
-- 職員
-- =========================================================

CREATE TABLE "職員" (
    "職員番号" VARCHAR(20) PRIMARY KEY,
    "職員氏名" VARCHAR(30) NOT NULL,
    "職員所属" VARCHAR(30) NOT NULL
);


-- =========================================================
-- 問題
-- =========================================================

CREATE TABLE "問題" (
    "問題番号" INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "問題名称" VARCHAR(30) NOT NULL,
    "問題の原因" VARCHAR(1000),
    "情シス側での対応" VARCHAR(1000),
    "問い合わせ者側で必要な対応" VARCHAR(1000),
    "原因と対応の確定日時" TIMESTAMP
);


-- =========================================================
-- 問い合わせ
-- =========================================================

CREATE TABLE "問い合わせ" (
    "問い合わせ番号" INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "問い合わせ職員番号" VARCHAR(20) NOT NULL,
    "問い合わせ当時の所属" VARCHAR(30) NOT NULL,
    "受付経路" VARCHAR(20) NOT NULL,
    "問い合わせ分類" VARCHAR(30) NOT NULL,
    "件名" VARCHAR(100) NOT NULL,
    "緊急度" VARCHAR(10) NOT NULL,
    "受付時の処理" INTEGER NOT NULL
        CHECK ("受付時の処理" IN (1, 2, 3)),
    "問い合わせ詳細" VARCHAR(1000),
    "受付担当者" VARCHAR(30) NOT NULL,
    "対応担当者" VARCHAR(30),
    "受信日時" TIMESTAMP NOT NULL,
    "登録日時" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "引き受け日時" TIMESTAMP,
    "対応完了日時" TIMESTAMP,

    CONSTRAINT "fk_問い合わせ_職員"
        FOREIGN KEY ("問い合わせ職員番号")
        REFERENCES "職員" ("職員番号")
);


-- =========================================================
-- 問い合わせ問題
-- =========================================================

CREATE TABLE "問い合わせ問題" (
    "問題番号" INTEGER NOT NULL,
    "問い合わせ番号" INTEGER NOT NULL,
    "現在の調査状況" VARCHAR(1000) NOT NULL,
    "内部メモ" VARCHAR(1000),
    "予定解決日時" TIMESTAMP,
    "次回進捗更新予定日時" TIMESTAMP,
    "調査開始日時" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "調査を終えた日時" TIMESTAMP,
    "問題解決確認日時" TIMESTAMP,
    "未解決リアクション日時" TIMESTAMP,

    PRIMARY KEY ("問題番号", "問い合わせ番号"),

    CONSTRAINT "fk_問い合わせ問題_問題"
        FOREIGN KEY ("問題番号")
        REFERENCES "問題" ("問題番号"),

    CONSTRAINT "fk_問い合わせ問題_問い合わせ"
        FOREIGN KEY ("問い合わせ番号")
        REFERENCES "問い合わせ" ("問い合わせ番号")
);


-- =========================================================
-- 対応担当者変更履歴
-- =========================================================

CREATE TABLE "対応担当者変更履歴" (
    "問い合わせ番号" INTEGER NOT NULL,
    "変更日時" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "変更後の対応担当者氏名" VARCHAR(30) NOT NULL,
    "変更処理した職員氏名" VARCHAR(30) NOT NULL,

    PRIMARY KEY ("問い合わせ番号", "変更日時"),

    CONSTRAINT "fk_対応担当者変更履歴_問い合わせ"
        FOREIGN KEY ("問い合わせ番号")
        REFERENCES "問い合わせ" ("問い合わせ番号")
);

-- =========================================================
-- テスト用職員マスタ
-- =========================================================

INSERT INTO "職員" (
    "職員番号",
    "職員氏名",
    "職員所属"
)
VALUES (
    'T0001',
    '山田太郎',
    '総務課'
);