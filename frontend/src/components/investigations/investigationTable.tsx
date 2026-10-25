
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
      <h3>問題調査一覧</h3>

      <p>検索結果：{total} 件</p>

      <table>
        <thead>
          <tr>
            <th>問題調査番号</th>
            <th>名称や仮説</th>
            <th>問題調査状態</th>
            <th>対応担当者</th>
            <th>関連問い合わせ件数</th>
            <th>自分の問い合わせ</th>
          </tr>
        </thead>

        <tbody>
          {investigations.length === 0 ? (
            <tr>
              <td colSpan={6}>
                {loading
                  ? '検索中...'
                  : '該当する問題調査はありません。'}
              </td>
            </tr>
          ) : (
            investigations.map((investigation) => (
              <tr key={investigation.問題調査番号}>
                <td>
                  <button
                    type="button"
                    onClick={() =>
                      onSelectInvestigation(investigation.問題調査番号)
                    }
                  >
                    {investigation.問題調査番号}
                  </button>
                </td>
                <td>
                  <button
                    type="button"
                    onClick={() =>
                      onSelectInvestigation(investigation.問題調査番号)
                    }
                  >
                    {investigation.問題調査の名称や仮説}
                  </button>
                </td>
                <td>
                  {{
                    1: '調査中',
                    2: 'リアクション要求済み',
                    3: '調査断念',
                  }[investigation.問題調査状態] ?? '不明'}
                </td>
                <td>
                  {investigation.対応担当者職員氏名 ?? '未設定'}
                </td>
                <td>{investigation.関連問い合わせ件数}</td>
                <td>
                  {investigation.自分の問い合わせを含む
                    ? 'あり'
                    : 'なし'}
                  </td>
                </tr>
              ))
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
