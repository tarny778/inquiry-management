
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

// 一般職員T0001としてログインする
async function loginAsT0001(page: Page): Promise<void> {
  await page.goto('http://127.0.0.1:5173')
  await loginAs(page, 'T0001', getE2ETestPassword())

  await expect(
    page.getByRole('heading', {
      name: '問い合わせ一覧',
      level: 2,
    }),
  ).toBeVisible()
}

// J0001が対応中の問い合わせを作成する
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

// 調査と問い合わせを関連付ける
async function createInvestigationWithInquiry(
  db: Parameters<typeof createInvestigation>[0],
  investigationName: string,
  inquiryNumber: number,
  investigationOptions: Parameters<typeof createInvestigation>[1] = {},
  relationOptions: Parameters<typeof createInquiryInvestigation>[3] = {},
): Promise<number> {
  const investigationNumber = await createInvestigation(db, {
    調査の名称: investigationName,
    ...investigationOptions,
  })

  await createInquiryInvestigation(
    db,
    inquiryNumber,
    investigationNumber,
    relationOptions,
  )

  return investigationNumber
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

// 調査名で検索する
async function searchInvestigationByName(
  page: Page,
  investigationName: string,
): Promise<void> {
  await page.getByLabel('名称や仮説').fill(investigationName)

  await page.getByRole('button', {
    name: '検索',
    exact: true,
  }).click()

  await expect(
    getInvestigationNameButton(page, investigationName),
  ).toBeVisible()
}

// 調査一覧の名称ボタンを取得する
function getInvestigationNameButton(
  page: Page,
  investigationName: string,
) {
  return page
    .locator('.investigation-table')
    .getByRole('button', {
      name: investigationName,
      exact: true,
    })
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

// =========================================================
// G-01 調査一覧の初期条件
// =========================================================

// G-01-01 情報システム課職員の初期条件
test(
  'G-01-01 情報システム課職員は自分が担当する対応中問い合わせの調査を表示する',
  async ({ page, db }) => {
    // J0001が担当する問い合わせ
    const ownInquiry = await createAssignedInquiry(
      db,
      'E2E-G01-01-J0001担当',
      'T0001',
      'J0001',
    )

    // J0002が担当する問い合わせ
    const otherInquiry = await createAssignedInquiry(
      db,
      'E2E-G01-01-J0002担当',
      'T0001',
      'J0002',
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G01-01-J0001担当の調査',
      ownInquiry,
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G01-01-J0002担当の調査',
      otherInquiry,
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    // J0001が担当する調査だけが表示される
    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G01-01-J0001担当の調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G01-01-J0002担当の調査',
      ),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  },
)

// G-01-02 一般職員の初期条件
test(
  'G-01-02 一般職員は自分が問い合わせた対応中問い合わせの調査を表示する',
  async ({ page, db }) => {
    // T0001自身が問い合わせたもの
    const ownInquiry = await createAssignedInquiry(
      db,
      'E2E-G01-02-T0001の問い合わせ',
      'T0001',
      'J0001',
    )

    // J0002が問い合わせたもの
    // J0002はテストDBに存在する職員番号を使用する
    const otherInquiry = await createAssignedInquiry(
      db,
      'E2E-G01-02-J0002の問い合わせ',
      'J0002',
      'J0001',
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G01-02-T0001の調査',
      ownInquiry,
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G01-02-J0002の調査',
      otherInquiry,
    )

    await loginAsT0001(page)
    await openInvestigationList(page)

    // T0001自身が問い合わせた調査だけが表示される
    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G01-02-T0001の調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G01-02-J0002の調査',
      ),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  },
)

// =========================================================
// G-02 初期条件の解除
// =========================================================

test(
  'G-02 初期条件を解除して通常検索に切り替えられる',
  async ({ page, db }) => {
    const ownInquiry = await createAssignedInquiry(
      db,
      'E2E-G02-初期条件対象',
      'T0001',
      'J0001',
    )

    const otherInquiry = await createAssignedInquiry(
      db,
      'E2E-G02-通常検索対象',
      'J0002',
      'J0001',
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G02-初期条件で表示される調査',
      ownInquiry,
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G02-通常検索で表示される調査',
      otherInquiry,
    )

    await loginAsT0001(page)
    await openInvestigationList(page)

    // 初期条件では自分の問い合わせに関する調査だけが表示される
    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G02-初期条件で表示される調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G02-通常検索で表示される調査',
      ),
    ).toHaveCount(0)

    // 検索条件をクリアする
    await page.getByRole('button', {
      name: 'クリア',
      exact: true,
    }).click()

    // 条件なしで通常検索する
    await page.getByRole('button', {
      name: '検索',
      exact: true,
    }).click()

    // どちらの調査も表示される
    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G02-初期条件で表示される調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G02-通常検索で表示される調査',
      ),
    ).toBeVisible()

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(2)
  },
)

