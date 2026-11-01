
import { test, expect } from './fixtures/test.ts'
import { loginAs } from './helpers/auth.ts'

// E2E用の正しいパスワードを取得する
function getE2ETestPassword(): string {
  const password = process.env.E2E_TEST_PASSWORD

  if (!password) {
    throw new Error(
      '環境変数 E2E_TEST_PASSWORD が設定されていません。',
    )
  }

  return password
}

// A-01 未ログイン状態でのアクセス
test('A-01 未ログイン状態でアクセスするとログイン画面が表示される', async ({ page }) => {
  await page.goto('http://127.0.0.1:5173')
  // ログイン画面の表示を確認
  await expect(
    page.getByRole('heading', { name: 'ログイン', level: 2 }),
  ).toBeVisible()

  // 職員番号・パスワードの入力欄を確認
  await expect(page.getByLabel('職員番号')).toBeVisible()
  await expect(page.getByLabel('パスワード')).toBeVisible()

  // ログインボタンを確認
  await expect(
    page.getByRole('button', { name: 'ログイン' }),
  ).toBeVisible()
})


// A-02 正常ログイン
test('A-02 正常ログインすると問い合わせ一覧が表示される', async ({ page }) => {
  const password = getE2ETestPassword()

  await page.goto('http://127.0.0.1:5173')

  await loginAs(page, 'J0001', password)

  // 問い合わせ一覧の表示を確認
  await expect(
    page.getByRole('heading', {
      name: '問い合わせ一覧',
      level: 2,
    }),
  ).toBeVisible()
})


// A-03 ログイン失敗
test('A-03 誤ったパスワードではログインできない', async ({ page }) => {
  await page.goto('http://127.0.0.1:5173')

  await page.getByLabel('職員番号').fill('J0001')
  await page.getByLabel('パスワード').fill(
    'wrong-password-for-e2e-test',
  )

  await page.getByRole('button', { name: 'ログイン' }).click()

  // エラーメッセージが表示される
  await expect(
    page.getByRole('alert'),
  ).toBeVisible()

  // ログイン画面に留まっている
  await expect(
    page.getByRole('heading', { name: 'ログイン', level: 2 }),
  ).toBeVisible()

  // ログイン状態になっていない
  await expect(
    page.getByRole('button', { name: 'ログアウト' }),
  ).toHaveCount(0)
})


// A-04 ログアウト
test('A-04 ログアウトするとログイン画面に戻る', async ({ page }) => {
  const password = getE2ETestPassword()

  await page.goto('http://127.0.0.1:5173')

  await loginAs(page, 'J0001', password)

  // ログアウトする
  await page.getByRole('button', { name: 'ログアウト' }).click()

  // ログイン画面に戻ったことを確認
  await expect(
    page.getByRole('heading', { name: 'ログイン', level: 2 }),
  ).toBeVisible()

  // ログアウトボタンがなくなったことを確認
  await expect(
    page.getByRole('button', { name: 'ログアウト' }),
  ).toHaveCount(0)
})


// A-05 セッション復元
test('A-05 ページ再読み込み後もログイン状態が復元される', async ({ page }) => {
  const password = getE2ETestPassword()

  await page.goto('http://127.0.0.1:5173')

  await loginAs(page, 'J0001', password)

  // ページを再読み込みする
  await page.reload()

  // セッションが復元され、問い合わせ一覧が表示される
  await expect(
    page.getByRole('heading', {
      name: '問い合わせ一覧',
      level: 2,
    }),
  ).toBeVisible()

  // ログイン状態が維持されていることを確認
  await expect(
    page.getByRole('button', { name: 'ログアウト' }),
  ).toBeVisible()
})


// A-06 画面切り替え
test('A-06 問い合わせ一覧と調査一覧を切り替えられる', async ({ page }) => {
  const password = getE2ETestPassword()

  await page.goto('http://127.0.0.1:5173')

  await loginAs(page, 'J0001', password)

  // 問い合わせ一覧から調査一覧へ移動
  await page.getByRole('button', {
    name: '調査一覧へ →',
  }).click()

  await expect(
    page.getByRole('heading', {
      name: '調査一覧',
      level: 2,
    }),
  ).toBeVisible()

  // 調査一覧から問い合わせ一覧へ戻る
  await page.getByRole('button', {
    name: '← 問い合わせ一覧へ',
  }).click()

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ一覧',
      level: 2,
    }),
  ).toBeVisible()
})
