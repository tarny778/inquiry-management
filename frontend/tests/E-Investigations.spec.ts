
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

// 情報システム課職員J0001としてログインする
async function loginAsJ0001(page: Page): Promise<void> {
  await page.goto('http://127.0.0.1:5173')

  await loginAs(page, 'J0001', getE2ETestPassword())

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ一覧',
      level: 2,
    }),
  ).toBeVisible()
}

// 問い合わせを対応中の状態で作成する
async function createInProgressInquiry(
  db: Parameters<typeof createInquiry>[0],
  subject: string,
): Promise<number> {
  return createInquiry(db, {
    件名: subject,
    問い合わせ職員番号: 'T0001',
    対応担当者: 'J0001',
    引き受け日時: new Date(),
  })
}

// 問い合わせ一覧から調査一覧へ移動する
async function openInvestigationList(page: Page): Promise<void> {
  await page.getByRole('button', {
    name: '調査一覧へ →',
  }).click()

  await expect(
    page.getByRole('heading', {
      name: '調査一覧',
      level: 2,
    }),
  ).toBeVisible()
}

// 調査一覧から調査詳細を開く
async function openInvestigationDetail(
  page: Page,
  investigationName: string,
): Promise<void> {
  await openInvestigationList(page)

  await expect(
    page.locator('.investigation-table').getByRole('button', {
      name: investigationName,
      exact: true,
    }),
  ).toBeVisible()

  await page.locator('.investigation-table').getByRole('button', {
    name: investigationName,
    exact: true,
  }).click()

  await expect(
    page.getByRole('heading', {
      name: '調査詳細',
      level: 2,
    }),
  ).toBeVisible()
}

// 調査詳細画面の項目の値を取得する
function getInvestigationDetailValue(
  page: Page,
  label: string,
) {
  return page
    .locator('.investigation-detail-item')
    .filter({
      has: page.locator('dt', { hasText: label }),
    })
    .locator('dd')
}


// E-01 複数問い合わせから調査を新規作成
test('E-01 複数の問い合わせから新しい調査を作成・関連付けできる', async ({
  page,
  db,
}) => {
  const subject1 = 'E2E-E01-問い合わせ1'
  const subject2 = 'E2E-E01-問い合わせ2'
  const investigationName = 'E2E-E01-複数問い合わせの調査'

  // 関連付け対象の問い合わせを2件作成する
  const inquiryNumber1 = await createInProgressInquiry(
    db,
    subject1,
  )

  const inquiryNumber2 = await createInProgressInquiry(
    db,
    subject2,
  )

  await loginAsJ0001(page)

  // 2件の問い合わせを選択する
  await page.getByRole('checkbox', {
    name: `問い合わせ番号 ${inquiryNumber1} を選択`,
  }).check()

  await page.getByRole('checkbox', {
    name: `問い合わせ番号 ${inquiryNumber2} を選択`,
  }).check()

  // 選択件数を確認する
  await expect(
    page.locator('.selected-count'),
  ).toHaveText('選択中：2件')

  // 新しい調査の作成ダイアログを開く
  await page.getByRole('button', {
    name: '新しい調査を作成・関連付け',
  }).click()

  await expect(
    page.getByRole('heading', {
      name: '新しい調査を作成・関連付け',
    }),
  ).toBeVisible()

  // 調査名を入力して作成する
  await page.getByLabel('調査の名称・仮説（30文字以内）')
    .fill(investigationName)

  // 確認ダイアログを承認する
  page.once('dialog', (dialog) => dialog.accept())

  await page.getByRole('button', {
    name: '作成・関連付ける',
  }).click()

  // 処理完了メッセージを確認する
  await expect(
    page.getByRole('status'),
  ).toHaveText('問い合わせを新規の調査に関連付けました。')

  // DB上に調査が1件作成されたことを確認する
  const investigationResult = await db.query(
    `
      SELECT "調査番号"
      FROM "調査"
      WHERE "調査の名称" = $1
    `,
    [investigationName],
  )

  expect(investigationResult.rows).toHaveLength(1)

  const investigationNumber =
    investigationResult.rows[0].調査番号

  // 2件の問い合わせが関連付けられたことを確認する
  const relationResult = await db.query(
    `
      SELECT
        "問い合わせ番号",
        "問い合わせ調査状態"
      FROM "問い合わせ調査"
      WHERE "調査番号" = $1
      ORDER BY "問い合わせ番号"
    `,
    [investigationNumber],
  )

  expect(
    relationResult.rows.map((row) => row.問い合わせ番号),
  ).toEqual(
    [inquiryNumber1, inquiryNumber2].sort((a, b) => a - b),
  )

  // どちらの関連も「調査中」であることを確認する
  expect(
    relationResult.rows.every(
      (row) => row.問い合わせ調査状態 === 1,
    ),
  ).toBe(true)
})


