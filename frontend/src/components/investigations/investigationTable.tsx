
import type { Investigation } from '../../types'

type InvestigationTableProps = {
  loading: boolean
  investigations: Investigation[]
  total: number
  currentPage: number
  onPreviousPage: () => void
  onNextPage: () => void
  onSelectInvestigation: (investigationNumber: number) => void
}

export default function InvestigationTable({
  loading,
  investigations,
  total,
  currentPage,
  onPreviousPage,
  onNextPage,
  onSelectInvestigation,
}: InvestigationTableProps) {
  return (
    <section className="list-section">
      <h3>調査一覧</h3>

      <p>検索結果：{total} 件</p>

      <table className="investigation-table">
        <colgroup>
          <col className="col-investigation-number" />
          <col className="col-investigation-name" />
          <col className="col-investigation-handler" />
          <col className="col-investigation-status" />
          <col className="col-my-inquiry" />
        </colgroup>

        <thead>
          <tr>
            <th>番号</th>
            <th>調査の名称</th>
            <th>対応担当者</th>
            <th>状態</th>
            <th>自分の問い合わせ</th>
          </tr>
        </thead>

        <tbody>
          {investigations.length === 0 ? (
            <tr>
              <td colSpan={5}>
                {loading
                  ? '検索中...'
                  : '該当する調査はありません。'}
              </td>
            </tr>
          ) : (
            investigations.map((investigation) => {
              const statusInfo = {
                1: {
                  label: '調査中',
                  className: 'investigating',
                },
                2: {
                  label: 'リアクション要求済み',
                  className: 'reaction-requested',
                },
                3: {
                  label: '断念',
                  className: 'abandoned',
                },
              }[investigation.調査状態] ?? {
                label: '不明',
                className: 'unknown',
              }

              return (
                <tr key={investigation.調査番号}>
                  <td className="investigation-number-cell">
                    <button
                      type="button"
                      className="link-button"
                      onClick={() =>
                        onSelectInvestigation(
                          investigation.調査番号,
                        )
                      }
                      disabled={loading}
                    >
                      {investigation.調査番号}
                    </button>
                  </td>

                  <td className="investigation-name-cell">
                    <button
                      type="button"
                      className="link-button"
                      onClick={() =>
                        onSelectInvestigation(
                          investigation.調査番号,
                        )
                      }
                      disabled={loading}
                    >
                      {investigation.調査の名称}
                    </button>
                  </td>

                  <td className="investigation-handler-cell">
                    {investigation.対応担当者職員番号 ?? '未設定'}
                  </td>

                  <td>
                    <span
                      className={`status ${statusInfo.className}`}
                    >
                      {statusInfo.label}
                    </span>
                  </td>

                  <td className="my-inquiry-cell">
                    {investigation.自分の問い合わせを含む
                      ? 'あり'
                      : 'なし'}
                  </td>
                </tr>
              )
            })
          )}
        </tbody>
      </table>

      <div className="pagination">
        <button
          type="button"
          onClick={onPreviousPage}
          disabled={currentPage <= 1 || loading}
        >
          前へ
        </button>

        <span>
          {currentPage} / {Math.max(1, Math.ceil(total / 50))} ページ
        </span>

        <button
          type="button"
          onClick={onNextPage}
          disabled={
            currentPage >= Math.ceil(total / 50) || loading
          }
        >
          次へ
        </button>
      </div>
    </section>
  )
}
