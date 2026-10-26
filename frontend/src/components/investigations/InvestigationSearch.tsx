
type InvestigationSearchProps = {
  loading: boolean
  // 検索条件
  investigationNumber: string
  setInvestigationNumber: (value: string) => void

  inquiryNumber: string
  setInquiryNumber: (value: string) => void

  requesterStaffNumber: string
  setRequesterStaffNumber: (value: string) => void

  handlerStaffNumber: string
  setHandlerStaffNumber: (value: string) => void

  inquiryStatus: string
  setInquiryStatus: (value: string) => void

  investigationStatus: string
  setInvestigationStatus: (value: string) => void

  keyword: string
  setKeyword: (value: string) => void

  // 検索操作
  handleSearch: () => void
  clearSearch: () => void
  onApplyInitialCondition: () => void
}

export default function InvestigationSearch({
  loading,
  investigationNumber,
  setInvestigationNumber,
  inquiryNumber,
  setInquiryNumber,
  requesterStaffNumber,
  setRequesterStaffNumber,
  handlerStaffNumber,
  setHandlerStaffNumber,
  inquiryStatus,
  setInquiryStatus,
  investigationStatus,
  setInvestigationStatus,
  keyword,
  setKeyword,
  handleSearch,
  clearSearch,
  onApplyInitialCondition,
}: InvestigationSearchProps) {
  return (
    <section className="search-section">
        <h3>検索条件</h3>

        <p>検索条件を指定して検索ボタンを押してください。</p>

        <div className="search-fields">
        <label className="search-subject">
            名称や仮説
            <input
            type="text"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="名称や仮説の一部を入力"
            />
        </label>

        <label>
            調査番号
            <input
            type="number"
            min="1"
            value={investigationNumber}
            onChange={(event) =>
                setInvestigationNumber(event.target.value)
            }
            placeholder="調査番号"
            />
        </label>

        <label>
            調査状態
            <select
            value={investigationStatus}
            onChange={(event) =>
                setInvestigationStatus(event.target.value)
            }
            >
            <option value="">すべて</option>
            <option value="1">調査中</option>
            <option value="2">リアクション要求済み</option>
            <option value="3">調査断念</option>
            </select>
        </label>

        <label>
            問い合わせ番号
            <input
            type="number"
            min="1"
            value={inquiryNumber}
            onChange={(event) => setInquiryNumber(event.target.value)}
            placeholder="問い合わせ番号"
            />
        </label>

        <label>
            問い合わせ者（職員番号）
            <input
            type="text"
            value={requesterStaffNumber}
            onChange={(event) =>
                setRequesterStaffNumber(event.target.value)
            }
            placeholder="職員番号"
            />
        </label>

        <label>
            対応担当者（職員番号）
            <input
            type="text"
            value={handlerStaffNumber}
            onChange={(event) =>
                setHandlerStaffNumber(event.target.value)
            }
            placeholder="職員番号"
            />
        </label>

        <label>
            問い合わせ状態
            <select
            value={inquiryStatus}
            onChange={(event) => setInquiryStatus(event.target.value)}
            >
            <option value="">すべて</option>
            <option value="引き受け待ち">引き受け待ち</option>
            <option value="対応中">対応中</option>
            <option value="対応完了">対応完了</option>
            </select>
        </label>
        </div>

        <div className="search-buttons">
        <button
            className="button-secondary"
            type="button"
            onClick={onApplyInitialCondition}
            disabled={loading}
        >
            初期条件
        </button>

        <button
            className="button-primary"
            type="button"
            onClick={handleSearch}
            disabled={loading}
        >
            {loading ? '検索中...' : '検索'}
        </button>

        <button
            type="button"
            className="button-secondary"
            onClick={clearSearch}
            disabled={loading}
        >
            クリア
        </button>
        </div>
    </section>
  )
}
