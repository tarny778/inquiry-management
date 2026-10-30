
import { test, expect } from './fixtures/test.ts'
import { loginAs } from './helpers/auth.ts'
import {
  createInquiry,
  createInvestigation,
  createInquiryInvestigation,
} from './fixtures/test-data.ts'
import type { Page } from '@playwright/test'

// =========================================================
// 共通ヘルパー
// =========================================================

function getE2ETestPassword(): string {
  const password = process.env.E2E_TEST_PASSWORD

  if (!password) {
    throw new Error('E2E_TEST_PASSWORD が設定されていません。')
  }

  return password
}

async function loginAsJ0001(page: Page): Promise<void> {
  await page.goto('http://localhost:5173')
  await loginAs(page, 'J0001', getE2ETestPassword())

  await expect(
    page.getByRole('heading', { name: '問い合わせ一覧' }),
  ).toBeVisible()
}

async function loginAsT0001(page: Page): Promise<void> {
  await page.goto('http://localhost:5173')
  await loginAs(page, 'T0001', getE2ETestPassword())

  await expect(
    page.getByRole('heading', { name: '問い合わせ一覧' }),
  ).toBeVisible()
}

/**
 * 調査一覧を開く。
 *
 * 初回表示時にはApp.tsxの処理によって
 * 初期条件が自動適用される。
 */
async function openInvestigationList(page: Page): Promise<void> {
  await page.getByRole('button', { name: /調査一覧へ/ }).click()

  await expect(
    page.getByRole('heading', { name: '調査一覧' }),
  ).toBeVisible()
}

/**
 * 調査名を指定して検索する。
 */
async function searchInvestigationByName(
  page: Page,
  name: string,
): Promise<void> {
  await page.getByLabel('名称や仮説').fill(name)
  await page.getByRole('button', { name: '検索' }).click()

  await expect(
    page.getByRole('button', { name, exact: true }).first(),
  ).toBeVisible()
}

/**
 * 対応中の問い合わせを作成する。
 *
 * 問い合わせ者・対応担当者を指定できる。
 */
async function createAssignedInquiry(
  db: Parameters<typeof createInquiry>[0],
  subject: string,
  requesterStaffNumber = 'T0001',
  handlerStaffNumber = 'J0001',
): Promise<number> {
  return createInquiry(db, {
    問い合わせ職員番号: requesterStaffNumber,
    件名: subject,
    対応担当者: handlerStaffNumber,
    引き受け日時: new Date(),
  })
}

/**
 * 調査と問い合わせを関連付ける。
 */
async function createInvestigationWithInquiry(
  db: Parameters<typeof createInvestigation>[0],
  investigationName: string,
  inquiryNumber: number,
  options: Parameters<typeof createInvestigation>[1] = {},
): Promise<number> {
  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
    ...options,
  })

  await createInquiryInvestigation(
    db,
    inquiryNumber,
    investigationNumber,
  )

  return investigationNumber
}

/**
 * 調査一覧に表示されている名称を取得する。
 */
function getInvestigationNameButton(
  page: Page,
  name: string,
) {
  return page
    .locator('.investigation-table')
    .getByRole('button', { name, exact: true })
}

// =========================================================
// G-01 初期条件
// =========================================================

