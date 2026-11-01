
import { Client } from 'pg'

const EXPECTED_DATABASE = 'inquiry_management_e2e'

/**
 * E2E用DBに接続する。
 * 接続後、実際のDB名を検証する。
 */
export async function connectE2EDatabase(): Promise<Client> {
  const connectionString = process.env.DATABASE_URL

  if (!connectionString) {
    throw new Error('DATABASE_URL が設定されていません。')
  }

  const client = new Client({
    connectionString,
  })

  try {
    await client.connect()

    const result = await client.query(
      'SELECT current_database() AS database_name',
    )

    const databaseName = result.rows[0]?.database_name

    if (databaseName !== EXPECTED_DATABASE) {
      throw new Error(
        `接続先DBが違います。期待値: ${EXPECTED_DATABASE}, 実際: ${databaseName}`,
      )
    }

    return client
  } catch (error) {
    await client.end().catch(() => undefined)
    throw error
  }
}

/**
 * E2E用DBの業務データとセッションを削除する。
 * 職員・職員認証情報・採番シーケンスは維持する。
 */
export async function resetE2EDatabase(
  client: Client,
): Promise<void> {
  // 接続時だけでなく、削除直前にもDB名を検証する。
  const result = await client.query(
    'SELECT current_database() AS database_name',
  )

  const databaseName = result.rows[0]?.database_name

  if (databaseName !== EXPECTED_DATABASE) {
    throw new Error(
      `削除を中止しました。接続先DBが違います: ${databaseName}`,
    )
  }

  await client.query('BEGIN')

  try {
    // セッションを削除
    await client.query('DELETE FROM "ログインセッション"')

    // 問い合わせと調査の関連を削除
    await client.query('DELETE FROM "問い合わせ調査"')

    // 調査テーブル内の自己参照を解除
    await client.query(
      'UPDATE "調査" SET "最新移行先の調査番号" = NULL',
    )

    // 調査と問い合わせを削除
    await client.query('DELETE FROM "調査"')
    await client.query('DELETE FROM "問い合わせ"')

    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK')
    throw error
  }
}
