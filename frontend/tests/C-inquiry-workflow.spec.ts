import { test, expect } from './fixtures/test.ts'
import { loginAs } from './helpers/auth.ts'
import {
  createInquiry,
  createInvestigation,
  createInquiryInvestigation,
} from './fixtures/test-data.ts'
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

// 一般職員としてログインする
async function loginAsT0001(page: Page) {
  await page.goto('http://127.0.0.1:5173')
  await loginAs(page, 'T0001', getE2ETestPassword())

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ一覧',
      level: 2,
    }),
  ).toBeVisible()
}

// 一覧から件名を指定して問い合わせ詳細を開く
async function openInquiryFromList(
  page: Page,
  subject: string,
) {
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

// 詳細画面の項目の値を取得する
function getDetailValue(page: Page, label: string) {
  return page
    .locator('.inquiry-detail-item')
    .filter({
      has: page.locator('dt', { hasText: label }),
    })
    .locator('dd')
}

// C-01 一括引き受け
test('C-01 複数の問い合わせを一括で引き受けられる', async ({ page, db }) => {
  const subject1 = 'E2E-C01-一括引き受け1'
  const subject2 = 'E2E-C01-一括引き受け2'

  // DBに引き受け待ちの問い合わせを2件準備する
  const inquiryNumber1 = await createInquiry(db, {
    件名: subject1,
  })

  const inquiryNumber2 = await createInquiry(db, {
    件名: subject2,
  })

  await loginAsJ0001(page)

  // 2件を選択する
  await page.getByRole('checkbox', {
    name: `問い合わせ番号 ${inquiryNumber1} を選択`,
  }).check()

  await page.getByRole('checkbox', {
    name: `問い合わせ番号 ${inquiryNumber2} を選択`,
  }).check()

  // 一括引き受けを実行する
  page.once('dialog', dialog => dialog.accept())

  await page.getByRole('button', {
    name: '引き受け',
    exact: true,
  }).click()

  // 2件とも対応中になったことを確認する
  const row1 = page.locator('.inquiry-table tbody tr').filter({
    has: page.getByRole('button', { name: subject1 }),
  })

  const row2 = page.locator('.inquiry-table tbody tr').filter({
    has: page.getByRole('button', { name: subject2 }),
  })

  await expect(row1).toContainText('対応中')
  await expect(row2).toContainText('対応中')

  await expect(row1).toContainText('J0001')
  await expect(row2).toContainText('J0001')
})


// C-02 個別引き受け
test('C-02 問い合わせ詳細画面から個別に引き受けられる', async ({ page, db }) => {
  const subject = 'E2E-C02-個別引き受け'

  // DBに引き受け待ちの問い合わせを準備する
  await createInquiry(db, {
    件名: subject,
  })

  await loginAsJ0001(page)
  await openInquiryFromList(page, subject)

  // 個別引き受けを実行する
  page.once('dialog', dialog => dialog.accept())

  await page.getByRole('button', {
    name: '引き受け',
  }).click()

  // 対応中になったことを確認する
  await expect(
    getDetailValue(page, '状態'),
  ).toHaveText('対応中')

  await expect(
    getDetailValue(page, '対応担当者'),
  ).toHaveText('J0001')

  await expect(
    getDetailValue(page, '引き受け日時'),
  ).not.toHaveText('—')
})


// C-03 対応完了
test('C-03 対応中の問い合わせを対応完了にできる', async ({ page, db }) => {
  const subject = 'E2E-C03-対応完了'

  // DBにJ0001が対応中の問い合わせを準備する
  await createInquiry(db, {
    件名: subject,
    対応担当者: 'J0001',
    引き受け日時: new Date(),
  })

  await loginAsJ0001(page)
  await openInquiryFromList(page, subject)

  await expect(
    getDetailValue(page, '状態'),
  ).toHaveText('対応中')

  // 対応完了を実行する
  page.once('dialog', dialog => dialog.accept())

  await page.getByRole('button', {
    name: '対応完了',
  }).click()

  // 対応完了になったことを確認する
  await expect(
    getDetailValue(page, '状態'),
  ).toHaveText('対応完了')

  await expect(
    getDetailValue(page, '対応完了日時'),
  ).not.toHaveText('—')
})


// C-04 未完了の関連調査がある場合の対応完了制限
test('C-04 未完了の関連調査がある問い合わせは対応完了にできない', async ({ page, db }) => {
  const cases = [
    {
      subject: 'E2E-C04-調査中',
      investigationName: 'E2E-C04-調査中の調査',
      investigationStatus: 1 as const,
      relationStatus: 1 as const,
    },
    {
      subject: 'E2E-C04-リアクション待ち',
      investigationName: 'E2E-C04-リアクション待ちの調査',
      investigationStatus: 2 as const,
      relationStatus: 3 as const,
    },
  ]

  // 調査中・リアクション待ちの2パターンをDBに準備する
  for (const item of cases) {
    const inquiryNumber = await createInquiry(db, {
      件名: item.subject,
      対応担当者: 'J0001',
      引き受け日時: new Date(),
    })

    const investigationNumber = await createInvestigation(db, {
      調査の名称: item.investigationName,
      調査状態: item.investigationStatus,
      リアクション要求日時:
        item.relationStatus === 3 ? new Date() : null,
    })

    await createInquiryInvestigation(
      db,
      inquiryNumber,
      investigationNumber,
      {
        問い合わせ調査状態: item.relationStatus,
        リアクション被要求日時:
          item.relationStatus === 3 ? new Date() : null,
      },
    )
  }

  await loginAsJ0001(page)

  for (const item of cases) {
    await openInquiryFromList(page, item.subject)

    await expect(
      getDetailValue(page, '状態'),
    ).toHaveText('対応中')

    // 対応完了を試みる
    page.once('dialog', dialog => dialog.accept())

    await page.getByRole('button', {
      name: '対応完了',
    }).click()

    // エラーが表示されることを確認
    const errorMessage = page.getByRole('alert')

    await expect(errorMessage).toBeVisible()

    await expect(errorMessage).toContainText(
      '調査中またはリアクション待ちの問い合わせ調査が残っています。',
    )

    // 問い合わせは対応中のままである
    await expect(
      getDetailValue(page, '状態'),
    ).toHaveText('対応中')

    // 一覧に戻る
    await page.getByRole('button', {
      name: '↑ 一覧に戻る',
    }).click()

    await expect(
      page.getByRole('heading', {
        name: '問い合わせ一覧',
        level: 2,
      }),
    ).toBeVisible()
  }
})


// C-05 対応完了した問い合わせの再開
test('C-05 対応完了した問い合わせを再開できる', async ({ page, db }) => {
  const subject = 'E2E-C05-再開'

  // DBにJ0001が対応した完了済み問い合わせを準備する
  await createInquiry(db, {
    件名: subject,
    対応担当者: 'J0001',
    引き受け日時: new Date(),
    対応完了日時: new Date(),
  })

  await loginAsJ0001(page)
  // 初期条件を解除する
  await page.getByRole('checkbox', {
    name: '初期条件',
  }).uncheck()

  // 件名で検索する
  await page.getByRole('textbox', {
    name: 'キーワード（件名）',
  }).fill(subject)

  await page.getByRole('button', {
    name: '検索',
    exact: true,
  }).click()

  // 検索結果から詳細画面を開く
  await page.locator('.inquiry-table').getByRole('button', {
    name: subject,
    exact: true,
  }).click()

  // 詳細画面が表示されたことを確認
  await expect(
    page.getByRole('heading', {
      name: '問い合わせ詳細',
    }),
  ).toBeVisible()

  await expect(
    getDetailValue(page, '状態'),
  ).toHaveText('対応完了')

  // 再開を実行する
  page.once('dialog', dialog => dialog.accept())

  await page.getByRole('button', {
    name: '再開',
  }).click()

  // 対応中に戻ったことを確認する
  await expect(
    getDetailValue(page, '状態'),
  ).toHaveText('対応中')

  // 対応完了日時がNULLに戻ったことを確認する
  await expect(
    getDetailValue(page, '対応完了日時'),
  ).toHaveText('—')

  // 対応担当者と引き受け日時は維持される
  await expect(
    getDetailValue(page, '対応担当者'),
  ).toHaveText('J0001')

  await expect(
    getDetailValue(page, '引き受け日時'),
  ).not.toHaveText('—')
})


// C-06 職員の所属・権限による操作ボタンの制御
test('C-06 情報システム課職員と一般職員で操作ボタンの表示が異なる', async ({ page, db }) => {
  const subject = 'E2E-C06-権限制御'

  // DBに引き受け待ちの問い合わせを準備する
  await createInquiry(db, {
    件名: subject,
  })

  // 情報システム課職員としてログイン
  await loginAsJ0001(page)
  await openInquiryFromList(page, subject)

  // 情報システム課職員には操作ボタンが表示される
  const editButton = page.getByRole('button', { name: '編集' })
  const acceptButton = page.getByRole('button', { name: '引き受け' })
  const completeButton = page.getByRole('button', { name: '対応完了' })
  const reopenButton = page.getByRole('button', { name: '再開' })

  await expect(editButton).toBeVisible()
  await expect(acceptButton).toBeVisible()
  await expect(completeButton).toBeVisible()
  await expect(reopenButton).toBeVisible()

  // 引き受け待ちの状態に応じた有効・無効を確認
  await expect(editButton).toBeEnabled()
  await expect(acceptButton).toBeEnabled()
  await expect(completeButton).toBeDisabled()
  await expect(reopenButton).toBeDisabled()

  // 一般職員に切り替える
  await page.getByRole('button', {
    name: 'ログアウト',
  }).click()

  await loginAsT0001(page)
  await openInquiryFromList(page, subject)

  // 一般職員には状態遷移・編集ボタンが表示されない
  await expect(
    page.getByRole('button', { name: '編集' }),
  ).toHaveCount(0)

  await expect(
    page.getByRole('button', { name: '引き受け' }),
  ).toHaveCount(0)

  await expect(
    page.getByRole('button', { name: '対応完了' }),
  ).toHaveCount(0)

  await expect(
    page.getByRole('button', { name: '再開' }),
  ).toHaveCount(0)
})