// E-02 1件の問い合わせから調査を新規作成
test('E-02 1件の問い合わせから新しい調査を作成・関連付けできる', async ({
  page,
  db,
}) => {
  const subject = 'E2E-E02-問い合わせ'
  const investigationName = 'E2E-E02-単独問い合わせの調査'

  // 問い合わせを1件作成する
  const inquiryNumber = await createInProgressInquiry(
    db,
    subject,
  )

  await loginAsJ0001(page)

  // 対象の問い合わせを選択する
  await page.getByRole('checkbox', {
    name: `問い合わせ番号 ${inquiryNumber} を選択`,
  }).check()

  await expect(
    page.locator('.selected-count'),
  ).toHaveText('選択中：1件')

  // 新しい調査の作成ダイアログを開く
  await page.getByRole('button', {
    name: '新しい調査を作成・関連付け',
  }).click()

  await page.getByLabel('調査の名称・仮説（30文字以内）')
    .fill(investigationName)

  // 確認ダイアログを承認する
  page.once('dialog', (dialog) => dialog.accept())

  await page.getByRole('button', {
    name: '作成・関連付ける',
  }).click()

  // 処理完了メッセージを確認する
  await expect(
    page.getByRole('status'),
  ).toHaveText('問い合わせを新規の調査に関連付けました。')

  // DB上に調査が1件作成されたことを確認する
  const investigationResult = await db.query(
    `
      SELECT "調査番号"
      FROM "調査"
      WHERE "調査の名称" = $1
    `,
    [investigationName],
  )

  expect(investigationResult.rows).toHaveLength(1)

  const investigationNumber =
    investigationResult.rows[0].調査番号

  // 問い合わせが1件だけ関連付けられたことを確認する
  const relationResult = await db.query(
    `
      SELECT
        "問い合わせ番号",
        "問い合わせ調査状態"
      FROM "問い合わせ調査"
      WHERE "調査番号" = $1
    `,
    [investigationNumber],
  )

  expect(relationResult.rows).toHaveLength(1)
  expect(relationResult.rows[0].問い合わせ番号).toBe(
    inquiryNumber,
  )
  expect(
    relationResult.rows[0].問い合わせ調査状態,
  ).toBe(1)
})


