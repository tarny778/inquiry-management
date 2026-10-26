
import AppHeader from '../AppHeader'
import PageHeader from '../PageHeader'
import type { InquiryDetail, InquiryFilters, ScreenMode } from '../../types'

type InquiryViewProps = {
  user: {
    氏名: string
    職員番号: string
  } | null
  selectedInquiry: InquiryDetail
  setSelectedInquiry: (inquiry: InquiryDetail | null) => void
  setScreenMode: (mode: ScreenMode) => void
  loading: boolean
  error: string
  listDisplayMode: string
  currentPage: number
  appliedFilters: InquiryFilters
  refreshCurrentInquiryList: () => Promise<boolean>
  loadInquiries: (pageNumber?: number) => Promise<boolean>
  fetchSearchResults: (
    filters: InquiryFilters,
    pageNumber?: number,
  ) => Promise<boolean>
  openInquiryEdit: () => void
  handleAcceptInquiry: (inquiryNumber: number) => void
  handleCompleteInquiry: (inquiryNumber: number) => void
  handleReopenInquiry: (inquiryNumber: number) => void
  onLogout: () => void
}




export default function InquiryView({
  user,
  selectedInquiry,
  setSelectedInquiry,
  setScreenMode,
  loading,
  error,
  refreshCurrentInquiryList,
  openInquiryEdit,
  handleAcceptInquiry,
  handleCompleteInquiry,
  handleReopenInquiry,
  onLogout,
}: InquiryViewProps) {
  return (
    // ここから下は、今ある JSX を残す
    <div className="app">
        <AppHeader
            user={user}
            onLogout={onLogout}
            loading={loading}
        />

        <main className="main">
        
        <PageHeader
            section="問い合わせ"
            title="問い合わせ詳細"
            actions={
                <>
                <button
                    type="button"
                    onClick={async () => {
                    await refreshCurrentInquiryList()
                    setSelectedInquiry(null)
                    setScreenMode('list')
                    }}
                    disabled={loading}
                >
                    一覧に戻る
                </button>

                <button
                    type="button"
                    onClick={openInquiryEdit}
                    disabled={loading || selectedInquiry.状態 === '対応完了'}
                >
                    編集
                </button>

                <button
                    type="button"
                    onClick={() =>
                    handleAcceptInquiry(selectedInquiry.問い合わせ番号)
                    }
                    disabled={loading || selectedInquiry.状態 !== '引き受け待ち'}
                >
                    {loading ? '処理中...' : '引き受け'}
                </button>

                <button
                    type="button"
                    onClick={() =>
                    handleCompleteInquiry(selectedInquiry.問い合わせ番号)
                    }
                    disabled={loading || selectedInquiry.状態 !== '対応中'}
                >
                    {loading ? '処理中...' : '対応完了'}
                </button>

                <button
                    type="button"
                    onClick={() =>
                    handleReopenInquiry(selectedInquiry.問い合わせ番号)
                    }
                    disabled={loading || selectedInquiry.状態 !== '対応完了'}
                >
                    {loading ? '処理中...' : '再開'}
                </button>
                </>
            }
        />

        {error && (
            <p className="error-message" role="alert">
            {error}
            </p>
        )}

        <section className="list-section">
            <h3>
            問い合わせ番号：{selectedInquiry.問い合わせ番号}
            </h3>

            <dl className="inquiry-detail">
            <dt>状態</dt>
            <dd>{selectedInquiry.状態}</dd>

            <dt>件名</dt>
            <dd>{selectedInquiry.件名}</dd>

            <dt>問い合わせ職員番号</dt>
            <dd>{selectedInquiry.問い合わせ職員番号 || '—'}</dd>

            <dt>問い合わせ当時の所属</dt>
            <dd>{selectedInquiry.問い合わせ当時の所属 || '—'}</dd>

            <dt>受付経路</dt>
            <dd>{selectedInquiry.受付経路 || '—'}</dd>

            <dt>問い合わせ分類</dt>
            <dd>{selectedInquiry.問い合わせ分類 || '—'}</dd>

            <dt>緊急度</dt>
            <dd>{selectedInquiry.緊急度 ?? '—'}</dd>

            <dt>受付時の処理</dt>
            <dd>{selectedInquiry.受付時の処理 || '—'}</dd>

            <dt>問い合わせ詳細</dt>
            <dd>{selectedInquiry.問い合わせ詳細 || '—'}</dd>

            <dt>受付担当者</dt>
            <dd>{selectedInquiry.受付担当者 || '—'}</dd>

            <dt>対応担当者</dt>
            <dd>{selectedInquiry.対応担当者 || '—'}</dd>

            <dt>受信日時</dt>
            <dd>{selectedInquiry.受信日時 || '—'}</dd>

            <dt>登録日時</dt>
            <dd>{selectedInquiry.登録日時 || '—'}</dd>

            <dt>引き受け日時</dt>
            <dd>{selectedInquiry.引き受け日時 || '—'}</dd>

            <dt>対応完了日時</dt>
            <dd>{selectedInquiry.対応完了日時 || '—'}</dd>

            <dt>関連する調査番号</dt>
            <dd>
                {selectedInquiry.関連する調査番号一覧.length > 0
                ? selectedInquiry.関連する調査番号一覧.join('、')
                : 'なし'}
            </dd>
            </dl>
        </section>
        </main>
    </div>
  )
}