// =========================================================
// G-03 調査検索
// =========================================================

// G-03-01 調査名の部分一致検索
test(
  'G-03-01 調査名の一部を指定して検索できる',
  async ({ page, db }) => {
    const inquiry1 = await createAssignedInquiry(
      db,
      'E2E-G03-01-対象問い合わせ',
    )

    const inquiry2 = await createAssignedInquiry(
      db,
      'E2E-G03-01-対象外問い合わせ',
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-01-ネットワーク調査',
      inquiry1,
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-01-プリンター調査',
      inquiry2,
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    await page.getByLabel('名称や仮説').fill('ネットワーク')

    await page.getByRole('button', {
      name: '検索',
      exact: true,
    }).click()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-01-ネットワーク調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-01-プリンター調査',
      ),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  },
)

// G-03-02 調査番号による検索
test(
  'G-03-02 調査番号を指定して検索できる',
  async ({ page, db }) => {
    const inquiry1 = await createAssignedInquiry(
      db,
      'E2E-G03-02-対象問い合わせ',
    )

    const inquiry2 = await createAssignedInquiry(
      db,
      'E2E-G03-02-対象外問い合わせ',
    )

    const targetInvestigationNumber =
      await createInvestigationWithInquiry(
        db,
        'E2E-G03-02-対象調査',
        inquiry1,
      )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-02-対象外調査',
      inquiry2,
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    await page.getByLabel('調査番号').fill(
      String(targetInvestigationNumber),
    )

    await page.getByRole('button', {
      name: '検索',
      exact: true,
    }).click()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-02-対象調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-02-対象外調査',
      ),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  },
)

// G-03-03 調査状態による検索
test(
  'G-03-03 調査状態を指定して検索できる',
  async ({ page, db }) => {
    const inquiry1 = await createAssignedInquiry(
      db,
      'E2E-G03-03-調査中の問い合わせ',
    )

    const inquiry2 = await createAssignedInquiry(
      db,
      'E2E-G03-03-リアクション要求済みの問い合わせ',
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-03-調査中の調査',
      inquiry1,
      {
        調査状態: 1,
      },
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-03-リアクション要求済みの調査',
      inquiry2,
      {
        調査状態: 2,
        リアクション要求日時: new Date(),
      },
      {
        問い合わせ調査状態: 3,
        リアクション被要求日時: new Date(),
      },
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    await page.getByLabel('調査状態').selectOption('2')

    await page.getByRole('button', {
      name: '検索',
      exact: true,
    }).click()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-03-リアクション要求済みの調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-03-調査中の調査',
      ),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  },
)