// E-03 既存調査への関連付け
test('E-03 進行中の既存調査に問い合わせを関連付けできる', async ({
  page,
  db,
}) => {
  const existingSubject = 'E2E-E03-既存の関連問い合わせ'
  const targetSubject = 'E2E-E03-新しく関連付けたい問い合わせ'
  const investigationName = 'E2E-E03-既存調査'

  // 既存調査を作成する
  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
  })

  // 既存調査に、すでに1件の問い合わせを関連付けておく
  const existingInquiryNumber = await createInProgressInquiry(
    db,
    existingSubject,
  )

  await createInquiryInvestigation(
    db,
    existingInquiryNumber,
    investigationNumber,
  )

  // 新しく関連付ける問い合わせを作成する
  const targetInquiryNumber = await createInProgressInquiry(
    db,
    targetSubject,
  )

  await loginAsJ0001(page)

  // 対象の問い合わせを選択する
  await page.getByRole('checkbox', {
    name: `問い合わせ番号 ${targetInquiryNumber} を選択`,
  }).check()

  // 既存調査への関連付けダイアログを開く
  await page.getByRole('button', {
    name: '既存の調査に関連付け',
  }).click()

  await expect(
    page.getByRole('heading', {
      name: '既存の調査に関連付け',
    }),
  ).toBeVisible()

  // 既存調査の番号を入力する
  await page.getByLabel('調査番号').fill(
    String(investigationNumber),
  )

  // 確認ダイアログを承認する
  page.once('dialog', (dialog) => dialog.accept())

  await page.getByRole('button', {
    name: '関連付ける',
  }).click()

  // 処理完了メッセージを確認する
  await expect(
    page.getByRole('status'),
  ).toHaveText('問い合わせを既存の調査に関連付けました。')

  // DB上で関連が2件になったことを確認する
  const relationResult = await db.query(
    `
      SELECT
        "問い合わせ番号",
        "問い合わせ調査状態"
      FROM "問い合わせ調査"
      WHERE "調査番号" = $1
      ORDER BY "問い合わせ番号"
    `,
    [investigationNumber],
  )

  expect(relationResult.rows).toHaveLength(2)

  expect(
    relationResult.rows.map((row) => row.問い合わせ番号),
  ).toContain(existingInquiryNumber)

  expect(
    relationResult.rows.map((row) => row.問い合わせ番号),
  ).toContain(targetInquiryNumber)

  // 新しく追加した関連の状態が「調査中」であることを確認する
  const targetRelation = relationResult.rows.find(
    (row) => row.問い合わせ番号 === targetInquiryNumber,
  )

  expect(targetRelation?.問い合わせ調査状態).toBe(1)
})


// E-04 調査詳細の表示
test('E-04 調査一覧から詳細を開き、関連問い合わせを確認できる', async ({
  page,
  db,
}) => {
  const subject = 'E2E-E04-関連問い合わせ'
  const investigationName = 'E2E-E04-詳細表示確認'

  // 調査と関連問い合わせを準備する
  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
    原因・仮説: 'E2E-E04-原因・仮説',
  })

  const inquiryNumber = await createInProgressInquiry(
    db,
    subject,
  )

  await createInquiryInvestigation(
    db,
    inquiryNumber,
    investigationNumber,
  )

  await loginAsJ0001(page)

  // 調査詳細を開く
  await openInvestigationDetail(page, investigationName)

  // 調査の基本情報を確認する
  await expect(
    page.locator('.investigation-detail-title'),
  ).toContainText(`調査番号：${investigationNumber}`)

  await expect(
    getInvestigationDetailValue(page, '調査の名称'),
  ).toHaveText(investigationName)

  await expect(
    getInvestigationDetailValue(page, '調査状態'),
  ).toHaveText('調査中')

  await expect(
    getInvestigationDetailValue(page, '原因・仮説'),
  ).toHaveText('E2E-E04-原因・仮説')

  // 関連問い合わせ一覧を確認する
  await expect(
    page.getByRole('heading', {
      name: '関連する問い合わせ調査',
    }),
  ).toBeVisible()

  await expect(
    page.locator('.related-inquiries-table'),
  ).toContainText(String(inquiryNumber))

  await expect(
    page.locator('.related-inquiries-table'),
  ).toContainText('調査中')

  await expect(
    page.locator('.list-count'),
  ).toContainText('1 件')
})


