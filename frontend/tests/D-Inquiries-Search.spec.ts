
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

// 件名を指定して一覧に存在する行を取得する
function getInquiryRow(page: Page, subject: string) {
  return page.locator('.inquiry-table tbody tr').filter({
    has: page.getByRole('button', {
      name: subject,
      exact: true,
    }),
  })
}

// 検索ボタンを押す
async function executeSearch(page: Page) {
  await page.getByRole('button', {
    name: '検索',
    exact: true,
  }).click()
}

// 初期条件を解除する
async function disableInitialCondition(page: Page) {
  await page.getByRole('checkbox', {
    name: '初期条件',
  }).uncheck()
}

// D-01 初期条件の適用
test(
  'D-01 情シス職員と一般職員で初期条件に合った問い合わせが表示される',
  async ({ page, db }) => {
    // 情シス職員J0001が対応中
    await createInquiry(db, {
      件名: 'E2E-D01-J0001-対応中',
      問い合わせ職員番号: 'T0001',
      対応担当者: 'J0001',
      引き受け日時: new Date(),
    })

    // 情シス職員J0002が対応中
    await createInquiry(db, {
      件名: 'E2E-D01-J0002-対応中',
      問い合わせ職員番号: 'T0001',
      対応担当者: 'J0002',
      引き受け日時: new Date(),
    })

    // J0002が登録した引き受け待ち
    await createInquiry(db, {
      件名: 'E2E-D01-J0002-引き受け待ち',
      問い合わせ職員番号: 'J0002',
    })

    // 一般職員T0001が登録した引き受け待ち
    await createInquiry(db, {
      件名: 'E2E-D01-T0001-引き受け待ち',
      問い合わせ職員番号: 'T0001',
    })

    // 一般職員T0001が登録した対応中
    await createInquiry(db, {
      件名: 'E2E-D01-T0001-対応中',
      問い合わせ職員番号: 'T0001',
      対応担当者: 'J0001',
      引き受け日時: new Date(),
    })

    // 一般職員T0001が登録した対応完了
    await createInquiry(db, {
      件名: 'E2E-D01-T0001-対応完了',
      問い合わせ職員番号: 'T0001',
      対応担当者: 'J0001',
      引き受け日時: new Date(),
      対応完了日時: new Date(),
    })

    // 情報システム課職員としてログイン
    await loginAsJ0001(page)

    // 初期条件が有効である
    await expect(
      page.getByRole('checkbox', {
        name: '初期条件',
      }),
    ).toBeChecked()

    // 情シス職員：
    // 全職員の引き受け待ち ＋ 自分が担当する対応中
    await expect(
      getInquiryRow(page, 'E2E-D01-J0001-対応中'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D01-J0002-引き受け待ち'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D01-T0001-引き受け待ち'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D01-J0002-対応中'),
    ).toHaveCount(0)

    await expect(
      getInquiryRow(page, 'E2E-D01-T0001-対応中'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D01-T0001-対応完了'),
    ).toHaveCount(0)

    // ログアウトして一般職員に切り替える
    await page.getByRole('button', {
      name: 'ログアウト',
    }).click()

    await loginAsT0001(page)

    // 一般職員：
    // 自分が問い合わせたもののうち、対応完了前
    await expect(
      getInquiryRow(page, 'E2E-D01-T0001-引き受け待ち'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D01-T0001-対応中'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D01-T0001-対応完了'),
    ).toHaveCount(0)

    await expect(
      getInquiryRow(page, 'E2E-D01-J0001-対応中'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D01-J0002-対応中'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D01-J0002-引き受け待ち'),
    ).toHaveCount(0)
  },
)


// D-02 初期条件の解除
test(
  'D-02 初期条件を解除して通常検索に切り替えられる',
  async ({ page, db }) => {
    await createInquiry(db, {
      件名: 'E2E-D02-他職員の問い合わせ',
      問い合わせ職員番号: 'J0002',
    })

    await loginAsT0001(page)

    // 初期条件が有効で、他職員の引き受け待ちは表示されない
    await expect(
      getInquiryRow(page, 'E2E-D02-他職員の問い合わせ'),
    ).toHaveCount(0)

    // 初期条件を解除する
    await disableInitialCondition(page)

    // チェックが外れ、検索条件を入力できる
    await expect(
      page.getByRole('checkbox', {
        name: '初期条件',
      }),
    ).not.toBeChecked()

    await expect(
      page.getByRole('textbox', {
        name: 'キーワード（件名）',
      }),
    ).toBeEnabled()

    await expect(
      page.getByRole('button', {
        name: '検索',
        exact: true,
      }),
    ).toBeEnabled()

    // 通常検索を実行する
    await page.getByRole('textbox', {
      name: 'キーワード（件名）',
    }).fill('E2E-D02-')

    await executeSearch(page)

    await expect(
      getInquiryRow(page, 'E2E-D02-他職員の問い合わせ'),
    ).toHaveCount(1)
  },
)


// D-03 キーワード検索
test(
  'D-03 件名のキーワードで問い合わせを検索できる',
  async ({ page, db }) => {
    await createInquiry(db, {
      件名: 'E2E-D03-ネットワーク障害',
    })

    await createInquiry(db, {
      件名: 'E2E-D03-プリンター障害',
    })

    await createInquiry(db, {
      件名: 'E2E-D03-アカウント登録',
    })

    await loginAsJ0001(page)
    await disableInitialCondition(page)

    // 件名の一部を入力
    await page.getByRole('textbox', {
      name: 'キーワード（件名）',
    }).fill('障害')

    await executeSearch(page)

    // 該当する2件が表示される
    await expect(
      getInquiryRow(page, 'E2E-D03-ネットワーク障害'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D03-プリンター障害'),
    ).toHaveCount(1)

    // 該当しない問い合わせは表示されない
    await expect(
      getInquiryRow(page, 'E2E-D03-アカウント登録'),
    ).toHaveCount(0)

    await expect(
      page.locator('.list-count'),
    ).toContainText('全件数：2件')
  },
)


// D-04 複数条件検索
test(
  'D-04 複数の検索条件を組み合わせて問い合わせを検索できる',
  async ({ page, db }) => {
    // すべての条件に一致する問い合わせ
    await createInquiry(db, {
      件名: 'E2E-D04-ネットワーク障害',
      問い合わせ分類: '分類A',
      緊急度: 1,
      対応担当者: 'J0001',
      引き受け日時: new Date(),
    })

    // 件名は一致するが分類が異なる
    await createInquiry(db, {
      件名: 'E2E-D04-ネットワーク障害',
      問い合わせ分類: '分類B',
      緊急度: 1,
      対応担当者: 'J0001',
      引き受け日時: new Date(),
    })

    // 件名・分類は一致するが緊急度が異なる
    await createInquiry(db, {
      件名: 'E2E-D04-ネットワーク障害',
      問い合わせ分類: '分類A',
      緊急度: 2,
      対応担当者: 'J0001',
      引き受け日時: new Date(),
    })

    // 件名・分類・緊急度は一致するが状態が異なる
    await createInquiry(db, {
      件名: 'E2E-D04-ネットワーク障害',
      問い合わせ分類: '分類A',
      緊急度: 1,
    })

    await loginAsJ0001(page)
    await disableInitialCondition(page)

    // 件名
    await page.getByRole('textbox', {
      name: 'キーワード（件名）',
    }).fill('ネットワーク')

    // 分類
    await page.getByLabel('問い合わせ分類').selectOption('分類A')

    // 対応状態
    await page.getByLabel('対応状態').selectOption('対応中')

    // 詳細検索を開く
    await page.getByRole('button', {
      name: /詳細検索/,
    }).click()

    // 緊急度
    await page.getByLabel('緊急度').selectOption('1')

    await executeSearch(page)

    // すべての条件に一致する1件だけが表示される
    await expect(
      getInquiryRow(page, 'E2E-D04-ネットワーク障害'),
    ).toHaveCount(1)

    await expect(
      page.locator('.list-count'),
    ).toContainText('全件数：1件')
  },
)


// D-05 検索条件のクリア
test(
  'D-05 検索条件をクリアして再検索できる',
  async ({ page, db }) => {
    await createInquiry(db, {
      件名: 'E2E-D05-問い合わせA',
      問い合わせ分類: '分類A',
    })

    await createInquiry(db, {
      件名: 'E2E-D05-問い合わせB',
      問い合わせ分類: '分類B',
    })

    await createInquiry(db, {
      件名: 'E2E-D05-問い合わせC',
      問い合わせ分類: '分類C',
    })

    await loginAsJ0001(page)
    await disableInitialCondition(page)

    // 検索条件を入力する
    await page.getByRole('textbox', {
      name: 'キーワード（件名）',
    }).fill('問い合わせA')

    await page.getByLabel('問い合わせ分類').selectOption('分類A')

    await executeSearch(page)

    // 検索結果は1件
    await expect(
      page.locator('.list-count'),
    ).toContainText('全件数：1件')

    // 検索条件をクリアする
    await page.getByRole('button', {
      name: 'クリア',
    }).click()

    // 入力条件が初期値に戻る
    await expect(
      page.getByRole('textbox', {
        name: 'キーワード（件名）',
      }),
    ).toHaveValue('')

    await expect(
      page.getByLabel('問い合わせ分類'),
    ).toHaveValue('')

    await expect(
      page.getByLabel('対応状態'),
    ).toHaveValue('')

    // クリア後に再検索する
    await executeSearch(page)

    // 全件が検索結果に表示される
    await expect(
      page.locator('.list-count'),
    ).toContainText('全件数：3件')

    await expect(
      getInquiryRow(page, 'E2E-D05-問い合わせA'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D05-問い合わせB'),
    ).toHaveCount(1)

    await expect(
      getInquiryRow(page, 'E2E-D05-問い合わせC'),
    ).toHaveCount(1)
  },
)


// D-06 ページング
test(
  'D-06 50件を超える問い合わせをページ切り替えできる',
  async ({ page, db }) => {
    // 51件の問い合わせを作成する
    for (let i = 1; i <= 51; i++) {
      await createInquiry(db, {
        件名: `E2E-D06-ページング-${String(i).padStart(2, '0')}`,
        問い合わせ職員番号: 'T0001',
        受信日時: new Date(
          Date.UTC(2026, 0, 1, 0, 0, i),
        ),
      })
    }

    await loginAsJ0001(page)

    // 初期条件を解除し、全件を検索する
    await disableInitialCondition(page)
    await executeSearch(page)

    // 全件数は51件、1ページ目には50件表示される
    await expect(
      page.locator('.list-count'),
    ).toContainText('全件数：51件')

    await expect(
      page.locator('.inquiry-table tbody tr'),
    ).toHaveCount(50)

    await expect(
      page.locator('.pagination'),
    ).toContainText('1 / 2 ページ')

    // 次のページへ移動
    const nextButton = page.getByRole('button', {
      name: '次へ',
    })

    await expect(nextButton).toBeEnabled()
    await nextButton.click()

    // 2ページ目には残り1件が表示される
    await expect(
      page.locator('.pagination'),
    ).toContainText('2 / 2 ページ')

    await expect(
      page.locator('.inquiry-table tbody tr'),
    ).toHaveCount(1)

    // 前のページへ戻る
    await page.getByRole('button', {
      name: '前へ',
    }).click()

    await expect(
      page.locator('.pagination'),
    ).toContainText('1 / 2 ページ')

    await expect(
      page.locator('.inquiry-table tbody tr'),
    ).toHaveCount(50)
  },
)
