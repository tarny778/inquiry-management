
import type {
  InquiryFilters,
  Inquiry,
} from '../../types'

type InquiryListProps = {
  user: {
    氏名: string
    職員番号: string
    所属: string
  } | null

  loading: boolean
  error: string
  setError: (error: string) => void

  inquiries: Inquiry[]
  total: number
  currentPage: number

  listDisplayMode: string
  listDescription: string
  appliedFilters: InquiryFilters

  loadInquiries: (pageNumber?: number) => Promise<boolean>
  fetchSearchResults: (
    filters: InquiryFilters,
    pageNumber?: number,
  ) => Promise<boolean>

  handleLogout: () => void
  openNewInquiry: () => void
  openInquiryDetail: (inquiryNumber: number) => void

  handleInitialConditionChange: (checked: boolean) => void
  initialCondition: boolean
  initialConditionDescription: string

  keyword: string
  setKeyword: (value: string) => void
  categoryFilter: string
  setCategoryFilter: (value: string) => void
  statusFilter: string
  setStatusFilter: (value: string) => void
  urgencyFilter: string
  setUrgencyFilter: (value: string) => void
  receptionistFilter: string
  setReceptionistFilter: (value: string) => void
  handlerFilter: string
  setHandlerFilter: (value: string) => void
  receivedFrom: string
  setReceivedFrom: (value: string) => void
  receivedTo: string
  setReceivedTo: (value: string) => void

  showAdvancedSearch: boolean
  setShowAdvancedSearch: (value: boolean) => void
  handleSearch: () => void
  clearSearch: () => void

  selectedNumbers: number[]
  setSelectedNumbers: (
    value: number[] | ((current: number[]) => number[]),
  ) => void
  actionMessage: string
  setActionMessage: (message: string) => void

  handleBulkAccept: () => Promise<void>
  handleBulkComplete: () => Promise<void>
  handleBulkLinkInvestigation: () => Promise<void>
  handleBulkCreateInvestigation: () => Promise<void>

  isLinkInvestigationDialogOpen: boolean
  setIsLinkInvestigationDialogOpen: (open: boolean) => void
  isCreateInvestigationDialogOpen: boolean
  setIsCreateInvestigationDialogOpen: (open: boolean) => void

  existingInvestigationNumber: string
  setExistingInvestigationNumber: (value: string) => void
  newInvestigationName: string
  setNewInvestigationName: (value: string) => void
}