// E-05 調査の編集
test('E-05 調査詳細から編集し、変更内容を保存できる', async ({
  page,
  db,
}) => {
  const subject = 'E2E-E05-関連問い合わせ'
  const investigationName = 'E2E-E05-編集前の調査名'
  const updatedName = 'E2E-E05-編集後の調査名'
  const updatedCause = 'E2E-E05-編集後の原因・仮説'

  // 調査と関連問い合わせを準備する
  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
    原因・仮説: 'E2E-E05-編集前の原因・仮説',
  })

  const inquiryNumber = await createInProgressInquiry(
    db,
    subject,
  )

  await createInquiryInvestigation(
    db,
    inquiryNumber,
    investigationNumber,
  )

  await loginAsJ0001(page)

  // 調査詳細を開く
  await openInvestigationDetail(page, investigationName)

  // 編集ボタンが有効であることを確認する
  await expect(
    page.getByRole('button', { name: '編集' }),
  ).toBeEnabled()

  // 編集画面へ移動する
  await page.getByRole('button', { name: '編集' }).click()

  await expect(
    page.getByRole('heading', {
      name: '調査編集',
      level: 2,
    }),
  ).toBeVisible()

  // 編集内容を入力する
  await page.getByLabel('調査の名称').fill(updatedName)
  await page.getByLabel('原因・仮説').fill(updatedCause)
  await page.getByLabel('情シス側での対応').fill(
    'E2E-E05-編集後の情シス側対応',
  )
  await page.getByLabel('問い合わせ者側で必要な対応').fill(
    'E2E-E05-編集後の問い合わせ者側対応',
  )

  // 保存する
  await page.getByRole('button', { name: '保存' }).click()

  // 詳細画面に戻ったことを確認する
  await expect(
    page.getByRole('heading', {
      name: '調査詳細',
      level: 2,
    }),
  ).toBeVisible()

  // 変更内容が詳細画面に反映されていることを確認する
  await expect(
    getInvestigationDetailValue(page, '調査の名称'),
  ).toHaveText(updatedName)

  await expect(
    getInvestigationDetailValue(page, '原因・仮説'),
  ).toHaveText(updatedCause)

  await expect(
    getInvestigationDetailValue(page, '情シス側での対応'),
  ).toHaveText('E2E-E05-編集後の情シス側対応')

  await expect(
    getInvestigationDetailValue(
      page,
      '問い合わせ者側で必要な対応',
    ),
  ).toHaveText('E2E-E05-編集後の問い合わせ者側対応')

  // DBにも変更が保存されていることを確認する
  const result = await db.query(
    `
      SELECT
        "調査の名称",
        "原因・仮説",
        "情シス側での対応",
        "問い合わせ者側で必要な対応"
      FROM "調査"
      WHERE "調査番号" = $1
    `,
    [investigationNumber],
  )

  expect(result.rows).toHaveLength(1)
  expect(result.rows[0]).toMatchObject({
    調査の名称: updatedName,
    '原因・仮説': updatedCause,
    情シス側での対応: 'E2E-E05-編集後の情シス側対応',
    問い合わせ者側で必要な対応:
      'E2E-E05-編集後の問い合わせ者側対応',
  })
})


// E-06 終了した調査の編集制限
test('E-06 断念済みの調査では編集ボタンが無効になる', async ({
  page,
  db,
}) => {
  const investigationName = 'E2E-E06-断念済み調査'

  // 断念済みの調査を準備する
  await createInvestigation(db, {
    調査の名称: investigationName,
    調査状態: 3,
    調査断念日時: new Date(),
  })

  await loginAsJ0001(page)

  // 調査一覧へ移動する
  await openInvestigationList(page)

  // 初期条件をクリアして、対象調査を検索する
  await page.getByRole('button', { name: 'クリア' }).click()

  await page.getByLabel('名称や仮説').fill(investigationName)

  await page.getByRole('button', { name: '検索' }).click()

  // 対象調査が表示されることを確認する
  await expect(
    page.locator('.investigation-table').getByRole('button', {
      name: investigationName,
      exact: true,
    }),
  ).toBeVisible()

  // 調査詳細を開く
  await page.locator('.investigation-table').getByRole('button', {
    name: investigationName,
    exact: true,
  }).click()

  await expect(
    page.getByRole('heading', {
      name: '調査詳細',
      level: 2,
    }),
  ).toBeVisible()

  // 断念済みであることを確認する
  await expect(
    getInvestigationDetailValue(page, '調査状態'),
  ).toHaveText('調査断念')

  // 編集ボタンは表示されるが、無効になっている
  await expect(
    page.getByRole('button', { name: '編集' }),
  ).toBeVisible()

  await expect(
    page.getByRole('button', { name: '編集' }),
  ).toBeDisabled()
})
