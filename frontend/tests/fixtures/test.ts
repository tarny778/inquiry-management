import { test as base, expect } from '@playwright/test'
import type { Client } from 'pg'

import {
  connectE2EDatabase,
  resetE2EDatabase,
} from './database.ts'

/**
 * E2Eテストで共通して使用するfixture
 */
type TestFixtures = {
  db: Client
}

/**
 * DB fixtureを組み込んだ共通test
 *
 * 各テストについて、
 * 1. E2E用DBに接続
 * 2. テスト開始前にDBをリセット
 * 3. テストにDB接続を渡す
 * 4. テスト終了後にDBをリセット
 * 5. DB接続を閉じる
 */
export const test = base.extend<TestFixtures>({
  // Playwrightのfixture仕様上、空のオブジェクト分割代入が必要なため、この行だけESLintを抑制する
  // eslint-disable-next-line no-empty-pattern
  db: async ({}, provide) => {
    const client = await connectE2EDatabase()

    try {
      // テスト開始前の初期化
      await resetE2EDatabase(client)

      // テスト本体にDB接続を渡す
      await provide(client)

    } finally {
      try {
        // テスト終了後の後片付け
        await resetE2EDatabase(client)
      } finally {
        // DB接続を閉じる
        await client.end()
      }
    }
  },
})

export { expect }