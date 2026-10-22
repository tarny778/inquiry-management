

type InquirySearchProps = {
  loading: boolean
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
}

export default function InquirySearch({
  loading,
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
}: InquirySearchProps) {
  return (
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
  )
}
