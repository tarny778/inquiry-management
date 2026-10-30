
import { expect, type Page } from '@playwright/test'

/**
 * ログイン画面からログインする共通関数
 *
 * @param page Playwrightのブラウザページ
 * @param staffNumber ログインする職員番号
 * @param password パスワード
 */
export async function loginAs(
  page: Page,
  staffNumber: string,
  password: string,
): Promise<void> {
  // 職員番号を入力
  await page.getByLabel('職員番号').fill(staffNumber)

  // パスワードを入力
  await page.getByLabel('パスワード').fill(password)

  // ログインボタンをクリック
  await page.getByRole('button', { name: 'ログイン' }).click()

  // ログイン完了を確認
  await expect(
    page.getByRole('button', { name: 'ログアウト' }),
  ).toBeVisible()
}
