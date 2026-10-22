import InquirySearch  from './InquirySearch'

import type {
  InquiryFilters,
  Inquiry,
} from '../../types'
import InquiryTable from './InquiryTable'

type InquiryListPageProps = {
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

export default function InquiryListPage({
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
}: InquiryListPageProps) {
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

        // 検索セクション
        <InquirySearch
          loading={loading}
          handleInitialConditionChange={handleInitialConditionChange}
          initialCondition={initialCondition}
          initialConditionDescription={initialConditionDescription}
          keyword={keyword}
          setKeyword={setKeyword}
          categoryFilter={categoryFilter}
          setCategoryFilter={setCategoryFilter}
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          urgencyFilter={urgencyFilter}
          setUrgencyFilter={setUrgencyFilter}
          receptionistFilter={receptionistFilter}
          setReceptionistFilter={setReceptionistFilter}
          handlerFilter={handlerFilter}
          setHandlerFilter={setHandlerFilter}
          receivedFrom={receivedFrom}
          setReceivedFrom={setReceivedFrom}
          receivedTo={receivedTo}
          setReceivedTo={setReceivedTo}
          showAdvancedSearch={showAdvancedSearch}
          setShowAdvancedSearch={setShowAdvancedSearch}
          handleSearch={handleSearch}
          clearSearch={clearSearch}
        />

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

          <InquiryTable
            loading={loading}
            inquiries={inquiries}
            selectedNumbers={selectedNumbers}
            setSelectedNumbers={setSelectedNumbers}
            openInquiryDetail={openInquiryDetail}
            actionMessage={actionMessage}
            setActionMessage={setActionMessage}
          />

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
