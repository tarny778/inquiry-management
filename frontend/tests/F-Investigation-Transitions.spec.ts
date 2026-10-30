
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
  await page.goto('http://localhost:5173')
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
  await page.goto('http://localhost:5173')
  await loginAs(page, 'T0001', getE2ETestPassword())

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ一覧',
      level: 2,
    }),
  ).toBeVisible()
}

// 調査一覧を開き、調査名で検索する
async function openInvestigationList(
  page: Page,
  investigationName: string,
) {
  await page.getByRole('button', {
    name: '調査一覧へ →',
  }).click()

  await expect(
    page.getByRole('heading', {
      name: '調査一覧',
      level: 2,
    }),
  ).toBeVisible()

  await page.getByLabel('名称や仮説').fill(investigationName)

  await page.getByRole('button', {
    name: '検索',
    exact: true,
  }).click()

  await expect(
    page.locator('.investigation-table').getByRole('button', {
      name: investigationName,
      exact: true,
    }),
  ).toBeVisible()
}

// 調査一覧から調査詳細を開く
async function openInvestigationDetail(
  page: Page,
  investigationName: string,
) {
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

// 調査詳細の項目の値を取得する
function getInvestigationDetailValue(
  page: Page,
  label: string,
) {
  return page
    .locator('.investigation-detail-item')
    .filter({
      has: page.locator('dt', {
        hasText: label,
      }),
    })
    .locator('dd')
}

// 問い合わせ調査の行を取得する
function getRelatedInquiryRow(
  page: Page,
  relationNumber: number,
) {
  return page
    .locator('.related-inquiries-table tbody tr')
    .filter({
      has: page.locator('td:first-child').getByText(
        String(relationNumber),
        { exact: true },
      ),
    })
}

// J0001が対応中の問い合わせを作成する
async function createAssignedInquiry(
  db: Parameters<typeof createInquiry>[0],
  subject: string,
): Promise<number> {
  return createInquiry(db, {
    問い合わせ職員番号: 'T0001',
    件名: subject,
    対応担当者: 'J0001',
    引き受け日時: new Date(),
  })
}


// F-01 問い合わせ調査の個別断念
test('F-01 問い合わせ調査を個別に断念できる', async ({ page, db }) => {
  const investigationName = 'E2E-F01-個別断念'

  // 調査中の調査を準備する
  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
  })

  // 同じ調査に問い合わせを2件関連付ける
  const inquiryNumber1 = await createAssignedInquiry(
    db,
    'E2E-F01-個別断念対象',
  )

  const inquiryNumber2 = await createAssignedInquiry(
    db,
    'E2E-F01-個別断念対象外',
  )

  const relationNumber1 = await createInquiryInvestigation(
    db,
    inquiryNumber1,
    investigationNumber,
  )

  const relationNumber2 = await createInquiryInvestigation(
    db,
    inquiryNumber2,
    investigationNumber,
  )

  await loginAsJ0001(page)
  await openInvestigationList(page, investigationName)
  await openInvestigationDetail(page, investigationName)

  // 対象の問い合わせ調査だけ個別断念する
  const targetRow = getRelatedInquiryRow(page, relationNumber1)

  page.once('dialog', dialog => dialog.accept())

  await targetRow.getByRole('button', {
    name: '断念',
    exact: true,
  }).click()

  // 対象だけが断念になったことを確認する
  await expect(
    getRelatedInquiryRow(page, relationNumber1).locator('.related-status'),
  ).toHaveText('断念')

  // もう一方は調査中のままである
  await expect(
    getRelatedInquiryRow(page, relationNumber2).locator('.related-status'),
  ).toHaveText('調査中')

  // DBでも対象だけが更新されたことを確認する
  const result = await db.query(
    `
      SELECT
        "問い合わせ調査番号",
        "問い合わせ調査状態",
        "断念日時"
      FROM "問い合わせ調査"
      WHERE "問い合わせ調査番号" = ANY($1)
      ORDER BY "問い合わせ調査番号"
    `,
    [[relationNumber1, relationNumber2]],
  )

  expect(result.rows).toHaveLength(2)

  const abandonedRelation = result.rows.find(
    row => row.問い合わせ調査番号 === relationNumber1,
  )

  const activeRelation = result.rows.find(
    row => row.問い合わせ調査番号 === relationNumber2,
  )

  expect(abandonedRelation.問い合わせ調査状態).toBe(2)
  expect(abandonedRelation.断念日時).not.toBeNull()

  expect(activeRelation.問い合わせ調査状態).toBe(1)
  expect(activeRelation.断念日時).toBeNull()

  // 調査本体は調査中のままである
  const investigation = await db.query(
    `
      SELECT "調査状態"
      FROM "調査"
      WHERE "調査番号" = $1
    `,
    [investigationNumber],
  )

  expect(investigation.rows[0].調査状態).toBe(1)
})