export default function InquiryList({
  user,
  loading,
  error,
  setError,
  inquiries,
  total,
  currentPage,
  listDisplayMode,
  listDescription,
  appliedFilters,
  loadInquiries,
  fetchSearchResults,
  handleLogout,
  openNewInquiry,
  openInquiryDetail,
  handleInitialConditionChange,
  initialCondition,
  initialConditionDescription,
  keyword,
  setKeyword,
  categoryFilter,
  setCategoryFilter,
  statusFilter,
  setStatusFilter,
  urgencyFilter,
  setUrgencyFilter,
  receptionistFilter,
  setReceptionistFilter,
  handlerFilter,
  setHandlerFilter,
  receivedFrom,
  setReceivedFrom,
  receivedTo,
  setReceivedTo,
  showAdvancedSearch,
  setShowAdvancedSearch,
  handleSearch,
  clearSearch,
  selectedNumbers,
  setSelectedNumbers,
  actionMessage,
  setActionMessage,
  handleBulkAccept,
  handleBulkComplete,
  handleBulkLinkInvestigation,
  handleBulkCreateInvestigation,
  isLinkInvestigationDialogOpen,
  setIsLinkInvestigationDialogOpen,
  isCreateInvestigationDialogOpen,
  setIsCreateInvestigationDialogOpen,
  existingInvestigationNumber,
  setExistingInvestigationNumber,
  newInvestigationName,
  setNewInvestigationName,
}: InquiryListProps) {
  return (
    <div className="app">
      <header className="app-header">
        <h1>問い合わせ管理システム</h1>
        <span className="app-department">情報システム課</span>

        <div className="user-panel">
          {user && (
            <span>
              {user.氏名}（{user.職員番号}）
            </span>
          )}
          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
            disabled={loading}
          >
            ログアウト
          </button>
        </div>
      </header>

      <main className="main">
        <div className="list-header">
          <h2>問い合わせ一覧</h2>

          <span className="list-description">
            問い合わせを検索・確認できます。
          </span>

          {user?.所属 === '情報システム課' && (
            <button
              type="button"
              onClick={openNewInquiry}
              disabled={loading}
            >
              ＋ 新規登録
            </button>
          )}
        </div>

        {error && (
          <div className="modal-overlay">
            <section
              className="error-dialog"
              role="alertdialog"
              aria-modal="true"
              aria-labelledby="error-dialog-title"
              aria-describedby="error-dialog-message"
            >
              <h2 id="error-dialog-title">エラー</h2>

              <p id="error-dialog-message">
                {error}
              </p>

              <button
                type="button"
                onClick={() => setError('')}
                autoFocus
              >
                閉じる
              </button>
            </section>
          </div>
        )}

      
        <section className="search-section">
          <h3>検索条件</h3>

          <div className="initial-condition">
            <label>
              <input
                type="checkbox"
                checked={initialCondition}
                onChange={(event) =>
                  handleInitialConditionChange(event.target.checked)
                }
                disabled={loading}
              />
              初期条件
            </label>

            <span className="initial-condition-description">
              {initialCondition
                ? initialConditionDescription
                : '検索条件を指定して検索ボタンを押してください'}
            </span>
          </div>

          <fieldset
            className={`search-condition-fields ${
              initialCondition ? 'initial-condition-active' : ''
            }`}
            disabled={initialCondition || loading}
          >
            <div className="search-fields">
              <label className="search-subject">
                キーワード（件名）
                <input
                  type="text"
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                  placeholder="件名の一部を入力"
                />
              </label>

              <label className="search-category">
                問い合わせ分類
                <select
                  value={categoryFilter}
                  onChange={(event) => setCategoryFilter(event.target.value)}
                >
                  <option value="">すべて</option>
                  <option value="分類A">分類A</option>
                  <option value="分類B">分類B</option>
                  <option value="分類C">分類C</option>
                </select>
              </label>
              
              <label className="search-status">
                対応状態
                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                >
                  <option value="">すべて</option>
                  <option value="引き受け待ち">引き受け待ち</option>
                  <option value="対応中">対応中</option>
                  <option value="対応完了">対応完了</option>
                </select>
              </label>

            </div>

            <button
              type="button"
              className="advanced-search-toggle"
              aria-expanded={showAdvancedSearch}
              onClick={() => setShowAdvancedSearch(!showAdvancedSearch)}
            >
              {showAdvancedSearch ? '▼' : '▶'} 詳細検索
            </button>

            {showAdvancedSearch && (
              <div className="advanced-search-fields">
                <label className="advanced-urgency">
                  緊急度
                  <select
                    value={urgencyFilter}
                    onChange={(event) => setUrgencyFilter(event.target.value)}
                  >
                    <option value="">すべて</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                  </select>
                </label>

                <label className="advanced-receptionist">
                  受付担当者（職員番号）
                  <input
                    type="text"
                    value={receptionistFilter}
                    onChange={(event) =>
                      setReceptionistFilter(event.target.value)
                    }
                    placeholder="職員番号"
                  />
                </label>

                <label className="advanced-handler">
                  対応担当者（職員番号）
                  <input
                    type="text"
                    value={handlerFilter}
                    onChange={(event) => setHandlerFilter(event.target.value)}
                    placeholder="職員番号"
                  />
                </label>

                <label className="advanced-start-date">
                  受付日（開始）
                  <input
                    type="date"
                    value={receivedFrom}
                    onChange={(event) => setReceivedFrom(event.target.value)}
                  />
                </label>

                <label className="advanced-end-date">
                  受付日（終了）
                  <input
                    type="date"
                    value={receivedTo}
                    onChange={(event) => setReceivedTo(event.target.value)}
                  />
                </label>
              </div>
            )}
          </fieldset>

          <div className="search-buttons">
            <button
              type="button"
              onClick={handleSearch}
              disabled={initialCondition || loading}
            >
              {loading ? '検索中...' : '検索'}
            </button>

            <button
              type="button"
              className="clear-button"
              onClick={clearSearch}
              disabled={initialCondition || loading}
            >
              クリア
            </button>
          </div>
        </section>

          
        <section className="list-section">
          <div className="list-heading">
            <h3>問い合わせ一覧</h3>
            <p className="list-source">
              <strong>表示中の一覧：</strong>
              {listDescription}
            </p>
            <p className="list-count">
              表示中：{inquiries.length}件
              （全件数：{total}件、最大50件取得）
            </p>
          </div>

          <div className="bulk-toolbar">
            <span className="selected-count">
              選択中：{selectedNumbers.length}件
            </span>

            <div className="bulk-buttons">
              <button
                type="button"
                onClick={() => void handleBulkAccept()}
                disabled={selectedNumbers.length === 0 || loading}
              >
                {loading ? '処理中...' : '引き受け'}
              </button>

              
              <div className="bulk-investigation-actions">
                <button
                  type="button"
                  onClick={() => setIsLinkInvestigationDialogOpen(true)}
                  disabled={selectedNumbers.length === 0 || loading}
                >
                  既存の問題調査に関連付け
                </button>

                <button
                  type="button"
                  onClick={() => setIsCreateInvestigationDialogOpen(true)}
                  disabled={selectedNumbers.length === 0 || loading}
                >
                  新しい問題調査を作成・関連付け
                </button>
              </div>


              
              <button
                type="button"
                onClick={() => void handleBulkComplete()}
                disabled={selectedNumbers.length === 0 || loading}
              >
                {loading ? '処理中...' : '対応完了'}
              </button>

            </div>
          </div>

          {actionMessage && (
            <p className="action-message" role="status">
              {actionMessage}
            </p>
          )}

          {inquiries.length === 0 ? (
            <p>該当する問い合わせはありません。</p>
          ) : (
            <table className="inquiry-table">
              <colgroup>
                <col className="col-check" />
                <col className="col-number" />
                <col className="col-category" />
                <col className="col-subject" />
                <col className="col-urgency" />
                <col className="col-handler" />
                <col className="col-status" />
              </colgroup>

              <thead>
                <tr>
                  <th>
                    <input
                      type="checkbox"
                      aria-label="表示中の問い合わせをすべて選択"
                      checked={
                        inquiries.length > 0 &&
                        inquiries.every((item) =>
                          selectedNumbers.includes(item.問い合わせ番号)
                        )
                      }
                      onChange={(event) => {
                        const visibleNumbers = inquiries.map(
                          (item) => item.問い合わせ番号
                        )

                        setSelectedNumbers((current) =>
                          event.target.checked
                            ? Array.from(new Set([...current, ...visibleNumbers]))
                            : current.filter(
                                (number) => !visibleNumbers.includes(number)
                              )
                        )
                        setActionMessage('')
                      }}
                    />
                  </th>
                  <th>番号</th>
                  <th>分類</th>
                  <th>件名</th>
                  <th>緊急度</th>
                  <th>対応担当者</th>
                  <th>状態</th>
                </tr>
              </thead>

              <tbody>
                {inquiries.map((inquiry) => (
                  <tr key={inquiry.問い合わせ番号}>
                    <td className="check-cell">
                      <input
                        type="checkbox"
                        aria-label={`問い合わせ番号 ${inquiry.問い合わせ番号} を選択`}
                        checked={selectedNumbers.includes(
                          inquiry.問い合わせ番号
                        )}
                        onChange={(event) => {
                          setSelectedNumbers((current) =>
                            event.target.checked
                              ? [...current, inquiry.問い合わせ番号]
                              : current.filter(
                                  (number) =>
                                    number !== inquiry.問い合わせ番号
                                )
                          )
                          setActionMessage('')
                        }}
                      />
                    </td>

                    <td className="number-cell">
                      <button
                        type="button"
                        className="link-button"
                        onClick={() => openInquiryDetail(inquiry.問い合わせ番号)}
                        disabled={loading}
                      >
                        {inquiry.問い合わせ番号}
                      </button>
                    </td>

                    <td>{inquiry.問い合わせ分類 || '—'}</td>

                    <td className="subject-cell">
                      <button
                        type="button"
                        className="link-button"
                        onClick={() => openInquiryDetail(inquiry.問い合わせ番号)}
                        disabled={loading}
                      >
                        {inquiry.件名}
                      </button>
                    </td>

                    <td>
                      {inquiry.緊急度 == null
                        ? '—'
                        : inquiry.緊急度}
                    </td>

                    <td className="handler-cell">
                      {inquiry.対応担当者 || '未割当'}
                    </td>

                    <td>
                      <span
                        className={`status ${
                          inquiry.状態 === '引き受け待ち'
                            ? 'waiting'
                            : inquiry.状態 === '対応中'
                              ? 'in-progress'
                              : 'completed'
                        }`}
                      >
                        {inquiry.状態}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="pagination">
            <button
              type="button"
              onClick={async () => {
                const nextPage = currentPage - 1

                if (nextPage < 1 || loading) return

                setSelectedNumbers([])
                setActionMessage('')

                if (listDisplayMode === 'initial') {
                  await loadInquiries(nextPage)
                } else {
                  await fetchSearchResults(appliedFilters, nextPage)
                }
              }}
              disabled={currentPage <= 1 || loading}
            >
              前へ
            </button>

            <span>
              {currentPage} / {Math.max(1, Math.ceil(total / 50))} ページ
            </span>

            <button
              type="button"
              onClick={async () => {
                const nextPage = currentPage + 1
                const totalPages = Math.ceil(total / 50)

                if (nextPage > totalPages || loading) return

                setSelectedNumbers([])
                setActionMessage('')

                if (listDisplayMode === 'initial') {
                  await loadInquiries(nextPage)
                } else {
                  await fetchSearchResults(appliedFilters, nextPage)
                }
              }}
              disabled={
                currentPage >= Math.ceil(total / 50) || loading
              }
            >
              次へ
            </button>
          </div>
        </section>


      </main>
  
      {/* 既存の問題調査への関連付けダイアログ */}
      {isLinkInvestigationDialogOpen && (
        <div className="modal-overlay">
          <section
            className="input-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="link-investigation-title"
          >
            <h2 id="link-investigation-title">
              既存の問題調査に関連付け
            </h2>

            <label htmlFor="existing-investigation-number">
              問題調査番号
            </label>

            <input
              id="existing-investigation-number"
              type="number"
              min={1}
              step={1}
              value={existingInvestigationNumber}
              onChange={(event) =>
                setExistingInvestigationNumber(event.target.value)
              }
              placeholder="例：1"
              disabled={loading}
              autoFocus
            />

            <div className="dialog-actions">
              <button
                type="button"
                onClick={() => setIsLinkInvestigationDialogOpen(false)}
                disabled={loading}
              >
                キャンセル
              </button>

              <button
                type="button"
                onClick={async () => {
                  try {
                    await handleBulkLinkInvestigation()
                  } finally {
                    setIsLinkInvestigationDialogOpen(false)
                  }
                }}
                disabled={
                  selectedNumbers.length === 0 ||
                  loading ||
                  existingInvestigationNumber.trim() === '' ||
                  !Number.isInteger(Number(existingInvestigationNumber)) ||
                  Number(existingInvestigationNumber) < 1
                }
              >
                {loading ? '処理中...' : '関連付ける'}
              </button>
            </div>
          </section>
        </div>
      )}

      {/* 新しい問題調査の作成・関連付けダイアログ */}
      {isCreateInvestigationDialogOpen && (
        <div className="modal-overlay">
          <section
            className="input-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-investigation-title"
          >
            <h2 id="create-investigation-title">
              新しい問題調査を作成・関連付け
            </h2>

            <label htmlFor="new-investigation-name">
              問題調査の名称・仮説（30文字以内）
            </label>

            <input
              id="new-investigation-name"
              type="text"
              value={newInvestigationName}
              onChange={(event) =>
                setNewInvestigationName(event.target.value)
              }
              maxLength={30}
              placeholder="例：メール送信エラーの原因調査"
              disabled={loading}
              autoFocus
            />

            <div className="dialog-actions">
              <button
                type="button"
                onClick={() => setIsCreateInvestigationDialogOpen(false)}
                disabled={loading}
              >
                キャンセル
              </button>

              <button
                type="button"
                onClick={async () => {
                  try {
                    await handleBulkCreateInvestigation()
                  } finally {
                    setIsCreateInvestigationDialogOpen(false)
                  }
                }}
                disabled={
                  selectedNumbers.length === 0 ||
                  loading ||
                  !newInvestigationName.trim() ||
                  newInvestigationName.trim().length > 30
                }
              >
                {loading ? '処理中...' : '作成・関連付ける'}
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}
