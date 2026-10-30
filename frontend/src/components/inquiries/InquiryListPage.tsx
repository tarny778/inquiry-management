import type {
  Inquiry,
} from '../../types'

import PageHeader from '../PageHeader'
import InquirySearch  from './InquirySearch'
import InquiryTable from './InquiryTable'
import InquiryBulkAction from './InquiryBulkAction'
import InvestigationDailog from './InvestigationDialog'

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
  listDescription: string

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

  onOpenInvestigations: () => void
  handlePageChange: (nextPage: number) => void
}

export default function InquiryListPage({
  user,
  loading,
  error,
  setError,
  inquiries,
  total,
  currentPage,
  listDescription,
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
  onOpenInvestigations,
  handlePageChange,
}: InquiryListPageProps) {
  return (
    <div className="app">

      <main className="main">
        <PageHeader
          section="問い合わせ"
          title="問い合わせ一覧"
          actions={
            <>
              {user?.所属 === '情報システム課' && (
                <button
                  className="button-primary"
                  type="button"
                  onClick={openNewInquiry}
                  disabled={loading}
                >
                  ＋ 新規登録
                </button>
              )}

              <button
                className="button-secondary"
                type="button"
                onClick={onOpenInvestigations}
                disabled={loading}
              >
                調査一覧へ →
              </button>
            </>
          }
        />
        <p className="list-description">
          問い合わせを検索・確認できます。
        </p>

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

        {/*検索セクション*/}
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
          
          {/* 一括操作*/}
          <InquiryBulkAction
            loading={loading}
            user={user}
            selectedNumbers={selectedNumbers}
            handleBulkAccept={handleBulkAccept}
            handleBulkComplete={handleBulkComplete}
            setIsLinkInvestigationDialogOpen={setIsLinkInvestigationDialogOpen}
            setIsCreateInvestigationDialogOpen={setIsCreateInvestigationDialogOpen}
          />

          {/* テーブル部分 */}
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
              onClick={() => handlePageChange(currentPage-1)}
              disabled={currentPage <= 1 || loading}
            >
              前へ
            </button>

            <span>
              {currentPage} / {Math.max(1, Math.ceil(total / 50))} ページ
            </span>

            <button
              type="button"
              onClick={() => handlePageChange(currentPage+1)}
              disabled={currentPage >= (Math.max(1, Math.ceil(total / 50))) || loading}
            >
              次へ
            </button>
          </div>
        </section>


      </main>
      {/*関連付けダイアログ */}
      <InvestigationDailog
        loading={loading}
        selectedNumbers={selectedNumbers}
        handleBulkLinkInvestigation={handleBulkLinkInvestigation}
        handleBulkCreateInvestigation={handleBulkCreateInvestigation}
        isLinkInvestigationDialogOpen={isLinkInvestigationDialogOpen}
        setIsLinkInvestigationDialogOpen={setIsLinkInvestigationDialogOpen}
        isCreateInvestigationDialogOpen={isCreateInvestigationDialogOpen}
        setIsCreateInvestigationDialogOpen={setIsCreateInvestigationDialogOpen}

        existingInvestigationNumber={existingInvestigationNumber}
        setExistingInvestigationNumber={setExistingInvestigationNumber}
        newInvestigationName={newInvestigationName}
        setNewInvestigationName={setNewInvestigationName}
      />
    </div>
  )
}