// F-02 調査全体の断念
test('F-02 調査全体を断念すると関連する問い合わせ調査がすべて断念になる', async ({ page, db }) => {
  const investigationName = 'E2E-F02-調査全体の断念'

  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
  })

  const inquiryNumber1 = await createAssignedInquiry(
    db,
    'E2E-F02-調査中の問い合わせ',
  )

  const inquiryNumber2 = await createAssignedInquiry(
    db,
    'E2E-F02-既に断念した問い合わせ',
  )

  const inquiryNumber3 = await createAssignedInquiry(
    db,
    'E2E-F02-もう一件の調査中問い合わせ',
  )

  const relationNumber1 = await createInquiryInvestigation(
    db,
    inquiryNumber1,
    investigationNumber,
  )

  const relationNumber2 = await createInquiryInvestigation(
    db,
    inquiryNumber2,
    investigationNumber,
    {
      問い合わせ調査状態: 2,
      断念日時: new Date(),
    },
  )

  const relationNumber3 = await createInquiryInvestigation(
    db,
    inquiryNumber3,
    investigationNumber,
  )

  await loginAsJ0001(page)
  await openInvestigationList(page, investigationName)
  await openInvestigationDetail(page, investigationName)

  // 調査全体を断念する
  await page.locator('.page-header-actions').getByRole('button', {
    name: '断念',
    exact: true,
  }).click()

  // 調査本体が断念になったことを確認する
  await expect(
    getInvestigationDetailValue(page, '調査状態'),
  ).toHaveText('調査断念')

  await expect(
    getInvestigationDetailValue(page, '調査断念日時'),
  ).not.toHaveText('—')

  // 関連する問い合わせ調査がすべて断念になったことを確認する
  for (const relationNumber of [
    relationNumber1,
    relationNumber2,
    relationNumber3,
  ]) {
    await expect(
      getRelatedInquiryRow(page, relationNumber).locator('.related-status'),
    ).toHaveText('断念')
  }

  // DBで関連レコードの状態を確認する
  const relations = await db.query(
    `
      SELECT
        "問い合わせ調査番号",
        "問い合わせ調査状態"
      FROM "問い合わせ調査"
      WHERE "調査番号" = $1
    `,
    [investigationNumber],
  )

  expect(relations.rows).toHaveLength(3)

  for (const relation of relations.rows) {
    expect(relation.問い合わせ調査状態).toBe(2)
  }

  // 調査本体の状態もDBで確認する
  const investigation = await db.query(
    `
      SELECT
        "調査状態",
        "調査断念日時"
      FROM "調査"
      WHERE "調査番号" = $1
    `,
    [investigationNumber],
  )

  expect(investigation.rows[0].調査状態).toBe(3)
  expect(investigation.rows[0].調査断念日時).not.toBeNull()
})


