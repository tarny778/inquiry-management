
import { test, expect } from '@playwright/test';

test('未ログイン時にログイン画面が表示される', async ({ page }) => {
  await page.goto('http://localhost:5173');

  await expect(
    page.getByRole('heading', { name: 'ログイン' })
  ).toBeVisible();

  await expect(
    page.getByLabel('職員番号')
  ).toBeVisible();

  await expect(
    page.getByLabel('パスワード')
  ).toBeVisible();

  await expect(
    page.getByRole('button', { name: 'ログイン' })
  ).toBeVisible();
});

test('正しい認証情報でログインすると問い合わせ一覧が表示される', async ({ page }) => {
  await page.goto('http://localhost:5173');

  await page.getByLabel('職員番号').fill('J0001');
  const password = process.env.E2E_TEST_PASSWORD;

  if (!password) {
    throw new Error('環境変数 E2E_TEST_PASSWORD が設定されていません。');
  }

await page.getByLabel('パスワード').fill(password);

  await page.getByRole('button', { name: 'ログイン' }).click();

  await expect(
    page.getByRole('button', { name: 'ログアウト' })
  ).toBeVisible();

    // 問い合わせ一覧の見出しが表示される
  await expect(
    page.getByRole('heading', {
        name: '問い合わせ一覧',
        level: 2,
    })
    ).toBeVisible();
  // 一覧の件数が表示される
  await expect(
    page.getByText(/表示中：\d+件/)
  ).toBeVisible();

  // 表、またはデータがない場合のメッセージが表示される
  await expect(
    page.getByRole('table').or(
      page.getByText('該当する問い合わせはありません。')
    )
  ).toBeVisible();
});