// G-03-04 問い合わせ番号による検索
test(
  'G-03-04 問い合わせ番号を指定して関連する調査を検索できる',
  async ({ page, db }) => {
    const targetInquiry = await createAssignedInquiry(
      db,
      'E2E-G03-04-対象問い合わせ',
    )

    const otherInquiry = await createAssignedInquiry(
      db,
      'E2E-G03-04-対象外問い合わせ',
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-04-対象調査',
      targetInquiry,
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-04-対象外調査',
      otherInquiry,
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    await page.getByLabel('問い合わせ番号').fill(
      String(targetInquiry),
    )

    await page.getByRole('button', {
      name: '検索',
      exact: true,
    }).click()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-04-対象調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-04-対象外調査',
      ),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  },
)

// G-03-05 問い合わせ者の職員番号による検索
test(
  'G-03-05 問い合わせ者の職員番号を指定して検索できる',
  async ({ page, db }) => {
    const targetInquiry = await createAssignedInquiry(
      db,
      'E2E-G03-05-対象問い合わせ',
      'J0002',
      'J0001',
    )

    const otherInquiry = await createAssignedInquiry(
      db,
      'E2E-G03-05-対象外問い合わせ',
      'T0001',
      'J0001',
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-05-J0002の調査',
      targetInquiry,
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-05-T0001の調査',
      otherInquiry,
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    await page.getByLabel('問い合わせ者（職員番号）').fill('J0002')

    await page.getByRole('button', {
      name: '検索',
      exact: true,
    }).click()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-05-J0002の調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-05-T0001の調査',
      ),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  },
)

// G-03-06 対応担当者の職員番号による検索
test(
  'G-03-06 対応担当者の職員番号を指定して検索できる',
  async ({ page, db }) => {
    const targetInquiry = await createAssignedInquiry(
      db,
      'E2E-G03-06-対象問い合わせ',
      'T0001',
      'J0002',
    )

    const otherInquiry = await createAssignedInquiry(
      db,
      'E2E-G03-06-対象外問い合わせ',
      'T0001',
      'J0001',
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-06-J0002担当の調査',
      targetInquiry,
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-06-J0001担当の調査',
      otherInquiry,
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    await page.getByLabel('対応担当者（職員番号）').fill('J0002')

    await page.getByRole('button', {
      name: '検索',
      exact: true,
    }).click()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-06-J0002担当の調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-06-J0001担当の調査',
      ),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  },
)

// G-03-07 問い合わせ状態による検索
test(
  'G-03-07 問い合わせ状態を指定して関連する調査を検索できる',
  async ({ page, db }) => {
    // 対応中の問い合わせ
    const inProgressInquiry = await createAssignedInquiry(
      db,
      'E2E-G03-07-対応中の問い合わせ',
    )

    // 引き受け待ちの問い合わせ
    const waitingInquiry = await createInquiry(db, {
      問い合わせ職員番号: 'T0001',
      件名: 'E2E-G03-07-引き受け待ちの問い合わせ',
    })

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-07-対応中の問い合わせに関する調査',
      inProgressInquiry,
    )

    await createInvestigationWithInquiry(
      db,
      'E2E-G03-07-引き受け待ちの問い合わせに関する調査',
      waitingInquiry,
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    // 初期条件による担当者・問い合わせ状態の条件を解除する
    await page.getByRole('button', {
      name: 'クリア',
      exact: true,
    }).click()

    // 引き受け待ちで検索する
    await page.getByLabel('問い合わせ状態').selectOption('引き受け待ち')

    await page.getByRole('button', {
      name: '検索',
      exact: true,
    }).click()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-07-引き受け待ちの問い合わせに関する調査',
      ),
    ).toBeVisible()

    await expect(
      getInvestigationNameButton(
        page,
        'E2E-G03-07-対応中の問い合わせに関する調査',
      ),
    ).toHaveCount(0)

    await expect(
      page.locator('.investigation-table tbody tr'),
    ).toHaveCount(1)
  },
)

// =========================================================
// G-04 調査詳細と関連問い合わせ調査
// =========================================================