// F-03 調査からリアクションを要求する
test('F-03 リアクション要求により調査中の関連だけがリアクション待ちになる', async ({ page, db }) => {
  const investigationName = 'E2E-F03-リアクション要求'

  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
  })

  const inquiryNumber1 = await createAssignedInquiry(
    db,
    'E2E-F03-リアクション対象',
  )

  const inquiryNumber2 = await createAssignedInquiry(
    db,
    'E2E-F03-断念済み',
  )

  const relationNumber1 = await createInquiryInvestigation(
    db,
    inquiryNumber1,
    investigationNumber,
  )

  const relationNumber2 = await createInquiryInvestigation(
    db,
    inquiryNumber2,
    investigationNumber,
    {
      問い合わせ調査状態: 2,
      断念日時: new Date(),
    },
  )

  await loginAsJ0001(page)
  await openInvestigationList(page, investigationName)
  await openInvestigationDetail(page, investigationName)

  // リアクション要求を実行する
  await page.locator('.page-header-actions').getByRole('button', {
    name: 'リアクション要求',
    exact: true,
  }).click()

  // 調査本体がリアクション要求済みになる
  await expect(
    getInvestigationDetailValue(page, '調査状態'),
  ).toHaveText('リアクション要求済み')

  await expect(
    getInvestigationDetailValue(page, 'リアクション要求日時'),
  ).not.toHaveText('—')

  // 状態1だった関連だけがリアクション待ちになる
  await expect(
    getRelatedInquiryRow(page, relationNumber1).locator('.related-status'),
  ).toHaveText('リアクション待ち')

  // 断念済みの関連はそのまま維持される
  await expect(
    getRelatedInquiryRow(page, relationNumber2).locator('.related-status'),
  ).toHaveText('断念')

  // DBでも状態を確認する
  const relations = await db.query(
    `
      SELECT
        "問い合わせ調査番号",
        "問い合わせ調査状態"
      FROM "問い合わせ調査"
      WHERE "調査番号" = $1
    `,
    [investigationNumber],
  )

  const relation1 = relations.rows.find(
    row => row.問い合わせ調査番号 === relationNumber1,
  )

  const relation2 = relations.rows.find(
    row => row.問い合わせ調査番号 === relationNumber2,
  )

  expect(relation1.問い合わせ調査状態).toBe(3)
  expect(relation2.問い合わせ調査状態).toBe(2)

  const investigation = await db.query(
    `
      SELECT "調査状態"
      FROM "調査"
      WHERE "調査番号" = $1
    `,
    [investigationNumber],
  )

  expect(investigation.rows[0].調査状態).toBe(2)
})


// F-04 問い合わせ者がOK回答する
test('F-04 問い合わせ者がリアクションにOKと回答できる', async ({ page, db }) => {
  const investigationName = 'E2E-F04-OK回答'

  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
    調査状態: 2,
    リアクション要求日時: new Date(),
  })

  const inquiryNumber = await createAssignedInquiry(db, 'E2E-F04-OK回答対象',)

  const relationNumber = await createInquiryInvestigation(
    db,
    inquiryNumber,
    investigationNumber,
    {
      問い合わせ調査状態: 3,
      リアクション被要求日時: new Date(),
    },
  )

  await loginAsT0001(page)
  await openInvestigationList(page, investigationName)
  await openInvestigationDetail(page, investigationName)

  // 問い合わせ者本人としてOK回答する
  const targetRow = getRelatedInquiryRow(page, relationNumber)

  await targetRow.getByRole('button', {
    name: 'OK',
    exact: true,
  }).click()

  // 画面上でOKになったことを確認する
  await expect(
    targetRow.locator('.related-status'),
  ).toHaveText('OK')

  await expect(targetRow).toContainText('OK')

  // DBで回答内容・回答日時を確認する
  const result = await db.query(
    `
      SELECT
        "問い合わせ調査状態",
        "リアクション内容",
        "リアクション日時"
      FROM "問い合わせ調査"
      WHERE "問い合わせ調査番号" = $1
    `,
    [relationNumber],
  )

  expect(result.rows[0].問い合わせ調査状態).toBe(4)
  expect(result.rows[0].リアクション内容).toBe(1)
  expect(result.rows[0].リアクション日時).not.toBeNull()
})


