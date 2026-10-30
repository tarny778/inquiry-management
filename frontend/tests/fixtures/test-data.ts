
import type { Client } from 'pg'

/**
 * 問い合わせ作成時に指定できる項目
 */
export interface CreateInquiryOptions {
  問い合わせ職員番号?: string
  受付経路?: string
  問い合わせ分類?: string
  件名?: string
  緊急度?: 1 | 2 | 3
  受付時の処理?: 1 | 2 | 3
  問い合わせ詳細?: string | null
  受付担当者?: string | null
  対応担当者?: string | null
  受信日時?: Date | string
  引き受け日時?: Date | string | null
  対応完了日時?: Date | string | null
}

/**
 * E2Eテスト用の問い合わせを1件作成する。
 *
 * 問い合わせ当時の所属は、問い合わせ職員の現在の所属から取得する。
 * 問い合わせ番号はDBの採番結果を返す。
 */
export async function createInquiry(
  client: Client,
  options: CreateInquiryOptions = {},
): Promise<number> {
  const {
    問い合わせ職員番号 = 'T0001',
    受付経路 = '電話',
    問い合わせ分類 = '分類A',
    件名 = 'E2Eテスト用問い合わせ',
    緊急度 = 2,
    受付時の処理 = 2,
    問い合わせ詳細 = 'E2Eテスト用の問い合わせ詳細',
    受付担当者 = 'J0001',
    対応担当者 = null,
    受信日時 = new Date(),
    引き受け日時 = null,
    対応完了日時 = null,
  } = options

  // 問い合わせ職員の所属を取得する。
  const staffResult = await client.query(
    `
      SELECT "所属"
      FROM "職員"
      WHERE "職員番号" = $1
    `,
    [問い合わせ職員番号],
  )

  if (staffResult.rowCount !== 1) {
    throw new Error(
      `問い合わせ職員が見つかりません: ${問い合わせ職員番号}`,
    )
  }

  const 問い合わせ当時の所属 = staffResult.rows[0].所属

  // 問い合わせを登録し、採番された番号を取得する。
  const result = await client.query(
    `
      INSERT INTO "問い合わせ" (
        "問い合わせ職員番号",
        "問い合わせ当時の所属",
        "受付経路",
        "問い合わせ分類",
        "件名",
        "緊急度",
        "受付時の処理",
        "問い合わせ詳細",
        "受付担当者",
        "対応担当者",
        "受信日時",
        "引き受け日時",
        "対応完了日時"
      )
      VALUES (
        $1, $2, $3, $4, $5, $6, $7,
        $8, $9, $10, $11, $12, $13
      )
      RETURNING "問い合わせ番号"
    `,
    [
      問い合わせ職員番号,
      問い合わせ当時の所属,
      受付経路,
      問い合わせ分類,
      件名,
      緊急度,
      受付時の処理,
      問い合わせ詳細,
      受付担当者,
      対応担当者,
      受信日時,
      引き受け日時,
      対応完了日時,
    ],
  )

  return result.rows[0].問い合わせ番号
}

/**
 * 調査作成時に指定できる項目
 */
export interface CreateInvestigationOptions {
  調査の名称?: string
  原因・仮説?: string | null
  情シス側での対応?: string | null
  問い合わせ者側で必要な対応?: string | null
  調査状態?: 1 | 2 | 3
  調査開始日時?: Date | string
  対応案策定予定日時?: Date | string | null
  進捗更新の次回更新予定日時?: Date | string | null
  リアクション要求日時?: Date | string | null
  調査断念日時?: Date | string | null
  最新移行先の調査番号?: number | null
}

/**
 * E2Eテスト用の調査を1件作成する。
 *
 * 調査番号はDBの採番結果を返す。
 */
export async function createInvestigation(
  client: Client,
  options: CreateInvestigationOptions = {},
): Promise<number> {
  const {
    調査の名称 = 'E2Eテスト用調査',
    原因・仮説 = 'E2Eテスト用の原因・仮説',
    情シス側での対応 = null,
    問い合わせ者側で必要な対応 = null,
    調査状態 = 1,
    調査開始日時 = new Date(),
    対応案策定予定日時 = null,
    進捗更新の次回更新予定日時 = null,
    リアクション要求日時 = null,
    調査断念日時 = null,
    最新移行先の調査番号 = null,
  } = options

  const result = await client.query(
    `
      INSERT INTO "調査" (
        "調査の名称",
        "原因・仮説",
        "情シス側での対応",
        "問い合わせ者側で必要な対応",
        "調査状態",
        "調査開始日時",
        "対応案策定予定日時",
        "進捗更新の次回更新予定日時",
        "リアクション要求日時",
        "調査断念日時",
        "最新移行先の調査番号"
      )
      VALUES (
        $1, $2, $3, $4, $5, $6,
        $7, $8, $9, $10, $11
      )
      RETURNING "調査番号"
    `,
    [
      調査の名称,
      原因・仮説,
      情シス側での対応,
      問い合わせ者側で必要な対応,
      調査状態,
      調査開始日時,
      対応案策定予定日時,
      進捗更新の次回更新予定日時,
      リアクション要求日時,
      調査断念日時,
      最新移行先の調査番号,
    ],
  )

  return result.rows[0].調査番号
}

/**
 * 問い合わせ調査作成時に指定できる項目
 */
export interface CreateInquiryInvestigationOptions {
  問い合わせ調査状態?: 1 | 2 | 3 | 4 | 5
  調査開始日時?: Date | string
  断念日時?: Date | string | null
  リアクション被要求日時?: Date | string | null
  リアクション日時?: Date | string | null
  リアクション内容?: 1 | 2 | null
  NGでの移行先調査番号?: number | null
}

/**
 * E2Eテスト用の問い合わせ調査を1件作成する。
 *
 * 問い合わせ番号と調査番号を指定して関連付ける。
 * 問い合わせ調査番号はDBの採番結果を返す。
 */
export async function createInquiryInvestigation(
  client: Client,
  inquiryNumber: number,
  investigationNumber: number,
  options: CreateInquiryInvestigationOptions = {},
): Promise<number> {
  const {
    問い合わせ調査状態 = 1,
    調査開始日時 = new Date(),
    断念日時 = null,
    リアクション被要求日時 = null,
    リアクション日時 = null,
    リアクション内容 = null,
    NGでの移行先調査番号 = null,
  } = options

  const result = await client.query(
    `
      INSERT INTO "問い合わせ調査" (
        "問い合わせ番号",
        "調査番号",
        "問い合わせ調査状態",
        "調査開始日時",
        "断念日時",
        "リアクション被要求日時",
        "リアクション日時",
        "リアクション内容",
        "NGでの移行先調査番号"
      )
      VALUES (
        $1, $2, $3, $4, $5,
        $6, $7, $8, $9
      )
      RETURNING "問い合わせ調査番号"
    `,
    [
      inquiryNumber,
      investigationNumber,
      問い合わせ調査状態,
      調査開始日時,
      断念日時,
      リアクション被要求日時,
      リアクション日時,
      リアクション内容,
      NGでの移行先調査番号,
    ],
  )

  return result.rows[0].問い合わせ調査番号
}