test(
  'G-04 調査詳細と関連問い合わせ調査の情報を確認できる',
  async ({ page, db }) => {
    const inquiryOk = await createAssignedInquiry(
      db,
      'E2E-G04-OK回答の問い合わせ',
    )

    const inquiryNg = await createAssignedInquiry(
      db,
      'E2E-G04-NG回答の問い合わせ',
    )

    const reactionRequestDate =
      new Date('2026-10-20T09:00:00+09:00')

    const reactionDate =
      new Date('2026-10-20T10:30:00+09:00')

    // リアクション要求済みの調査を作成する
    const investigationNumber = await createInvestigation(db, {
      調査の名称: 'E2E-G04-詳細確認用の調査',
      原因・仮説: 'ネットワーク機器の設定に問題がある可能性',
      情シス側での対応: '設定内容を確認する',
      問い合わせ者側で必要な対応: '端末を再起動する',
      調査状態: 2,
      調査開始日時: new Date('2026-10-19T09:00:00+09:00'),
      リアクション要求日時: reactionRequestDate,
    })

    // OK回答済みの問い合わせ調査
    const okRelationNumber = await createInquiryInvestigation(
      db,
      inquiryOk,
      investigationNumber,
      {
        問い合わせ調査状態: 4,
        リアクション被要求日時: reactionRequestDate,
        リアクション日時: reactionDate,
        リアクション内容: 1,
      },
    )

    // NG回答済みの問い合わせ調査
    const ngRelationNumber = await createInquiryInvestigation(
      db,
      inquiryNg,
      investigationNumber,
      {
        問い合わせ調査状態: 5,
        リアクション被要求日時: reactionRequestDate,
        リアクション日時: reactionDate,
        リアクション内容: 2,
      },
    )

    await loginAsJ0001(page)
    await openInvestigationList(page)

    await searchInvestigationByName(
      page,
      'E2E-G04-詳細確認用の調査',
    )

    await getInvestigationNameButton(
      page,
      'E2E-G04-詳細確認用の調査',
    ).click()

    await expect(
      page.getByRole('heading', {
        name: '調査詳細',
        level: 2,
      }),
    ).toBeVisible()

    // -----------------------------------------------------
    // 調査本体の情報
    // -----------------------------------------------------

    await expect(
      page.getByText(`調査番号：${investigationNumber}`),
    ).toBeVisible()

    await expect(
      getInvestigationDetailValue(page, '調査の名称'),
    ).toHaveText('E2E-G04-詳細確認用の調査')

    await expect(
      getInvestigationDetailValue(page, '調査状態'),
    ).toHaveText('リアクション要求済み')

    await expect(
      getInvestigationDetailValue(page, '原因・仮説'),
    ).toHaveText('ネットワーク機器の設定に問題がある可能性')

    await expect(
      getInvestigationDetailValue(page, '情シス側での対応'),
    ).toHaveText('設定内容を確認する')

    await expect(
      getInvestigationDetailValue(
        page,
        '問い合わせ者側で必要な対応',
      ),
    ).toHaveText('端末を再起動する')

    // -----------------------------------------------------
    // 関連する問い合わせ調査の一覧
    // -----------------------------------------------------

    await expect(
      page.getByText('関連する問い合わせ：2 件'),
    ).toBeVisible()

    const okRow = getRelatedInquiryRow(
      page,
      okRelationNumber,
    )

    const ngRow = getRelatedInquiryRow(
      page,
      ngRelationNumber,
    )

    await expect(
      page.locator('.related-inquiries-table tbody tr'),
    ).toHaveCount(2)

    // OK回答の関連情報
    await expect(okRow).toContainText(String(inquiryOk))

    await expect(
      okRow.locator('.related-status'),
    ).toHaveText('OK')

    await expect(okRow).toContainText('OK')

    // NG回答の関連情報
    await expect(ngRow).toContainText(String(inquiryNg))

    await expect(
      ngRow.locator('.related-status'),
    ).toHaveText('NG')

    await expect(ngRow).toContainText('NG')
  },
)
