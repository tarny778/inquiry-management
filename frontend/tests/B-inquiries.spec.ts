import { test, expect } from './fixtures/test.ts'
import { loginAs } from './helpers/auth.ts'
import { createInquiry } from './fixtures/test-data.ts'
import type { Page } from '@playwright/test'

// E2E用パスワードを取得する
function getE2ETestPassword(): string {
  const password = process.env.E2E_TEST_PASSWORD

  if (!password) {
    throw new Error(
      '環境変数 E2E_TEST_PASSWORD が設定されていません。',
    )
  }

  return password
}

// 情報システム課職員としてログインする
async function loginAsJ0001(page: Page) {
  await page.goto('http://127.0.0.1:5173')
  await loginAs(page, 'J0001', getE2ETestPassword())

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ一覧',
      level: 2,
    }),
  ).toBeVisible()
}

// 問い合わせを画面から新規登録する
async function createInquiryThroughUI(
  page: Page,
  handling: '1' | '2' | '3',
  subject: string,
) {
  await page.getByRole('button', { name: /新規登録/ }).click()

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ新規登録',
      level: 2,
    }),
  ).toBeVisible()

  await page.getByLabel('問い合わせ職員番号').fill('T0001')
  await page.getByLabel('受付時の処理').selectOption(handling)
  await page.getByLabel('件名').fill(subject)

  await page.getByRole('button', { name: '登録' }).click()

  // 登録後は詳細画面へ移動する
  await expect(
    page.getByRole('heading', {
      name: '問い合わせ詳細',
      level: 2,
    }),
  ).toBeVisible()

  await expect(
    page.locator('.inquiry-detail').getByText(subject, {
      exact: true,
    }),
  ).toBeVisible()
}

// DBに準備した問い合わせを一覧から開く
async function openInquiryFromList(
  page: Page,
  subject: string,
) {
  await expect(
    page.locator('.inquiry-table').getByRole('button', {
      name: subject,
    }),
  ).toBeVisible()

  await page.locator('.inquiry-table').getByRole('button', {
    name: subject,
  }).click()

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ詳細',
      level: 2,
    }),
  ).toBeVisible()
}

// 詳細画面の項目の値を取得するためのLocator
function getDetailValue(page: Page, label: string) {
  return page
    .locator('.inquiry-detail-item')
    .filter({
      has: page.locator('dt', { hasText: label }),
    })
    .locator('dd')
}

// B-01 要調査の問い合わせ登録
test('B-01 要調査の問い合わせを登録すると引き受け待ちになる', async ({ page }) => {
  await loginAsJ0001(page)

  await createInquiryThroughUI(
    page,
    '2',
    'E2E-B01-要調査の問い合わせ',
  )

  await expect(getDetailValue(page, '状態')).toHaveText('引き受け待ち')
})

// B-02 即時解決の問い合わせ登録
test('B-02 即時解決の問い合わせを登録すると対応完了になる', async ({ page }) => {
  await loginAsJ0001(page)

  await createInquiryThroughUI(
    page,
    '1',
    'E2E-B02-即時解決の問い合わせ',
  )

  await expect(getDetailValue(page, '状態')).toHaveText('対応完了')

  // 対応担当者・引き受け日時はNULL
  await expect(getDetailValue(page, '対応担当者')).toHaveText('—')
  await expect(getDetailValue(page, '引き受け日時')).toHaveText('—')

  // 対応完了日時は設定されている
  await expect(getDetailValue(page, '対応完了日時')).not.toHaveText('—')
})

// B-03 他所属へ案内する問い合わせ登録
test('B-03 他所属へ案内する問い合わせを登録すると対応完了になる', async ({ page }) => {
  await loginAsJ0001(page)

  await createInquiryThroughUI(
    page,
    '3',
    'E2E-B03-他所属案内の問い合わせ',
  )

  await expect(getDetailValue(page, '状態')).toHaveText('対応完了')

  // 対応担当者・引き受け日時はNULL
  await expect(getDetailValue(page, '対応担当者')).toHaveText('—')
  await expect(getDetailValue(page, '引き受け日時')).toHaveText('—')

  // 対応完了日時は設定されている
  await expect(getDetailValue(page, '対応完了日時')).not.toHaveText('—')
})