test.describe('G-01 調査一覧の初期条件', () => {
  test('G-01-01 情報システム課職員は自分が担当する対応中問い合わせの調査を表示する', async ({
    page,
    db,
  }) => {
    // J0001が担当する問い合わせ
    const ownHandlerInquiry = await createAssignedInquiry(
      db,
      'J0001担当の問い合わせ',
      'T0001',
      'J0001',
    )

    // J0002が担当する問い合わせ
    const otherHandlerInquiry = await createAssignedInquiry(
      db,
      'J0002担当の問い合わせ',
      'T0001',
      'J0002',
    )

    const ownInvestigation = await createInvestigationWithInquiry(
      db,
      'J0001担当の調査',
      ownHandlerInquiry,
    )

    const otherInvestigation = await createInvestigationWithInquiry(
      db,
      'J0002担当の調査',
      otherHandlerInquiry,
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    await expect(
      getInvestigationNameButton(page, 'J0001担当の調査'),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(page, 'J0002担当の調査'),
    ).toHaveCount(0)

    // 初期条件の対象が1件であることも確認する
    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)

    expect(ownInvestigation).toBeGreaterThan(0)
    expect(otherInvestigation).toBeGreaterThan(0)
  })

  test('G-01-02 一般職員は自分が問い合わせた対応中問い合わせの調査を表示する', async ({
    page,
    db,
  }) => {
    // T0001自身が問い合わせたもの
    const ownInquiry = await createAssignedInquiry(
      db,
      'T0001自身の問い合わせ',
      'T0001',
      'J0001',
    )

    // T0002が問い合わせたもの
    const otherInquiry = await createAssignedInquiry(
      db,
      'T0002の問い合わせ',
      'T0002',
      'J0001',
    )

    await createInvestigationWithInquiry(
      db,
      'T0001自身の調査',
      ownInquiry,
    )

    await createInvestigationWithInquiry(
      db,
      'T0002の調査',
      otherInquiry,
    )

    await loginAsT0001(page)
    await openInvestigationList(page)

    await expect(
      getInvestigationNameButton(page, 'T0001自身の調査'),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(page, 'T0002の調査'),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  })
})

// =========================================================
// G-02 初期条件の解除
// =========================================================

test('G-02 初期条件を解除して通常検索に切り替えられる', async ({
  page,
  db,
}) => {
  const ownInquiry = await createAssignedInquiry(
    db,
    '初期条件対象の問い合わせ',
    'T0001',
    'J0001',
  )

  const otherInquiry = await createAssignedInquiry(
    db,
    '通常検索対象の問い合わせ',
    'T0002',
    'J0001',
  )

  await createInvestigationWithInquiry(
    db,
    '初期条件で表示される調査',
    ownInquiry,
  )

  await createInvestigationWithInquiry(
    db,
    '通常検索で表示される調査',
    otherInquiry,
  )

  await loginAsT0001(page)
  await openInvestigationList(page)

  // 初期条件では自分の問い合わせに関する調査だけが表示される
  await expect(
    getInvestigationNameButton(page, '初期条件で表示される調査'),
  ).toBeVisible()

  await expect(
    getInvestigationNameButton(page, '通常検索で表示される調査'),
  ).toHaveCount(0)

  // 検索条件をクリアし、条件なしで通常検索する
  await page.getByRole('button', { name: 'クリア' }).click()

  await page.getByRole('button', { name: '検索' }).click()

  await expect(
    getInvestigationNameButton(page, '初期条件で表示される調査'),
  ).toBeVisible()

  await expect(
    getInvestigationNameButton(page, '通常検索で表示される調査'),
  ).toBeVisible()

  await expect(
    page.locator('.investigation-table tbody tr'),
  ).toHaveCount(2)
})

// =========================================================
// G-03 調査検索
// =========================================================

test('G-03-01 調査名で部分一致検索できる', async ({ page, db }) => {
  const inquiryNumber = await createAssignedInquiry(
    db,
    '調査名検索用問い合わせ',
  )

  await createInvestigationWithInquiry(
    db,
    '検索テスト用のネットワーク調査',
    inquiryNumber,
  )

  await createInvestigationWithInquiry(
    db,
    '検索対象外のプリンター調査',
    inquiryNumber,
  )

  await loginAsJ0001(page)
  await openInvestigationList(page)

  await searchInvestigationByName(page, 'ネットワーク')

  await expect(
    page.locator('.investigation-table tbody tr'),
  ).toHaveCount(1)

  await expect(
    getInvestigationNameButton(
      page,
      '検索テスト用のネットワーク調査',
    ),
  ).toBeVisible()
})

test('G-03-02 調査状態で検索できる', async ({ page, db }) => {
  const inquiryNumber = await createAssignedInquiry(
    db,
    '調査状態検索用問い合わせ',
  )

  await createInvestigationWithInquiry(
    db,
    '調査中の調査',
    inquiryNumber,
    { 調査状態: 1 },
  )

  await createInvestigationWithInquiry(
    db,
    'リアクション要求済みの調査',
    inquiryNumber,
    {
      調査状態: 2,
      リアクション要求日時: new Date(),
    },
  )

  await loginAsJ0001(page)
  await openInvestigationList(page)

  await page.getByLabel('調査状態').selectOption('2')
  await page.getByRole('button', { name: '検索' }).click()

  await expect(
    getInvestigationNameButton(
      page,
      'リアクション要求済みの調査',
    ),
  ).toBeVisible()

  await expect(
    getInvestigationNameButton(page, '調査中の調査'),
  ).toHaveCount(0)

  await expect(
    page.locator('.investigation-table tbody tr'),
  ).toHaveCount(1)
})

test('G-03-03 問い合わせ番号で関連する調査を検索できる', async ({
  page,
  db,
}) => {
  const targetInquiry = await createAssignedInquiry(
    db,
    '問い合わせ番号検索対象',
  )

  const otherInquiry = await createAssignedInquiry(
    db,
    '問い合わせ番号検索対象外',
  )

  await createInvestigationWithInquiry(
    db,
    '問い合わせ番号検索対象の調査',
    targetInquiry,
  )

  await createInvestigationWithInquiry(
    db,
    '別の問い合わせの調査',
    otherInquiry,
  )

  await loginAsJ0001(page)
  await openInvestigationList(page)

  await page.getByLabel('問い合わせ番号').fill(String(targetInquiry))
  await page.getByRole('button', { name: '検索' }).click()

  await expect(
    getInvestigationNameButton(
      page,
      '問い合わせ番号検索対象の調査',
    ),
  ).toBeVisible()

  await expect(
    getInvestigationNameButton(page, '別の問い合わせの調査'),
  ).toHaveCount(0)

  await expect(
    page.locator('.investigation-table tbody tr'),
  ).toHaveCount(1)
})

test('G-03-04 問い合わせ者の職員番号で検索できる', async ({
  page,
  db,
}) => {
  const targetInquiry = await createAssignedInquiry(
    db,
    '問い合わせ者検索対象',
    'T0001',
    'J0001',
  )

  const otherInquiry = await createAssignedInquiry(
    db,
    '問い合わせ者検索対象外',
    'T0002',
    'J0001',
  )

  await createInvestigationWithInquiry(
    db,
    'T0001の問い合わせに関する調査',
    targetInquiry,
  )

  await createInvestigationWithInquiry(
    db,
    'T0002の問い合わせに関する調査',
    otherInquiry,
  )

  await loginAsJ0001(page)
  await openInvestigationList(page)

  await page
    .getByLabel('問い合わせ者（職員番号）')
    .fill('T0001')

  await page.getByRole('button', { name: '検索' }).click()

  await expect(
    getInvestigationNameButton(
      page,
      'T0001の問い合わせに関する調査',
    ),
  ).toBeVisible()

  await expect(
    getInvestigationNameButton(
      page,
      'T0002の問い合わせに関する調査',
    ),
  ).toHaveCount(0)
})

test('G-03-05 対応担当者の職員番号で検索できる', async ({
  page,
  db,
}) => {
  const targetInquiry = await createAssignedInquiry(
    db,
    '対応担当者検索対象',
    'T0001',
    'J0001',
  )

  const otherInquiry = await createAssignedInquiry(
    db,
    '対応担当者検索対象外',
    'T0001',
    'J0002',
  )

  await createInvestigationWithInquiry(
    db,
    'J0001担当の検索対象調査',
    targetInquiry,
  )

  await createInvestigationWithInquiry(
    db,
    'J0002担当の検索対象外調査',
    otherInquiry,
  )

  await loginAsJ0001(page)
  await openInvestigationList(page)

  await page
    .getByLabel('対応担当者（職員番号）')
    .fill('J0001')

  await page.getByRole('button', { name: '検索' }).click()

  await expect(
    getInvestigationNameButton(
      page,
      'J0001担当の検索対象調査',
    ),
  ).toBeVisible()

  await expect(
    getInvestigationNameButton(
      page,
      'J0002担当の検索対象外調査',
    ),
  ).toHaveCount(0)
})

test('G-03-06 問い合わせ状態で検索できる', async ({
  page,
  db,
}) => {
  // 対応中
  const inProgressInquiry = await createAssignedInquiry(
    db,
    '対応中の問い合わせ',
  )

  // 引き受け待ち
  const waitingInquiry = await createInquiry(db, {
    問い合わせ職員番号: 'T0001',
    件名: '引き受け待ちの問い合わせ',
  })

  await createInvestigationWithInquiry(
    db,
    '対応中問い合わせに関する調査',
    inProgressInquiry,
  )

  await createInvestigationWithInquiry(
    db,
    '引き受け待ち問い合わせに関する調査',
    waitingInquiry,
  )

  await loginAsJ0001(page)
  await openInvestigationList(page)

  await page.getByLabel('問い合わせ状態').selectOption('対応中')
  await page.getByRole('button', { name: '検索' }).click()

  await expect(
    getInvestigationNameButton(
      page,
      '対応中問い合わせに関する調査',
    ),
  ).toBeVisible()

  await expect(
    getInvestigationNameButton(
      page,
      '引き受け待ち問い合わせに関する調査',
    ),
  ).toHaveCount(0)
})

// =========================================================
// G-04 調査詳細の関連情報
// =========================================================

test('G-04 調査詳細と関連問い合わせ調査の情報を確認できる', async ({
  page,
  db,
}) => {
  const inquiryOk = await createAssignedInquiry(
    db,
    'OK回答の問い合わせ',
    'T0001',
    'J0001',
  )

  const inquiryNg = await createAssignedInquiry(
    db,
    'NG回答の問い合わせ',
    'T0001',
    'J0001',
  )

  const reactionDate = new Date('2026-10-20T10:30:00+09:00')

  const investigationNumber = await createInvestigation(db, {
    調査の名称: '詳細確認用のネットワーク調査',
    原因・仮説: 'ネットワーク機器の設定に問題がある可能性',
    情シス側での対応: '設定内容を確認する',
    問い合わせ者側で必要な対応: '端末を再起動する',
    調査状態: 2,
    調査開始日時: new Date('2026-10-19T09:00:00+09:00'),
    リアクション要求日時: new Date('2026-10-20T09:00:00+09:00'),
  })

  const okRelationNumber = await createInquiryInvestigation(
    db,
    inquiryOk,
    investigationNumber,
    {
      問い合わせ調査状態: 4,
      リアクション日時: reactionDate,
      リアクション内容: 1,
    },
  )

  const ngRelationNumber = await createInquiryInvestigation(
    db,
    inquiryNg,
    investigationNumber,
    {
      問い合わせ調査状態: 5,
      リアクション日時: reactionDate,
      リアクション内容: 2,
    },
  )

  await loginAsJ0001(page)
  await openInvestigationList(page)

  await searchInvestigationByName(
    page,
    '詳細確認用のネットワーク調査',
  )

  await getInvestigationNameButton(
    page,
    '詳細確認用のネットワーク調査',
  ).click()

  await expect(
    page.getByRole('heading', { name: '調査詳細' }),
  ).toBeVisible()

  // 調査そのものの情報
  const detailItems = page.locator('.investigation-detail-item')

  await expect(
    detailItems.filter({ has: page.locator('dt', { hasText: '調査の名称' }) }),
  ).toContainText('詳細確認用のネットワーク調査')

  await expect(
    detailItems.filter({ has: page.locator('dt', { hasText: '調査状態' }) }),
  ).toContainText('リアクション要求済み')

  await expect(
    detailItems.filter({ has: page.locator('dt', { hasText: '原因・仮説' }) }),
  ).toContainText('ネットワーク機器の設定に問題がある可能性')

  await expect(
    detailItems.filter({ has: page.locator('dt', { hasText: '情シス側での対応' }) }),
  ).toContainText('設定内容を確認する')

  await expect(
    detailItems.filter({
      has: page.locator('dt', { hasText: '問い合わせ者側で必要な対応' }),
    }),
  ).toContainText('端末を再起動する')

  // 関連問い合わせ調査の件数
  await expect(
    page.getByText('関連件数：2 件'),
  ).toBeVisible()

  const relatedRows = page.locator(
    '.related-inquiries-table tbody tr',
  )

  await expect(relatedRows).toHaveCount(2)

  // OK回答の関連情報
  const okRow = relatedRows.filter({
    hasText: String(okRelationNumber),
  })

  await expect(okRow).toContainText(String(inquiryOk))
  await expect(okRow).toContainText('OK')

  // NG回答の関連情報
  const ngRow = relatedRows.filter({
    hasText: String(ngRelationNumber),
  })

  await expect(ngRow).toContainText(String(inquiryNg))
  await expect(ngRow).toContainText('NG')
})