// F-05 NG回答して新しい調査へ移行する
test('F-05 NG回答時に新しい移行先調査が作成される', async ({ page, db }) => {
  const investigationName = 'E2E-F05-NG新規移行'

  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
    原因・仮説: 'E2E-F05-原因・仮説',
    情シス側での対応: 'E2E-F05-情シス側の対応',
    問い合わせ者側で必要な対応: 'E2E-F05-問い合わせ者側の対応',
    調査状態: 2,
    リアクション要求日時: new Date(),
  })

  const inquiryNumber = await createAssignedInquiry(db, 'E2E-F05-NG回答対象',)

  const relationNumber = await createInquiryInvestigation(
    db,
    inquiryNumber,
    investigationNumber,
    {
      問い合わせ調査状態: 3,
      リアクション被要求日時: new Date(),
    },
  )

  await loginAsT0001(page)
  await openInvestigationList(page, investigationName)
  await openInvestigationDetail(page, investigationName)

  // NG回答する
  const targetRow = getRelatedInquiryRow(page, relationNumber)

  await targetRow.getByRole('button', {
    name: 'NG',
    exact: true,
  }).click()

  // 元の関連がNGになったことを確認する
  await expect(
    targetRow.locator('.related-status'),
  ).toHaveText('NG')

  // NGでの移行先調査番号が表示される
  const destinationButton = targetRow.locator('td').nth(6).getByRole('button')

  await expect(destinationButton).toBeVisible()

  const destinationNumber = Number(
    await destinationButton.textContent(),
  )

  expect(destinationNumber).toBeGreaterThan(0)
  expect(destinationNumber).not.toBe(investigationNumber)

  // 移行先調査が新規作成され、元の内容が複写されている
  const destination = await db.query(
    `
      SELECT
        "調査状態",
        "調査の名称",
        "原因・仮説",
        "情シス側での対応",
        "問い合わせ者側で必要な対応"
      FROM "調査"
      WHERE "調査番号" = $1
    `,
    [destinationNumber],
  )

  expect(destination.rows).toHaveLength(1)
  expect(destination.rows[0].調査状態).toBe(1)
  expect(destination.rows[0].調査の名称).toBe(
    'E2E-F05-NG新規移行から複写',
  )
  expect(destination.rows[0].原因・仮説).toBe(
    'E2E-F05-原因・仮説',
  )
  expect(destination.rows[0].情シス側での対応).toBe(
    'E2E-F05-情シス側の対応',
  )
  expect(destination.rows[0].問い合わせ者側で必要な対応).toBe(
    'E2E-F05-問い合わせ者側の対応',
  )

  // 元の調査に最新移行先が記録されている
  const oldInvestigation = await db.query(
    `
      SELECT "最新移行先の調査番号"
      FROM "調査"
      WHERE "調査番号" = $1
    `,
    [investigationNumber],
  )

  expect(
    oldInvestigation.rows[0].最新移行先の調査番号,
  ).toBe(destinationNumber)

  // 元の関連はNG、移行先の関連は調査中
  const relations = await db.query(
    `
      SELECT
        "調査番号",
        "問い合わせ調査状態",
        "リアクション内容",
        "NGでの移行先調査番号"
      FROM "問い合わせ調査"
      WHERE "問い合わせ番号" = $1
      ORDER BY "問い合わせ調査番号"
    `,
    [inquiryNumber],
  )

  expect(relations.rows).toHaveLength(2)

  const oldRelation = relations.rows.find(
    row => row.調査番号 === investigationNumber,
  )

  const newRelation = relations.rows.find(
    row => row.調査番号 === destinationNumber,
  )

  expect(oldRelation.問い合わせ調査状態).toBe(5)
  expect(oldRelation.リアクション内容).toBe(2)
  expect(oldRelation.NGでの移行先調査番号).toBe(destinationNumber)

  expect(newRelation.問い合わせ調査状態).toBe(1)
})


// F-06 NG回答時に調査中の最新移行先を再利用する
test('F-06 NG回答時に調査中の最新移行先が再利用される', async ({ page, db }) => {
  const oldInvestigationName = 'E2E-F06-NG既存移行'

  // 既存の移行先調査を先に作成する
  const destinationInvestigationNumber = await createInvestigation(db, {
    調査の名称: 'E2E-F06-既存の移行先',
    調査状態: 1,
  })

  // 最新移行先を持つ、リアクション要求済みの調査を作成する
  const oldInvestigationNumber = await createInvestigation(db, {
    調査の名称: oldInvestigationName,
    調査状態: 2,
    リアクション要求日時: new Date(),
    最新移行先の調査番号: destinationInvestigationNumber,
  })

  const inquiryNumber = await createAssignedInquiry(db, 'E2E-F06-NG回答対象',)

  const relationNumber = await createInquiryInvestigation(
    db,
    inquiryNumber,
    oldInvestigationNumber,
    {
      問い合わせ調査状態: 3,
      リアクション被要求日時: new Date(),
    },
  )

  await loginAsT0001(page)
  await openInvestigationList(page, oldInvestigationName)
  await openInvestigationDetail(page, oldInvestigationName)

  // NG回答する
  const targetRow = getRelatedInquiryRow(page, relationNumber)

  await targetRow.getByRole('button', {
    name: 'NG',
    exact: true,
  }).click()

  // 既存の移行先調査番号が表示される
  const destinationButton = targetRow.locator('td').nth(6).getByRole('button')

  await expect(destinationButton).toHaveText(
    String(destinationInvestigationNumber),
  )

  // 既存の移行先調査が再利用されたことを確認する
  const destinationRelations = await db.query(
    `
      SELECT
        "問い合わせ調査番号",
        "問い合わせ調査状態"
      FROM "問い合わせ調査"
      WHERE "調査番号" = $1
        AND "問い合わせ番号" = $2
    `,
    [destinationInvestigationNumber, inquiryNumber],
  )

  expect(destinationRelations.rows).toHaveLength(1)
  expect(
    destinationRelations.rows[0].問い合わせ調査状態,
  ).toBe(1)

  // 元の関連はNGになっている
  const oldRelation = await db.query(
    `
      SELECT
        "問い合わせ調査状態",
        "リアクション内容",
        "NGでの移行先調査番号"
      FROM "問い合わせ調査"
      WHERE "問い合わせ調査番号" = $1
    `,
    [relationNumber],
  )

  expect(oldRelation.rows[0].問い合わせ調査状態).toBe(5)
  expect(oldRelation.rows[0].リアクション内容).toBe(2)
  expect(
    oldRelation.rows[0].NGでの移行先調査番号,
  ).toBe(destinationInvestigationNumber)

  // 調査レコードが余分に作成されていないことを確認する
  const investigationCount = await db.query(
    `
      SELECT COUNT(*) AS count
      FROM "調査"
    `,
  )

  expect(Number(investigationCount.rows[0].count)).toBe(2)
})