// B-04 引き受け待ちの問い合わせ編集
test('B-04 引き受け待ちの問い合わせを編集できる', async ({ page, db }) => {
  const subject = 'E2E-B04-編集前の件名'

  // DBに引き受け待ちの問い合わせを準備する
  await createInquiry(db, {
    件名: subject,
  })

  await loginAsJ0001(page)
  await openInquiryFromList(page, subject)

  await page.getByRole('button', { name: '編集' }).click()

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ編集',
      level: 2,
    }),
  ).toBeVisible()

  await page.getByLabel('件名').fill('E2E-B04-編集後の件名')
  await page.getByRole('button', { name: '保存' }).click()

  // 詳細画面に戻り、変更内容が表示される
  await expect(
    page.locator('.inquiry-detail').getByText(
      'E2E-B04-編集後の件名',
      { exact: true },
    ),
  ).toBeVisible()

  await expect(getDetailValue(page, '状態')).toHaveText('引き受け待ち')
})

// B-05 対応中の問い合わせ編集
test('B-05 対応中の問い合わせを編集できる', async ({ page, db }) => {
  const subject = 'E2E-B05-編集前の件名'

  // DBに対応中の問い合わせを準備する
  await createInquiry(db, {
    件名: subject,
    対応担当者: 'J0001',
    引き受け日時: new Date(),
  })

  await loginAsJ0001(page)
  await openInquiryFromList(page, subject)

  await expect(getDetailValue(page, '状態')).toHaveText('対応中')

  // 編集画面へ移動
  await page.getByRole('button', { name: '編集' }).click()

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ編集',
      level: 2,
    }),
  ).toBeVisible()

  await page.getByLabel('件名').fill('E2E-B05-編集後の件名')
  await page.getByRole('button', { name: '保存' }).click()

  // 詳細画面に戻り、変更内容が表示される
  await expect(
    page.locator('.inquiry-detail').getByText(
      'E2E-B05-編集後の件名',
      { exact: true },
    ),
  ).toBeVisible()

  await expect(getDetailValue(page, '状態')).toHaveText('対応中')
})

// B-06 編集結果の表示確認
test('B-06 編集結果が詳細画面と一覧に反映される', async ({ page, db }) => {
  const subject = 'E2E-B06-編集前の件名'

  // DBに引き受け待ちの問い合わせを準備する
  await createInquiry(db, {
    件名: subject,
  })

  await loginAsJ0001(page)
  await openInquiryFromList(page, subject)

  await page.getByRole('button', { name: '編集' }).click()

  await page.getByLabel('件名').fill('E2E-B06-一覧反映確認')
  await page.getByRole('button', { name: '保存' }).click()

  // 詳細画面で確認
  await expect(
    page.locator('.inquiry-detail').getByText(
      'E2E-B06-一覧反映確認',
      { exact: true },
    ),
  ).toBeVisible()

  // 一覧へ戻る
  await page.getByRole('button', { name: '↑ 一覧に戻る' }).click()

  // 一覧の件名にも反映されている
  await expect(
    page.locator('.inquiry-table').getByRole('button', {
      name: 'E2E-B06-一覧反映確認',
    }),
  ).toBeVisible()
})

// B-07 対応完了問い合わせの編集制限
test('B-07 対応完了した問い合わせは編集できない', async ({ page }) => {
  await loginAsJ0001(page)

  // 即時解決として画面から登録し、対応完了状態を作る
  await createInquiryThroughUI(
    page,
    '1',
    'E2E-B07-編集制限確認',
  )

  await expect(getDetailValue(page, '状態')).toHaveText('対応完了')

  // 編集ボタンは表示されるが、無効になっている
  await expect(
    page.getByRole('button', { name: '編集' }),
  ).toBeVisible()

  await expect(
    page.getByRole('button', { name: '編集' }),
  ).toBeDisabled()
})