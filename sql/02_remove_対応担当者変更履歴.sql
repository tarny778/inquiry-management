-- 既存DBから未使用の対応担当者変更履歴テーブルを削除する。
-- 実行前に接続先DBを確認すること。
-- sql/01_create_tables.sql は全テーブルを再構築するため、既存DBでは実行しない。

DROP TABLE IF EXISTS "対応担当者変更履歴";