// F-07 複数の問い合わせ調査に対する個別回答
test('F-07 1件の問い合わせ調査へのOK回答が他の関連に影響しない', async ({ page, db }) => {
  const investigationName = 'E2E-F07-個別回答の非干渉'

  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
    調査状態: 2,
    リアクション要求日時: new Date(),
  })

  // 同じ問い合わせ者の問い合わせを2件準備する
  const inquiryNumber1 = await createAssignedInquiry(db, 'E2E-F07-回答対象1',)
  const inquiryNumber2 = await createAssignedInquiry(db, 'E2E-F07-回答対象2',)

  const relationNumber1 = await createInquiryInvestigation(
    db,
    inquiryNumber1,
    investigationNumber,
    {
      問い合わせ調査状態: 3,
      リアクション被要求日時: new Date(),
    },
  )

  const relationNumber2 = await createInquiryInvestigation(
    db,
    inquiryNumber2,
    investigationNumber,
    {
      問い合わせ調査状態: 3,
      リアクション被要求日時: new Date(),
    },
  )

  await loginAsT0001(page)
  await openInvestigationList(page, investigationName)
  await openInvestigationDetail(page, investigationName)

  // 1件目だけOK回答する
  const targetRow = getRelatedInquiryRow(page, relationNumber1)

  await targetRow.getByRole('button', {
    name: 'OK',
    exact: true,
  }).click()

  // 1件目はOKになる
  await expect(
    getRelatedInquiryRow(page, relationNumber1).locator('.related-status'),
  ).toHaveText('OK')

  // 2件目はリアクション待ちのまま、回答ボタンも残る
  const otherRow = getRelatedInquiryRow(page, relationNumber2)

  await expect(
    otherRow.locator('.related-status'),
  ).toHaveText('リアクション待ち')

  await expect(
    otherRow.getByRole('button', {
      name: 'OK',
      exact: true,
    }),
  ).toBeVisible()

  await expect(
    otherRow.getByRole('button', {
      name: 'NG',
      exact: true,
    }),
  ).toBeVisible()

  // DBでも1件目だけが更新されたことを確認する
  const relations = await db.query(
    `
      SELECT
        "問い合わせ調査番号",
        "問い合わせ調査状態",
        "リアクション内容",
        "リアクション日時"
      FROM "問い合わせ調査"
      WHERE "調査番号" = $1
      ORDER BY "問い合わせ調査番号"
    `,
    [investigationNumber],
  )

  expect(relations.rows).toHaveLength(2)

  const relation1 = relations.rows.find(
    row => row.問い合わせ調査番号 === relationNumber1,
  )

  const relation2 = relations.rows.find(
    row => row.問い合わせ調査番号 === relationNumber2,
  )

  expect(relation1.問い合わせ調査状態).toBe(4)
  expect(relation1.リアクション内容).toBe(1)
  expect(relation1.リアクション日時).not.toBeNull()

  expect(relation2.問い合わせ調査状態).toBe(3)
  expect(relation2.リアクション内容).toBeNull()
  expect(relation2.リアクション日時).toBeNull()

  // 調査本体はリアクション要求済みのまま維持される
  const investigation = await db.query(
    `
      SELECT "調査状態"
      FROM "調査"
      WHERE "調査番号" = $1
    `,
    [investigationNumber],
  )

  expect(investigation.rows[0].調査状態).toBe(2)
})
