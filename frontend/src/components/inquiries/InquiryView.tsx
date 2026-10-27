
import PageHeader from '../PageHeader'
import type { InquiryDetail, InquiryFilters, ScreenMode } from '../../types'

type InquiryViewProps = {
  user: {
    氏名: string
    職員番号: string
    所属: string
  } | null
  selectedInquiry: InquiryDetail
  setSelectedInquiry: (inquiry: InquiryDetail | null) => void
  setScreenMode: (mode: ScreenMode) => void
  loading: boolean
  setLoading: (loading: boolean) => void
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
}

const receptionHandlingLabels: Record<string, string> = {
  '1': '即時解決',
  '2': '要調査',
  '3': '他部署へ引き継ぎ',
}


export default function InquiryView({
  user,
  selectedInquiry,
  setSelectedInquiry,
  setScreenMode,
  loading,
  setLoading,
  error,
  refreshCurrentInquiryList,
  openInquiryEdit,
  handleAcceptInquiry,
  handleCompleteInquiry,
  handleReopenInquiry,
}: InquiryViewProps) {
  const canEditInquiry =
    (selectedInquiry.状態 === '引き受け待ち' &&
        selectedInquiry.受付担当者 === user?.職員番号) ||
    (selectedInquiry.状態 === '対応中' &&
        selectedInquiry.対応担当者 === user?.職員番号)
  const canAcceptInq =
    selectedInquiry.状態 === '引き受け待ち' &&
        user?.所属 === '情報システム課'
  const canCompleteInq =
    selectedInquiry.状態 === '対応中' &&
        user?.職員番号 === selectedInquiry.対応担当者
  const canReopenInq =
    selectedInquiry.状態 === '対応完了' &&
        user?.職員番号 === selectedInquiry.対応担当者
  return (
    // ここから下は、今ある JSX を残す
    <div className="app">

        <main className="main">
        
        <PageHeader
            section="問い合わせ"
            title="問い合わせ詳細"
            actions={
                <>
                {user?.所属 === '情報システム課' && (
                    <button
                        className="button-primary"
                        type="button"
                        onClick={openInquiryEdit}
                        disabled={loading || !canEditInquiry}
                    >
                        編集
                    </button>
                )}
                {user?.所属 === '情報システム課' && (
                    <button
                        className="button-primary"
                        type="button"
                        onClick={() =>
                        handleAcceptInquiry(selectedInquiry.問い合わせ番号)
                        }
                        disabled={loading || !canAcceptInq}
                    >
                        {loading ? '処理中...' : '引き受け'}
                    </button>
                )}
                {user?.所属 === '情報システム課' && (
                    <button
                        className="button-primary"
                        type="button"
                        onClick={() =>
                        handleCompleteInquiry(selectedInquiry.問い合わせ番号)
                        }
                        disabled={loading || !canCompleteInq}
                    >
                        {loading ? '処理中...' : '対応完了'}
                    </button>
                )}
                {user?.所属 === '情報システム課' && (
                    <button
                        className="button-primary"
                        type="button"
                        onClick={() =>
                        handleReopenInquiry(selectedInquiry.問い合わせ番号)
                        }
                        disabled={loading || !canReopenInq}
                    >
                        {loading ? '処理中...' : '再開'}
                    </button>
                )}
                <button
                    className="button-secondary"
                    type="button"
                    onClick={async () => {
                        setLoading(true)

                        try {
                        await refreshCurrentInquiryList()
                        setSelectedInquiry(null)
                        setScreenMode('list')
                        } finally {
                        setLoading(false)
                        }
                    }}
                    disabled={loading}
                    >
                    ↑ 一覧に戻る
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
              <div className="inquiry-detail-item inquiry-detail-full">
                <dt>件名</dt>
                <dd>{selectedInquiry.件名}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>問い合わせ分類</dt>
                <dd>{selectedInquiry.問い合わせ分類 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>緊急度</dt>
                <dd>{selectedInquiry.緊急度 ?? '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>受付経路</dt>
                <dd>{selectedInquiry.受付経路 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>受信日時</dt>
                <dd>{selectedInquiry.受信日時 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>問い合わせ職員番号</dt>
                <dd>{selectedInquiry.問い合わせ職員番号 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>問い合わせ当時の所属</dt>
                <dd>{selectedInquiry.問い合わせ当時の所属 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>受付担当者</dt>
                <dd>{selectedInquiry.受付担当者 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>登録日時</dt>
                <dd>{selectedInquiry.登録日時 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>受付時の処理</dt>
                <dd>
                  {selectedInquiry.受付時の処理 !== null
                    ? receptionHandlingLabels[selectedInquiry.受付時の処理] ??
                      selectedInquiry.受付時の処理
                    : '—'}
                </dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>状態</dt>
                <dd>{selectedInquiry.状態}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>対応担当者</dt>
                <dd>{selectedInquiry.対応担当者 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>引き受け日時</dt>
                <dd>{selectedInquiry.引き受け日時 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>関連する調査番号</dt>
                <dd>
                  {selectedInquiry.関連する調査番号一覧.length > 0
                    ? selectedInquiry.関連する調査番号一覧.join('、')
                    : 'なし'}
                </dd>
              </div>

              <div className="inquiry-detail-item">
                <dt>対応完了日時</dt>
                <dd>{selectedInquiry.対応完了日時 || '—'}</dd>
              </div>

              <div className="inquiry-detail-item inquiry-detail-full">
                <dt>問い合わせ詳細</dt>
                <dd>{selectedInquiry.問い合わせ詳細 || '—'}</dd>
              </div>
            </dl>

        </section>
        </main>
    </div>
  )
}