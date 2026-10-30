
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

// 新規登録テスト
test('問い合わせを新規登録すると詳細画面に表示される', async ({ page }) => {
  await page.goto('http://localhost:5173');

  // ログイン
  const password = process.env.E2E_TEST_PASSWORD;

  if (!password) {
    throw new Error('環境変数 E2E_TEST_PASSWORD が設定されていません。');
  }

  await page.getByLabel('職員番号').fill('J0001');
  await page.getByLabel('パスワード').fill(password);
  await page.getByRole('button', { name: 'ログイン' }).click();

  // 問い合わせ一覧が表示されるまで待つ
  await expect(
    page.getByRole('heading', { name: '問い合わせ一覧', level: 2 })
  ).toBeVisible();

  // 新規登録画面を開く
  await page.getByRole('button', { name: /新規登録/ }).click();

  await expect(
    page.getByRole('heading', { name: '問い合わせ新規登録' })
  ).toBeVisible();

  // フォームに入力する
  const title = `E2Eテスト ${Date.now()}`;

  await page.getByLabel(/問い合わせ職員番号/).fill('T0001');
  await page.getByLabel(/^受付経路/).selectOption('電話');
  await page.getByLabel(/^受付時の処理/).selectOption('2');
  await page.getByLabel(/^件名/).fill(title);
  await page.getByLabel(/^問い合わせ分類/).selectOption('分類A');
  await page.getByLabel(/^緊急度/).selectOption('2');
  await page.getByLabel('問い合わせ詳細').fill('E2Eテストで登録した問い合わせです。');

  // 登録する
  await page.getByRole('button', { name: '登録' }).click();

  // 登録後、詳細画面に内容が表示されることを確認する
  await expect(
    page.getByRole('heading', { name: '問い合わせ詳細' })
  ).toBeVisible();

  await expect(page.getByText(title, { exact: true })).toBeVisible();
  await expect(page.getByText('T0001', { exact: true })).toBeVisible();
  await expect(page.getByText('引き受け待ち', { exact: true })).toBeVisible();
});


test('問い合わせ一覧から件名をクリックすると詳細画面が表示される', async ({ page }) => {
  await page.goto('http://localhost:5173');

  // ログイン
  const password = process.env.E2E_TEST_PASSWORD;

  if (!password) {
    throw new Error('環境変数 E2E_TEST_PASSWORD が設定されていません。');
  }

  await page.getByLabel('職員番号').fill('J0001');
  await page.getByLabel('パスワード').fill(password);
  await page.getByRole('button', { name: 'ログイン' }).click();

  // 問い合わせ一覧が表示されることを確認
  await expect(
    page.getByRole('heading', { name: '問い合わせ一覧', level: 2 })
  ).toBeVisible();

  // 一覧に問い合わせが1件以上あることを確認
  const firstInquiry = page.getByRole('table').locator('tbody tr').first();

  await expect(firstInquiry).toBeVisible();

  // 先頭行の件名をクリック
  const subjectButton = firstInquiry.locator('td').nth(3).getByRole('button');
  const title = await subjectButton.textContent();

  await subjectButton.click();

  // 詳細画面に遷移し、クリックした件名が表示されることを確認
  await expect(
    page.getByRole('heading', { name: '問い合わせ詳細' })
  ).toBeVisible();

  await expect(
    page.getByText(title!.trim(), { exact: true })
  ).toBeVisible();

  // 一覧に戻るボタンも表示されることを確認
  await expect(
    page.getByRole('button', { name: /一覧に戻る/ })
  ).toBeVisible();
});
